"""Unit tests for the VHDL address decoder generator."""

from unittest import TestCase
from vhdmmio.vhdl.decoder import decoder_template, Decoder
from vhdmmio.template import TemplateEngine

class TestVhdlDecoder(TestCase):
    """Unit tests for the VHDL address decoder generator."""

    maxDiff = None

    def test_empty(self):
        """tests constructing an empty address decoder"""
        self.assertEqual(decoder_template(32, []), '')

    def test_if(self):
        """tests address decoder if statement construction"""
        self.assertEqual(decoder_template(32, [(8, 3)]), '\n'.join([
            'if $address$(31 downto 2) = "000000000000000000000000000010" then',
            '  -- $address$ = 000000000000000000000000000010--',
            '$ ADDR_0x8',
            'end if;',
        ]))

        self.assertEqual(decoder_template(32, [(8, 3)], optimize=True), '\n'.join([
            '-- $address$ = 000000000000000000000000000010--',
            '$ADDR_0x8',
        ]))

    def test_if_else(self):
        """tests address decoder if-else statement construction"""
        self.assertEqual(decoder_template(32, [(4, 3), (0, 3)]), '\n'.join([
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

        self.assertEqual(decoder_template(32, [(4, 3), (0, 3)], optimize=True), '\n'.join([
            'if $address$(2) = \'0\' then',
            '  -- $address$ = 000000000000000000000000000000--',
            '$ ADDR_0x0',
            'else',
            '  -- $address$ = 000000000000000000000000000001--',
            '$ ADDR_0x4',
            'end if;',
        ]))

    def test_if_elsif(self):
        """tests address decoder if-elsif statement construction"""
        self.assertEqual(decoder_template(32, [(8, 7), (4, 3), (0, 3)], optimize=True), '\n'.join([
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

        self.assertEqual(decoder_template(32, [(12, 3), (8, 3), (0, 7)], optimize=True), '\n'.join([
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
        """tests address decoder case statement construction"""
        self.assertEqual(decoder_template(32, [(8, 3), (4, 3)]), '\n'.join([
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

        self.assertEqual(decoder_template(32, [(8, 3), (4, 3)], optimize=True), '\n'.join([
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
        """tests address decoder common suffix detection"""
        self.assertEqual(decoder_template(32, [16, 32]), '\n'.join([
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

        self.assertEqual(decoder_template(32, [16, 32], optimize=True), '\n'.join([
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
        """tests address decoder duplicate address error"""
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            decoder_template(32, [3, 3])

    def test_overlapping(self):
        """tests address decoder overlapping address error"""
        with self.assertRaisesRegex(ValueError, 'overlap'):
            decoder_template(32, [3, (3, 3)])

        self.assertEqual(decoder_template(32, [3, (3, 3)], allow_overlap=True), '\n'.join([
            'if $address$(31 downto 2) = "000000000000000000000000000000" then',
            '  if $address$(1 downto 0) = "11" then',
            '    -- $address$ = 00000000000000000000000000000011',
            '$   ADDR_0x3',
            '  end if;',
            '',
            '  -- $address$ = 000000000000000000000000000000--',
            '$ ADDR_0x0',
            'end if;',
        ]))

    def test_builder(self):
        """tests address decoder builder"""
        decoder = Decoder('addr', 32, True)
        decoder.add_action('block for address 0', 0)
        decoder.add_action('block for address 4', 4, 2)
        decoder.add_action('another block for address 0', 0)
        self.assertEqual(decoder.generate(), '\n'.join([
            'if addr(2) = \'0\' then',
            '  -- addr = 00000000000000000000000000000000',
            '',
            '  block for address 0',
            '',
            '  another block for address 0',
            '',
            'else',
            '  -- addr = 000000000000000000000000000001-0',
            '',
            '  block for address 4',
            '',
            'end if;',
        ]))
        tple = TemplateEngine()
        decoder.append_to_template(tple, 'BLOCK', 'comment for decoder')
        self.assertEqual(tple.apply_str_to_str('$BLOCK', comment='-- '), '\n'.join([
            '-- comment for decoder',
            'if addr(2) = \'0\' then',
            '  -- addr = 00000000000000000000000000000000',
            '',
            '  block for address 0',
            '',
            '  another block for address 0',
            '',
            'else',
            '  -- addr = 000000000000000000000000000001-0',
            '',
            '  block for address 4',
            '',
            'end if;',
            ''
        ]))
