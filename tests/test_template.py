"""Module for unit-testing vhdmmio.template."""

from unittest import TestCase
import os
import tempfile

from vhdmmio.template import TemplateEngine, TemplateSyntaxError, annotate_block

class TestTemplateEngine(TestCase):
    """Unit-tests for vhdmmio.template."""

    def test_var_get_set(self):
        """test template variable access"""
        engine = TemplateEngine()
        self.assertEqual(sorted(engine), [])
        engine['a'] = 'a'
        engine['b'] = 3
        self.assertEqual(engine['a'], 'a')
        self.assertEqual(engine['b'], 3)
        self.assertEqual(sorted(engine), ['a', 'b'])
        engine['a'] = 'b'
        self.assertEqual(engine['a'], 'b')
        self.assertEqual(engine['b'], 3)
        del engine['a']
        with self.assertRaises(Exception):
            engine['a'] #pylint: disable=W0104
        self.assertEqual(sorted(engine), ['b'])
        self.assertEqual(engine['b'], 3)

    def test_split_directives(self):
        """test template directive splitting"""
        #pylint: disable=W0212
        self.assertEqual(TemplateEngine._split_directives('\n'.join([
            '$if a',
            'good',
            'a$a$a',
            '$endif',
        ])), [
            '',
            ((None, 1), '$if a\n'),
            'good\na',
            ((None, 3), '$a$'),
            'a\n',
            ((None, 4), '$endif\n'),
            '',
        ])

        self.assertEqual(TemplateEngine._split_directives(annotate_block('\n'.join([
            '$if a',
            'good',
            'a$a$a',
            '$endif',
        ]), fname='test')), [
            '@!v->source=test:1\n',
            (('test', 1), '$if a\n'),
            '@!v->source=test:2\ngood\n@!v->source=test:3\na',
            (('test', 3), '$a$'),
            'a\n@!v->source=test:4\n',
            (('test', 4), '$endif\n'),
            '@!^->end\n',
        ])

        self.assertEqual(TemplateEngine._split_directives('\n'.join([
            'good',
            '$if a',
            'good',
            '$else',
            'bad',
            '$else',
            'good again because why not',
            'a$a$a',
            '$endif',
            'good',
        ])), [
            'good\n',
            ((None, 2), '$if a\n'),
            'good\n',
            ((None, 4), '$else\n'),
            'bad\n',
            ((None, 6), '$else\n'),
            'good again because why not\na',
            ((None, 8), '$a$'),
            'a\n',
            ((None, 9), '$endif\n'),
            'good\n',
        ])

    def test_conditionals(self):
        """test template condition directives"""
        engine = TemplateEngine()

        engine['a'] = True
        self.assertEqual(engine.apply_str_to_str([
            'good',
            '$if a',
            'good',
            '$else',
            'bad',
            '$else',
            'good again because why not',
            '$a$',
            '$endif',
            'good',
        ]), '\n'.join([
            'good',
            'good',
            'good again because why not',
            'True',
            'good',
        ]) + '\n')

        engine['a'] = False
        self.assertEqual(engine.apply_str_to_str([
            'good',
            '$if a',
            'bad',
            '$else',
            'good',
            '$else',
            'also bad',
            '$bad directive',
            '$endif',
            'good',
        ]), '\n'.join([
            'good',
            'good',
            'good',
        ]) + '\n')

        for i in range(4):
            engine['a'] = i
            self.assertEqual(engine.apply_str_to_str([
                '$if a < 2',
                '$if a < 1',
                '0',
                '$else',
                '1',
                '$endif',
                '$else',
                '$if a < 3',
                '2',
                '$else',
                '3',
                '$endif',
                '$endif',
            ]), '{}\n'.format(i))

        del engine['a']
        with self.assertRaisesRegex(
                TemplateSyntaxError,
                r"on <unknown> line 2: error in \$if expression: name 'a' is not defined"):
            engine.apply_str_to_str([
                'good',
                '$if a',
                'aaaagh',
                '$endif',
            ])

        with self.assertRaisesRegex(
                TemplateSyntaxError,
                r"on <unknown> line 2: \$if without expression"):
            engine.apply_str_to_str([
                'good',
                '$if',
                'aaaagh',
                '$endif',
            ])

        with self.assertRaisesRegex(
                TemplateSyntaxError,
                r"on <unknown> line 1: \$else without \$if"):
            engine.apply_str_to_str([
                '$else',
            ])

        with self.assertRaisesRegex(
                TemplateSyntaxError,
                r"on <unknown> line 3: \$endif without \$if"):
            engine.apply_str_to_str([
                '$if True',
                '$endif',
                '$endif',
            ])

        with self.assertRaisesRegex(
                TemplateSyntaxError,
                r"on <unknown> line 3: \$if without \$endif"):
            engine.apply_str_to_str([
                '$if True',
                '$endif',
                '$if True',
                '$if True',
                '$endif',
            ])

        with self.assertRaisesRegex(
                TemplateSyntaxError,
                r"on <unknown> line 2: unexpected argument for \$endif"):
            engine.apply_str_to_str([
                '$if True',
                '$endif a',
            ])

        with self.assertRaisesRegex(
                TemplateSyntaxError,
                r"on <unknown> line 2: unexpected argument for \$else"):
            engine.apply_str_to_str([
                '$if True',
                '$else a',
                '$endif',
            ])

    def test_inline(self):
        """test template inline expansion"""
        engine = TemplateEngine()

        with self.assertRaisesRegex(
                TemplateSyntaxError,
                r"on <unknown> line 1: error in inline expression:"):
            engine.apply_str_to_str('error = $a$')

        self.assertEqual(engine.apply_str_to_str('$$'), '$\n')

        self.assertEqual(engine.apply_str_to_str('$"*"*10$'), '**********\n')

        engine['a'] = 3
        self.assertEqual(engine.apply_str_to_str('$33*a$'), '99\n')

    def test_block_and_formatting(self):
        """test template formatting"""
        self.maxDiff = None #pylint: disable=C0103

        test = [
            '@ hello!',
            "@ I'm a bit of test code.",
            '@    I should be a new block.',
            '@  - So should I,',
            '@    but this should be the same line.',
            '@    At some point this should start wrapping... '
            'At some point this should start wrapping... '
            'At some point this should start wrapping... '
            'At some point this should start wrapping...',
            '@  - Different line!',
            '@',
            '@ Paragraph N...',
            '@',
            '@ ...and paragraph N+1.',
            '@',
            '    @ This comment should be indented.',
            'this big line of code should not wrap. '
            'this big line of code should not wrap. '
            'this big line of code should not wrap. '
            'this big line of code should not wrap. '
            'this big line of code should not wrap.',
            'this big line of code can wrap here@and here@and here.@'
            'this big line of code can wrap here@and here@and here.@'
            "here's an at and a wrapping marker: @@@"
            'this big line of code can wrap here@and here@and here.@',
            '@@this big line of code should not wrap. '
            'this big line of code should not wrap '
            'this big line of code should not wrap '
            'this big line of code should not wrap',
            '@@this big line of code can wrap here@and here@and here.@'
            'this big line of code can wrap here@and here@and here.@'
            "here's an at and a wrapping marker: @@@"
            'this big line of code can wrap here@and here@and here.@',
            '@@@ <- at over there and over here -> @@ <-',
        ]

        engine = TemplateEngine()
        engine.append_block('TEST', test)
        engine.append_block('TEST', '')
        engine.append_block('TEST', '@ second block!\nhello\n\n', '', 'there')
        engine.append_block('STUFF', ['@ a bunch of other stuff goes here'])

        self.assertEqual(engine.apply_str_to_str([
            '$STUFF',
            '$ STUFF',
            '$   STUFF',
            '$NOTHING',
        ]), '\n'.join([
            '# a bunch of other stuff goes here',
            '',
            '  # a bunch of other stuff goes here',
            '',
            '    # a bunch of other stuff goes here',
        ]) + '\n')

        engine.reset_block('STUFF')

        self.assertEqual(engine.apply_str_to_str([
            '$STUFF',
            '$ STUFF',
            '$   STUFF',
            '$NOTHING',
        ]), '\n')

        self.assertEqual(engine.apply_str_to_str([
            '$ TEST',
            '@ comment at the end',
        ]), '\n'.join([
            "  # hello! I'm a bit of test code.",
            '  #    I should be a new block.',
            '  #  - So should I, but this should be the same line. At some point this should',
            '  #    start wrapping... At some point this should start wrapping... At some',
            '  #    point this should start wrapping... At some point this should start',
            '  #    wrapping...',
            '  #  - Different line!',
            '  #',
            '  # Paragraph N...',
            '  #',
            '  # ...and paragraph N+1.',
            '  #',
            '      # This comment should be indented.',
            '  this big line of code should not wrap. '
            'this big line of code should not wrap. '
            'this big line of code should not wrap. '
            'this big line of code should not wrap. '
            'this big line of code should not wrap.',
            '  this big line of code can wrap here and here and here.',
            '      this big line of code can wrap here and here and here.',
            "      here's an at and a wrapping marker: @ this big line of code can wrap here",
            '      and here and here.',
            '  # this big line of code should not wrap. '
            'this big line of code should not wrap '
            'this big line of code should not wrap '
            'this big line of code should not wrap',
            '  # this big line of code can wrap here and here and here.',
            '  #     this big line of code can wrap here and here and here.',
            "  #     here's an at and a wrapping marker: @",
            '  #     this big line of code can wrap here and here and here.',
            '  @ <- at over there and over here -> @ <-',
            '',
            '  # second block!',
            '  hello',
            '',
            '  there',
            '',
            '# comment at the end',
        ]) + '\n')

    def test_unknown_directive(self):
        """test template unknown directive error"""
        engine = TemplateEngine()
        with self.assertRaisesRegex(
                TemplateSyntaxError,
                r"on <unknown> line 2: unknown directive: \$i"):
            engine.apply_str_to_str([
                '$test',
                '$i am wrong',
                'boooo',
            ])

    def test_block_definitions(self):
        """test template block definition directives"""
        engine = TemplateEngine()
        engine.append_block('TEST', 'programmatic block', 'second line')
        self.assertEqual(engine.apply_str_to_str([
            '$TEST',
            '$block TEST',
            'template block',
            '  second line, indented',
            '$endblock',
            '$ TEST',
        ]), '\n'.join([
            'programmatic block',
            'second line',
            '',
            '  programmatic block',
            '  second line',
            '',
            '  template block',
            '    second line, indented',
        ]) + '\n')

        self.assertEqual(engine.apply_str_to_str([
            '$block a',
            '$b',
            '$endblock',
            '$block b',
            'expected',
            '$endblock',
            '$a',
        ]), '\n'.join([
            'expected',
        ]) + '\n')

        self.assertEqual(engine.apply_str_to_str([
            '$block a',
            '$33$',
            '$b',
            '$endblock',
            '$block b',
            'expected',
            '$endblock',
            '$a',
        ]), '\n'.join([
            '33',
            '',
            'expected',
        ]) + '\n')

        with self.assertRaisesRegex(
                TemplateSyntaxError,
                r"on <unknown> line 2: block recursion limit reached"):
            engine.apply_str_to_str([
                '$block a',
                '$a',
                '$endblock',
                '$a',
            ])

        with self.assertRaisesRegex(
                TemplateSyntaxError,
                r"on <unknown> line 1: \$block without key"):
            engine.apply_str_to_str([
                '$block',
                '$endblock',
            ])

        with self.assertRaisesRegex(
                TemplateSyntaxError,
                r"on <unknown> line 2: unexpected argument for \$endblock"):
            engine.apply_str_to_str([
                '$block a',
                '$endblock a',
            ])

        with self.assertRaisesRegex(
                TemplateSyntaxError,
                r"on <unknown> line 1: \$endblock without \$block"):
            engine.apply_str_to_str([
                '$endblock',
            ])

        with self.assertRaisesRegex(
                TemplateSyntaxError,
                r"on <unknown> line 1: \$block without \$endblock"):
            engine.apply_str_to_str([
                '$block a',
            ])


    def test_files(self):
        """test template file I/O"""
        engine = TemplateEngine()

        with tempfile.TemporaryDirectory() as base:
            template_filename = base + os.sep + 'input'
            output_filename = base + os.sep + 'output'

            with open(template_filename, 'w') as template_file:
                template_file.write('test   ')

            engine.apply_file_to_file(template_filename, output_filename)

            with open(output_filename, 'r') as output_file:
                self.assertEqual(output_file.read(), 'test\n')

        with tempfile.TemporaryDirectory() as base:
            template_filename = base + os.sep + 'input_file_name.tpl'
            output_filename = base + os.sep + 'output'

            with open(template_filename, 'w') as template_file:
                template_file.write('$bad directive')

            with self.assertRaisesRegex(
                    TemplateSyntaxError,
                    r"input_file_name\.tpl line 1: unknown directive: \$bad"):
                engine.apply_file_to_file(template_filename, output_filename)

            self.assertFalse(os.path.isfile(output_filename))

        with tempfile.TemporaryDirectory() as base:
            output_filename = base + os.sep + 'output'

            engine.apply_str_to_file('test', output_filename)

            with open(output_filename, 'r') as output_file:
                self.assertEqual(output_file.read(), 'test\n')
