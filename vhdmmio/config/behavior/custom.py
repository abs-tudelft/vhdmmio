"""Submodule for `Primitive` configurable."""

import re
from ...configurable import configurable, Configurable, choice, listconfig
from .registry import behavior

@configurable(name='Interfaces for `custom` field behavior')
class CustomInterfaceConfig(Configurable):
    """Custom fields can specify any interfaces and state variables they want
    to use through this configuration structure. The interface type is
    determined based on which of the `input`, `output`, `generic`, `drive`,
    `strobe`, `monitor`, and `state` keys is present to reduce verbosity in the
    configuration files; exactly *one* of these must therefore be specified."""
    #pylint: disable=E0211

    @choice
    def input():
        """Use this key to request an input signal to be generated."""
        yield None, 'this interface does not specify an input port.'
        yield (re.compile(r'[a-zA-Za-z][a-zA-Z0-9_]*'), 'a scalar input port '
               'with the specified name is generated. The VHDL identifier for '
               'it is made available to the templates through `$s.<name>$`.')
        yield (re.compile(r'[a-zA-Za-z][a-zA-Z0-9_]*:[0-9]+'), 'as above, but '
               'the port is a vector of the specified width.')

    @choice
    def output():
        """Use this key to request an output signal to be generated."""
        yield None, 'this interface does not specify an output port.'
        yield (re.compile(r'[a-zA-Za-z][a-zA-Z0-9_]*'), 'a scalar output port '
               'with the specified name is generated. The VHDL identifier for '
               'it is made available to the templates through `$s.<name>$`.')
        yield (re.compile(r'[a-zA-Za-z][a-zA-Z0-9_]*:[0-9]+'), 'as above, but '
               'the port is a vector of the specified width.')

    @choice
    def generic():
        """Use this key to request a generic to be generated."""
        yield None, 'this interface does not specify a generic.'
        yield (re.compile(r'[a-zA-Za-z][a-zA-Z0-9_]*'), 'a scalar generic '
               'with the specified name is generated. The VHDL identifier for '
               'it is made available to the templates through `$s.<name>$`.')
        yield (re.compile(r'[a-zA-Za-z][a-zA-Z0-9_]*:[0-9]+'), 'as above, but '
               'the generic is a vector of the specified width.')

    @choice
    def drive():
        """Use this key to request an internal signal driven by this field to
        be generated."""
        yield None, 'this interface does not specify a driven internal.'
        yield (re.compile(r'[a-zA-Za-z][a-zA-Z0-9_]*'), 'an internal '
               'with the specified name is generated and expected to be '
               'driven by this field. If the field is not repeated, the '
               'signal is scalar, otherwise its width equals the field '
               'repetition. The VHDL identifier for it is made available to '
               'the templates through `$s.<name>$`; it always behaves like '
               'an `std_logic`.')
        yield (re.compile(r'[a-zA-Za-z][a-zA-Z0-9_]*:[0-9]+'), 'as above, but '
               'the internal signal is a vector of the specified width. This '
               'prevents field repetition from being used.')

    @choice
    def strobe():
        """Use this key to request an internal signal strobed by this field to
        be generated. A strobed internal should only ever be or'd or written
        high!"""
        yield None, 'this interface does not specify a strobed internal.'
        yield (re.compile(r'[a-zA-Za-z][a-zA-Z0-9_]*'), 'an internal '
               'with the specified name is generated and expected to be '
               'strobed by this field. If the field is not repeated, the '
               'signal is scalar, otherwise its width equals the field '
               'repetition. The VHDL identifier for it is made available to '
               'the templates through `$s.<name>$`; it always behaves like '
               'an `std_logic`.')
        yield (re.compile(r'[a-zA-Za-z][a-zA-Z0-9_]*:[0-9]+'), 'as above, but '
               'the internal signal is a vector of the specified width. This '
               'prevents field repetition from being used.')

    @choice
    def monitor():
        """Use this key to request an internal signal monitored by this field
        to be generated."""
        yield None, 'this interface does not specify a monitored internal.'
        yield (re.compile(r'[a-zA-Za-z][a-zA-Z0-9_]*'), 'an internal '
               'with the specified name is generated and expected to only '
               'be read by this field. If the field is not repeated, the '
               'signal is scalar, otherwise its width equals the field '
               'repetition. The VHDL identifier for it is made available to '
               'the templates through `$s.<name>$`; it always behaves like '
               'an `std_logic`.')
        yield (re.compile(r'[a-zA-Za-z][a-zA-Z0-9_]*:[0-9]+'), 'as above, but '
               'the internal signal is a vector of the specified width. This '
               'prevents field repetition from being used.')

    @choice
    def state():
        """Use this key to request a state variable to be generated."""
        yield None, 'this interface does not specify a state variable.'
        yield (re.compile(r'[a-zA-Za-z][a-zA-Z0-9_]*'), 'a scalar state '
               'variable with the specified name is generated. The VHDL '
               'identifier for it is made available to the templates through '
               '`$s.<name>$`.')
        yield (re.compile(r'[a-zA-Za-z][a-zA-Z0-9_]*:[0-9]+'), 'as above, but '
               'the state variable is a vector of the specified width.')

    @choice
    def type():
        """This key specifies the type of the signal. Note that only generics
        support `natural` and `boolean` types, and only input and output ports
        support the `axi4l-*-*` types."""
        yield 'std_logic', 'this interface is an `std_logic` or `std_logic_vector`.'
        yield 'natural', 'this interface is a VHDL `natural`.'
        yield 'boolean', 'this interface is a VHDL `boolean`.'
        yield 'axi4l-req-32', 'this interface is a 32-bit AXI4-lite request structure.'
        yield 'axi4l-req-64', 'this interface is a 64-bit AXI4-lite request structure.'
        yield 'axi4l-resp-32', 'this interface is a 32-bit AXI4-lite response structure.'
        yield 'axi4l-resp-64', 'this interface is a 64-bit AXI4-lite response structure.'


@behavior(
    'custom', 'allows you to specify the field-specific VHDL code manually.')
@configurable(name='`custom` behavior')
class Custom(Configurable):
    """Custom fields allow you to describe the behavior of the field using
    VHDL snippits. This is very powerful, but not for the faint-hearted. Also,
    with great power comes great responsibility: you can easily break
    `vhdmmio`'s generated entities by writing incorrect code. Furthermore,
    `vhdmmio`'s internal template engine can execute arbitrary Python code, so
    building a register file from an untrusted source that contains custom
    fields is a big security risk. Therefore, `vhdmmio` requires you to specify
    `--trusted` on the command line to be able to use these fields.

    `vhdmmio` implements custom fields in a tightly integrated way; it doesn't
    just copypaste your code directly into the generated output file. Instead,
    it lets you write code snippits for various actions, that get executed
    within the generated VHDL process at the appropriate times. This is exactly
    how the predefined field behaviors are programmed within `vhdmmio` - custom
    fields basically just allow direct access to this API. The big advantage of
    this is that you still don't need to worry about things like the AXI4L
    interface or interoperability with any other fields in the logical register
    or register file, but it does mean that you need to specify quite some
    metadata to `vhdmmio` to make things work, and that you need a good
    understanding of how `vhdmmio`'s generated VHDL code works.

    # Specifying field behavior

    The behavior of a field needs to be specified in two different ways. The
    first is obvious: (templates for) the VHDL code that gets inserted into
    the generated entity. The second consists of a more abstract description of
    the field's capabilities and characteristics, which `vhdmmio` uses to
    generate the glue logic between the fields and the AXI4L bus, the header
    files for accessing the registers, and in some cases the documentation.

    `vhdmmio` allows you to specify the following VHDL code blocks. Note that
    `vhdmmio`'s generated entity is entirely synchronous and uses variables to
    maintain state, so the order of the blocks is important; the blocks are
    listed in the order in which they are executed.

     - `pre-access`: this code block is executed every clock cycle *before* the
       AXI4L bus access is handled.
     - `read`: this code block is executed when the bus is trying to read the
       field, and the bus interface logic is ready for the field's response.
     - `read-lookahead`: like `read`, but the bus interface logic is *not* yet
       ready for the response.
     - `read-request`: this code block is executed when a read request for the
       field is available, regardless of whether the bus interface logic is
       ready for the response.
     - `read-response`: this code block is executed when one of the above
       blocks deferred a read, and the bus interface logic is ready for the
       response.
     - `write`, `write-lookahead`, `write-request`, and `write-response`: the
       write analogues for the above.
     - `post-access`: this code block is executed every clock cycle *after* the
       AXI4L bus access is handled.

    For more information about each block, refer to the documentation below.

    `vhdmmio` needs the following metadata in addition to the code blocks:

     - whether the `read`/`read-request`/`write`/`write-request` code blocks
       can block a bus access (that is, delay the bus response);
     - whether reads/writes are volatile (that is, the result of accessing the
       field once differs from accessing it twice);
     - how the field can be accessed without affecting its state, if this is
       possible at all (used when a different field within a single logical
       register is to be accessed).

    This metadata is also used to determine whether two fields can coexist
    within the same register. The rules are:

     - blocking fields cannot be combined with other blocking fields;
     - blocking fields cannot be combined with volatile fields;
     - fields that support multiple outstanding requests cannot be combined
       with any other field.

    # Template syntax

    `vhdmmio` uses a custom template engine to preprocess VHDL code. The code
    blocks specified in for custom fields pass through this template engine as
    well.

    The template engine is controlled using three characters that are normally
    not used in VHDL: `|`, `$`, and `@`. Each corresponds to a different phase
    of the template logic.

    ## Indentation stripping phase (`|`)

    In this phase, all whitespace at the start of a line followed by a `|` is
    stripped. This allows you to indent your template however you want, without
    this indentation appearing in the generated code block. If you need to
    start a line with an `|` for some reason, simply prefix a second `|`; the
    substitution is only done once per line.

    ## Substitution phase (`$`)

    This is the most important phase, dealing with substitutions and
    conditionals, similar to the functionality of the C preprocessor.

    The template engine supports both inline and single-line directives.
    Single-line directives start with a `$`, followed by any amount of
    whitespace, followed by a command, followed by some arguments depending on
    the command. There should not be any whitespace before the `$` sign; to
    indent such commands you need to use the `|` syntax described above.
    Conversely, inline directives both start and end with a `$` and can be
    anywhere on a line. To insert a `$` in the output, use `$$`.

    The following single-line directives are available:

     - `$if <python-expression>`: opens a conditional block based on an
       expression evaluated by Python.
     - `$else`: opens the `else` block for a previous `$if`.
     - `$endif`: terminates an `$if` or `$else` block.
     - `$block <name>`: defines/adds code to a named block. This is like
       `#define` in the C preprocessor, but multiline.
     - `$end_block`: terminates a block definition.
     - `$<name>`: inserts a previously defined block. If there are no spaces
       between the `$` and the name, no indentation is added; otherwise one
       space plus the spacing between the `$` and the name is added for each
       line.

    Inline directives are always evaluated directly by Python. The result of
    the Python expression is cast to a string and inserted in place of the
    directive.

    The custom field logic makes some variables available within these
    Python expressions. These are:

     - `i`: the field index within the field descriptor, or `None` if the
       field descriptor describes only one field (that is, `repeat` is not
       specified).
     - `s`: structure containing the VHDL identifiers for each signal/variable
       specified through the `interfaces` configuration key.

    Additional variables may be available depending on the block.

    ## Comment and wrapping phase (`@`)

    This phase deals with generating aestetically pleasing, properly
    line-wrapped code regardless of the current indentation depth, which is
    impossible (or at least hard) to know when the template is written. The
    following constructs are available:

     - Lines that start with `@` are treated as comments. Subsequent comment
       lines are treated as markdown, and are rewrapped as such to get to
       column 80.
     - Lines that start with `@@` are also treated as comments, but are not
       rewrapped.
     - `@@@` at the start of a line maps to a single `@` in the output.
     - Inline `@` are replaced with either a space or a newline followed by
       appropriate indentation, depending on line wrapping.
     - Inline `@@` maps to a single `@` in the output.
    """
    #pylint: disable=E0211

    @listconfig
    def interfaces():
        """This key specifies the interfaces and state variables that this
        field uses."""
        return CustomInterfaceConfig

    @choice
    def pre_access():
        """This key specifies the VHDL template for the code block that is
        executed each cycle *before* the bus is accessed. This is usually used
        for initializing non-state variables and for connecting input signals
        to the internal state."""
        yield None, 'no pre-access code block is needed.'
        yield str, 'insert the given pre-access code block.'

    @choice
    def read():
        """This key specifies the VHDL template for the code block that is
        executed when the bus is attempting to read the field while also ready
        for the response.

        The template must perform one of the following actions to respond to
        the bus.

         - Set the `$ack$` boolean variable to `true`, and the `$data$`
           variable to the read result. `$data$` is appropriately sliced to
           represent the shape of the field; that is, it is sliced to an
           `std_logic` for scalar fields and to an appropriately sized
           `std_logic_vector` for vector fields.
         - Set the `$nack$` boolean variable to `true` to respond with a
           slave error.
         - Set the `$block$` boolean variable to `true` to stall. In this
           case, the block will be executed again the next cycle. The
           `read-can-block` key must be set in order to use this variable.
         - Set the `$defer$` boolean variable to `true` to defer. In this
           case, the request logic will accept the bus request and send
           subsequent requests to `read-lookahead` blocks, while the
           response logic will start calling the `read-response` block to get
           the response. Such a `read-response` block must be specified in
           order to use this variable.
         - Nothing: the bus behaves as if the field does not exist. If there
           are no other fields in the addressed register, a decode error is
           returned.

        In addition to the field's interfaces, the template can use the
        following variables:

         - `$prot$`: the `prot` field associated with the request as a
           3-bit `std_logic_vector`.
         - `$addr$`: the incoming bus address for the request as a 32-bit
           `std_logic_vector`.
         - `$sub$`: the subaddress for the for the request as an
           `std_logic_vector` slice, of which the width depends on the
           field's subaddress configuration.
        """
        yield None, 'no read code block is needed.'
        yield str, 'insert the given read code block.'

    @choice
    def read_lookahead():
        """This key specifies the VHDL template for the code block that is
        executed when the bus is attempting to read the field, but the
        response logic is not yet ready for the response. This can be used to
        initiate long transactions a few cycles earlier, or can be used in
        conjunction with multiple outstanding request support.

        The template must perform one of the following actions to respond to
        the bus.

         - Set the `$defer$` boolean variable to `true` to defer. In this
           case, the request logic will accept the bus request and send
           subsequent requests to `read-lookahead` blocks, while the
           response logic will start calling the `read-response` block to get
           the response. Such a `read-response` block must be specified in
           order to use this variable.
         - Nothing: the bus interface logic will continue to call this block
           in subsequent cycles until the response logic is ready, at which
           point the regular `read` block is executed instead.

        In addition to the field's interfaces, the template can use the
        following variables:

         - `$prot$`: the `prot` field associated with the request as a
           3-bit `std_logic_vector`.
         - `$addr$`: the incoming bus address for the request as a 32-bit
           `std_logic_vector`.
         - `$sub$`: the subaddress for the for the request as an
           `std_logic_vector` slice, of which the width depends on the
           field's subaddress configuration.
        """
        yield None, 'no read lookahead code block is needed.'
        yield str, 'insert the given read lookahead code block.'

    @choice
    def read_request():
        """This key specifies the VHDL template for the code block that is
        executed when the bus is attempting to read the field, regardless of
        whether the bus is ready for the response. It is up to the code block
        itself to check this where needed, using the `$resp_ready$` boolean
        variable. Depending on this boolean, the block must respond to the
        access as described in the documentation for the `read` and
        `read-lookahead` blocks.

        While uncommon, both `read`/`read-lookahead` and `read-request` may be
        specified at the same time. In this case, `read`/`read-lookahead` is
        executed before `read-request`."""
        yield None, 'no read request code block is needed.'
        yield str, 'insert the given read request code block.'

    @choice
    def read_response():
        """This key specifies the VHDL template for the code block that is
        executed when the bus is ready for the response of a previously
        deferred read.

        The template must perform one of the following actions to respond to
        the bus.

         - Set the `$ack$` boolean variable to `true`, and the `$data$`
           variable to the read result. `$data$` is appropriately sliced to
           represent the shape of the field; that is, it is sliced to an
           `std_logic` for scalar fields and to an appropriately sized
           `std_logic_vector` for vector fields.
         - Set the `$nack$` boolean variable to `true` to respond with a
           slave error.
         - Set the `$block$` boolean variable to `true` to stall. In this
           case, the block will be executed again the next cycle. The
           `read-can-block` key must be set in order to use this variable.
         - Nothing: the bus behaves as if the field does not exist. If there
           are no other fields in the addressed register, a decode error is
           returned.
        """
        yield None, ('no read response code block is needed; multiple outstanding'
                     'read requests are not supported for this field.')
        yield str, ('insert the given read response code block; this field '
                    'supports multiple outstanding requests in read mode.')

    @choice
    def write():
        """This key specifies the VHDL template for the code block that is
        executed when the bus is attempting to write to the field while also
        ready for the response.

        The template must perform one of the following actions to respond to
        the bus.

         - Set the `$ack$` boolean variable to `true` to respond with an
           acknowledgement.
         - Set the `$nack$` boolean variable to `true` to respond with a
           slave error.
         - Set the `$block$` boolean variable to `true` to stall. In this
           case, the block will be executed again the next cycle. The
           `write-can-block` key must be set in order to use this variable.
         - Set the `$defer$` boolean variable to `true` to defer. In this
           case, the request logic will accept the bus request and send
           subsequent requests to `write-lookahead` blocks, while the
           response logic will start calling the `write-response` block to get
           the response. Such a `write-response` block must be specified in
           order to use this variable.
         - Nothing: the bus behaves as if the field does not exist. If there
           are no other fields in the addressed register, a decode error is
           returned.

        In addition to the field's interfaces, the template can use the
        following variables:

         - `$data$`: the write data for the request, appropriately sliced for
           the shape of the field. That is, `$data$` behaves like an
           `std_logic` for scalar fields, and like an appropriately sized
           `std_logic_vector` for vector fields.
         - `$strb$`: the write strobe for the request. The variable has the
           same shape as `$data$` and thus behaves as a bit strobe, even though
           AXI4L's strobe signal is byte-oriented. If a bit in `$strb$` is
           zero, the respective `$data$` bit is guaranteed to also be zero, and
           should not be written.
         - `$prot$`: the `prot` field associated with the request as a
           3-bit `std_logic_vector`.
         - `$addr$`: the incoming bus address for the request as a 32-bit
           `std_logic_vector`.
         - `$sub$`: the subaddress for the for the request as an
           `std_logic_vector` slice, of which the width depends on the
           field's subaddress configuration.
        """
        yield None, 'no write code block is needed.'
        yield str, 'insert the given write code block.'

    @choice
    def write_lookahead():
        """This key specifies the VHDL template for the code block that is
        executed when the bus is attempting to write to the field, but the
        response logic is not yet ready for the response. This can be used to
        initiate long transactions a few cycles earlier, or can be used in
        conjunction with multiple outstanding request support.

        The template must perform one of the following actions to respond to
        the bus.

         - Set the `$defer$` boolean variable to `true` to defer. In this
           case, the request logic will accept the bus request and send
           subsequent requests to `write-lookahead` blocks, while the
           response logic will start calling the `write-response` block to get
           the response. Such a `write-response` block must be specified in
           order to use this variable.
         - Nothing: the bus interface logic will continue to call this block
           in subsequent cycles until the response logic is ready, at which
           point the regular `write` block is executed instead.

        In addition to the field's interfaces, the template can use the
        following variables:

         - `$data$`: the write data for the request, appropriately sliced for
           the shape of the field. That is, `$data$` behaves like an
           `std_logic` for scalar fields, and like an appropriately sized
           `std_logic_vector` for vector fields.
         - `$strb$`: the write strobe for the request. The variable has the
           same shape as `$data$` and thus behaves as a bit strobe, even though
           AXI4L's strobe signal is byte-oriented. If a bit in `$strb$` is
           zero, the respective `$data$` bit is guaranteed to also be zero, and
           should not be written.
         - `$prot$`: the `prot` field associated with the request as a
           3-bit `std_logic_vector`.
         - `$addr$`: the incoming bus address for the request as a 32-bit
           `std_logic_vector`.
         - `$sub$`: the subaddress for the for the request as an
           `std_logic_vector` slice, of which the width depends on the
           field's subaddress configuration.
        """
        yield None, 'no write lookahead code block is needed.'
        yield str, 'insert the given write lookahead code block.'

    @choice
    def write_request():
        """This key specifies the VHDL template for the code block that is
        executed when the bus is attempting to write to the field, regardless
        of whether the bus is ready for the response. It is up to the code
        block itself to check this where needed, using the `$resp_ready$`
        boolean variable. Depending on this boolean, the block must respond to
        the access as described in the documentation for the `write` and
        `write-lookahead` blocks.

        While uncommon, both `write`/`write-lookahead` and `write-request` may
        be specified at the same time. In this case, `write`/`write-lookahead`
        is executed before `write-request`."""
        yield None, 'no write request code block is needed.'
        yield str, 'insert the given write request code block.'

    @choice
    def write_response():
        """This key specifies the VHDL template for the code block that is
        executed when the bus is ready for the response of a previously
        deferred write.

        The template must perform one of the following actions to respond to
        the bus.

         - Set the `$ack$` boolean variable to `true` to respond with an
           acknowledgement.
         - Set the `$nack$` boolean variable to `true` to respond with a
           slave error.
         - Set the `$block$` boolean variable to `true` to stall. In this
           case, the block will be executed again the next cycle. The
           `write-can-block` key must be set in order to use this variable.
         - Nothing: the bus behaves as if the field does not exist. If there
           are no other fields in the addressed register, a decode error is
           returned.
        """
        yield None, ('no write response code block is needed; multiple outstanding'
                     'write requests are not supported for this field.')
        yield str, ('insert the given write response code block; this field '
                    'supports multiple outstanding requests in write mode.')

    @choice
    def post_access():
        """This key specifies the VHDL template for the code block that is
        executed each cycle *after* the bus is accessed. This is usually used
        for connecting the internal state to output signals."""
        yield None, 'no pre-access code block is needed.'
        yield str, 'insert the given pre-access code block.'

    @choice
    def read_can_block():
        """This key specifies whether the field can block read accesses."""
        yield False, 'this field cannot block reads.'
        yield True, 'this field can block reads.'

    @choice
    def read_volatile():
        """This key specifies whether the field is volatile in read mode.
        `vhdmmio` defines volatility as the read result or side effects being
        different when the field is accessed once versus when it is accessed
        more than once."""
        yield False, 'this field is not read-volatile.'
        yield True, 'this field is read-volatile.'

    @choice
    def read_has_side_effects():
        """This key specifies whether reads have side effects."""
        yield False, 'reading this field does not have side effects.'
        yield True, 'reading this field may have side effects.'

    @choice
    def read_write_related():
        """This key specifies whether the read data carries the same
        significance as the write data. If this is not set, `vhdmmio` will
        never attempt to read-modify-write this field."""
        yield False, 'the read and write data of this field are not related.'
        yield True, 'the read and write data of this field are related.'

    @choice
    def write_can_block():
        """This key specifies whether the field can block write accesses."""
        yield False, 'this field cannot block writes.'
        yield True, 'this field can block writes.'

    @choice
    def write_volatile():
        """This key specifies whether the field is volatile in write mode.
        `vhdmmio` defines volatility as the write result or side effects being
        different when the field is accessed once versus when it is accessed
        more than once."""
        yield False, 'this field is not write-volatile.'
        yield True, 'this field is write-volatile.'

    @choice
    def write_no_op():
        """This key specifies what strategies `vhdmmio` can use to write the
        logical register that this field resides in without affecting this
        field, if this is possible at all."""
        yield 'never', 'it is impossible to write to this field without side effects.'
        yield 'zero', 'writing zero to this field never has any side effects (flags).'
        yield 'current', ('writing the current value never has any side effects. '
                          'The current value must either be known from context, or, '
                          'if `read-write-related` is set, can be read from the field '
                          'first (read-modify-write).')
        yield 'mask', ('this field can only be masked out using the AXI4L byte strobe '
                       'signal.')
        yield 'current-or-mask', ('this field can be masked out by writing the current '
                                  'value, or through the AXI4L byte strobe signal.')
        yield 'always', ('anything goes: writing to this field never has any '
                         'side effects that `vhdmmio` has to concern itself with.')
