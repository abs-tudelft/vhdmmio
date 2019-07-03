"""Unit tests for the `vhdmmio.core.metadata` submodule."""

from unittest import TestCase
from vhdmmio.core.metadata import Metadata, ExpandedMetadata

class TestMetadata(TestCase):
    """Unit tests for the `vhdmmio.core.metadata` submodule."""

    def _assert_meta(self, metadata, mnemonic, name, brief, doc):
        """Asserts that the components of the given metadata object match the
        given values."""
        self.assertEqual(metadata.mnemonic, mnemonic)
        self.assertEqual(metadata.name, name)
        self.assertEqual(metadata.markdown_brief, brief)
        self.assertEqual(metadata.markdown_doc, doc)

    def test_constructor(self):
        """test the Metadata constructor"""
        self._assert_meta(
            Metadata(name='test_snake_case'),
            'TEST_SNAKE_CASE',
            'test_snake_case',
            'Test snake case.',
            '')

        self._assert_meta(
            Metadata(name='camelCaseWITHAbbreviations'),
            'CAMELCASEWITHABBREVIATIONS',
            'camelCaseWITHAbbreviations',
            'Camel Case WITH Abbreviations.',
            '')

        self._assert_meta(
            Metadata(mnemonic='HELLO'),
            'HELLO',
            'hello',
            'Hello.',
            '')

        self._assert_meta(
            Metadata(mnemonic='MNEM', name='name', brief='Brief!', doc='Docu-\nmen-\ntation!'),
            'MNEM',
            'name',
            'Brief!',
            'Docu-\nmen-\ntation!')

        with self.assertRaisesRegex(ValueError, 'either name or mnemonic'):
            Metadata()

        with self.assertRaisesRegex(ValueError, 'count must be positive'):
            Metadata(count=-1, name='hello')

    def test_mnemonic_validity(self):
        """tests the metadata mnemonic validity checker"""
        with self.assertRaisesRegex(ValueError, 'not a valid mnemonic'):
            Metadata(mnemonic='hello')

        with self.assertRaisesRegex(ValueError, 'cannot end in a digit'):
            Metadata(mnemonic='MNEM33', count=1)

        Metadata(mnemonic='MNEM33')

    def test_name_validity(self):
        """tests the metadata name validity checker"""
        with self.assertRaisesRegex(ValueError, 'not a valid identifier'):
            Metadata(mnemonic='X', name='hello there')

        with self.assertRaisesRegex(ValueError, 'cannot end in a digit'):
            Metadata(mnemonic='X', name='hello33', count=1)

        Metadata(mnemonic='X', name='hello33')

    def test_brief_validity(self):
        """tests the metadata brief validity checker"""
        with self.assertRaisesRegex(ValueError, 'newlines'):
            Metadata(name='hello', brief='hello\nthere')

    def test_expansion(self):
        """tests expanding array indices in metadata objects"""
        meta = Metadata(name='hello', doc='test {index}')

        with self.assertRaisesRegex(ValueError, 'index out of range'):
            meta[2] #pylint: disable=W0104

        self._assert_meta(
            meta[None],
            'HELLO',
            'hello',
            'Hello.',
            'test ')

        meta = Metadata(
            count=3,
            name='hello',
            brief='test {index} test',
            doc='foo {index} bar {index} baz')

        self.assertEqual(len(meta), 3)
        self.assertEqual(list(map(lambda x: x.name, meta)), ['hello0', 'hello1', 'hello2'])

        self._assert_meta(
            meta[1],
            'HELLO1',
            'hello1',
            'test 1 test',
            'foo 1 bar 1 baz')

        with self.assertRaisesRegex(ValueError, 'cannot get mnemonic for range of objects'):
            meta[None].mnemonic #pylint: disable=W0104
        with self.assertRaisesRegex(ValueError, 'cannot get name for range of objects'):
            meta[None].name #pylint: disable=W0104
        self.assertEqual(meta[None].markdown_mnemonic, '`HELLO`*0..2*')
        self.assertEqual(meta[None].markdown_name, '`hello`*0..2*')
        self.assertEqual(meta[None].markdown_brief, 'test *0..2* test')
        self.assertEqual(meta[None].markdown_doc, 'foo *0..2* bar *0..2* baz')

        self.assertEqual(meta[1].to_markdown(), '\n'.join([
            '# `hello1` (`HELLO1`)',
            '',
            'test 1 test',
            '',
            'foo 1 bar 1 baz',
            '',
            '',
        ]))

    def test_conflicts(self):
        """tests metadata conflict detection"""

        metas = [
            Metadata(mnemonic='A', name='x')[None],
            Metadata(mnemonic='A', name='y')[None]]

        with self.assertRaisesRegex(ValueError, 'mnemonics for [xy] and [xy] are both A'):
            ExpandedMetadata.check_siblings(metas)
        ExpandedMetadata.check_cousins(metas)

        metas = [
            Metadata(mnemonic='A', name='x')[None],
            Metadata(mnemonic='B', name='X')[None]]

        ExpandedMetadata.check_siblings(metas)
        with self.assertRaisesRegex(ValueError, 'duplicate name [xX]'):
            ExpandedMetadata.check_cousins(metas)
