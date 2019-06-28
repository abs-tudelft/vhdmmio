from unittest import TestCase
import os
import re
import tempfile

import vhdmmio
from vhdmmio.core.regfile import RegisterFile

class MatchError(Exception):
    def __init__(self, stack, msg, *args):
        super().__init__('.'.join(stack) + ': ' + msg % args)

def _match_partial(actual, expected, stack=[]):
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            raise MatchError(stack, 'not a dict: %s', actual)
        for key, expected_value in expected.items():
            _match_partial(actual.get(key, None), expected_value, stack + [key])

    elif isinstance(expected, set):
        if not isinstance(actual, list):
            raise MatchError(stack, 'not a list: %s', actual)
        for expected_value in expected:
            for idx, actual_value in enumerate(actual):
                try:
                    _match_partial(actual_value, expected_value, stack + [str(idx)])
                    break
                except MatchError:
                    pass
            else:
                raise MatchError(stack, 'no match found for %s', expected_value)

    elif isinstance(expected, list):
        if not isinstance(actual, list):
            raise MatchError(stack, 'not a list: %s', actual)
        idx = 0
        for expected_value in expected:
            match_found = False
            while not match_found and i < len(actual):
                try:
                    _match_partial(actual_value, expected_value, stack + [str(idx)])
                    match_found = True
                except MatchError:
                    pass
                idx += 1
            if not match_found:
                raise MatchError(stack, 'no match found for %s', expected_value)

    elif isinstance(expected, tuple):
        if not isinstance(actual, list):
            raise MatchError(stack, 'not a list: %s', actual)
        idx = -1
        for idx, (actual_value, expected_value) in enumerate(zip(actual, expected)):
            _match_partial(actual_value, expected_value, stack + [str(idx)])
        if idx < len(expected) - 1:
            raise MatchError(stack + [str(idx+1)], 'does not exist')
        elif idx < len(actual) - 1:
            raise MatchError(stack + [str(idx+1)], 'unexpected output: %s', actual_value[idx+1])

    elif hasattr(expected, 'match') and hasattr(expected, 'findall'):
        # probably a regex matcher...
        if not expected.match(str(expected)):
            raise MatchError(stack, 'failed to match: ', expected)

    elif actual != expected:
        raise MatchError(stack, 'incorrect value: ', expected)

class TestCoreIntegration(TestCase):

    def _test_valid(self, input_dict, exact=None, partial=None, regs=None):
        regfile = RegisterFile.from_dict(input_dict)
        output_dict = regfile.to_dict()
        self.maxDiff = None
        self.assertEquals(RegisterFile.from_dict(output_dict).to_dict(), output_dict)

        # Exact matching.
        if exact is not None:
            self.assertEquals(output_dict, exact)

        # Partial matching.
        if partial is not None:
            _match_partial(output_dict, partial)

        # Register matching.
        if regs is not None:
            self.assertEquals(len(regfile.registers), len(regs), 'number of registers')
            for reg_idx, (act_reg, exp_reg) in enumerate(zip(regfile.registers, regs)):
                self.assertEquals(len(act_reg.fields), len(exp_reg),
                                  'number of fields in register %d' % reg_idx)
                for field_idx, (act_field, exp_field) in enumerate(zip(act_reg.fields, exp_reg)):
                    exp_name, exp_bitrange, exp_index = exp_field
                    self.assertEquals(act_field.meta.name, exp_name,
                                      'field %d.%d name' % (reg_idx, field_idx))
                    self.assertEquals(act_field.bitrange.to_spec(), exp_bitrange,
                                      'field %d.%d bitrange' % (reg_idx, field_idx))
                    self.assertEquals(act_field.index, exp_index,
                                      'field %d.%d index' % (reg_idx, field_idx))

        return regfile

    def _test_invalid(self, input_dict, exception, regex=None):
        if regex is None:
            checker = self.assertRaises(exception)
        else:
            checker = self.assertRaisesRegex(exception, regex)
        with checker:
            RegisterFile.from_dict(input_dict)

    def test_empty(self):
        self._test_valid({
            'meta': {'name': 'test'},
        }, partial={
            'meta': {'name': 'test'},
            'fields': (),
        }, regs=[])

    def test_missing_meta(self):
        self._test_invalid({}, (ValueError, TypeError), 'missing')

    def test_bus_width(self):
        self.assertEquals(self._test_valid({
            'meta': {'name': 'test'}
        }).bus_width, 32)

        self.assertEquals(self._test_valid({
            'meta': {'name': 'test'},
            'features': {'bus-width': 32}
        }).bus_width, 32)

        self.assertEquals(self._test_valid({
            'meta': {'name': 'test'},
            'features': {'bus-width': 64}
        }).bus_width, 64)

        self._test_invalid({
            'meta': {'name': 'test'},
            'features': {'bus-width': 33}
        }, ValueError, 'bus-width')

        self._test_invalid({
            'meta': {'name': 'test'},
            'features': {'bus-width': 'hello'}
        }, ValueError)

    def test_repetition(self):
        self._test_valid({
            'meta': {'name': 'test'},
            'fields': [
                {
                    'register-name': 'reg',
                    'name': 'reg',
                    'address': '0x0:7..0',
                    'repeat': 4,
                }
            ]
        }, regs=[
            [
                ('reg0', '0x00000000:7..0', 0),
                ('reg1', '0x00000000:15..8', 1),
                ('reg2', '0x00000000:23..16', 2),
                ('reg3', '0x00000000:31..24', 3),
            ]
        ])

        self._test_invalid({
            'meta': {'name': 'test'},
            'fields': [
                {
                    'register-name': 'reg',
                    'name': 'reg',
                    'address': [],
                }
            ]
        }, ValueError, 'at least one address must be specified')

        self._test_invalid({
            'meta': {'name': 'test'},
            'fields': [
                {
                    'register-name': 'reg',
                    'name': 'reg',
                    'address': '0x0:7..0',
                    'repeat': 0,
                }
            ]
        }, ValueError, 'repeat must be positive')

        self._test_invalid({
            'meta': {'name': 'test'},
            'fields': [
                {
                    'register-name': 'reg',
                    'name': 'reg',
                    'address': ['0x0:7..0', '0x0:17..10', '0x0:27..20', '0x8:7..0'],
                    'repeat': 4
                }
            ]
        }, ValueError, 'cannot combine automatic repetition with multiple addresses')

    def test_strided_repetition(self):
        self._test_valid({
            'meta': {'name': 'test'},
            'fields': [
                {
                    'register-name': 'reg',
                    'name': 'reg',
                    'address': '0x0:7..0',
                    'repeat': 4,
                    'field-repeat': 2,
                }
            ]
        }, regs=[
            [
                ('reg0', '0x00000000:7..0', 0),
                ('reg1', '0x00000000:15..8', 1),
            ], [
                ('reg2', '0x00000004:7..0', 2),
                ('reg3', '0x00000004:15..8', 3),
            ]
        ])

        self._test_valid({
            'meta': {'name': 'test'},
            'fields': [
                {
                    'register-name': 'reg',
                    'name': 'reg',
                    'address': '0x0:7..0',
                    'repeat': 4,
                    'field-repeat': 3,
                    'stride': 8,
                    'field-stride': 10,
                }
            ]
        }, regs=[
            [
                ('reg0', '0x00000000:7..0', 0),
                ('reg1', '0x00000000:17..10', 1),
                ('reg2', '0x00000000:27..20', 2),
            ], [
                ('reg3', '0x00000008:7..0', 3),
            ]
        ])

        self._test_valid({
            'meta': {'name': 'test'},
            'fields': [
                {
                    'register-name': 'reg',
                    'name': 'reg',
                    'address': '0x4:31..24',
                    'repeat': 4,
                    'field-repeat': 3,
                    'stride': -4,
                    'field-stride': -10,
                }
            ]
        }, regs=[
            [
                ('reg3', '0x00000000:31..24', 3),
            ], [
                ('reg2', '0x00000004:11..4', 2),
                ('reg1', '0x00000004:21..14', 1),
                ('reg0', '0x00000004:31..24', 0),
            ]
        ])

        self._test_invalid({
            'meta': {'name': 'test'},
            'fields': [
                {
                    'register-name': 'reg',
                    'name': 'reg',
                    'address': '0x4:31..24',
                    'repeat': 6,
                    'field-stride': -8,
                }
            ]
        }, ValueError, 'negative bit index')

        self._test_invalid({
            'meta': {'name': 'test'},
            'fields': [
                {
                    'register-name': 'reg',
                    'name': 'reg',
                    'address': '0x4:31..24',
                    'repeat': 6,
                    'field-stride': -6,
                }
            ]
        }, ValueError, 'field-stride is smaller than the width of a single field')

        self._test_invalid({
            'meta': {'name': 'test'},
            'fields': [
                {
                    'register-name': 'reg',
                    'name': 'reg',
                    'address': '0x4:31..24',
                    'repeat': 6,
                    'field-repeat': 1,
                    'stride': 0
                }
            ]
        }, ValueError, 'stride is smaller than')

        self._test_invalid({
            'meta': {'name': 'test'},
            'fields': [
                {
                    'register-name': 'reg',
                    'name': 'reg',
                    'address': '0x4:31..24',
                    'repeat': 6,
                    'field-repeat': 1,
                    'stride': 5
                }
            ]
        }, ValueError, 'stride is not aligned')

        self._test_invalid({
            'meta': {'name': 'test'},
            'fields': [
                {
                    'register-name': 'reg',
                    'name': 'reg',
                    'address': '0x4:31..24',
                    'repeat': 6,
                    'field-repeat': -1,
                    'stride': 0
                }
            ]
        }, ValueError, 'must be positive')

        self._test_valid({
            'meta': {'name': 'test'},
            'fields': [
                {
                    'register-name': 'reg',
                    'name': 'reg',
                    'address': ['0x0:7..0', '0x0:17..10', '0x0:27..20', '0x8:7..0'],
                }
            ]
        }, regs=[
            [
                ('reg0', '0x00000000:7..0', 0),
                ('reg1', '0x00000000:17..10', 1),
                ('reg2', '0x00000000:27..20', 2),
            ], [
                ('reg3', '0x00000008:7..0', 3),
            ]
        ])
