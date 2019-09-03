"""Submodule for managing deferral tags."""

from .mixins import Unique

class _DeferTag(Unique):
    """Represents a deferral tag."""

    def __init__(self, manager, index):
        self._manager = manager
        self._index = index

    def __int__(self):
        return self._index

    def __str__(self):
        return ('"{:0%db}"' % self._manager.width).format(self._index)

    @property
    def address(self):
        """The defer tag index for the address matcher."""
        return self._index

    @property
    def mask(self):
        """The mask for the defer tag index address matcher."""
        return (1 << self._manager.width) - 1


class DeferTagManager:
    """Manages the deferral tags for one of the two bus access modes
    (read/write). Deferral tags are used to manage multiple outstanding
    requests. Each register that supports this gets one (per access mode). When
    the register defers an access (that is, when it acknowledges the bus access
    request but doesn't provide a response yet), the register's tag is pushed
    into a FIFO and the next request is handled. The tag at the front of the
    FIFO is then used to select which register should provide the next bus
    response."""

    def __init__(self):
        self._count = 0

    @property
    def count(self):
        """The number of deferral tags handed out."""
        return self._count

    @property
    def width(self):
        """The number of bits needed to represent the deferral tags."""
        return max(1, (self.count - 1).bit_length())

    def __bool__(self):
        return self._count > 0

    def get_next(self):
        """Returns the next available deferral tag."""
        tag = _DeferTag(self, self._count)
        self._count += 1
        return tag


class DeferTagInfo:
    """Exposes defer tag properties needed for the VHDL code generator."""

    def __init__(self, read, write, max_outstanding):
        super().__init__()
        self._read_count = read.count
        self._read_width = read.width
        self._write_count = write.count
        self._write_width = write.width
        self._tag_depth_log2 = (max_outstanding - 1).bit_length()

    @property
    def read_count(self):
        """The number of read tags used by the associated register file."""
        return self._read_count

    @property
    def read_width(self):
        """The width of the `std_logic_vector`s used to represent the read tags
        for the associated register file."""
        return self._read_width

    @property
    def write_count(self):
        """The number of write tags used by the associated register file."""
        return self._write_count

    @property
    def write_width(self):
        """The width of the `std_logic_vector`s used to represent the write tags
        for the associated register file."""
        return self._write_width

    @property
    def tag_depth_log2(self):
        """Log2 of the maximum number of outstanding requests."""
        return self._tag_depth_log2
