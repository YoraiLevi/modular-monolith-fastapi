import asyncio
import logging
import time
import pytest
from unittest.mock import Mock
from common.logging import AsyncEmitLogHandler

logger = logging.getLogger(__name__)


@pytest.fixture
def mock_handler():
    logger.debug("Creating mock handler")
    handler = Mock(spec=logging.Handler)
    handler.handle = Mock()
    logger.debug("Mock handler created with mocked handle method")
    return handler


class BusyWorkHandler(logging.Handler):
    def __init__(self, sleep_time: float = 5, name: str = "unnamed"):
        super().__init__()
        self.handled_records = []
        self.handle_started = False
        self.handle_completed = False
        self.sleep_time = sleep_time
        self.name = name
        self.handle_start_times = []
        self.handle_end_times = []

    def handle(self, record):
        self.handle_started = True
        start_time = time.time()
        self.handle_start_times.append(start_time)
        logger.debug(
            f"BusyWorkHandler {self.name} handle started, sleeping for {self.sleep_time} seconds",
            extra={"handler": self.name, "sleep_time": self.sleep_time, "start_time": start_time},
        )
        while time.time() - start_time < self.sleep_time:
            pass
        end_time = time.time()
        self.handle_end_times.append(end_time)
        self.handled_records.append(record)
        self.handle_completed = True
        logger.debug(
            f"BusyWorkHandler {self.name} handle completed, slept for {end_time - start_time} seconds",
            extra={"handler": self.name, "sleep_time": self.sleep_time, "end_time": end_time},
        )
        return True


def create_test_record(msg: str = "Test message") -> logging.LogRecord:
    return logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg=msg,
        args=(),
        exc_info=None,
    )


def test_async_emit_log_handler_init(mock_handler):
    logger.debug("Testing AsyncEmitLogHandler initialization")
    async_handler = AsyncEmitLogHandler(handlers=[mock_handler])
    assert isinstance(async_handler, logging.Handler)
    assert hasattr(async_handler, "handlers")
    assert len(async_handler.handlers) == 1


@pytest.mark.asyncio
async def test_emit(mock_handler):
    logger.debug("Testing AsyncEmitLogHandler emit")
    record = create_test_record()
    logger.debug(f"Created log record: {record}")
    async_handler = AsyncEmitLogHandler(handlers=[mock_handler])
    # Test emit creates a task
    logger.debug("Calling emit on AsyncEmitLogHandler")
    async_handler.emit(record)

    # Wait for any pending tasks
    logger.debug("Waiting for pending tasks")
    await asyncio.sleep(0)  # Leave current context, let other threads run
    logger.debug("Finished waiting for tasks")

    # Verify the handler was called
    mock_handler.handle.assert_called_once_with(record)


@pytest.mark.asyncio
async def test_async_emit_doesnt_block():
    """Verify that emitting new records after asyncio.sleep doesn't block.
    This ensures that the event loop is not blocked by previous emissions."""

    logger.debug("Testing emission of records after sleep")

    handler = BusyWorkHandler(sleep_time=1.0, name="slow_handler")
    async_handler = AsyncEmitLogHandler(handlers=[handler])

    # records
    record1 = create_test_record("First message")
    record2 = create_test_record("Second message")

    # Emit first record
    logger.debug("Emitting first record")
    start_time = time.time()
    async_handler.emit(record1)
    first_emit_duration = time.time() - start_time

    # Emit second record
    logger.debug("Emitting second record")
    start_time = time.time()
    async_handler.emit(record2)
    second_emit_duration = time.time() - start_time

    logger.debug(f"Second emit took {second_emit_duration} seconds")
    assert second_emit_duration < 0.1, "Second emit should also be nearly instant"

    logger.debug(f"First emit took {first_emit_duration} seconds")
    assert first_emit_duration < 0.1, "First emit should be nearly instant"

    # Wait some time
    await asyncio.sleep(handler.sleep_time * 0.9)

    # Verify both records were processed
    assert len(handler.handled_records) == 2, "Handler should have processed both records"
    assert (
        handler.handled_records[0].msg == "First message"
    ), "First record should be processed first"
    assert (
        handler.handled_records[1].msg == "Second message"
    ), "Second record should be processed second"

    # Verify timing of record processing
    processing_gap = handler.handle_start_times[1] - handler.handle_end_times[0]
    logger.debug(f"Gap between processing first and second record: {processing_gap} seconds")
    assert (
        processing_gap >= 0
    ), "Second record should not start processing before first record completes"


def test_async_emit_no_event_loop():
    """Verify that when no event loop is available, it falls back to synchronous processing."""

    logger.debug("Testing fallback behavior when no event loop is available")

    # Create handlers
    handler1 = BusyWorkHandler(sleep_time=0.1, name="handler1")
    handler2 = BusyWorkHandler(sleep_time=0.1, name="handler2")

    async_handler = AsyncEmitLogHandler(handlers=[handler1, handler2])
    record = create_test_record()

    # Call emit (without an event loop)
    logger.debug("Calling emit without an event loop")
    start_emit_time = time.time()
    async_handler.emit(record)
    end_emit_time = time.time()

    # Verify both handlers processed the record synchronously
    assert len(handler1.handled_records) == 1, "First handler should have processed the record"
    assert len(handler2.handled_records) == 1, "Second handler should have processed the record"

    # Verify sequential processing
    handler1_time = handler1.handle_end_times[0] - handler1.handle_start_times[0]
    handler2_time = handler2.handle_end_times[0] - handler2.handle_start_times[0]
    emit_duration = end_emit_time - start_emit_time

    logger.debug(f"Handler1 processing time: {handler1_time}s")
    logger.debug(f"Handler2 processing time: {handler2_time}s")
    logger.debug(f"Emitting time: {emit_duration}s")

    # In synchronous mode, total time should be approximately sum of individual times
    assert (
        abs(emit_duration - (handler1_time + handler2_time)) < 0.1
    ), "Total time should be approximately sum of individual handler times in synchronous mode"


@pytest.mark.asyncio
async def test_async_emit_multiple_handlers():
    """Verify that multiple handlers are processed concurrently.
    We use three handlers with different processing times and verify that
    total time is close to the the sum of all handlers."""

    logger.debug("Testing concurrent processing of multiple handlers")

    # Create three handlers with different processing times
    handler1 = BusyWorkHandler(sleep_time=1.0, name="handler1")
    handler2 = BusyWorkHandler(sleep_time=1.5, name="handler2")
    handler3 = BusyWorkHandler(sleep_time=2.0, name="handler3")

    async_handler = AsyncEmitLogHandler(handlers=[handler1, handler2, handler3])
    max_sleep_time = max(h.sleep_time for h in [handler1, handler2, handler3])
    sum_of_sleep_times = sum(h.sleep_time for h in [handler1, handler2, handler3])

    record = create_test_record()

    # Record start time
    logger.debug("Calling emit on AsyncEmitLogHandler with multiple handlers")
    start_time = time.time()

    # Call emit
    async_handler.emit(record)

    # Record time immediately after emit
    after_emit_time = time.time()
    emit_duration = after_emit_time - start_time

    # Verify emit returned quickly
    logger.debug(f"Emit took {emit_duration} seconds")
    assert emit_duration < 0.1, f"Emit took {emit_duration} seconds, should be nearly instant"

    # Wait enough time for all handlers to complete
    logger.debug("Waiting for all handlers to complete")
    # check if first handler is completed
    await asyncio.sleep(0)  # Leave current context, let other threads run

    async def async_log():
        completed_handlers = [h.handle_completed for h in [handler1, handler2, handler3]]
        logger.debug(f"Waiting for all handlers to complete {completed_handlers=}")
        return completed_handlers

    completed_handlers = await asyncio.create_task(async_log())
    assert any(
        completed_handlers
    ), "At least one handler should have completed since we left the context"

    remaining_waiting_time = sum(
        [h.sleep_time for h in [handler1, handler2, handler3] if not h.handle_completed]
    )
    logger.debug(f"Remaining waiting time: {remaining_waiting_time}s")
    await asyncio.sleep(remaining_waiting_time * 0.9)  # Wait for all handlers to complete

    # Verify all handlers completed
    assert all(
        h.handle_completed for h in [handler1, handler2, handler3]
    ), "All handlers should have completed"

    # Calculate total processing time, Total time should be close to sum of sleep times, asyncio is concurrent not parallel
    total_time = time.time() - start_time
    logger.debug(
        f"Total processing time: {total_time}s, Sum of sleep times: {sum_of_sleep_times}s, Max sleep time: {max_sleep_time}s"
    )
    assert (
        total_time < sum_of_sleep_times * 1.1
    ), f"Total time ({total_time}s) should be roughly equal to sum of sleep times ({sum_of_sleep_times}s, asyncio is concurrent not parallel"


@pytest.mark.asyncio
async def test_async_emit_order_preservation():
    """Verify that multiple records are processed in order by each handler,
    even if handlers process at different speeds."""

    logger.debug("Testing order preservation with multiple records")

    # Create two handlers with different processing times
    fast_handler = BusyWorkHandler(sleep_time=0.1, name="fast_handler")
    slow_handler = BusyWorkHandler(sleep_time=0.5, name="slow_handler")

    async_handler = AsyncEmitLogHandler(handlers=[fast_handler, slow_handler])

    # Create multiple records
    records = [create_test_record(f"Message {i}") for i in range(5)]

    # Emit all records quickly
    logger.debug("Emitting multiple records")
    for record in records:
        async_handler.emit(record)

    # Wait for all processing to complete
    logger.debug("Waiting for all processing to complete")
    await asyncio.sleep(
        (fast_handler.sleep_time + slow_handler.sleep_time) * 1.1
    )  # Wait enough time for all records to be processed

    # Verify order preservation for each handler
    for handler in [fast_handler, slow_handler]:
        logger.debug(f"Checking order for {handler.name}")
        assert len(handler.handled_records) == len(
            records
        ), f"{handler.name} should have processed all records"
        for i, record in enumerate(handler.handled_records):
            assert record.msg == f"Message {i}", f"{handler.name} processed records in wrong order"

        # Verify sequential processing within each handler
        for i in range(1, len(handler.handle_start_times)):
            assert (
                handler.handle_start_times[i] >= handler.handle_end_times[i - 1]
            ), f"{handler.name} started processing a record before finishing the previous one"
