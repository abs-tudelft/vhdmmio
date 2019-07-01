"""Test submodule for constructing an interactive simulation."""

import re
import os
import sys
from threading import Thread
from tempfile import TemporaryDirectory
from vhdmmio.template import TemplateEngine, annotate_block
import vhdeps

_TEMPLATE = annotate_block("""
-- pragma simulation timeout 1000 ms

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library std;
use std.textio.all;

library work;
use work.vhdmmio_pkg.all;

entity runner_tc is
end runner_tc;

architecture arch of runner_tc is
  signal clk        : std_logic := '1';
  signal reset      : std_logic := '0';
  signal inputs     : std_logic_vector($in_bits-1$ downto 0) := (others => '0');
  signal outputs    : std_logic_vector($out_bits-1$ downto 0) := (others => '0');

$ UUT_HEAD

begin

$ UUT_BODY

  stim_proc: process is
    file request_file   : text;
    file response_file  : text;
    variable data       : line;
    variable index      : natural;
    variable triggers   : std_logic_vector($out_bits-1$ downto 0) := (others => '-');
    variable cycle      : natural := 0;

    impure function recv_init return character is
      variable cmd : character;
    begin
$if com_debug
      report "reading request..." severity note;
$endif
      readline(request_file, data);
$if com_debug
      report "got request: " & data.all severity note;
$endif
      assert data.all'length >= 1 severity failure;
      index := data.all'low + 1;
      return data.all(data.all'low);
    end function;

    impure function recv_nat return natural is
      variable c: integer;
      variable x: natural;
    begin
      assert data.all'high >= index + 4 severity failure;
      x := 0;
      for i in 1 to 5 loop
        c := character'pos(data.all(index)) - character'pos('0');
        index := index + 1;
        assert c >= 0 and c <= 9 severity failure;
        x := 10*x + c;
      end loop;
      return x;
    end function;

    impure function recv_slv(size: natural) return std_logic_vector is
      variable x: std_logic_vector(size-1 downto 0);
    begin
      assert data.all'high >= index + size - 1 severity failure;
      for i in x'range loop
        case data.all(index) is
          when 'U' => x(i) := 'U';
          when 'Z' => x(i) := 'Z';
          when 'L' => x(i) := 'L';
          when 'H' => x(i) := 'H';
          when 'W' => x(i) := 'W';
          when '0' => x(i) := '0';
          when '1' => x(i) := '1';
          when 'X' => x(i) := 'X';
          when '-' => x(i) := '-';
          when others => assert false severity failure;
        end case;
        index := index + 1;
      end loop;
      return x;
    end function;

    procedure recv_done is
    begin
      assert index = data.all'high + 1 severity failure;
      deallocate(data);
    end procedure;

    procedure send_init(code: character) is
    begin
      write(data, integer'image(cycle));
      write(data, character'(','));
      write(data, code);
    end procedure;

    procedure send_nat(val: natural) is
    begin
      write(data, integer'image(val));
    end procedure;

    procedure send_slv(x: std_logic_vector) is
    begin
      for i in x'range loop
        case x(i) is
          when 'U' => write(data, character'('U'));
          when 'Z' => write(data, character'('Z'));
          when 'L' => write(data, character'('L'));
          when 'H' => write(data, character'('H'));
          when 'W' => write(data, character'('W'));
          when '0' => write(data, character'('0'));
          when '1' => write(data, character'('1'));
          when 'X' => write(data, character'('X'));
          when '-' => write(data, character'('-'));
        end case;
      end loop;
    end procedure;

    procedure send_done is
    begin
$if com_debug
      report "pushing response: " & data.all severity note;
$endif
      writeline(response_file, data);
      flush(response_file);
$if com_debug
      report "pushed response" & data.all severity note;
$endif
    end procedure;

    procedure handle_set is
      variable hi : natural;
      variable lo : natural;
    begin
      hi := recv_nat;
      lo := recv_nat;
      assert hi >= lo severity failure;
      assert hi < $in_bits$ severity failure;
      inputs(hi downto lo) <= recv_slv(hi - lo + 1);
      recv_done;
      send_init('C');
      send_nat(0);
      send_done;
    end procedure;

    procedure handle_get is
      variable hi : natural;
      variable lo : natural;
    begin
      hi := recv_nat;
      lo := recv_nat;
      recv_done;
      assert hi >= lo severity failure;
      assert hi < $out_bits$ severity failure;
      send_init('D');
      send_slv(outputs(hi downto lo));
      send_done;
    end procedure;

    procedure handle_set_interrupt is
      variable idx : natural;
    begin
      idx := recv_nat;
      assert idx < $out_bits$ severity failure;
      triggers(idx) := recv_slv(1)(0);
      recv_done;
      send_init('C');
      send_nat(0);
      send_done;
    end procedure;

    procedure send_clock is
    begin
      wait for 5 ns;
      clk <= '0';
      wait for 5 ns;
      clk <= '1';
      wait until rising_edge(clk);
      cycle := cycle + 1;
      for i in triggers'range loop
        if triggers(i) /= '-' and triggers(i) = outputs(i) then
          triggers(i) := '-';
          send_init('I');
          send_nat(i);
          send_done;
          interrupt: loop
            case recv_init is
              when 'S' => handle_set;
              when 'G' => handle_get;
              when 'I' => handle_set_interrupt;
              when 'X' => exit interrupt;
              when others => assert false severity failure;
            end case;
          end loop;
          recv_done;
        end if;
      end loop;
    end send_clock;

    type slv_ptr is access std_logic_vector;

    variable hi         : natural;
    variable lo         : natural;
    variable cnt        : natural;
    variable xcnt       : natural;
    variable slv        : slv_ptr;

  begin
$if com_debug
    report "open req..." severity note;
$endif
    file_open(request_file,  "$req_fname$",  read_mode);
$if com_debug
    report "open resp..." severity note;
$endif
    file_open(response_file, "$resp_fname$", write_mode);
$if com_debug
    report "files open" severity note;
$endif

    main: loop
      case recv_init is
        when 'R' => -- reset
          cnt := recv_nat;
          recv_done;
          reset <= '1';
          for i in 1 to cnt loop
            send_clock;
          end loop;
          reset <= '0';
          send_init('C');
          send_nat(cnt);
          send_done;

        when 'C' => -- clock
          cnt := recv_nat;
          recv_done;
          for i in 1 to cnt loop
            send_clock;
          end loop;
          send_init('C');
          send_nat(cnt);
          send_done;

        when 'E' => -- clock until equal
          cnt := recv_nat;
          hi := recv_nat;
          lo := recv_nat;
          assert hi >= lo severity failure;
          assert hi < $out_bits$ severity failure;
          slv := new std_logic_vector(hi downto lo);
          slv.all := recv_slv(hi - lo + 1);
          recv_done;
          xcnt := 0;
          for i in 1 to cnt loop
            exit when std_match(outputs(hi downto lo), slv.all);
            send_clock;
            xcnt := xcnt + 1;
          end loop;
          deallocate(slv);
          send_init('C');
          send_nat(xcnt);
          send_done;

        when 'W' => -- clock until change
          cnt := recv_nat;
          hi := recv_nat;
          lo := recv_nat;
          recv_done;
          assert hi >= lo severity failure;
          assert hi < $out_bits$ severity failure;
          slv := new std_logic_vector(hi downto lo);
          slv.all := outputs(hi downto lo);
          xcnt := 0;
          for i in 1 to cnt loop
            exit when outputs(hi downto lo) /= slv.all;
            send_clock;
            xcnt := xcnt + 1;
          end loop;
          deallocate(slv);
          send_init('C');
          send_nat(xcnt);
          send_done;

        when 'S' => handle_set;
        when 'G' => handle_get;
        when 'I' => handle_set_interrupt;

        when 'Q' => -- quit
          recv_done;
          send_init('Q');
          send_done;
          exit main;

        when others => -- ?
          assert false severity failure;

      end case;
    end loop;

    file_close(request_file);
    file_close(response_file);

    wait;
  end process;
end arch;
""", comment='--')

class _Signal:
    """Representation of a logical signal inside the testbench, part of either
    the `inputs` or `outputs` vector (depending on the subclass used)."""

    def __init__(self, tb, offset, width):
        """Constructs a signal belonging to `Testbench` `tb`, at the given
        offset in the vector, and with the given width in bits."""
        super().__init__()
        self._tb = tb
        self._offset = offset
        self._width = width

    @property
    def tb(self):
        """The testbench associated with this signal."""
        return self._tb

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

    def __init__(self, tb, communicate, offset, width=1):
        """Constructs an input signal wrapper."""
        super().__init__(tb, offset, width)
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

    def __init__(self, tb, communicate, offset, width=1):
        """Constructs an output signal wrapper."""
        super().__init__(tb, offset, width)
        self._cache_val = None
        self._cache_cycle = None
        self._communicate = communicate

    @property
    def val(self):
        """Returns the current value of this signal as a bitstring."""
        if self._cache_val is None or self._cache_cycle < self.tb.cycle:
            data = self._communicate('G%s' % self.rnge)
            if not data or data[0] != 'D' or len(data) != self.width + 1:
                raise RuntimeError('communication error')
            self._cache_val = data[1:]
            self._cache_cycle = self.tb.cycle
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

    def set_interrupt(self, value, fn, *args, **kwargs):
        """Requests that `fn` be called when this single-bit output signal is
        set to the given value by the UUT."""
        value = self.convert_value(value)
        if self.width != 1:
            raise ValueError('interrupts are only supported for single bits')
        self.tb.configure_interrupt(self.offset, value, fn, args, kwargs)

    def clear_interrupt(self):
        """Unregisters a previously enabled interrupt that didn't fire yet.
        Note that interrupts clear themselves when they fire."""
        if self.width != 1:
            raise ValueError('interrupts are only supported for single bits')
        self.tb.configure_interrupt(self.offset)


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
        ob = _Input(self, self._communicate, self._input_bits, xsize)
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
        return ob

    def add_output(self, name, size=None):
        """Registers an output signal of the UUT, that is, a signal driven by
        the UUT. The output signal can be referred to in `add_body()` blocks
        using `<name>`. If `size` is `None`, this refers to an `std_logic`,
        otherwise it refers to an `std_logic_vector` of the give size in
        bits."""
        self._assert_not_running()
        xsize = 1 if size is None else size
        ob = _Output(self, self._communicate, self._output_bits, xsize)
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
        return ob

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
        self._tple.apply_str_to_file(_TEMPLATE, runner)
        os.mkfifo(req)
        os.mkfifo(resp)

        def run():
            args = ['ghdl', 'runner_tc', '-i', runner]
            if self._gui:
                args.append('--gui')
            for include in self._includes:
                args.append('-i')
                args.append(include)
            exit = vhdeps.run_cli(args)
            if exit:
                raise ValueError('vhdeps exit code was %d' % exit)

        self._thread = Thread(target=run)
        self._thread.start()
        if self._com_debug:
            print('open req...', file=sys.stderr)
        self._request_file = open(req, 'w')
        if self._com_debug:
            print('open resp...', file=sys.stderr)
        self._response_file = open(resp, 'r')
        if self._com_debug:
            print('files open', file=sys.stderr)
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
            handler = self._interrupts.pop(int(result[1:]), None)
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

    def configure_interrupt(self, offset, value='-', fn=None, args=None, kwargs=None):
        """Enables or disables an interrupt when the output bit at the given
        offset is set to the given value. When the interrupt occurs,
        `fn(*args, **kwargs)` is called and the interrupt is automatically
        disabled. It is illegal to terminate the simulation or advance time
        during these callbacks, but signals can be read/set and interrupts
        can be (re)configured."""
        if value not in 'UZLHW01X-':
            raise ValueError('invalid std_logic value')
        self._communicate('I%05d%s' % (offset, value))
        if fn is None:
            del self._interrupts[offset]
        else:
            self._interrupts[offset] = (fn, args, kwargs)

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


class StreamSourceMock:
    """Represents a mockup stream source."""

    def __init__(self, valid, ready, *data):
        """Constructs a stream source from the given valid, ready, and data
        signals. These must have been previously constructed and must share
        the same testbench."""
        super().__init__()
        self._tb = valid.tb
        self._valid = valid
        self._ready = ready
        self._data = data
        self._queue = []

    @property
    def tb(self):
        """The testbench associated with this stream."""
        return self._tb

    @property
    def valid(self):
        """The valid signal for this stream."""
        return self._tb

    @property
    def ready(self):
        """The ready signal for this stream."""
        return self._tb

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
        max_cycle = self._tb.cycle + max_cycles
        while self._queue:
            remain = max_cycle - self._tb.cycle
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
        self._tb = valid.tb
        self._valid = valid
        self._ready = ready
        self._data = data
        self._queue = []

    @property
    def tb(self):
        """The testbench associated with this stream."""
        return self._tb

    @property
    def valid(self):
        """The valid signal for this stream."""
        return self._tb

    @property
    def ready(self):
        """The ready signal for this stream."""
        return self._tb

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
        fn, args, kwargs = self._queue.pop(0)
        if fn(*self._data, *args, **kwargs):
            self._queue.insert(0, (fn, args, kwargs))
        self._next()

    def _next(self):
        """Prepares for the next transfer."""
        if not self._queue:
            self._ready.val = '0'
            return
        self._ready.val = '1'
        self._valid.set_interrupt('1', self._call_handler)

    def handle(self, fn, *args, **kwargs):
        """Queues a transfer handler. This makes the stream ready. When a
        transfer is received `fn(*data, *args, **kwargs)` will be called,
        where `data` represents the data *signals* (so use `.val` et. al. to
        get the value in the desired format/at all). If the transfer handler
        returns `True`, it will be called again for the next transfer. Note
        that this differs from calling `handle()` again, in that the handler
        will be replaced at the front of the queue instead of at the end of
        the queue."""
        self._queue.append((fn, args, kwargs))
        if len(self._queue) == 1:
            self._next()

    def wait(self, max_cycles):
        """Waits for all queued transfers to complete."""
        max_cycle = self._tb.cycle + max_cycles
        while self._queue:
            remain = max_cycle - self._tb.cycle
            if not remain:
                raise TimeoutError('timeout')
            self._valid.wait(remain, '1')


class AXI4LMasterMock:
    """Represents a mockup AXI4L master."""

    def __init__(self, tb, name, bus_width=32):
        """Adds a mockup AXI4L master to the given testbench to control an
        AXI4L slave. Returns an object with an object that can be used to
        control the master. The request and response records can be referred to
        in `add_body()` blocks using `<name>_req` and `<name>_resp`.
        `bus_width` must be 32 or 64 to specify the data width of the bus."""
        if bus_width not in [32, 64]:
            raise ValueError('unsupported bus width: %r' % bus_width)

        super().__init__()
        self._tb = tb
        self._name = name
        self._bus_width = bus_width

        tb.add_head(
            'signal {name}_req  : axi4l{width}_m2s_type := AXI4L{width}_M2S_RESET;\n'
            'signal {name}_resp : axi4l{width}_s2m_type := AXI4L{width}_S2M_RESET;\n'
            .format(name=name, width=bus_width))

        body = []

        def def_inp(path, width=None):
            ident = '%s_%s' % (name, path.replace('.', '_'))
            body.append('%s_req.%s <= %s;' % (name, path, ident))
            return tb.add_input(ident, width)

        def def_out(path, width=None):
            ident = '%s_%s' % (name, path.replace('.', '_'))
            body.append('%s <= %s_resp.%s;' % (ident, name, path))
            return tb.add_output(ident, width)

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

        tb.add_body(body)

    def async_write(self, cb, addr, data, strb='1', prot='0'):
        """Performs an asynchronous write, which calls `cb(resp)` when done.
        `resp` is the signal wrapper, so use `resp.val` etc. to get the
        value."""
        self._aw.send(addr, prot)
        self._w.send(data, strb)
        self._b.handle(cb)

    def async_read(self, cb, addr, prot='0'):
        """Performs an asynchronous read, which calls `cb(data, resp)` when
        done. `data` and `resp` are the signal wrappers, so use `.val` etc.
        to get the values."""
        self._ar.send(addr, prot)
        self._r.handle(cb)

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
        raise ValueError('unknown resp: %s' % result)

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

    def __init__(self, tb, name, bus_width=32):
        """Adds a mockup AXI4L slave to the given testbench to connect to an
        AXI4L master in the UUT. Returns an object with an object that can be
        used to control the slave. The request and response records can be
        referred to in `add_body()` blocks using `<name>_req` and
        `<name>_resp`. `bus_width` must be 32 or 64 to specify the data width
        of the bus."""
        if bus_width not in [32, 64]:
            raise ValueError('unsupported bus width: %r' % bus_width)

        super().__init__()
        self._tb = tb
        self._name = name
        self._bus_width = bus_width

        tb.add_head(
            'signal {name}_req  : axi4l{width}_m2s_type := AXI4L{width}_M2S_RESET;\n'
            'signal {name}_resp : axi4l{width}_s2m_type := AXI4L{width}_S2M_RESET;\n'
            .format(name=name, width=bus_width))

        body = []

        def def_inp(path, width=None):
            ident = '%s_%s' % (name, path.replace('.', '_'))
            body.append('%s_resp.%s <= %s;' % (name, path, ident))
            return tb.add_input(ident, width)

        def def_out(path, width=None):
            ident = '%s_%s' % (name, path.replace('.', '_'))
            body.append('%s <= %s_req.%s;' % (ident, name, path))
            return tb.add_output(ident, width)

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

        tb.add_body(body)

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
        if value is None:
            self._handle_write = self.handle_write_default
        else:
            self._handle_write = handler

    def handle_write_default(self, addr, prot, data, strb):
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
        for b in range(self._bus_width // 8):
            if strb[b] == '1':
                word += data[b*8:b*8+8]
            else:
                word += cur[b*8:b*8+8]
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
        if value is None:
            self._handle_read = self.handle_read_default
        else:
            self._handle_read = handler

    def handle_read_default(self, addr, prot):
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
