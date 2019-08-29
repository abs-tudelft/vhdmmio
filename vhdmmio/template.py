"""Simple templating engine. See `TemplateEngine` class."""

import os
import re
import inspect

__all__ = ['TemplateEngine', 'TemplateSyntaxError', 'annotate_block']

class TemplateEngine:
    """Simple templating engine.

    WARNING: do NOT use this engine with templates from untrusted sources.
    Expressions in the template file are passed to `eval()`, and can therefore
    call any Python function.

    This engine supports:

     - inline replacement through `$<expr>$`;
     - block replacement with template-controlled indentation through
       `\n$<indent><name>\n`;
     - blocks can be defined both programmatically and from within the template
       through `\n$block <name>\n` and `\n$endblock\n`;
     - conditional blocks through `\n$if <expr>\n`, `\n$else\n`, and
       `\n$endif\n`.

    Note that `<indent>` is one space less than the actual indent to make the
    block name line up with where the block should be. If no indent is
    specified, no indent is added, so it's not currently possible to output
    blocks indented by a single space. A dollar sign can be inserted into the
    output by writing `$$`. To indent the template itself for readability with
    lots of nesting, any number of spaces followed by a | sign will be removed
    before any other processing (when a line in the output needs to start with
    a |, just add a second | in front).

    Additionally, some pretty-printing is supported through @ characters:

     - Inline @ signs are replaced with spaces or newlines based on line length
       in a way that preserves indentation. An additional four-space indent is
       added when auto-wrapping.
     - Double inline @ signs escape this; they are changed into a single @
       sign.
     - A single @ sign at the start of a line, usually followed by a space,
       indicates that the line is a comment. The appropriate comment character
       sequence will be prefixed when the comment is inserted. The content is
       interpreted as markdown text; heuristics are used to try to rewrap the
       text to the appropriate line width. @ signs on these lines are NOT
       interpreted as spacing (they are literal), since this would have no
       effect anyway.
     - A double @ sign at the start of a line is replaced by the appropriate
       comment sequence, but otherwise the line is treated the same way as
       normal code. That is, wrapping points have to be specified explicitly
       using @ symbols, and @@ is escaped to @.
     - Three @ signs at the start of a line are replaced with a single @ sign
       in the output. The line is treated as regular code.

    The formatting step can be disabled, allowing the output of the template
    engine to be used as a block within a subsequent engine.

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

    def passthrough(self, *names):
        """Pass expansion of the given variable names on to the next template
        by assigning them to `$<name>$`."""
        for name in names:
            self[name] = '$%s$' % name

    def _get_scope(self):
        """Returns the dictionary of variables that should be available for
        eval()-based directives."""
        variables = self._variables.copy()
        variables['defined'] = lambda x: bool(self._blocks.get(x, []))
        variables['re'] = re
        return variables

    def append_block(self, key, code, *args):
        """Add a block of code to the given key.

        `code` must be a string or a list of strings, the latter case being
        equivalent with passing `'\n'.join(code)`. Regardless of the number of
        terminating newlines, the spacing between consecutive blocks is always
        a single empty line."""

        # Preprocess the arguments to allow for different calling conventions.
        if isinstance(code, list):
            code = '\n'.join(code)
        if args:
            code += '\n' + '\n'.join(args)

        # Blocks can contain directives and are internally stored as directive
        # lists. So split the code into directives now.
        directives = self._split_directives(code)

        # Save the block.
        key = str(key)
        if key not in self._blocks:
            self._blocks[key] = []
        self._blocks[key].append(directives)

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
            template = annotate_block(
                template_file.read(),
                template_filename,
                kwargs.get('comment', '#').strip())
        try:
            return self.apply_str_to_str(template, *args, **kwargs)
        except TemplateSyntaxError as exc:
            exc.set_filename(template_filename)
            raise

    def apply_str_to_str(self, template, comment='# ', wrap=80,
                         postprocess=True, annotate=False):
        """Applies this template engine to the given template string, returning
        the result as a string. The `comment` keyword argument specifies the
        character sequence that leads comment lines; it defaults to '# ' for
        Python files. The `wrap` keyword argument specifies the desired number
        of characters per line when wrapping; it defaults to 80. The
        `postprocess` keyword argument can be set to `False` to disable
        post-processing altogether; use this when the output of this templating
        step will be used within a later templating step."""

        # If the template is specified as a list of strings, join them first.
        if isinstance(template, list):
            template = '\n'.join(template)

        # Remove any template indentation, which is separated from output
        # indentation through pipe symbols.
        template = re.sub(r'\n *\|', '\n', template)

        # Split the template file into a list of alternating literals and
        # directives.
        directives = self._split_directives(template)

        # Handle $ directives.
        markers = self._process_directives(directives)
        output = self._process_markers(markers)

        # Process @ directives to clean up the output.
        if postprocess:
            output = self._process_wrapping(output, comment, wrap, annotate)

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
        directives = re.split(r'(\$[^$\n]*\$|(?<=\n)\$[^\n]+\n)', '\n' + template + '\n')
        directives[0] = directives[0][1:]

        # Insert line number information.
        line_number = 1
        directive_line_number = 1
        directive_source = None
        for idx, item in enumerate(directives):
            if directive_source is None:
                directive_line_number = line_number
            line_number += item.count('\n')
            if idx % 2 == 1:
                directive = item
                directives[idx] = ((directive_source, directive_line_number), directive)
            else:
                source = re.findall(r'@![v\^]->[^\n]+\n', item)
                if not source:
                    continue
                source = source[-1]
                if source.startswith('@!^->'):
                    directive_source = None
                elif source.startswith('@!v->source='):
                    directive_source, directive_line_number = source[12:].rsplit(':', maxsplit=1)
                    directive_line_number = int(directive_line_number)
                else:
                    assert False

        return directives

    def _process_directives(self, directives, block_recursion_limit=100): #pylint: disable=R0912,R0914,R0915
        """Process a directive list as returned by `_split_directives()` into a
        list of literals and markers. Literals and markers are distinguished by
        type: literals are strings, markers are N-tuples. The first entry of a
        marker tuple is a string that identifies what it represents.

        Currently the only marker is 'indent'. It's a two-tuple; the second
        entry is an integer representing an indentation delta (number of
        spaces). This indentation needs to be applied to subsequent literals."""

        # Make a copy of the directive list so we can consume it one entry at a
        # time without affecting the argument.
        directive_stack = list(directives)

        # Conditional code block stack. For code to be handled, all entries in
        # this list must be True (or there must be zero entries). Each $if
        # directive appends its condition to the list, $else directives invert
        # the last one, and $endif directives remove from the list.
        condition_stack = []

        # Line number of the outermost $if statement, used for line number info
        # when we're missing an $endif.
        outer_if_line_nr = None

        # Block definition buffer.
        block_buffer = None
        block_key = None

        # Number of recursive $block definitions.
        block_level = 0

        # Block definitions.
        block_definitions = {}

        # Number of recursive block insertions.
        block_recursion = 0

        # Line number of the outermost $block statement, used for line number
        # info when we're missing an $endblock.
        outer_block_line_nr = None

        # Output buffer.
        output_buffer = []

        # Iterate over all the directives and literals.
        while directive_stack:
            directive_or_literal = directive_stack.pop(0)

            # Handle literals first.
            if isinstance(directive_or_literal, str):
                literal = directive_or_literal

                # If we're in the middle of a block definition, save the
                # literal to the block buffer.
                if block_buffer is not None:
                    block_buffer.append(literal)
                    continue

                # Delete literals that have been conditioned away.
                if not all(condition_stack):
                    continue

                # Output the literal.
                output_buffer.append(literal)
                continue

            # Unpack the directive.
            directive_tuple = directive_or_literal
            line_nr, directive = directive_tuple

            # Handle markers inserted into the stack by this function.
            if line_nr is None:
                marker = directive
                if marker[0] == 'end_block':
                    block_recursion -= 1
                else:
                    output_buffer.append(marker)
                continue

            # Parse/simplify the directive syntax.
            if directive.endswith('$'):
                indent = 0
                directive = directive[1:-1]
                argument = None
            else:
                matches = re.match(r'\$( *)([^ ]*)(?: (.*))?$', directive)
                indent = len(matches.group(1))
                if indent:
                    indent += 1
                directive = '$' + matches.group(2).rstrip()
                argument = matches.group(3)

            # Handle $block directive.
            if directive == '$block':
                if not argument:
                    raise TemplateSyntaxError(
                        line_nr, '$block without key')
                block_level += 1
                if block_level == 1:
                    block_buffer = []
                    block_key = argument
                    outer_block_line_nr = line_nr
                    continue
                # Don't continue here; save nested $block directives to the
                # buffer!

            # Handle $endblock directive.
            if directive == '$endblock':
                if argument:
                    raise TemplateSyntaxError(
                        line_nr, 'unexpected argument for $endblock')
                if block_level == 0:
                    raise TemplateSyntaxError(
                        line_nr, '$endblock without $block')
                block_level -= 1
                if block_level == 0:
                    if block_key not in block_definitions:
                        block_definitions[block_key] = []
                    block_definitions[block_key].append(block_buffer)
                    block_key = None
                    block_buffer = None
                    continue
                # Don't continue here; save nested $endblock directives to the
                # buffer!

            # If we're in the middle of a block definition, don't process
            # directives yet.
            if block_buffer is not None:
                block_buffer.append(directive_tuple)
                continue

            # Handle $if directive.
            if directive == '$if':
                if not argument:
                    raise TemplateSyntaxError(
                        line_nr, '$if without expression')
                if not condition_stack:
                    outer_if_line_nr = line_nr
                if not all(condition_stack):
                    # Don't try to evaluate the condition if we're already
                    # conditioned away.
                    condition = False
                else:
                    try:
                        condition = bool(eval(argument, self._get_scope())) #pylint: disable=W0123
                    except (NameError, ValueError, TypeError, SyntaxError) as exc:
                        raise TemplateSyntaxError(
                            line_nr, 'error in $if expression: {}'.format(exc))
                condition_stack.append(condition)
                continue

            # Handle $else directive.
            if directive == '$else':
                if argument:
                    raise TemplateSyntaxError(
                        line_nr, 'unexpected argument for $else')
                if not condition_stack:
                    raise TemplateSyntaxError(
                        line_nr, '$else without $if')
                condition_stack[-1] = not condition_stack[-1]
                continue

            # Handle $endif directive.
            if directive == '$endif':
                if argument:
                    raise TemplateSyntaxError(
                        line_nr, 'unexpected argument for $endif')
                if not condition_stack:
                    raise TemplateSyntaxError(
                        line_nr, '$endif without $if')
                del condition_stack[-1]
                continue

            # Don't process directives further if we're inside a false conditional
            # block.
            if not all(condition_stack):
                continue

            # Handle dollar escape sequences.
            if directive == '':
                output_buffer.append('$')
                continue

            # Handle inline directives.
            if not directive.startswith('$'):
                try:
                    result = str(eval(directive, self._get_scope())) #pylint: disable=W0123
                except (NameError, ValueError, TypeError, SyntaxError) as exc:
                    raise TemplateSyntaxError(
                        line_nr, 'error in inline expression: {}'.format(exc))
                output_buffer.append(result)
                continue

            # Handle block insertions.
            if directive.startswith('$') and not argument:
                block_recursion += 1
                if block_recursion > block_recursion_limit:
                    raise TemplateSyntaxError(
                        line_nr, 'block recursion limit reached ({})'.format(block_recursion_limit))
                key = directive[1:]

                # Get the blocks associated with the given key, if any.
                blocks = self._blocks.get(key, [])
                blocks.extend(block_definitions.get(key, []))

                # Flatten the directive lists.
                directives = [(None, ('indent', indent))]
                for block_directives in blocks:
                    directives.extend(block_directives)
                    directives.append('\n\n')
                directives.append((None, ('indent', -indent)))
                directives.append((None, ('end_block',)))

                # Insert the directives at the start of our directive stack.
                directive_stack[0:0] = directives
                continue

            # Unknown directive.
            raise TemplateSyntaxError(
                line_nr, 'unknown directive: {}'.format(directive))

        # Raise errors when we have unterminated blocks.
        if condition_stack:
            raise TemplateSyntaxError(
                outer_if_line_nr, '$if without $endif')
        if block_buffer is not None:
            raise TemplateSyntaxError(
                outer_block_line_nr, '$block without $endblock')

        return output_buffer

    @staticmethod
    def _process_markers(markers):
        """Processes a list of literals and markers as returned by
        `_process_directives()` into a single string representing the source
        code."""

        # Join all consecutive literals together, then split them into lines.
        # That allows us to prefix indentation properly.
        marker_buffer = [[]]
        for marker_or_literal in markers:
            if isinstance(marker_or_literal, tuple):
                marker_buffer[-1] = ''.join(marker_buffer[-1]).split('\n')
                marker_buffer.append(marker_or_literal)
                marker_buffer.append([])
            else:
                marker_buffer[-1].append(marker_or_literal)
        marker_buffer[-1] = ''.join(marker_buffer[-1]).split('\n')

        # Current number of spaces to indent by.
        indent = 0

        # Buffer to output processed literals to.
        output_buffer = []

        # State variables used to collapse empty lines and annotations.
        empty_line = False
        source_annotation = None

        for marker_or_literals in marker_buffer:

            # Handle markers.
            if isinstance(marker_or_literals, tuple):
                marker = marker_or_literals

                if marker[0] == 'indent':
                    indent += marker[1]
                    continue

                raise AssertionError('unknown marker: {}'.format(indent))

            # Handle blocks of literals. We process indentation markers and
            # collapse multiple newlines and source markers into one to
            # (hopefully) improve readability.
            for literal in marker_or_literals:
                literal = literal.rstrip()

                if not literal:
                    empty_line = True
                elif literal.startswith('@!'):
                    source_annotation = literal
                else:
                    if output_buffer and empty_line:
                        output_buffer.append('')
                    if source_annotation is not None:
                        output_buffer.append(source_annotation)
                    output_buffer.append(' ' * indent + literal)
                    empty_line = False
                    source_annotation = None

        # Make sure we output the source termination marker at the end, if any.
        if source_annotation and source_annotation.startswith('!@^->'):
            output_buffer.append(source_annotation)

        return '\n'.join(output_buffer)

    def _process_wrapping(self, text, comment, wrap, annotate): #pylint disable=R0912
        """Post-processes code by handling comment and wrapping markers."""

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

        # List of source annotations that have not been written yet.
        annotations = []

        for line in text.split('\n'):

            # Strip trailing spaces.
            line = line.rstrip()

            # Add indentation in the input block to the output indent.
            match = re.match(r'( *)(.*)$', line)
            indent = match.group(1)
            line = match.group(2)

            # Detect the type of input line (normal code, text comment, or code
            # comment).
            line_is_text = False

            if line.startswith('@@@'):

                # Escape sequence for @ at start of line in code. Just strip
                # the first at to turn it into an inline escape.
                line = line[1:]

            elif line.startswith('@@'):

                # Code comment.
                indent += comment

                # Strip the '@@' sequence.
                line = line[2:]

            elif line.startswith('@!'):

                # Source annotation.
                if annotate:
                    annotations.append(comment.strip() + line[2:])
                continue

            elif line.startswith('@'):

                # Text comment.
                indent += comment
                line_is_text = True

                # Strip the '@' or '@ ' sequence.
                if line.startswith('@ '):
                    line = line[2:]
                else:
                    line = line[1:]

            # If this is a comment line, figure out its indentation to
            # determine whether it's a continuation of the previous comment
            # paragraph, if any. If it is, or it starts a new block, buffer it
            # until we get a line that isn't a continuation of it.
            if line_is_text:

                # Output source annotations before processing the comment.
                output_lines.extend(annotations)
                annotations = []

                match = re.match(r'([-* ]*)(.*)$', line)
                comment_indent = match.group(1)
                line = match.group(2)

                if paragraph_buffer is not None:
                    if line and indent + comment_indent == paragraph_buffer_hanging:

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
                    paragraph_buffer_leading = indent + comment_indent
                    paragraph_buffer_hanging = indent + ' '*len(comment_indent)

                else:

                    # Output empty lines immediately to maintain them. They'd
                    # be lost if we'd stick them in the paragraph buffer.
                    output_lines.append((indent + comment_indent).rstrip())

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

            # Output annotations after dumping the comment paragraph buffer,
            # but before outputting the statement.
            output_lines.extend(annotations)
            annotations = []

            # Split the text into tokens split by single at signs. Also
            # handle escaping, which admittedly is a little awkward right now
            # with the double replacing.
            line = line.replace('@@', '@_')
            line = re.split(r'\@(?!_)', line)
            line = (token.replace('@_', '@') for token in line)

            # Wrap the text.
            output_lines.extend(self._wrap(
                indent,
                indent + '    ',
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

        # Join the lines together and ensure that the file ends in a single
        # newline.
        return '\n'.join(output_lines).rstrip() + '\n'

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


class TemplateSyntaxError(Exception):
    """Template syntax error class. Contains line number and source file
    information."""
    def __init__(self, source, message, filename=None):
        super().__init__(message)
        if isinstance(source, int):
            self._filename = filename
            self._line_nr = source
        else:
            self._filename, self._line_nr = source
        self._message = message

    def set_filename(self, filename):
        """Sets the filename associated with this syntax error."""
        if self._filename is None:
            self._filename = filename

    def __str__(self):
        filename = self._filename
        if filename is None:
            filename = '<unknown>'
        return 'on {} line {}: {}'.format(filename, self._line_nr, self._message)


def annotate_block(template, fname=None, comment='#'):
    """Annotates template source file + line number to every non-directive line
    of the given template. If `fname` is `None`, the filename and line number
    offset is taken from the caller of this function."""
    comment = comment.strip()

    if fname is None:
        previous_frame = inspect.currentframe().f_back
        (fname, offset, _, _, _) = inspect.getframeinfo(previous_frame)
        # inspect returns the last line of a statement. We assume that blocks
        # are defined as a """ multiline string, so we need to subtract the
        # number of newlines in the block.
        offset -= template.count('\n')
    else:
        offset = 1

    template = template.split('\n')
    annotated = []
    for line_no, line in enumerate(template):
        annotated.append('@!v->source=%s:%s' % (fname, line_no + offset))
        annotated.append(line)
    annotated.append('@!^->end')

    return '\n'.join(annotated)


def preload_template(fname, comment='#'):
    """Preloads a template from a file relative to the calling Python file."""
    comment = comment.strip()

    if not os.path.isabs(fname):
        previous_frame = inspect.currentframe().f_back
        caller_fname, _, _, _, _ = inspect.getframeinfo(previous_frame)
        fname = os.path.dirname(caller_fname) + os.sep + fname

    with open(fname, 'r') as fil:
        template = fil.read()

    return annotate_block(template, fname, comment)
