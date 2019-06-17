from unittest import TestCase
import os
import tempfile

from vhdmmio.vhdl.match import match_template

class TestVhdlMatch(TestCase):

    def test_empty(self):
        self.assertEquals(match_template(32, []), '')

    def test_if(self):
        self.assertEquals(match_template(32, [(8, 3)]), '\n'.join([
            'if $address$(31 downto 2) = "000000000000000000000000000010" then',
            '  -- $address$ = 000000000000000000000000000010--',
            '$ ADDR_0x8',
            'end if;',
        ]))

        self.assertEquals(match_template(32, [(8, 3)], optimize=True), '\n'.join([
            '-- $address$ = 000000000000000000000000000010--',
            '$ADDR_0x8',
        ]))

    def test_if_else(self):
        self.assertEquals(match_template(32, [(4, 3), (0, 3)]), '\n'.join([
            'if $address$(31 downto 3) = "00000000000000000000000000000" then',
            '  if $address$(2) = \'0\' then',
            '    -- $address$ = 000000000000000000000000000000--',
            '$   ADDR_0x0',
            '  else',
            '    -- $address$ = 000000000000000000000000000001--',
            '$   ADDR_0x4',
            '  end if;',
            'end if;',
        ]))

        self.assertEquals(match_template(32, [(4, 3), (0, 3)], optimize=True), '\n'.join([
            'if $address$(2) = \'0\' then',
            '  -- $address$ = 000000000000000000000000000000--',
            '$ ADDR_0x0',
            'else',
            '  -- $address$ = 000000000000000000000000000001--',
            '$ ADDR_0x4',
            'end if;',
        ]))

    def test_if_elsif(self):
        self.assertEquals(match_template(32, [(8, 7), (4, 3), (0, 3)], optimize=True), '\n'.join([
            'if $address$(3) = \'1\' then',
            '  -- $address$ = 00000000000000000000000000001---',
            '$ ADDR_0x8',
            'elsif $address$(2) = \'0\' then',
            '  -- $address$ = 000000000000000000000000000000--',
            '$ ADDR_0x0',
            'else',
            '  -- $address$ = 000000000000000000000000000001--',
            '$ ADDR_0x4',
            'end if;',
        ]))

        self.assertEquals(match_template(32, [(12, 3), (8, 3), (0, 7)], optimize=True), '\n'.join([
            'if $address$(3) = \'0\' then',
            '  -- $address$ = 00000000000000000000000000000---',
            '$ ADDR_0x0',
            'elsif $address$(2) = \'0\' then',
            '  -- $address$ = 000000000000000000000000000010--',
            '$ ADDR_0x8',
            'else',
            '  -- $address$ = 000000000000000000000000000011--',
            '$ ADDR_0xC',
            'end if;',
        ]))

    def test_case_statement(self):
        self.assertEquals(match_template(32, [(8, 3), (4, 3)]), '\n'.join([
            'if $address$(31 downto 4) = "0000000000000000000000000000" then',
            '  case $address$(3 downto 2) is',
            '    when "01" =>',
            '      -- $address$ = 000000000000000000000000000001--',
            '$     ADDR_0x4',
            '    when "10" =>',
            '      -- $address$ = 000000000000000000000000000010--',
            '$     ADDR_0x8',
            '    when others =>',
            '      null;',
            '  end case;',
            'end if;',
        ]))

        self.assertEquals(match_template(32, [(8, 3), (4, 3)], optimize=True), '\n'.join([
            'case $address$(3 downto 2) is',
            '  when "01" =>',
            '    -- $address$ = 000000000000000000000000000001--',
            '$   ADDR_0x4',
            '  when others => -- "10"',
            '    -- $address$ = 000000000000000000000000000010--',
            '$   ADDR_0x8',
            'end case;',
        ]))

    def test_common_suffix(self):
        self.assertEquals(match_template(32, [16, 32]), '\n'.join([
            'if $address$(31 downto 6) = "00000000000000000000000000" then',
            '  if $address$(3 downto 0) = "0000" then',
            '    case $address$(5 downto 4) is',
            '      when "01" =>',
            '        -- $address$ = 00000000000000000000000000010000',
            '$       ADDR_0x10',
            '      when "10" =>',
            '        -- $address$ = 00000000000000000000000000100000',
            '$       ADDR_0x20',
            '      when others =>',
            '        null;',
            '    end case;',
            '  end if;',
            'end if;',
        ]))

        self.assertEquals(match_template(32, [16, 32], optimize=True), '\n'.join([
            'case $address$(5 downto 4) is',
            '  when "01" =>',
            '    -- $address$ = 00000000000000000000000000010000',
            '$   ADDR_0x10',
            '  when others => -- "10"',
            '    -- $address$ = 00000000000000000000000000100000',
            '$   ADDR_0x20',
            'end case;',
        ]))

    def test_duplicate(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            match_template(32, [3, 3])

    def test_overlapping(self):
        with self.assertRaisesRegex(ValueError, 'overlap'):
            match_template(32, [3, (3, 3)])
