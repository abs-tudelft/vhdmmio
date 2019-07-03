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
