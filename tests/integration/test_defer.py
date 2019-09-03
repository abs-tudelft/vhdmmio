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
