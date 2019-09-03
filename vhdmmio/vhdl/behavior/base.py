"""Contains the base class for behaviors."""

from ...template import TemplateEngine, annotate_block

_BEHAVIOR_CODE_GEN_CLASS_MAP = []


_BUS_REQ_FIELD_TEMPLATE = annotate_block("""
|$block HANDLE
  |$if defined('NORMAL') or defined('BOTH')
    |$if dir == 'r'
      |if $dir$_req then
      |  $r_data$ := r_hold($rnge$);
      |end if;
    |$endif
  |$endif
  |$if defined('LOOKAHEAD') or defined('NORMAL') or defined('BOTH')
    |$if dir == 'w'
      |$w_data$ := w_hold($rnge$);
      |$w_strobe$ := w_hstb($rnge$);
    |$endif
  |$endif
  |$if defined('LOOKAHEAD')
    |if $dir$_lreq then
    |$ LOOKAHEAD
    |end if;
  |$endif
  |$if defined('NORMAL')
    |if $dir$_req then
    |$ NORMAL
    |end if;
  |$endif
  |$if defined('BOTH')
    |if $dir$_req or $dir$_lreq then
    |$ BOTH
    |end if;
  |$endif
  |$if defined('NORMAL') or defined('BOTH')
    |$if dir == 'r'
      |if $dir$_req then
      |  r_hold($rnge$) := $r_data$;
      |end if;
    |$endif
  |$endif
|$endblock
|
|@ ${'r': 'Read', 'w': 'Write'}[dir]$ logic for $desc$
|$if prot == '---'
  |$HANDLE
|$else
  |if std_match($dir$_prot, "$prot$") then
  |$ HANDLE
  |end if;
|$endif
""", comment='--')

_BUS_RESP_FIELD_TEMPLATE = annotate_block("""
|$RESP
|$if dir == 'r'
  |r_hold := (others => '0');
  |r_hold($rnge$) := $r_data$;
|$endif
""", comment='--')


def behavior_code_gen(behavior_cls):
    """Decorator generator which registers a behavior class."""
    def decorator(code_gen_cls):
        _BEHAVIOR_CODE_GEN_CLASS_MAP.append((behavior_cls, code_gen_cls))
        return behavior_cls
    return decorator


class BehaviorCodeGen:
    """Base class for field behavior VHDL code generators."""

    def __init__(self, field_descriptor,
                 tple, interface,
                 read_decoder, write_decoder,
                 read_tag_decoder, write_tag_decoder):
        super().__init__()
        self._field_descriptor = field_descriptor
        self._tple = tple
        self._interface = interface
        self._read_decoder = read_decoder
        self._write_decoder = write_decoder
        self._read_tag_decoder = read_tag_decoder
        self._write_tag_decoder = write_tag_decoder

    @staticmethod
    def construct(field_descriptor, *args, **kwargs):
        """Constructs a `BehaviorCodeGen` class instance based on the given
        parsed field descriptor. The remainder of the arguments are passed to
        the constructor of the selected behavior class. These arguments include
        the builder objects of the VHDL generator."""
        for behavior_cls, code_gen_cls in _BEHAVIOR_CODE_GEN_CLASS_MAP:
            if isinstance(field_descriptor.behavior, behavior_cls):
                return code_gen_cls(field_descriptor, *args, **kwargs)
        raise TypeError(
            'no mapping exists from type %s to a BehaviorCodeGen subclass'
            % type(field_descriptor.behavior).__name__)

    @staticmethod
    def generate():
        """This function must be overridden by the derived classes to generate
        the behavior code. It can make use of the public properties and methods
        exposed below. Briefly:

         - `field_descriptor`: maps to the field descriptor that is being
           generated.
         - `behavior`: shorthand to the parsed behavior class for the above.
         - `add_input()`, `add_output()`, `add_generic()`: register ports and
           generics for the field descriptor.
         - `add_declarations()`: registers declarations and public
           implementations thereof (in the package) to be used by the field
           descriptor logic. Should only be called once.
         - `add_interface_logic()`: adds code blocks that will always run
           before/after the field read/write logic, regardless of whether any
           field is accessed. Should only be called once.
         - `add_read_logic()`: adds the code blocks that handle bus reads.
           Should only be called once.
         - `add_write_logic()`: adds the code blocks that handle bus writes.
           Should only be called once.
        """
        raise NotImplementedError()

    @property
    def field_descriptor(self):
        """The field descriptor that this code generator object is
        representing."""
        return self._field_descriptor

    @property
    def behavior(self):
        """The behavior object that this code generator object is
        representing."""
        return self.field_descriptor.behavior

    def add_input(self, name, count=None, typ=None):
        """Registers an input port with the specified name, shape (defaults to
        scalar) and type object from `..types` (defaults to
        `std_logic`/`std_logic_vector`). Returns an object that represents
        the interface, which must be indexed by the field index first (index
        is ignored if the field is scalar) to get the requested type. It can
        then be converted to a string to get the VHDL representation."""
        return self.add_interface('i', name, count, typ)

    def add_output(self, name, count=None, typ=None):
        """Registers an output port with the specified name, shape (defaults to
        scalar) and type object from `..types` (defaults to
        `std_logic`/`std_logic_vector`). Returns an object that represents
        the interface, which must be indexed by the field index first (index
        is ignored if the field is scalar) to get the requested type. It can
        then be converted to a string to get the VHDL representation."""
        return self.add_interface('o', name, count, typ)

    def add_generic(self, name, count=None, typ=None):
        """Registers a generic with the specified name, shape (defaults to
        scalar) and type object from `..types` (defaults to
        `std_logic`/`std_logic_vector`). Returns an object that represents
        the interface, which must be indexed by the field index first (index
        is ignored if the field is scalar) to get the requested type. It can
        then be converted to a string to get the VHDL representation."""
        return self.add_interface('g', name, count, typ)

    def add_interface(self, mode, name, count=None, typ=None):
        """Implementation for registering generics and ports. `mode` must be
        `'i'`, `'o'`, or `'g'` for adding respectively an input, an output, or
        a generic."""
        return self._interface.add(
            self.field_descriptor.name, self._describe(),
            'f', self.field_descriptor.shape,
            name, mode, typ, count,
            self.field_descriptor.interface_options)

    def add_declarations(self, private=None, public=None, body=None):
        """Registers declarative code blocks for the represented field
        descriptor, expanded into respectively the process header, package
        header, and package body. A comment identifying the field is added
        before the blocks automatically."""
        desc = self._describe()
        if private is not None:
            self._tple.append_block(
                'DECLARATIONS', '@ Private declarations for %s' % desc, private)
        if public is not None:
            self._tple.append_block(
                'PACKAGE', '@ Public declarations for %s' % desc, public)
        if body is not None:
            self._tple.append_block(
                'PACKAGE_BODY', '@ Implementations for %s' % desc, body)

    def add_interface_logic(self, pre=None, post=None):
        """Registers code templates for the hardware interface of the
        represented field descriptor. `pre` is placed before the bus interface
        logic, `post` is placed after. These blocks are executed every cycle
        for each (enabled) field in the descriptor. The template parameter
        `$i$` can be used for the field index. A comment identifying the field
        is added before the blocks automatically."""
        tple = TemplateEngine()
        tple['desc'] = self._describe()
        template = '@ $position$-bus logic for $desc$\n'
        if self.field_descriptor.is_scalar():
            template += '$BLOCK'
            tple['i'] = '0'
        else:
            template += 'for i in 0 to $count-1$ loop\n$ BLOCK\nend loop;'
            tple['count'] = self.field_descriptor.width
            tple['i'] = 'i'
        if pre is not None:
            tple['position'] = 'Pre'
            tple.append_block('BLOCK', pre)
            block = tple.apply_str_to_str(template, postprocess=False)
            self._tple.append_block('FIELD_LOGIC_BEFORE', block)
        if post is not None:
            tple['position'] = 'Post'
            tple.reset_block('BLOCK')
            tple.append_block('BLOCK', post)
            block = tple.apply_str_to_str(template, postprocess=False)
            self._tple.append_block('FIELD_LOGIC_AFTER', block)

    def add_read_logic(self, normal=None, lookahead=None, both=None, deferred=None):
        """Registers code blocks for handling bus reads for this field
        behavior. The blocks can make use of the template variable `$i$` for
        getting the index of the field that is being expanded. The generator
        ensures that the generated code is only executed when the field is
        addressed, enabled, and the bus logic is performing the following
        actions:

         - `normal`: the bus is currently accessing the field, and the bus
           response buffers are ready to accept the read result. `r_prot` holds
           the protection flags for the read. The block can do the following
           things to interact with the bus:

            - Set `r_ack` to `true` and `$r_data$` to the read result.
            - Set `r_nack` to `true` to respond with a slave error.
            - Set `r_block` to `true` to stall, IF the `can_block` flag was
              set for the field's read capabilities. In this case, the block
              will be executed again the next cycle.
            - Set `r_defer` to `true` to defer, IF the `can_defer` flag was
              set for the field's read capabilities. In this case, the request
              logic will accept the bus request and send subsequent requests
              to `lookahead` blocks, while the response logic will start
              calling the `deferred` block to get the response.
            - Nothing: the bus behaves as if the field does not exist. If there
              are no other fields in the addressed register, a decode error is
              returned.

         - `lookahead`: the bus is currently accessing the field, but the
           response logic is not ready for the result yet. This can happen
           because the response channels are still blocked or because this or
           another field deferred a previous request. It can be useful for
           fields that have a long access time. `r_prot` holds the protection
           flags for the read. The block can do the following things to
           interact with the bus:

            - Set `r_defer` to `true` to defer, IF the `can_defer` flag was
              set for the field's read capabilities. In this case, the request
              logic will accept the bus request and send subsequent requests
              to `lookahead` blocks, while the response logic will start
              calling the `deferred` block to get the response when the
              response logic does become ready.
            - Nothing: the bus logic will continue calling the lookahead block
              until the response logic is ready for the response, at which
              point it will call the `normal` block.

         - `deferred`: the `normal` or `lookahead` deferred a read in a
           preceding cycle, and the response logic is ready to accept the read
           result. Multiple accesses can be deferred this way by the same
           field; in all cases it is up to the field to memorize the associated
           protection flags if it needs them. The block can do the following
           things to interact with the bus:

            - Set `r_ack` to `true` and `$r_data$` to the read result to
              complete the transfer.
            - Set `r_nack` to `true` to respond with a slave error.
            - Set `r_block` to `true` to stall, IF the `can_block` flag was
              set for the field's read capabilities. In this case, the block
              will be executed again the next cycle.
            - Nothing: the bus behaves as if the field does not exist. If there
              are no other fields in the addressed register, a decode error is
              returned.
        """
        self._add_bus_logic('r', normal, lookahead, both, deferred)

    def add_write_logic(self, normal=None, lookahead=None, both=None, deferred=None):
        """Registers code blocks for handling bus writes for this field
        behavior. The blocks can make use of the template variable `$i$` for
        getting the index of the field that is being expanded. The generator
        ensures that the generated code is only executed when the register
        that the field belongs to is addressed, enabled, and the bus logic is
        performing the following actions:

         - `normal`: the bus is currently writing to the register that the
           field belongs to, and the bus response buffers are ready to accept
           the write result. `$w_data$` and `$w_strobe$` hold the data that is
           being written. Both variables are `std_logic` or an appropriately
           sized `std_logic_vector` for the field. They carry the following
           significance:

            - `$w_strobe$` low, `$w_data$` low: bit was not written/was masked
              out.
            - `$w_strobe$` high, `$w_data$` low: bit was written zero.
            - `$w_strobe$` high, `$w_data$` high: bit was written one.

           `$w_strobe$` and `$w_data$` high is illegal; one can assume that the
           data for a masked bit is always zero. Note that it is possible that
           none of the bits belonging to the field were actually written; if
           the field wishes to honor the strobe bits, it must do so manually.
           `w_prot` furthermore holds the protection flags for the write. The
           block can do the following things to interact with the bus:

            - Set `w_ack` to `true` to acknowledge the request.
            - Set `w_nack` to `true` to respond with a slave error.
            - Set `w_block` to `true` to stall, IF the `can_block` flag was
              set for the field's write capabilities. In this case, the block
              will be executed again the next cycle.
            - Set `w_defer` to `true` to defer, IF the `can_defer` flag was
              set for the field's write capabilities. In this case, the request
              logic will accept the bus request and send subsequent requests
              to `lookahead` blocks, while the response logic will start
              calling the `deferred` block to get the response.
            - Nothing: the bus behaves as if the field does not exist. If there
              are no other fields in the addressed register, a decode error is
              returned.

         - `lookahead`: the bus is currently accessing the field, but the
           response logic is not ready for the result yet. This can happen
           because the response channels are still blocked or because this or
           another field deferred a previous request. It can be useful for
           fields that have a long access time. `$w_data$`, `$w_strobe$`, and
           `w_prot` carry the same significance that they do for the `normal`
           block. The block can do the following things to interact with the
           bus:

            - Set `w_defer` to `true` to defer, IF the `can_defer` flag was
              set for the field's write capabilities. In this case, the request
              logic will accept the bus request and send subsequent requests
              to `lookahead` blocks, while the response logic will start
              calling the `deferred` block to get the response when the
              response logic does become ready.
            - Nothing: the bus logic will continue calling the lookahead block
              until the response logic is ready for the response, at which
              point it will call the `normal` block.

         - `deferred`: the `normal` or `lookahead` deferred a write in a
           preceding cycle, and the response logic is ready to accept the read
           result. Multiple accesses can be deferred this way by the same
           field; in all cases it is up to the field to memorize the associated
           write data and protection flags if it still needs them. The block
           can do the following things to interact with the bus:

            - Set `w_ack` to `true` to complete the transfer.
            - Set `w_nack` to `true` to respond with a slave error.
            - Set `w_block` to `true` to stall, IF the `can_block` flag was
              set for the field's write capabilities. In this case, the block
              will be executed again the next cycle.
            - Nothing: the bus behaves as if the field does not exist. If there
              are no other fields in the addressed register, a decode error is
              returned.
        """
        self._add_bus_logic('w', normal, lookahead, both, deferred)

    def _describe(self):
        """Generates a description for the represented field descriptor, to be
        used as block comment."""
        return 'field %s%s: %s' % (
            'group ' if self.field_descriptor.is_vector() else '',
            self.field_descriptor.name,
            self.field_descriptor.brief)

    @staticmethod
    def _describe_field(field):
        """Generates a description for a field, to be used as block comment."""
        return 'field %s: %s' % (
            field.name,
            field.brief)

    def _add_bus_logic(self, direction, normal, lookahead, both, deferred):
        """Implements `add_read_logic()` and `add_write_logic()`. They are
        distinguished through `direction`, which must be `'r'` or `'w'`."""
        for index, field in enumerate(self.field_descriptor.fields):

            # Determine the address that the regular field logic should be
            # activated for.
            if direction == 'r':
                register = field.register_read
                address = register.blocks[0].internal_address
            else:
                register = field.register_write
                address = register.blocks[-1].internal_address

            # Describe the field for use in comments.
            desc = self._describe_field(field)

            # Create a template engine for processing the incoming blocks.
            tple = TemplateEngine()
            tple['i'] = index
            if field.bitrange.is_vector():
                rnge = '%d downto %d' % (field.bitrange.high, field.bitrange.low)
                suffix = '%d' % field.bitrange.width
            else:
                rnge = '%d' % field.bitrange.index
                suffix = ''
            tple['rnge'] = rnge
            tple['r_data'] = 'tmp_data%s' % suffix
            tple['r_sub'] = field.subaddress.name
            tple['w_data'] = 'tmp_data%s' % suffix
            tple['w_strobe'] = 'tmp_strb%s' % suffix
            tple['w_sub'] = field.subaddress.name
            tple['desc'] = desc
            tple['dir'] = direction
            if direction == 'r':
                tple['prot'] = self.field_descriptor.behavior.bus.read.prot_mask
            else:
                tple['prot'] = self.field_descriptor.behavior.bus.write.prot_mask

            # Add the normal and lookahead blocks.
            if normal is not None:
                tple.append_block('NORMAL', '@ Regular access logic.', normal)
            if lookahead is not None:
                tple.append_block('LOOKAHEAD', '@ Lookahead logic.', lookahead)
            if both is not None:
                tple.append_block('BOTH', '@ Access logic.', both)
            block = tple.apply_str_to_str(_BUS_REQ_FIELD_TEMPLATE, postprocess=False)
            decoder = {'r': self._read_decoder, 'w': self._write_decoder}[direction]
            decoder[address] = block

            # Add the deferred block.
            if deferred is not None:
                tple.append_block('RESP', '@ Response logic.', deferred)
                tag_decoder, tag = {
                    'r': (self._read_tag_decoder, register.blocks[0].read_tag),
                    'w': (self._write_tag_decoder, register.blocks[-1].write_tag)
                }[direction]
                block = tple.apply_str_to_str(_BUS_RESP_FIELD_TEMPLATE, postprocess=False)
                tag_decoder[tag] = block
