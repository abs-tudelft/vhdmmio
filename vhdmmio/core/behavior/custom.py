"""Submodule for custom behavior."""

from .base import Behavior, behavior, BusAccessNoOpMethod, BusAccessBehavior, BusBehavior
from ...template import annotate_block
from ...config.behavior import Custom
from ...vhdl.types import natural, boolean, Axi4Lite

@behavior(Custom)
class CustomBehavior(Behavior):
    """Behavior class for custom fields."""

    def __init__(self, resources, field_descriptor,
                 behavior_cfg, read_allow_cfg, write_allow_cfg):

        # Parse the interfaces and connect internal signals for them.
        external_interfaces = []
        internal_interfaces = []
        state = []
        names = set()
        for interface in behavior_cfg.interfaces:

            # Figure out what kind of interface we're dealing with.
            kind = None
            value = None
            kinds = ['input', 'output', 'generic',
                     'drive', 'strobe', 'monitor',
                     'state']
            for trial_kind in kinds:
                trial_value = getattr(interface, trial_kind)
                if trial_value is not None:
                    if kind is None:
                        kind = trial_kind
                        value = trial_value
                    else:
                        raise ValueError(
                            'can only specify one of the `input`, `output`, '
                            '`generic`, `drive`, `strobe`, `use`, and `state` '
                            'keys')
            if kind is None:
                raise ValueError(
                    'must specify one of the `input`, `output`, `generic`, '
                    '`drive`, `strobe`, `use`, and `state` keys')

            # Split the name from the shape.
            name, *shape = value.split(':')
            if shape:
                shape = int(shape[0])
            else:
                shape = None

            # Check for configuration errors.
            if name in names:
                raise ValueError(
                    'duplicate interface name %s'
                    % name)
            names.add(name)
            if interface.type in ['natural', 'boolean']:
                if kind != 'generic':
                    raise ValueError(
                        '%s type is only supported for generics'
                        % interface.type)
            if interface.type.startswith('axi4l-'):
                if kind not in ['input', 'output']:
                    raise ValueError(
                        '%s type is only supported for inputs and outputs'
                        % interface.type)
            if field_descriptor.is_vector() and shape is not None:
                if kind in ['drive', 'strobe', 'monitor']:
                    raise ValueError(
                        'repeated fields cannot %s a vector internal signal'
                        % kind)

            # Internal signals are shaped based on the field repetition.
            internal_shape = shape
            internal_suffix = ''
            if field_descriptor.is_vector():
                internal_shape = field_descriptor.width
                internal_suffix = '($i$)'

            # Determine the VHDL type.
            vhdl_type = None
            if interface.type == 'natural':
                vhdl_type = natural
            if interface.type == 'boolean':
                vhdl_type = boolean
            if interface.type.startswith('axi4l'):
                _, component, width = '-'.split(interface.type)
                vhdl_type = Axi4Lite(component, int(width))
            assert vhdl_type is not None or interface.type == 'std_logic'

            # Handle the interface.
            if kind == 'input':
                external_interfaces.append(('i', name, shape, vhdl_type))
            elif kind == 'output':
                external_interfaces.append(('o', name, shape, vhdl_type))
            elif kind == 'generic':
                external_interfaces.append(('g', name, shape, vhdl_type))
            elif kind == 'drive':
                assert vhdl_type is None
                internal = resources.internals.drive(
                    field_descriptor, name, internal_shape)
                internal_interfaces.append((
                    internal, True, internal_suffix))
            elif kind == 'strobe':
                assert vhdl_type is None
                internal = resources.internals.strobe(
                    field_descriptor, name, internal_shape)
                internal_interfaces.append((
                    internal, True, internal_suffix))
            elif kind == 'monitor':
                assert vhdl_type is None
                internal = resources.internals.use(
                    field_descriptor, name, internal_shape)
                internal_interfaces.append((
                    internal, False, internal_suffix))
            elif kind == 'state':
                assert vhdl_type is None
                state.append((name, shape))
            else:
                assert False

        # Freeze the interfaces we found.
        self._external_interfaces = tuple(external_interfaces)
        self._internal_interfaces = tuple(internal_interfaces)
        self._state = tuple(state)

        # Figure out a decent source "filename" for the template blocks, such
        # that parse error messages can be made somewhat sane.
        source = []
        if field_descriptor.regfile.cfg.source_file is not None:
            source.append(field_descriptor.regfile.cfg.source_file)
        source.append(field_descriptor.regfile.name)
        source.append(field_descriptor.name)
        source = '/'.join(source)

        # Annotate the template blocks with the source.
        def annotate(name):
            tpl = getattr(behavior_cfg, name.replace('-', '_'))
            if tpl is None:
                return None
            return annotate_block(tpl, '%s/%s' % (source, name))
        self._pre_access_template = annotate('pre-access')
        self._read_template = annotate('read')
        self._read_lookahead_template = annotate('read-lookahead')
        self._read_request_template = annotate('read-request')
        self._read_response_template = annotate('read-response')
        self._write_template = annotate('write')
        self._write_lookahead_template = annotate('write-lookahead')
        self._write_request_template = annotate('write-request')
        self._write_response_template = annotate('write-response')
        self._post_access_template = annotate('post-access')

        # Decode the bus access behavior.
        can_read = (
            self._read_template is not None
            or self._read_lookahead_template is not None
            or self._read_request_template is not None)
        if can_read:
            read_behavior = BusAccessBehavior(
                read_allow_cfg,
                blocking=behavior_cfg.read_can_block,
                volatile=behavior_cfg.read_volatile,
                deferring=behavior_cfg.read_response is not None,
                no_op_method={
                    True: BusAccessNoOpMethod.NEVER,
                    False: BusAccessNoOpMethod.ALWAYS,
                }[behavior_cfg.read_has_side_effects])
        else:
            read_behavior = None

        can_write = (
            self._write_template is not None
            or self._write_lookahead_template is not None
            or self._write_request_template is not None)
        if can_write:
            write_behavior = BusAccessBehavior(
                write_allow_cfg,
                blocking=behavior_cfg.write_can_block,
                volatile=behavior_cfg.write_volatile,
                deferring=behavior_cfg.write_response is not None,
                no_op_method={
                    'never': BusAccessNoOpMethod.NEVER,
                    'zero': BusAccessNoOpMethod.WRITE_ZERO,
                    'current': BusAccessNoOpMethod.WRITE_CURRENT,
                    'mask': BusAccessNoOpMethod.MASK,
                    'current-or-mask': BusAccessNoOpMethod.WRITE_CURRENT_OR_MASK,
                    'always': BusAccessNoOpMethod.ALWAYS,
                }[behavior_cfg.write_no_op])
        else:
            write_behavior = None

        bus_behavior = BusBehavior(
            read=read_behavior, write=write_behavior,
            can_read_for_rmw=behavior_cfg.read_write_related)

        super().__init__(field_descriptor, behavior_cfg, bus_behavior)

    @property
    def external_interfaces(self):
        """A tuple consisting of `(mode, name, count, type)` tuples,
        representing the external interfaces for this behavior."""
        return self._external_interfaces

    @property
    def internal_interfaces(self):
        """A tuple consisting of `(Internal, direction, suffix)` tuples,
        representing the internal interfaces for this behavior."""
        return self._internal_interfaces

    @property
    def state(self):
        """A tuple consisting of `(name, shape)` tuples, representing the
        state registers needed for this behavior."""
        return self._state

    @property
    def pre_access_template(self):
        """Pre-access VHDL template."""
        return self._pre_access_template

    @property
    def read_template(self):
        """Normal read VHDL template."""
        return self._read_template

    @property
    def read_lookahead_template(self):
        """Read lookahead VHDL template."""
        return self._read_lookahead_template

    @property
    def read_request_template(self):
        """Read request VHDL template."""
        return self._read_request_template

    @property
    def read_response_template(self):
        """Read response VHDL template."""
        return self._read_response_template

    @property
    def write_template(self):
        """Normal write VHDL template."""
        return self._write_template

    @property
    def write_lookahead_template(self):
        """Write lookahead VHDL template."""
        return self._write_lookahead_template

    @property
    def write_request_template(self):
        """Write request VHDL template."""
        return self._write_request_template

    @property
    def write_response_template(self):
        """Write response VHDL template."""
        return self._write_response_template

    @property
    def post_access_template(self):
        """Post-access VHDL template."""
        return self._post_access_template

    @property
    def doc_reset(self):
        """The reset value as printed in the documentation as an integer, or
        `None` if the field is driven by a signal and thus does not have a
        register to reset."""
        return None
