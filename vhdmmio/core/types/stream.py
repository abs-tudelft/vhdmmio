"""Module for fields that interface with AXI streams."""

from .primitive import PrimitiveField
from ..logic_registry import field_logic
from ..utils import override, default

@field_logic('stream-to-mmio')
class StreamToMmioField(PrimitiveField):
    """Hardware to software stream. The stream is "popped" when the field is
    read, so it is write-once read-once; for write-once read-many use
    `latching` instead. By default, the read is blocked until a value is
    available."""

    def __init__(self, field_descriptor, dictionary):
        override(dictionary, {
            'after_bus_read':   'invalidate',
            'bus_write':        'disabled',
            'after_bus_write':  'nothing',
            'hw_read':          'handshake', # for the ready flag
            'hw_write':         'stream', # data; write enable = valid & ready
            'after_hw_write':   'validate',
        })

        default(dictionary, {
            'bus_read':         'valid-wait',
            'reset':            None,
        })

        super().__init__(field_descriptor, dictionary)


@field_logic('mmio-to-stream')
class MmioToStreamField(PrimitiveField):
    """Software to hardware stream. By default, writes are blocked while the
    field has not been popped by hardware yet. The valid bit of the internal
    register maps one-to-one to the stream valid signal, while the invalidate
    signal is connected to `ready`."""

    def __init__(self, field_descriptor, dictionary):
        override(dictionary, {
            'bus_read':         'disabled',
            'after_bus_read':   'nothing',
            'after_bus_write':  'validate',
            'hw_read':          'enabled', # for data and stream valid
            'hw_write':         'disabled',
            'after_hw_write':   'nothing',
            'ctrl_ready':       'enabled', # ready flag
        })

        default(dictionary, {
            'bus_write':        'invalid-wait',
            'reset':            None,
        })

        super().__init__(field_descriptor, dictionary)
