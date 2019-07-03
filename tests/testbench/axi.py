"""Submodule for abstractions of AXI4-Lite busses in interactive
testbenches."""

from .streams import StreamSourceMock, StreamSinkMock

class AXI4LMasterMock:
    """Represents a mockup AXI4L master."""

    def __init__(self, testbench, name, bus_width=32):
        """Adds a mockup AXI4L master to the given testbench to control an
        AXI4L slave. Returns an object with an object that can be used to
        control the master. The request and response records can be referred to
        in `add_body()` blocks using `<name>_req` and `<name>_resp`.
        `bus_width` must be 32 or 64 to specify the data width of the bus."""
        if bus_width not in [32, 64]:
            raise ValueError('unsupported bus width: %r' % bus_width)

        super().__init__()
        self._testbench = testbench
        self._name = name
        self._bus_width = bus_width

        testbench.add_head(
            'signal {name}_req  : axi4l{width}_m2s_type := AXI4L{width}_M2S_RESET;\n'
            'signal {name}_resp : axi4l{width}_s2m_type := AXI4L{width}_S2M_RESET;\n'
            .format(name=name, width=bus_width))

        body = []

        def def_inp(path, width=None):
            ident = '%s_%s' % (name, path.replace('.', '_'))
            body.append('%s_req.%s <= %s;' % (name, path, ident))
            return testbench.add_input(ident, width)

        def def_out(path, width=None):
            ident = '%s_%s' % (name, path.replace('.', '_'))
            body.append('%s <= %s_resp.%s;' % (ident, name, path))
            return testbench.add_output(ident, width)

        self._aw = StreamSourceMock(
            def_inp('aw.valid'),
            def_out('aw.ready'),
            def_inp('aw.addr', 32),
            def_inp('aw.prot', 3))

        self._w = StreamSourceMock(
            def_inp('w.valid'),
            def_out('w.ready'),
            def_inp('w.data', bus_width),
            def_inp('w.strb', bus_width // 8))

        self._b = StreamSinkMock(
            def_out('b.valid'),
            def_inp('b.ready'),
            def_out('b.resp', 2))

        self._ar = StreamSourceMock(
            def_inp('ar.valid'),
            def_out('ar.ready'),
            def_inp('ar.addr', 32),
            def_inp('ar.prot', 3))

        self._r = StreamSinkMock(
            def_out('r.valid'),
            def_inp('r.ready'),
            def_out('r.data', bus_width),
            def_out('r.resp', 2))

        self.interrupt = def_out('u.irq')

        testbench.add_body(body)

    def async_write(self, callback, addr, data, strb='1', prot='0'):
        """Performs an asynchronous write, which calls `callback(resp)` when
        done. `resp` is the signal wrapper, so use `resp.val` etc. to get the
        value."""
        self._aw.send(addr, prot)
        self._w.send(data, strb)
        self._b.handle(callback)

    def async_read(self, callback, addr, prot='0'):
        """Performs an asynchronous read, which calls `callback(data, resp)`
        when done. `data` and `resp` are the signal wrappers, so use `.val`
        etc. to get the values."""
        self._ar.send(addr, prot)
        self._r.handle(callback)

    @staticmethod
    def _check_resp(resp):
        """Checks the given `resp` bitstring, raising the appropriate
        `ValueError` for nacks."""
        if resp[0] == '0':
            return
        if resp == '10':
            raise ValueError('slave error')
        if resp == '11':
            raise ValueError('decode error')
        raise ValueError('unknown resp: %s' % resp)

    def write(self, addr, data, strb='1', prot='0', timeout=1000):
        """Performs a write. A `ValueError` is raised when `resp` is nonzero.
        A `TimeoutError` is raised when no response was received within the
        given timeout."""
        result = []
        def handler(resp):
            result.append(resp.to_x01())
        self.async_write(handler, addr, data, strb, prot)
        self._b.wait(timeout)
        self._check_resp(result[0])

    def read_bits(self, addr, prot='0', timeout=1000):
        """Performs a read. The data is returned as bitstring. A `ValueError`
        is raised when `resp` is nonzero. A `TimeoutError` is raised when no
        response was received within the given timeout."""
        result = []
        def handler(data, resp):
            result.append((resp.to_x01(), data.to_x01()))
        self.async_read(handler, addr, prot)
        self._r.wait(timeout)
        self._check_resp(result[0][0])
        return result[0][1]

    def read(self, addr, prot='0', timeout=1000):
        """Performs a read. The data is returned as an integer. A `ValueError`
        is raised when `resp` is nonzero, or when the result contains undefined
        bits. A `TimeoutError` is raised when no response was received within
        the given timeout."""
        data = self.read_bits(addr, prot, timeout)
        if 'X' in data:
            raise ValueError('result is undefined: %s' % data)
        return int(data, 2)


class AXI4LSlaveMock:
    """Represents a mockup AXI4L slave."""

    def __init__(self, testbench, name, bus_width=32):
        """Adds a mockup AXI4L slave to the given testbench to connect to an
        AXI4L master in the UUT. Returns an object with an object that can be
        used to control the slave. The request and response records can be
        referred to in `add_body()` blocks using `<name>_req` and
        `<name>_resp`. `bus_width` must be 32 or 64 to specify the data width
        of the bus."""
        if bus_width not in [32, 64]:
            raise ValueError('unsupported bus width: %r' % bus_width)

        super().__init__()
        self._testbench = testbench
        self._name = name
        self._bus_width = bus_width

        testbench.add_head(
            'signal {name}_req  : axi4l{width}_m2s_type := AXI4L{width}_M2S_RESET;\n'
            'signal {name}_resp : axi4l{width}_s2m_type := AXI4L{width}_S2M_RESET;\n'
            .format(name=name, width=bus_width))

        body = []

        def def_inp(path, width=None):
            ident = '%s_%s' % (name, path.replace('.', '_'))
            body.append('%s_resp.%s <= %s;' % (name, path, ident))
            return testbench.add_input(ident, width)

        def def_out(path, width=None):
            ident = '%s_%s' % (name, path.replace('.', '_'))
            body.append('%s <= %s_req.%s;' % (ident, name, path))
            return testbench.add_output(ident, width)

        self._aw = StreamSinkMock(
            def_out('aw.valid'),
            def_inp('aw.ready'),
            def_out('aw.addr', 32),
            def_out('aw.prot', 3))

        self._w = StreamSinkMock(
            def_out('w.valid'),
            def_inp('w.ready'),
            def_out('w.data', bus_width),
            def_out('w.strb', bus_width // 8))

        self._b = StreamSourceMock(
            def_inp('b.valid'),
            def_out('b.ready'),
            def_inp('b.resp', 2))

        self._ar = StreamSinkMock(
            def_out('ar.valid'),
            def_inp('ar.ready'),
            def_out('ar.addr', 32),
            def_out('ar.prot', 3))

        self._r = StreamSourceMock(
            def_inp('r.valid'),
            def_out('r.ready'),
            def_inp('r.data', bus_width),
            def_inp('r.resp', 2))

        self.interrupt = def_inp('u.irq')

        testbench.add_body(body)

        self._handle_write = self.handle_write_default
        self._handle_read = self.handle_read_default
        self._memory = {}

    @property
    def handle_write(self):
        """Write handler. Can be set to an alternative function, or to `None`
        to restore it to the default handler. The function is called with X01
        bitstrings for `addr`, `prot`, `data`, and `strb`. It must return
        `'decode'` for a decode error, `'error'` for a slave error, or anything
        else for an acknowledgement."""
        return self._handle_write

    @handle_write.setter
    def handle_write(self, handler):
        if handler is None:
            self._handle_write = self.handle_write_default
        else:
            self._handle_write = handler

    def handle_write_default(self, addr, _, data, strb):
        """Default write handler."""
        if self._bus_width == 32:
            addr = addr[:-2]
        else:
            addr = addr[:-3]
        if 'X' in addr:
            raise ValueError('AXI slave mock %s found X in write address' % self._name)
        addr = int(addr, 2)
        cur = self._memory.get(addr, 'U' * self._bus_width)
        if cur in ['decode', 'error']:
            return cur
        word = ''
        for index in range(self._bus_width // 8):
            if strb[index] == '1':
                word += data[index*8:index*8+8]
            else:
                word += cur[index*8:index*8+8]
        self._memory[addr] = word
        return None

    @property
    def handle_read(self):
        """Read handler. Can be set to an alternative function, or to `None` to
        restore it to the default handler. The function is called with X01
        bitstrings for `addr` and `prot`. It must return `'decode'` for a
        decode error, `'error'` for a slave error, or something that can be
        cast to a bus-width-sized vector for an acknowledgement."""
        return self._handle_read

    @handle_read.setter
    def handle_read(self, handler):
        if handler is None:
            self._handle_read = self.handle_read_default
        else:
            self._handle_read = handler

    def handle_read_default(self, addr, _):
        """Default read handler."""
        if self._bus_width == 32:
            addr = addr[:-2]
        else:
            addr = addr[:-3]
        if 'X' in addr:
            raise ValueError('AXI slave mock %s found X in read address' % self._name)
        addr = int(addr, 2)
        return self._memory.get(addr, 'U' * self._bus_width)

    def start(self):
        """Registers the address channel handlers."""
        self._aw.handle(self._aw_handle)
        self._ar.handle(self._ar_handle)

    def write(self, addr, value):
        """Writes to the mockup internal memory. Writing the special values
        `'decode'` or `'error'` cause respectively a decode or slave error to
        be returned when the address is accessed."""
        if self._bus_width == 32:
            addr >>= 2
        else:
            addr >>= 3
        self._memory[addr] = value

    def read_bits(self, addr):
        """Reads from the mockup internal memory. Returns a bitstring, `None`
        if the value has never been written, the special code `'decode'` when
        the address is emulating a decode error, or the special code `'error'`
        when the address is emulating a slave error."""
        if self._bus_width == 32:
            addr >>= 2
        else:
            addr >>= 3
        return self._memory.get(addr, None)

    def read(self, addr):
        """Reads from the mockup internal memory. Returns the word at the
        given address as an `int`, or raises a `ValueError` if this is not
        possible."""
        return int(self.read_bits(addr), 2)

    def _aw_handle(self, addr, prot):
        """Handles a write address channel request."""
        self._w.handle(self._w_handle, addr.to_x01(), prot.to_x01())

    def _w_handle(self, data, strb, addr, prot):
        """Handles a write data channel request."""
        self._aw.handle(self._aw_handle)
        data = data.to_x01()
        strb = strb.to_x01()
        result = self.handle_write(addr, prot, data, strb)
        if result == 'decode':
            self._b.send('11')
        elif result == 'error':
            self._b.send('10')
        else:
            self._b.send('00')

    def _ar_handle(self, addr, prot):
        """Handles a read address channel request."""
        self._ar.handle(self._ar_handle)
        addr = addr.to_x01()
        prot = prot.to_x01()
        result = self.handle_read(addr, prot)
        if result == 'decode':
            self._r.send('U', '11')
        elif result == 'error':
            self._r.send('U', '10')
        else:
            self._r.send(result, '00')
