"""Submodule for the main builder/runner class for interactive testbenches,
and some support classes it needs."""

import re
import os
import sys
import signal
from threading import Thread
from tempfile import TemporaryDirectory
import vhdeps
from vhdmmio.template import TemplateEngine

class _Signal:
    """Representation of a logical signal inside the testbench, part of either
    the `inputs` or `outputs` vector (depending on the subclass used)."""

    def __init__(self, testbench, offset, width):
        """Constructs a signal belonging to `Testbench` `testbench`, at the
        given offset in the vector, and with the given width in bits."""
        super().__init__()
        self._testbench = testbench
        self._offset = offset
        self._width = width

    @property
    def testbench(self):
        """The testbench associated with this signal."""
        return self._testbench

    @property
    def offset(self):
        """The offset of this signal within the input/output vector."""
        return self._offset

    @property
    def width(self):
        """The width of this signal."""
        return self._width

    @property
    def rnge(self):
        """The range/identifier of this signal for use within the FIFO
        communication protocol."""
        return '%05d%05d' % (self._offset + self._width - 1, self._offset)

    @property
    def val(self):
        """Must be overridden to allow access to the signal."""
        raise NotImplementedError()

    def to_x01(self):
        """Returns the bitstring converted to only 0s, 1s, and Xs."""
        return ''.join(map(lambda x: '1' if x in '1H' else '0' if x in '0L' else 'X', self.val))

    def is_x(self):
        """Returns whether any of the bits in the signal are undefined."""
        return 'X' in self.to_x01()

    def to_01(self):
        """Returns the bitstring converted to only zeros and ones."""
        return ''.join(map(lambda x: '1' if x in '1H' else '0', self.val))

    def __str__(self):
        """Returns the current value as a bitstring."""
        return self.val

    def __bool__(self):
        """Returns the current value as a boolean."""
        return self.val != '0' * self._width

    def __int__(self):
        """Returns the current value as an integer."""
        if self.is_x():
            raise ValueError('value is undefined')
        return int(self.to_01(), 2)

    def convert_value(self, value):
        """Converts the given bitstring, boolean, or integer to an appropriate
        bitstring for this signal."""
        if isinstance(value, bool) and self.width == 1:
            return '1' if value else '0'
        if isinstance(value, int):
            return ('{:0%db}' % self.width).format(value & ((1 << self.width) - 1))
        strval = str(value)
        if len(strval) == 1:
            strval *= self.width
        if re.match('[-UZLHH01X]{%d}$' % self.width, strval):
            return strval
        raise TypeError('invalid value for vector of width %d: %r' % (self.width, value))


class _Input(_Signal):
    """Representation of an input signal for the UUT."""

    def __init__(self, testbench, communicate, offset, width=1):
        """Constructs an input signal wrapper."""
        super().__init__(testbench, offset, width)
        self._cache_val = '0' * width
        self._communicate = communicate

    @property
    def val(self):
        """Returns the current value of this signal as a bitstring."""
        return self._cache_val

    @val.setter
    def val(self, value):
        """Sets the value of the signal."""
        value = self.convert_value(value)
        if value == self._cache_val:
            return
        self._communicate('S%s%s' % (self.rnge, value))
        self._cache_val = value


class _Output(_Signal):
    """Representation of an output signal of the UUT."""

    def __init__(self, testbench, communicate, offset, width=1):
        """Constructs an output signal wrapper."""
        super().__init__(testbench, offset, width)
        self._cache_val = None
        self._cache_cycle = None
        self._communicate = communicate

    @property
    def val(self):
        """Returns the current value of this signal as a bitstring."""
        if self._cache_val is None or self._cache_cycle < self.testbench.cycle:
            data = self._communicate('G%s' % self.rnge)
            if not data or data[0] != 'D' or len(data) != self.width + 1:
                raise RuntimeError('communication error')
            self._cache_val = data[1:]
            self._cache_cycle = self.testbench.cycle
        return self._cache_val

    def wait(self, cycles, value=None):
        """Waits for at most `cycles` cycles for the signal to change (default)
        or to get the given `value` (if specified). Raises `TimeoutError` if
        the timeout expires."""
        if cycles < 0 or cycles > 99999:
            raise ValueError('max cycles out of range')
        if value is None:
            command = 'W%05d%s' % (cycles, self.rnge)
        else:
            command = 'E%05d%s%s' % (cycles, self.rnge, self.convert_value(value))
        result = self._communicate(command)
        if not isinstance(result, int):
            raise RuntimeError('communication error')
        if result == cycles:
            raise TimeoutError('timeout')

    def set_interrupt(self, value, func, *args, **kwargs):
        """Requests that `func` be called when this single-bit output signal is
        set to the given value by the UUT."""
        value = self.convert_value(value)
        if self.width != 1:
            raise ValueError('interrupts are only supported for single bits')
        self.testbench.configure_interrupt(self.offset, value, func, args, kwargs)

    def clear_interrupt(self):
        """Unregisters a previously enabled interrupt that didn't fire yet.
        Note that interrupts clear themselves when they fire."""
        if self.width != 1:
            raise ValueError('interrupts are only supported for single bits')
        self.testbench.configure_interrupt(self.offset)


class Testbench:
    """Testbench builder/runner class."""

    def __init__(self):
        """Constructs a testbench."""
        super().__init__()

        # Builder variables.
        self._tple = TemplateEngine()
        self._input_bits = 0
        self._output_bits = 0
        self._includes = []
        self._activity_dump = False
        self._com_debug = False
        self._gui = False
        self._signals = []
        self._assigns = []

        # Runtime variables.
        self._interrupts = {}
        self._in_isr = False
        self._cycle = None
        self._thread = None
        self._request_file = None
        self._response_file = None
        self._tempdir = None

    def _assert_not_running(self):
        """Raises a `ValueError` if the simulation is running."""
        if self._cycle is not None:
            raise ValueError('simulation is running')

    def add_input(self, name, size=None):
        """Registers an input signal for the UUT, that is, a signal driven by
        the testbench. The input signal can be referred to in `add_body()`
        blocks using `<name>`. If `size` is `None`, this refers to an
        `std_logic`, otherwise it refers to an `std_logic_vector` of the give
        size in bits."""
        self._assert_not_running()
        xsize = 1 if size is None else size
        obj = _Input(self, self._communicate, self._input_bits, xsize)
        if size is None:
            self._signals.append('signal %s : std_logic;' % name)
            self._assigns.append('%s <= inputs(%d);' % (
                name, self._input_bits))
        else:
            self._signals.append('signal %s : std_logic_vector(%d downto 0);' % (
                name, size-1))
            self._assigns.append('%s <= inputs(%d downto %d);' % (
                name, self._input_bits + size - 1, self._input_bits))
        self._input_bits += xsize
        return obj

    def add_output(self, name, size=None):
        """Registers an output signal of the UUT, that is, a signal driven by
        the UUT. The output signal can be referred to in `add_body()` blocks
        using `<name>`. If `size` is `None`, this refers to an `std_logic`,
        otherwise it refers to an `std_logic_vector` of the give size in
        bits."""
        self._assert_not_running()
        xsize = 1 if size is None else size
        obj = _Output(self, self._communicate, self._output_bits, xsize)
        if size is None:
            self._signals.append('signal %s : std_logic;' % name)
            self._assigns.append('outputs(%d) <= %s;' % (
                self._output_bits, name))
        else:
            self._signals.append('signal %s : std_logic_vector(%d downto 0);' % (
                name, size-1))
            self._assigns.append('outputs(%d downto %d) <= %s;' % (
                self._output_bits + size - 1, self._output_bits, name))
        self._output_bits += xsize
        return obj

    def add_head(self, *args):
        """Adds a header block to the testbench, i.e. code placed between
        `architecture` and `begin`."""
        self._assert_not_running()
        self._tple.append_block('UUT_HEAD', *args)

    def add_body(self, *args):
        """Adds a body block to the testbench, i.e. code placed between `begin`
        and `end architecture`. This code can make use of signals defined by
        `add_input()` and `add_output()` as described in those functions."""
        self._assert_not_running()
        self._tple.append_block('UUT_BODY', *args)

    def define_var(self, var, value):
        """Defines a custom variable within the template engine."""
        self._tple[var] = value

    def add_include(self, fname):
        """Adds a (recursive) include directory or file that should be
        considered by vhdeps when starting the simulation."""
        self._assert_not_running()
        self._includes.append(os.path.realpath(fname))

    def with_activity_dump(self):
        """Enables logging of communication with the testbench. Sometimes
        useful for debugging."""
        self._assert_not_running()
        self._activity_dump = True

    def with_com_debug(self):
        """Enables logging of all pipe-based communication. Useful for
        debugging deadlocks."""
        self._assert_not_running()
        self._com_debug = True

    def with_gui(self):
        """Enables the `--gui` flag for vhdeps, such that `gtkwave` is opened
        after the test completes. Useful for debugging the UUT."""
        self._assert_not_running()
        self._gui = True

    def __enter__(self):
        """Starts the simulation."""
        self._assert_not_running()
        self._tempdir = TemporaryDirectory()

        tmp = self._tempdir.name + os.sep
        runner = tmp + 'runner_tc.vhd'
        req = tmp + 'request.fifo'
        resp = tmp + 'response.fifo'

        self.add_head(self._signals)
        self.add_body(self._assigns)
        self._tple['in_bits'] = self._input_bits
        self._tple['out_bits'] = self._output_bits
        self._tple['req_fname'] = req
        self._tple['resp_fname'] = resp
        self._tple['com_debug'] = self._com_debug
        self._tple.apply_file_to_file(
            os.path.dirname(__file__) + os.sep + 'template.vhd', runner)
        os.mkfifo(req)
        os.mkfifo(resp)

        vhdeps_died = [False]
        def run():
            args = ['ghdl', 'runner_tc', '-i', runner]
            if self._gui:
                args.append('--gui')
            for include in self._includes:
                args.append('-i')
                args.append(include)
            code = vhdeps.run_cli(args)
            vhdeps_died[0] = True
            if code:
                raise ValueError('vhdeps exit code was %d' % code)

        self._thread = Thread(target=run)
        self._thread.start()
        def timeout(*_):
            if vhdeps_died[0]:
                raise ValueError('vhdeps died before we could connect')
            signal.alarm(1)
        try:
            signal.signal(signal.SIGALRM, timeout)
            signal.alarm(1)
            if self._com_debug:
                print('open req...', file=sys.stderr)
            self._request_file = open(req, 'w')
            if self._com_debug:
                print('open resp...', file=sys.stderr)
            self._response_file = open(resp, 'r')
            if self._com_debug:
                print('files open', file=sys.stderr)
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, signal.SIG_DFL)
        self._cycle = 0

        if self._activity_dump:
            print('Py In S', file=sys.stderr)
            print('v      ', file=sys.stderr)
            print('|---->.', '(start process)', file=sys.stderr)
        return self

    def _assert_running(self):
        """Raises a `ValueError` when the simulation is not running."""
        if self._cycle is None:
            raise ValueError('simulation is not running')

    @property
    def cycle(self):
        """Returns the current simulation cycle."""
        self._assert_running()
        return self._cycle

    def _communicate(self, command):
        """Sends `command` to the VHDL world and fetches the response. If this
        is a C response (clocked), the reported number of cycles are added to
        the cycle counter and returned as an `int`. Otherwise, the result is
        returned as string without modification. Neither the command nor the
        result include the terminating newline."""
        if self._in_isr and command[0] not in 'GSI':
            raise ValueError('invalid command in interrupt mode: %s' % command)
        if self._activity_dump:
            if self._in_isr:
                print(":  |->|", command, file=sys.stderr)
            else:
                print("|---->|", command, file=sys.stderr)
        while True:
            self._assert_running()
            if self._com_debug:
                print('pushing request:', command, file=sys.stderr)
            self._request_file.write(command + '\n')
            self._request_file.flush()
            if self._com_debug:
                print('request pushed', file=sys.stderr)
            cycle, result = self._response_file.readline().strip().split(',')
            cycle = int(cycle)
            if self._activity_dump and cycle > self._cycle:
                if cycle - self._cycle == 1:
                    message = '(simulating 1 cycle)'
                else:
                    message = '(simulating %d cycles)' % (cycle - self._cycle)
                if self._in_isr:
                    print(":  :  |", message, file=sys.stderr)
                else:
                    print(":     |", message, file=sys.stderr)
            self._cycle = cycle
            if self._com_debug:
                print('got response:', result, file=sys.stderr)
            if not result:
                raise RuntimeError('communication error')
            if result[0] != 'I':
                break
            if self._activity_dump:
                print(":  .<-|", result, file=sys.stderr)
            self._in_isr = True
            index = int(result[1:])
            handler = self._interrupts.pop(index, None)
            if handler is None:
                raise RuntimeError(
                    'received interrupt for %d with no callback assigned' % index)
            handler[0](*handler[1], **handler[2])
            command = 'X'
            self._in_isr = False
            if self._activity_dump:
                print(":  '->|", command, file=sys.stderr)
        if self._activity_dump:
            if self._in_isr:
                print(":  |<-|", result, file=sys.stderr)
            elif result == 'Q':
                print("|<----'", result, file=sys.stderr)
                print("v", file=sys.stderr)
            else:
                print("|<----|", result, file=sys.stderr)
        if result[0] == 'C':
            cycles = int(result[1:])
            return cycles
        return result

    def reset(self, cycles=10):
        """Asserts `reset` for the given amount of cycles."""
        if cycles < 0 or cycles > 99999:
            raise ValueError('cycles out of range')
        self._communicate('R%05d' % cycles)

    def clock(self, cycles=1):
        """Sends the given amount of clock cycles."""
        if cycles < 0 or cycles > 99999:
            raise ValueError('cycles out of range')
        self._communicate('C%05d' % cycles)

    def configure_interrupt(self, offset, value='-', func=None, args=None, kwargs=None):
        """Enables or disables an interrupt when the output bit at the given
        offset is set to the given value. When the interrupt occurs,
        `func(*args, **kwargs)` is called and the interrupt is automatically
        disabled. It is illegal to terminate the simulation or advance time
        during these callbacks, but signals can be read/set and interrupts
        can be (re)configured."""
        if value not in 'UZLHW01X-':
            raise ValueError('invalid std_logic value')
        self._communicate('I%05d%s' % (offset, value))
        if func is None:
            del self._interrupts[offset]
        else:
            self._interrupts[offset] = (func, args, kwargs)

    def __exit__(self, *_):
        """Ends the simulation."""
        self._communicate('Q')
        self._cycle = None
        self._request_file.close()
        self._request_file = None
        self._response_file.close()
        self._response_file = None
        self._thread.join()
        self._thread = None
        self._tempdir.cleanup()
        self._tempdir = None
