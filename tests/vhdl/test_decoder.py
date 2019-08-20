"""Unit tests for the VHDL address decoder generator."""

from unittest import TestCase
from vhdmmio.vhdl.address_decoder import AddressDecoder
from vhdmmio.core.address import MaskedAddress
from vhdmmio.template import TemplateEngine

class TestVhdlDecoder(TestCase):
    """Unit tests for the VHDL address decoder generator."""

    maxDiff = None

    def _test_decoder(self, addresses, match=None,
                      optimize=False, allow_overlap=False, allow_duplicate=False):
        dec = AddressDecoder('address', 32, optimize, allow_overlap, allow_duplicate)
        for address in addresses:
            dec[MaskedAddress.parse_config(address)] = str(address)
        result = str(dec)
        if match is not None:
            self.assertEqual(result, '\n'.join(match))
        return dec

    def test_empty(self):
        """tests constructing an empty address decoder"""
        self._test_decoder([], [''])

    def test_if(self):
        """tests address decoder if statement construction"""
        self._test_decoder(['8|3'], [
            'if address(31 downto 2) = "000000000000000000000000000010" then',
            '  -- address = 000000000000000000000000000010--',
            '',
            '  8|3',
            '',
            'end if;',
        ])

        self._test_decoder(['8|3'], optimize=True, match=[
            '-- address = 000000000000000000000000000010--',
            '',
            '8|3',
        ])

    def test_if_else(self):
        """tests address decoder if-else statement construction"""
        self._test_decoder(['4|3', '0|3'], match=[
            'if address(31 downto 3) = "00000000000000000000000000000" then',
            '  if address(2) = \'0\' then',
            '    -- address = 000000000000000000000000000000--',
            '',
            '    0|3',
            '',
            '  else',
            '    -- address = 000000000000000000000000000001--',
            '',
            '    4|3',
            '',
            '  end if;',
            'end if;',
        ])

        self._test_decoder(['4|3', '0|3'], optimize=True, match=[
            'if address(2) = \'0\' then',
            '  -- address = 000000000000000000000000000000--',
            '',
            '  0|3',
            '',
            'else',
            '  -- address = 000000000000000000000000000001--',
            '',
            '  4|3',
            '',
            'end if;',
        ])

    def test_if_elsif(self):
        """tests address decoder if-elsif statement construction"""
        self._test_decoder(['8|7', '4|3', '0|3'], optimize=True, match=[
            'if address(3) = \'1\' then',
            '  -- address = 00000000000000000000000000001---',
            '',
            '  8|7',
            '',
            'elsif address(2) = \'0\' then',
            '  -- address = 000000000000000000000000000000--',
            '',
            '  0|3',
            '',
            'else',
            '  -- address = 000000000000000000000000000001--',
            '',
            '  4|3',
            '',
            'end if;',
        ])

        self._test_decoder(['12|3', '8|3', '0|7'], optimize=True, match=[
            'if address(3) = \'0\' then',
            '  -- address = 00000000000000000000000000000---',
            '',
            '  0|7',
            '',
            'elsif address(2) = \'0\' then',
            '  -- address = 000000000000000000000000000010--',
            '',
            '  8|3',
            '',
            'else',
            '  -- address = 000000000000000000000000000011--',
            '',
            '  12|3',
            '',
            'end if;',
        ])

    def test_case_statement(self):
        """tests address decoder case statement construction"""
        self._test_decoder(['8|3', '4|3'], match=[
            'if address(31 downto 4) = "0000000000000000000000000000" then',
            '  case address(3 downto 2) is',
            '    when "01" =>',
            '      -- address = 000000000000000000000000000001--',
            '',
            '      4|3',
            '',
            '    when "10" =>',
            '      -- address = 000000000000000000000000000010--',
            '',
            '      8|3',
            '',
            '    when others =>',
            '      null;',
            '  end case;',
            'end if;',
        ])

        self._test_decoder(['8|3', '4|3'], optimize=True, match=[
            'case address(3 downto 2) is',
            '  when "01" =>',
            '    -- address = 000000000000000000000000000001--',
            '',
            '    4|3',
            '',
            '  when others => -- "10"',
            '    -- address = 000000000000000000000000000010--',
            '',
            '    8|3',
            '',
            'end case;',
        ])

    def test_common_suffix(self):
        """tests address decoder common suffix detection"""
        self._test_decoder([16, 32], match=[
            'if address(31 downto 6) = "00000000000000000000000000" then',
            '  if address(3 downto 0) = "0000" then',
            '    case address(5 downto 4) is',
            '      when "01" =>',
            '        -- address = 00000000000000000000000000010000',
            '',
            '        16',
            '',
            '      when "10" =>',
            '        -- address = 00000000000000000000000000100000',
            '',
            '        32',
            '',
            '      when others =>',
            '        null;',
            '    end case;',
            '  end if;',
            'end if;',
        ])

        self._test_decoder([16, 32], optimize=True, match=[
            'case address(5 downto 4) is',
            '  when "01" =>',
            '    -- address = 00000000000000000000000000010000',
            '',
            '    16',
            '',
            '  when others => -- "10"',
            '    -- address = 00000000000000000000000000100000',
            '',
            '    32',
            '',
            'end case;',
        ])

    def test_duplicate(self):
        """tests address decoder duplicate address error"""
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            self._test_decoder([3, '3|0'])

        self._test_decoder([3, '3|0'], allow_duplicate=True, match=[
            'if address(31 downto 0) = "00000000000000000000000000000011" then',
            '  -- address = 00000000000000000000000000000011',
            '',
            '  3',
            '',
            '  3|0',
            '',
            'end if;',
        ])

    def test_overlapping(self):
        """tests address decoder overlapping address error"""
        with self.assertRaisesRegex(ValueError, 'overlap'):
            self._test_decoder([3, '3|3'])

        self._test_decoder([3, '3|3'], allow_overlap=True, match=[
            'if address(31 downto 2) = "000000000000000000000000000000" then',
            '  if address(1 downto 0) = "11" then',
            '    -- address = 00000000000000000000000000000011',
            '',
            '    3',
            '',
            '  end if;',
            '',
            '  -- address = 000000000000000000000000000000--',
            '',
            '  3|3',
            '',
            'end if;',
        ])

    def test_template(self):
        """tests adding decoders to templates"""
        tple = TemplateEngine()
        self._test_decoder([3]).append_to_template(tple, 'BLOCK', 'comment for decoder')
        self.assertEqual(tple.apply_str_to_str('$BLOCK', comment='-- '), '\n'.join([
            '-- comment for decoder',
            'if address(31 downto 0) = "00000000000000000000000000000011" then',
            '  -- address = 00000000000000000000000000000011',
            '',
            '  3',
            '',
            'end if;',
            ''
        ]))
