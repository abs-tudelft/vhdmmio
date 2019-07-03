"""Submodule for abstractions of streams in interactive testbenches."""

class StreamSourceMock:
    """Represents a mockup stream source."""

    def __init__(self, valid, ready, *data):
        """Constructs a stream source from the given valid, ready, and data
        signals. These must have been previously constructed and must share
        the same testbench."""
        super().__init__()
        self._testbench = valid.testbench
        self._valid = valid
        self._ready = ready
        self._data = data
        self._queue = []

    @property
    def testbench(self):
        """The testbench associated with this stream."""
        return self._testbench

    @property
    def valid(self):
        """The valid signal for this stream."""
        return self._testbench

    @property
    def ready(self):
        """The ready signal for this stream."""
        return self._testbench

    @property
    def data(self):
        """The tuple of data signals for this stream."""
        return self._data

    def __len__(self):
        """Returns the number of queued transfers."""
        return len(self._queue)

    def _handler(self):
        del self._queue[0]
        self._next()

    def _next(self):
        """Places the next transfer on the bus."""
        if not self._queue:
            self._valid.val = '0'
            for sig in self._data:
                sig.val = 'U'
            return
        data = self._queue[0]
        for sig, val in zip(self._data, data):
            sig.val = val
        self._valid.val = '1'
        self._ready.set_interrupt('1', self._handler)

    def send(self, *data):
        """Queues a transfer."""
        if len(data) != len(self._data):
            raise ValueError('invalid data for stream')
        data = [sig.convert_value(val) for sig, val in zip(self._data, data)]
        self._queue.append(data)
        if len(self._queue) == 1:
            self._next()

    def wait(self, max_cycles):
        """Waits for all queued transfers to complete."""
        max_cycle = self._testbench.cycle + max_cycles
        while self._queue:
            remain = max_cycle - self._testbench.cycle
            if not remain:
                raise TimeoutError('timeout')
            self._ready.wait(remain, '1')


class StreamSinkMock:
    """Represents a mockup stream sink."""

    def __init__(self, valid, ready, *data):
        """Constructs a stream source from the given valid, ready, and data
        signals. These must have been previously constructed and must share
        the same testbench."""
        super().__init__()
        self._testbench = valid.testbench
        self._valid = valid
        self._ready = ready
        self._data = data
        self._queue = []

    @property
    def testbench(self):
        """The testbench associated with this stream."""
        return self._testbench

    @property
    def valid(self):
        """The valid signal for this stream."""
        return self._testbench

    @property
    def ready(self):
        """The ready signal for this stream."""
        return self._testbench

    @property
    def data(self):
        """The tuple of data signals for this stream."""
        return self._data

    def __len__(self):
        """Returns the number of queued transfer handlers."""
        return len(self._queue)

    def _call_handler(self):
        """Calls the current handler. If it returns `True`, the handler is
        not popped and will thus be called again; otherwise the next handler
        will be called next (if any). Proceeds to call `_next()` to set up
        for the next transfer."""
        function, args, kwargs = self._queue.pop(0)
        if function(*self._data, *args, **kwargs):
            self._queue.insert(0, (function, args, kwargs))
        self._next()

    def _next(self):
        """Prepares for the next transfer."""
        if not self._queue:
            self._ready.val = '0'
            return
        self._ready.val = '1'
        self._valid.set_interrupt('1', self._call_handler)

    def handle(self, function, *args, **kwargs):
        """Queues a transfer handler. This makes the stream ready. When a
        transfer is received `function(*data, *args, **kwargs)` will be called,
        where `data` represents the data *signals* (so use `.val` et. al. to
        get the value in the desired format/at all). If the transfer handler
        returns `True`, it will be called again for the next transfer. Note
        that this differs from calling `handle()` again, in that the handler
        will be replaced at the front of the queue instead of at the end of
        the queue."""
        self._queue.append((function, args, kwargs))
        if len(self._queue) == 1:
            self._next()

    def wait(self, max_cycles):
        """Waits for all queued transfers to complete."""
        max_cycle = self._testbench.cycle + max_cycles
        while self._queue:
            remain = max_cycle - self._testbench.cycle
            if not remain:
                raise TimeoutError('timeout')
            self._valid.wait(remain, '1')
