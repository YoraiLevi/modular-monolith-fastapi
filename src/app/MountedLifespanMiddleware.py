#

from starlette.types import ASGIApp, Scope, Receive, Send
from starlette.routing import Mount, Host
from asyncio import Queue
from starlette.types import Message
import anyio
from starlette.applications import Starlette


class MountedLifespanMiddleware:
    """
    This middleware is used to ensure that the lifespan of mounted apps is properly managed.
    lifespan events in sub-applications #649
    https://github.com/encode/starlette/issues/649#issuecomment-2093538541
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "lifespan":
            queues: list[Queue[Message]] = []

            async def wrap_receive() -> Message:
                msg = await receive()
                async with anyio.create_task_group() as tasks:
                    for queue in queues:
                        tasks.start_soon(queue.put, msg)
                return msg

            async def wrap_send(message: Message) -> None:
                if message["type"] == "lifespan.startup.complete":
                    return
                await send(message)

            async with anyio.create_task_group() as tasks:
                app = scope.get("app")
                if isinstance(app, Starlette):
                    for r in app.routes:
                        if isinstance(r, Mount | Host):
                            queues.append(queue := Queue())
                            tasks.start_soon(r.app, scope, queue.get, wrap_send)

                await self.app(scope, wrap_receive, send)
                return

        await self.app(scope, receive, send)
