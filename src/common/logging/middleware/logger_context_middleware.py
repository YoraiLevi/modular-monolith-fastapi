from starlette.types import ASGIApp, Scope, Receive, Send

from ..getLogger import current_logger_ctx


class LoggerContextMiddleware:
    def __init__(self, app: ASGIApp, logger_name: str):
        self.app = app
        self.logger_name = logger_name

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # Set the service context for this request
        token = current_logger_ctx.set(self.logger_name)
        try:
            await self.app(scope, receive, send)
        finally:
            # Reset the context
            current_logger_ctx.reset(token)
