from unittest import TestCase
import os
import tempfile

import vhdmmio
from vhdmmio.template import *

class TestTemplateEngine(TestCase):

    def test_var_get_set(self):
        engine = TemplateEngine()
        self.assertEquals(sorted(engine), [])
        engine['a'] = 'a'
        engine['b'] = 3
        self.assertEquals(engine['a'], 'a')
        self.assertEquals(engine['b'], 3)
        self.assertEquals(sorted(engine), ['a', 'b'])
        engine['a'] = 'b'
        self.assertEquals(engine['a'], 'b')
        self.assertEquals(engine['b'], 3)
        del engine['a']
        with self.assertRaises(Exception):
            engine['a']
        self.assertEquals(sorted(engine), ['b'])
        self.assertEquals(engine['b'], 3)

    def test_split_directives(self):
        self.assertEquals(TemplateEngine._split_directives('\n'.join([
            '$if a',
            'good',
            'a$a$a',
            '$endif',
        ])), [
            '',
            (1, '$if a\n'),
            'good\na',
            (3, '$a$'),
            'a\n',
            (4, '$endif\n'),
            '',
        ])

        self.assertEquals(TemplateEngine._split_directives('\n'.join([
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
            (2, '$if a\n'),
            'good\n',
            (4, '$else\n'),
            'bad\n',
            (6, '$else\n'),
            'good again because why not\na',
            (8, '$a$'),
            'a\n',
            (9, '$endif\n'),
            'good\n',
        ])

    def test_conditionals(self):
        engine = TemplateEngine()

        engine['a'] = True
        self.assertEquals(engine.apply_str_to_str([
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
        self.assertEquals(engine.apply_str_to_str([
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

        for a in range(4):
            engine['a'] = a
            self.assertEquals(engine.apply_str_to_str([
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
            ]), '{}\n'.format(a))

        del engine['a']
        with self.assertRaisesRegexp(
            TemplateSyntaxError,
            r"on <unknown> line 2: error in \$if expression: name 'a' is not defined"
        ):
            engine.apply_str_to_str([
                'good',
                '$if a',
                'aaaagh',
                '$endif',
            ])

        with self.assertRaisesRegexp(
            TemplateSyntaxError,
            r"on <unknown> line 2: \$if without expression"
        ):
            engine.apply_str_to_str([
                'good',
                '$if',
                'aaaagh',
                '$endif',
            ])

        with self.assertRaisesRegexp(
            TemplateSyntaxError,
            r"on <unknown> line 1: \$else without \$if"
        ):
            engine.apply_str_to_str([
                '$else',
            ])

        with self.assertRaisesRegexp(
            TemplateSyntaxError,
            r"on <unknown> line 3: \$endif without \$if"
        ):
            engine.apply_str_to_str([
                '$if True',
                '$endif',
                '$endif',
            ])

        with self.assertRaisesRegexp(
            TemplateSyntaxError,
            r"on <unknown> line 3: \$if without \$endif"
        ):
            engine.apply_str_to_str([
                '$if True',
                '$endif',
                '$if True',
                '$if True',
                '$endif',
            ])

        with self.assertRaisesRegexp(
            TemplateSyntaxError,
            r"on <unknown> line 2: unexpected argument for \$endif"
        ):
            engine.apply_str_to_str([
                '$if True',
                '$endif a',
            ])

        with self.assertRaisesRegexp(
            TemplateSyntaxError,
            r"on <unknown> line 2: unexpected argument for \$else"
        ):
            engine.apply_str_to_str([
                '$if True',
                '$else a',
                '$endif',
            ])

    def test_inline(self):
        engine = TemplateEngine()

        with self.assertRaisesRegexp(
            TemplateSyntaxError,
            r"on <unknown> line 1: error in inline expression:"
        ):
            engine.apply_str_to_str('error = $a$')

        self.assertEquals(engine.apply_str_to_str('$$'), '$\n')

        self.assertEquals(engine.apply_str_to_str('$"*"*10$'), '**********\n')

        engine['a'] = 3
        self.assertEquals(engine.apply_str_to_str('$33*a$'), '99\n')

    def test_block_and_formatting(self):
        self.maxDiff = None

        TEST = [
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
        engine.append_block('TEST', TEST)
        engine.append_block('TEST', '')
        engine.append_block('TEST', '@ second block!\nhello\n\n', '', 'there')
        engine.append_block('STUFF', ['@ a bunch of other stuff goes here'])

        self.assertEquals(engine.apply_str_to_str([
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

        self.assertEquals(engine.apply_str_to_str([
            '$STUFF',
            '$ STUFF',
            '$   STUFF',
            '$NOTHING',
        ]), '\n')

        self.assertEquals(engine.apply_str_to_str([
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
        engine = TemplateEngine()
        with self.assertRaisesRegexp(
            TemplateSyntaxError,
            r"on <unknown> line 2: unknown directive: \$i"
        ):
            engine.apply_str_to_str([
                '$test',
                '$i am wrong',
                'boooo',
            ])

    def test_block_definitions(self):
        engine = TemplateEngine()
        engine.append_block('TEST', 'programmatic block', 'second line')
        self.assertEquals(engine.apply_str_to_str([
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

        self.assertEquals(engine.apply_str_to_str([
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

        with self.assertRaisesRegexp(
            TemplateSyntaxError,
            r"on <unknown> line 2: block recursion limit reached"
        ):
            engine.apply_str_to_str([
                '$block a',
                '$a',
                '$endblock',
                '$a',
            ])

        with self.assertRaisesRegexp(
            TemplateSyntaxError,
            r"on <unknown> line 1: \$block without key"
        ):
            engine.apply_str_to_str([
                '$block',
                '$endblock',
            ])

        with self.assertRaisesRegexp(
            TemplateSyntaxError,
            r"on <unknown> line 2: unexpected argument for \$endblock"
        ):
            engine.apply_str_to_str([
                '$block a',
                '$endblock a',
            ])

        with self.assertRaisesRegexp(
            TemplateSyntaxError,
            r"on <unknown> line 1: \$endblock without \$block"
        ):
            engine.apply_str_to_str([
                '$endblock',
            ])

        with self.assertRaisesRegexp(
            TemplateSyntaxError,
            r"on <unknown> line 1: \$block without \$endblock"
        ):
            engine.apply_str_to_str([
                '$block a',
            ])


    def test_files(self):
        engine = TemplateEngine()

        with tempfile.TemporaryDirectory() as base:
            template_filename = base + os.sep + 'input'
            output_filename = base + os.sep + 'output'

            with open(template_filename, 'w') as template_file:
                template_file.write('test   ')

            engine.apply_file_to_file(template_filename, output_filename)

            with open(output_filename, 'r') as output_file:
                self.assertEquals(output_file.read(), 'test\n')

        with tempfile.TemporaryDirectory() as base:
            template_filename = base + os.sep + 'input_file_name.tpl'
            output_filename = base + os.sep + 'output'

            with open(template_filename, 'w') as template_file:
                template_file.write('$bad directive')

            with self.assertRaisesRegexp(
                TemplateSyntaxError,
                r"input_file_name\.tpl line 1: unknown directive: \$bad"
            ):
                engine.apply_file_to_file(template_filename, output_filename)

            self.assertFalse(os.path.isfile(output_filename))

        with tempfile.TemporaryDirectory() as base:
            output_filename = base + os.sep + 'output'

            engine.apply_str_to_file('test', output_filename)

            with open(output_filename, 'r') as output_file:
                self.assertEquals(output_file.read(), 'test\n')

    def test_real_input(self):
        engine = TemplateEngine()
        engine['NAME'] = 'test_mmio'
        engine['DATA_WIDTH'] = 32
        engine['N_IRQ'] = 3
        engine['IRQ_MASK_RESET'] = '"111"'
        engine['IRQ_ENAB_RESET'] = '"1___11"'
        filename = os.path.dirname(vhdmmio.__file__) + os.sep + 'vhd' + os.sep + 'entity.template.vhd'
        output = engine.apply_file_to_str(filename, '-- ')
        self.assertFalse('$' in output)
        self.assertTrue('"1___11"' in output)
