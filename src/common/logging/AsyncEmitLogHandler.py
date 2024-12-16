import asyncio
from logging import Handler, getHandlerByName
from typing import Union, override


class AsyncEmitLogHandler(Handler):
    def __init__(self, handlers: list[Union[str, Handler]] = []):
        ## This hack doesn't work, '()' key is popped from the dict in the logging config but is never restored on failure thus on deffered call it searched for 'class' key which is empty and fails
        ## https://github.com/python/cpython/blob/46006a1b355f75d06c10e7b8086912c483b34487/Lib/logging/config.py#L617
        ## https://github.com/python/cpython/blob/46006a1b355f75d06c10e7b8086912c483b34487/Lib/logging/config.py#L786
        # try:
        #     for hn in handlers:
        #         if getHandlerByName(hn) is None:
        #             raise TypeError('Required handler %r '
        #                             'is not configured yet' % hn)
        # except Exception as e:
        #     raise ValueError('Unable to set required handler %r' % hn) from e
        super().__init__()
        self._handlers = handlers

    # Cache? premature optimization?
    @property
    def handlers(self):
        result = []
        for h in self._handlers:
            if isinstance(h, str):
                handler = getHandlerByName(h)
                if handler is not None:
                    result.append(handler)
            else:
                result.append(h)
        return result

    async def async_emit(self, record):
        for (
            h
        ) in self.handlers:  # order of execution of handlers is guaranteed by the order of the list
            h.handle(record)
            await asyncio.sleep(0)  # Leave current context, let other tasks run

    @override
    def emit(self, record):
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.async_emit(record))
        except RuntimeError as e:
            if "no running event loop" in str(e):  # no running event loop, emit synchronously
                for h in self.handlers:
                    h.handle(record)
            else:
                raise e
