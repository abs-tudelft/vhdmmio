"""Simple templating engine. See `TemplateEngine` class."""

import re

__all__ = ['TemplateEngine', 'TemplateSyntaxError']

class TemplateEngine:
    """Simple templating engine.

    WARNING: do NOT use this engine with templates from untrusted sources.
    Expressions in the template file are passed to `eval()`, and can therefore
    call any Python function.

    This engine supports:

     - inline replacement through `$<expr>$`;
     - block replacement with template-controlled indentation and
       user-controlled line wrapping through `\n$<indent><name>\n`;
     - conditional blocks through `\n$if <expr>\n`, `\n$else\n`, and
       `\n$endif\n`.

    Note that `<indent>` is one space less than the actual indent to make the
    block name line up with where the block should be. If no indent is
    specified, no indent is added, so it's not currently possible to output
    blocks indented by a single space. A dollar sign can be inserted into the
    output by writing `$$`.

    Unlike the C preprocessor, line numbers are NOT preserved. The focus is on
    generating well-formatted, readable code.

    To use it, first define inline replacements, conditions, or add to blocks.
    Then `apply_*` the engine on files or strings."""

    def __init__(self):
        super().__init__()
        self._variables = {}
        self._blocks = {}

    def __setitem__(self, key, value):
        """Defines a variable within the expression engine."""
        self._variables[str(key)] = value

    def __getitem__(self, key):
        """Returns the current value of a variable within the expression
        engine."""
        return self._variables[str(key)]

    def __delitem__(self, key):
        """Undefines a variable within the expression engine."""
        del self._variables[str(key)]

    def __iter__(self):
        """Iterates over the variables defined within the expression engine."""
        return iter(self._variables)

    def append_block(self, key, code):
        """Add a block of code to the given key.

        `code` must be a string or a list of strings, the latter case being
        equivalent with passing `'\n'.join(code)`. Regardless of the number of
        terminating newlines, the spacing between consecutive blocks is always
        a single empty line and empty lines within a block are removed to help
        with code readability. Whitespace at the end of lines is automatically
        removed.

        Dollar characters are used as control characters for formatting:

         - Inline dollar signs are replaced with spaces or newlines based on
           line length in a way that preserves indentation. An additional
           four-space indent is added when auto-wrapping.
         - Double inline dollar signs escape this; they are changed into a
           single dollar sign.
         - A single dollar sign at the start of a line followed by a space
           indicates that the line is a comment. The appropriate comment
           character sequence will be prefixed when the comment is inserted.
           The content is interpreted as markdown text; heuristics are used
           to try to rewrap the text to the appropriate line width. Dollar
           signs on these lines are NOT interpreted as spacing, since this
           would have no effect anyway.
         - A double dollar sign at the start of a line is replaced by the
           appropriate comment sequence, but otherwise the line is treated
           the same way as normal code, i.e. requiring dollar signs to mark
           line wrapping boundaries.
         - Three dollar signs at the start of a line are replaced with a
           single dollar sign in the output. The line is treated as regular
           code.
        """
        if not isinstance(code, list):
            code = [code]
        lines = []
        for item in code:
            lines.extend(filter(bool, str(item).split('\n')))
        if not lines:
            return
        key = str(key)
        if key not in self._blocks:
            self._blocks[key] = [lines]
        else:
            self._blocks[key].append(lines)

    def reset_block(self, key):
        """Removes all code blocks associated with the given key."""
        key = str(key)
        if key in self._blocks:
            del self._blocks[key]

    def apply_file_to_file(self, template_filename, output_filename, *args, **kwargs):
        """Applies this template engine to the given template file, writing the
        result to the given output file. Extra arguments are passed to
        `apply_str_to_str()` and are documented there."""
        output = self.apply_file_to_str(template_filename, *args, **kwargs)
        with open(output_filename, 'w') as output_file:
            output_file.write(output)

    def apply_str_to_file(self, template, output_filename, *args, **kwargs):
        """Applies this template engine to the given template string, writing the
        result to the given output file. Extra arguments are passed to
        `apply_str_to_str()` and are documented there."""
        output = self.apply_str_to_str(template, *args, **kwargs)
        with open(output_filename, 'w') as output_file:
            output_file.write(output)

    def apply_file_to_str(self, template_filename, *args, **kwargs):
        """Applies this template engine to the given template file, returning
        the result as a string. Extra arguments are passed to
        `apply_str_to_str()` and are documented there."""
        with open(template_filename, 'r') as template_file:
            template = template_file.read()
        try:
            return self.apply_str_to_str(template, *args, **kwargs)
        except TemplateSyntaxError as exc:
            exc.set_filename(template_filename)
            raise

    def apply_str_to_str(self, template, comment='# ', wrap=80):
        """Applies this template engine to the given template string, returning
        the result as a string. The `comment` keyword argument specifies the
        character sequence that leads comment lines; it defaults to '# ' for
        Python files. The `wrap` keyword argument specifies the desired number
        of characters per line when wrapping; it defaults to 80."""

        # If the template is specified as a list of strings, join them first.
        if isinstance(template, list):
            template = '\n'.join(template)

        # Split the template file into a list of alternating literals and
        # directives.
        directives = self._split_directives(template)

        # Handle conditional directives first, so we don't try to process
        # anything within disabled conditional blocks.
        directives = self._process_conditionals(directives)

        # Replace inline directives.
        directives = self._process_inline(directives)

        # Handle block directives.
        directives = self._process_block(directives, comment, wrap)

        # Check that no more directives remain and clean up the output.
        output = self._postprocess(directives)

        return output

    @staticmethod
    def _split_directives(template):
        """Splits a template string into directives. The resulting list contains an
        odd amount of items, where every even-indexed item is a literal string and
        every odd-indexed item is a two-tuple of a line number and a directive.
        Inline directives include the surrounding dollar signs. Non-inline
        directives include the dollar prefix and newline suffix, while the newline
        before the directive is considered part of the preceding literal."""

        # Split the directive using regular expressions. A newline is prefixed and
        # suffixed to ensure that the newlines matched by block directives at the
        # start and end of the input are always there. The prefixed newline is
        # stripped immediately; the final newline is stripped when we finish
        # parsing when the template engine ensures that all files end in a single
        # newline.
        template = re.split(r'(\$[^$\n]*\$|(?<=\n)\$[^\n]+\n)', '\n' + template + '\n')
        template[0] = template[0][1:]

        # Insert line number information.
        line_number = 1
        for idx, item in enumerate(template):
            directive_line_number = line_number
            line_number += item.count('\n')
            if idx % 2 == 1:
                directive = item
                template[idx] = (directive_line_number, directive)

        return template

    def _process_conditionals(self, input_data):
        """Processes the conditional directives in a list of directives as returned
        by `_split_directives()`. Keyword arguments are used to specify the
        variables available to the expressions."""
        output_data = []
        directive_deleted = False
        first_if_line_nr = None
        condition_stack = []
        for idx, item in enumerate(input_data):
            if idx % 2 == 1:

                # Unpack the directive.
                line_nr, directive = item
                directive, *expression = directive.split(maxsplit=1)

                if directive == '$if':
                    if not condition_stack:
                        first_if_line_nr = line_nr
                    if not expression:
                        raise TemplateSyntaxError(
                            line_nr, '$if without expression')
                    try:
                        condition_stack.append(
                            all(condition_stack)
                            and bool(eval(expression[0], self._variables))) #pylint: disable=W0123
                    except (NameError, ValueError, TypeError, SyntaxError) as exc:
                        raise TemplateSyntaxError(
                            line_nr, 'error in $if expression: {}'.format(exc))
                    directive_deleted = True

                elif directive == '$else':
                    if not condition_stack:
                        raise TemplateSyntaxError(
                            line_nr, '$else without $if')
                    condition_stack[-1] = not condition_stack[-1]
                    directive_deleted = True

                elif directive == '$endif':
                    if not condition_stack:
                        raise TemplateSyntaxError(
                            line_nr, '$endif without $if')
                    del condition_stack[-1]
                    directive_deleted = True

                elif all(condition_stack):
                    output_data.append(item)

            elif not all(condition_stack):
                pass

            elif directive_deleted:
                output_data[-1] += item
                directive_deleted = False

            else:
                output_data.append(item)

        if condition_stack:
            raise TemplateSyntaxError(
                first_if_line_nr, '$if without $endif')

        return output_data

    def _process_inline(self, input_data):
        """Processes the inline expression directives and dollar escapes in a list
        of directives as returned by `_split_directives()`."""
        output_data = []
        directive_deleted = False
        for idx, item in enumerate(input_data):
            if idx % 2 == 1:

                # Unpack the directive.
                line_nr, directive = item

                if directive == '$$':
                    output_data[-1] += '$'
                    directive_deleted = True

                elif directive.startswith('$') and directive.endswith('$'):
                    try:
                        output_data[-1] += str(eval(directive[1:-1], self._variables)) #pylint: disable=W0123
                    except (NameError, ValueError, TypeError, SyntaxError) as exc:
                        raise TemplateSyntaxError(
                            line_nr, 'error in inline expression: {}'.format(exc))
                    directive_deleted = True

                else:
                    output_data.append(item)

            elif directive_deleted:
                output_data[-1] += item
                directive_deleted = False

            else:
                output_data.append(item)

        return output_data

    def _process_block(self, input_data, comment, wrap):
        """Processes the block insertion directives in a list of directives as
        returned by `_split_directives()`."""
        output_data = []
        directive_deleted = False
        for idx, item in enumerate(input_data):
            if idx % 2 == 1:

                # Unpack the directive.
                _, directive = item
                directive = re.match(r'\$( *)([a-zA-Z0-9_]+)\n', directive)

                # Ignore non-block-insert directives.
                if not directive:
                    output_data.append(item)
                    continue
                directive_deleted = True

                # Unpack further.
                indent = directive.group(1)
                if indent:
                    indent = ' ' + indent
                key = directive.group(2)

                # Get the blocks associated with the given key, if any.
                blocks = self._blocks.get(key, [])

                # Format the blocks.
                blocks = (
                    self._format_block(block, indent, comment, wrap)
                    for block in blocks)

                # Append the blocks.
                output_data[-1] += ''.join(blocks)

            elif directive_deleted:
                output_data[-1] += item
                directive_deleted = False

            else:
                output_data.append(item)

        return output_data

    def _format_block(self, block, indent, comment, wrap):
        """Formats a block as described in the docs for `append_block()`."""

        output_lines = []

        # Since multiple subsequent lines of commented text should be
        # interpreted as a single paragraph before they're wrapped, we need to
        # postpone this wrapping until we encounter a line that doesn't belong
        # to the current paragraph. `paragraph_buffer` maintains a list of
        # words within the current paragraph, while `paragraph_buffer_indent`
        # contains the indentation characters of the first line of the
        # paragraph, where indentation characters means any set of spaces,
        # dashes, and asterisks. For subsequent lines to belong to the same
        # paragraph, they must have the same indentation, except using only
        # spaces. Those rules make markdown-styled lists parse correctly.
        paragraph_buffer = None
        paragraph_buffer_leading = None
        paragraph_buffer_hanging = None

        for line in block:

            # Strip trailing spaces.
            line = line.rstrip()

            # Detect the type of input line (normal code, text comment, or code
            # comment).
            output_indent = indent
            line_is_text = False

            if line.startswith('$$$'):

                # Escape sequence for $ at start of line in code. Just strip
                # the first dollar to turn it into an inline escape.
                line = line[1:]

            elif line.startswith('$$'):

                # Code comment.
                output_indent += comment

                # Strip the '$$' sequence.
                line = line[2:]

            elif line.startswith('$'):

                # Text comment.
                output_indent += comment
                line_is_text = True

                # Strip the '$' or '$ ' sequence.
                if line.startswith('$ '):
                    line = line[2:]
                else:
                    line = line[1:]

            # If this is a comment line, figure out its indentation to
            # determine whether it's a continuation of the previous comment
            # paragraph, if any. If it is, or it starts a new block, buffer it
            # until we get a line that isn't a continuation of it.
            if line_is_text:
                match = re.match(r'([-* ]*)(.*)$', line)
                input_indent = match.group(1)
                line = match.group(2)

                if paragraph_buffer is not None:
                    if line and output_indent + input_indent == paragraph_buffer_hanging:

                        # Continuation of that paragraph.
                        paragraph_buffer.extend(line.split())
                        continue

                    else:

                        # Not a continuation of the buffered paragraph. Output the
                        # current buffer so we can start a new one.
                        output_lines.extend(self._wrap(
                            paragraph_buffer_leading,
                            paragraph_buffer_hanging,
                            paragraph_buffer,
                            wrap))
                        paragraph_buffer = None

                if line:

                    # Start a new paragraph.
                    paragraph_buffer = line.split()
                    paragraph_buffer_leading = output_indent + input_indent
                    paragraph_buffer_hanging = output_indent + ' '*len(input_indent)

                else:

                    # Output empty lines immediately to maintain them. They'd
                    # be lost if we'd stick them in the paragraph buffer.
                    output_lines.append((output_indent + input_indent).rstrip())

                continue

            # The current line is not commented text, so we need to write and
            # invalidate the current paragraph buffer, if any, before we can
            # continue.
            if paragraph_buffer is not None:
                output_lines.extend(self._wrap(
                    paragraph_buffer_leading,
                    paragraph_buffer_hanging,
                    paragraph_buffer,
                    wrap))
                paragraph_buffer = None

            # Split the text into tokens split by single dollar signs. Also
            # handle escaping, which admittedly is a little awkward right now
            # with the double replacing.
            line = line.replace('$$', '$_')
            line = re.split(r'\$(?!_)', line)
            line = (token.replace('$_', '$') for token in line)

            # Wrap the text.
            output_lines.extend(self._wrap(
                output_indent,
                output_indent + '    ',
                line,
                wrap))

        # If we were still buffering a paragraph of commented text, output it
        # now.
        if paragraph_buffer is not None:
            output_lines.extend(self._wrap(
                paragraph_buffer_leading,
                paragraph_buffer_hanging,
                paragraph_buffer,
                wrap))

        # Join the block back together and terminate it with a double newline.
        return '\n'.join(output_lines) + '\n\n'

    @staticmethod
    def _wrap(leading_indent, hanging_indent, tokens, wrap):
        """Wraps tokenized text.

        `tokens` is a list of non-breakable strings representing the line or
        paragraph that is to be wrapped. The first line is prefixed with
        `leading_indent`, subsequent lines are prefixed with `hanging_indent`.
        `wrap` specifies the maximum desired number of characters on a single
        line."""
        line = leading_indent
        first = True
        for token in tokens:

            # The first token gets some special treatment here.
            if first:
                line += token
                first = False
                continue

            if len(line) + len(token) + 1 > wrap:

                # Too long, need to wrap: yield the previous line and start a
                # new one.
                yield line.rstrip()
                line = hanging_indent + token

            else:

                # No overflow, add to current line.
                line += ' ' + token

        # If we saw at least one token, yield the final line.
        if not first:
            yield line.rstrip()

    @staticmethod
    def _postprocess(input_data):
        """Asserts that no more directives are available in the incoming list
        of directives as returned by `_split_directives()`. Post-processes the
        single remaining directive such that superfluous whitespace is removed
        and the file ends in a single newline."""

        # Check for superfluous directives.
        if len(input_data) > 1:
            line_nr, directive = input_data[1]
            directive = directive.strip()
            raise TemplateSyntaxError(
                line_nr, 'unknown directive: {}'.format(directive))
        text = input_data[0]

        # Strip whitespace at the end of lines.
        text = re.sub(r'\t +\n', '\n', text)

        # Make sure the file ends in a single newline.
        text = text.rstrip() + '\n'

        return text


class TemplateSyntaxError(Exception):
    """Template syntax error class. Contains line number and source file
    information."""
    def __init__(self, line_nr, message, filename=None):
        super().__init__(message)
        self._filename = filename
        self._line_nr = line_nr
        self._message = message

    def set_filename(self, filename):
        """Sets the filename associated with this syntax error."""
        self._filename = filename

    def __str__(self):
        filename = self._filename
        if filename is None:
            filename = '<unknown>'
        return 'on {} line {}: {}'.format(filename, self._line_nr, self._message)
