"""Test deferring fields."""

from unittest import TestCase
from ..testbench import RegisterFileTestbench

class TestDefer(TestCase):
    """Test deferring fields."""

    def test_read_defer(self):
        """test read-deferring fields"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'fields': [
                {
                    'address': 0,
                    'repeat': 4,
                    'field-repeat': 1,
                    'name': 'a',
                    'behavior': 'custom',
                    'interfaces': [{'state': 'count:3'}, {'state': 'data:32'}, {'state': 'busy'}],
                    'read-can-block': True,
                    'read-request': (
                        'if $s.busy$ = \'1\' then\n'
                        '  if $resp_ready$ then\n'
                        '    $block$ := true;\n'
                        '  end if;\n'
                        'else\n'
                        '  $s.busy$ := \'1\';\n'
                        '  $defer$ := true;\n'
                        'end if;\n'
                    ),
                    'read-response': (
                        'if $s.count$ = "111" then\n'
                        '  $ack$ := true;\n'
                        '  $data$ := $s.data$;\n'
                        '  $s.data$ := std_logic_vector(unsigned($s.data$) + 1);\n'
                        '  $s.busy$ := \'0\';\n'
                        'else\n'
                        '  $block$ := true;\n'
                        'end if;\n'
                    ),
                    'post-access': (
                        'if $s.busy$ = \'1\' then\n'
                        '  if $s.count$ /= "111" then\n'
                        '    $s.count$ := std_logic_vector(unsigned($s.count$) + 1);\n'
                        '  end if;\n'
                        'else\n'
                        '  $s.count$ := "000";\n'
                        'end if;\n'
                    ),
                },
            ]})
        self.assertEqual(rft.ports, ('bus',))
        with rft as objs:
            start = rft.testbench.cycle
            self.assertEqual(objs.bus.read(0), 0)
            self.assertEqual(rft.testbench.cycle - start, 9)

            start = rft.testbench.cycle
            responses = []
            def callback(data, _):
                responses.append(int(data))
            objs.bus.async_read(callback, 4)
            objs.bus.async_read(callback, 8)
            objs.bus.async_read(callback, 12)
            responses.append(objs.bus.read(0))
            self.assertEqual(responses, [0, 0, 0, 1])
            self.assertEqual(rft.testbench.cycle - start, 12)

            start = rft.testbench.cycle
            responses.clear()
            objs.bus.async_read(callback, 4)
            objs.bus.async_read(callback, 8)
            objs.bus.async_read(callback, 0)
            objs.bus.async_read(callback, 12)
            objs.bus.async_read(callback, 8)
            objs.bus.async_read(callback, 4)
            objs.bus.async_read(callback, 0)
            responses.append(objs.bus.read(0))
            self.assertEqual(responses, [1, 1, 2, 1, 2, 2, 3, 4])
            self.assertEqual(rft.testbench.cycle - start, 28)

            start = rft.testbench.cycle
            responses.clear()
            expected = []
            for i in range(10):
                objs.bus.async_read(callback, 0)
                objs.bus.async_read(callback, 4)
                objs.bus.async_read(callback, 8)
                objs.bus.async_read(callback, 12)
                expected.extend([5+i, 3+i, 3+i, 2+i])
            responses.append(objs.bus.read(0))
            expected.append(15)
            self.assertEqual(responses, expected)
            self.assertEqual(rft.testbench.cycle - start, 89)

    def test_wide_read_defer(self):
        """test multi-word read-deferring field"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'fields': [
                {
                    'address': 0,
                    'bitrange': '63..0',
                    'repeat': 2,
                    'field-repeat': 1,
                    'stride': 2,
                    'name': 'a',
                    'behavior': 'custom',
                    'interfaces': [{'state': 'count:3'}, {'state': 'busy'}],
                    'read-can-block': True,
                    'read-request': (
                        'if $s.busy$ = \'1\' then\n'
                        '  if $resp_ready$ then\n'
                        '    $block$ := true;\n'
                        '  end if;\n'
                        'else\n'
                        '  $s.busy$ := \'1\';\n'
                        '  $defer$ := true;\n'
                        'end if;\n'
                    ),
                    'read-response': (
                        'if $s.count$ = "111" then\n'
                        '  $ack$ := true;\n'
                        '  if $i$ = 0 then\n'
                        '    $data$ := X"1122334455667788";\n'
                        '  else\n'
                        '    $data$ := X"8877665544332211";\n'
                        '  end if;\n'
                        '  $s.busy$ := \'0\';\n'
                        'else\n'
                        '  $block$ := true;\n'
                        'end if;\n'
                    ),
                    'post-access': (
                        'if $s.busy$ = \'1\' then\n'
                        '  if $s.count$ /= "111" then\n'
                        '    $s.count$ := std_logic_vector(unsigned($s.count$) + 1);\n'
                        '  end if;\n'
                        'else\n'
                        '  $s.count$ := "000";\n'
                        'end if;\n'
                    ),
                },
                {
                    'address': 16,
                    'bitrange': '63..0',
                    'name': 'b',
                    'behavior': 'constant',
                    'value': 0xDEADBEEFC0DE,
                }
            ]})
        self.assertEqual(rft.ports, ('bus',))
        with rft as objs:
            start = rft.testbench.cycle
            responses = []
            def callback(data, _):
                responses.append(int(data))
            objs.bus.async_read(callback, 0)
            objs.bus.async_read(callback, 4)
            objs.bus.async_read(callback, 8)
            objs.bus.async_read(callback, 12)
            objs.bus.async_read(callback, 16)
            objs.bus.async_read(callback, 20)
            objs.bus.async_read(callback, 0)
            objs.bus.async_read(callback, 4)
            objs.bus.async_read(callback, 8)
            objs.bus.async_read(callback, 12)
            objs.bus.async_read(callback, 16)
            responses.append(objs.bus.read(20))
            self.assertEqual(responses, [
                0x55667788, 0x11223344,
                0x44332211, 0x88776655,
                0xBEEFC0DE, 0x0000DEAD,
                0x55667788, 0x11223344,
                0x44332211, 0x88776655,
                0xBEEFC0DE, 0x0000DEAD])
            self.assertEqual(rft.testbench.cycle - start, 41)

    def test_write_defer(self):
        """test write-deferring fields"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'fields': [
                {
                    'address': 0,
                    'repeat': 4,
                    'field-repeat': 1,
                    'name': 'a',
                    'behavior': 'custom',
                    'interfaces': [{'state': 'count:3'}, {'state': 'data:32'}, {'state': 'busy'}],
                    'write-can-block': True,
                    'write-request': (
                        'if $s.busy$ = \'1\' then\n'
                        '  if $resp_ready$ then\n'
                        '    $block$ := true;\n'
                        '  end if;\n'
                        'else\n'
                        '  $s.data$ := $data$;\n'
                        '  $s.busy$ := \'1\';\n'
                        '  $defer$ := true;\n'
                        'end if;\n'
                    ),
                    'write-response': (
                        'if $s.count$ = "111" then\n'
                        '  case $s.data$(1 downto 0) is\n'
                        '    when "00" => $ack$ := true;\n'
                        '    when "01" => $nack$ := true;\n'
                        '    when others => null;\n'
                        '  end case;\n'
                        '  $s.busy$ := \'0\';\n'
                        'else\n'
                        '  $block$ := true;\n'
                        'end if;\n'
                    ),
                    'post-access': (
                        'if $s.busy$ = \'1\' then\n'
                        '  if $s.count$ /= "111" then\n'
                        '    $s.count$ := std_logic_vector(unsigned($s.count$) + 1);\n'
                        '  end if;\n'
                        'else\n'
                        '  $s.count$ := "000";\n'
                        'end if;\n'
                    ),
                },
            ]})
        self.assertEqual(rft.ports, ('bus',))
        with rft as objs:
            start = rft.testbench.cycle
            objs.bus.write(0, 0)
            self.assertEqual(rft.testbench.cycle - start, 9)

            start = rft.testbench.cycle
            responses = []
            def callback(resp):
                responses.append(int(resp))
            objs.bus.async_write(callback, 4, 0)
            objs.bus.async_write(callback, 8, 1)
            objs.bus.async_write(callback, 12, 2)
            objs.bus.write(0, 0)
            self.assertEqual(responses, [0, 2, 3])
            self.assertEqual(rft.testbench.cycle - start, 12)

    def test_wide_write_defer(self):
        """test multi-word write-deferring fields"""
        rft = RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'fields': [
                {
                    'address': 0,
                    'bitrange': '63..0',
                    'repeat': 4,
                    'field-repeat': 1,
                    'stride': 2,
                    'name': 'a',
                    'behavior': 'custom',
                    'interfaces': [{'state': 'count:3'}, {'state': 'data:64'}, {'state': 'busy'}],
                    'write-can-block': True,
                    'write-request': (
                        'if $s.busy$ = \'1\' then\n'
                        '  if $resp_ready$ then\n'
                        '    $block$ := true;\n'
                        '  end if;\n'
                        'else\n'
                        '  $s.data$ := $data$;\n'
                        '  $s.busy$ := \'1\';\n'
                        '  $defer$ := true;\n'
                        'end if;\n'
                    ),
                    'write-response': (
                        'if $s.count$ = "111" then\n'
                        '  case $s.data$(1 downto 0) is\n'
                        '    when "00" => $ack$ := true;\n'
                        '    when "01" => $nack$ := true;\n'
                        '    when others => null;\n'
                        '  end case;\n'
                        '  $s.busy$ := \'0\';\n'
                        'else\n'
                        '  $block$ := true;\n'
                        'end if;\n'
                    ),
                    'post-access': (
                        'if $s.busy$ = \'1\' then\n'
                        '  if $s.count$ /= "111" then\n'
                        '    $s.count$ := std_logic_vector(unsigned($s.count$) + 1);\n'
                        '  end if;\n'
                        'else\n'
                        '  $s.count$ := "000";\n'
                        'end if;\n'
                    ),
                },
            ]})
        self.assertEqual(rft.ports, ('bus',))
        with rft as objs:
            start = rft.testbench.cycle
            objs.bus.write(0, 0)
            self.assertEqual(rft.testbench.cycle - start, 2)
            objs.bus.write(4, 0)
            self.assertEqual(rft.testbench.cycle - start, 11)

            start = rft.testbench.cycle
            responses = []
            def callback(resp):
                responses.append(int(resp))
            objs.bus.async_write(callback, 8, 0)
            objs.bus.async_write(callback, 12, 0)
            objs.bus.async_write(callback, 16, 1)
            objs.bus.async_write(callback, 20, 0)
            objs.bus.async_write(callback, 24, 2)
            objs.bus.async_write(callback, 28, 0)
            objs.bus.async_write(callback, 0, 0)
            objs.bus.write(4, 0)
            self.assertEqual(responses, [0, 0, 0, 2, 0, 3, 0])
            self.assertEqual(rft.testbench.cycle - start, 37)

    @staticmethod
    def test_mixed():
        """test register with write-defer and read field"""
        # Just check that constructing this doesn't raise an exception; this
        # was a problem at some point.
        RegisterFileTestbench({
            'metadata': {'name': 'test'},
            'fields': [
                {
                    'address': 0,
                    'bitrange': '3..0',
                    'name': 'a',
                    'behavior': 'custom',
                    'write-request': (
                        '$defer$ := true;\n'
                    ),
                    'write-response': (
                        '$ack$ := true;\n'
                    ),
                },
                {
                    'address': 0,
                    'bitrange': '7..4',
                    'name': 'b',
                    'behavior': 'constant',
                    'value': 0,
                },
            ]})

    def test_error(self):
        """test defer-related errors"""
        msg = r'deferring fields cannot share a register with other fields \(`A`\)'
        with self.assertRaisesRegex(Exception, msg):
            RegisterFileTestbench({
                'metadata': {'name': 'test'},
                'fields': [
                    {
                        'address': 0,
                        'bitrange': '3..0',
                        'name': 'a',
                        'behavior': 'custom',
                        'write-request': (
                            '$defer$ := true;\n'
                        ),
                        'write-response': (
                            '$ack$ := true;\n'
                        ),
                    },
                    {
                        'address': 0,
                        'bitrange': '7..4',
                        'name': 'b',
                        'behavior': 'control',
                    },
                ]})
