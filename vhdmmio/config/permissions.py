"""Submodule for `PermissionConfig` configurable."""

from ..configurable import configurable, Configurable, flag

@configurable(name='Permissions')
class PermissionConfig(Configurable):
    """This configuration structure defines the privilege levels that are
    allowed to access a field based on the `aw_prot` and `ar_prot` AXI4L
    signals. This is primarily intended to help you identify problems during
    development (such as a softcore deciding to jump to a register file).

    **If you're using `vhdmmio` in an environment where security is in any way
    meaningful, restrict yourself to using single-word, non-blocking registers.
    Even then, `vhdmmio` has not undergone any kind of auditing or
    certification process and therefore does not make ANY guarantees that
    your system will be secure.**

    The following best-effort logic is included based on access privileges:

     - Accessing a field for which the master has insufficient privileges
       makes the field behave like it does not exist. Depending on whether
       there are other fields in the surrounding register that can be
       accessed, a decode error may or may not be generated. Read data is
       always blanked out, and there will not be any side effects.

     - When a higher-privileged master is in the process of accessing a
       multi-word register, lower-privileged accesses are rejected. An access
       is considered less privileged when the ongoing access is privileged
       (`--1`) while the interrupting access is unprivileged (`--0`), OR
       when the ongoing access is secure (`-0-`) while the interrupting access
       is nonsecure (`-1-`). Such accesses are rejected by means of a slave
       error. Even though it would normally be ignored, the read data is
       forced to all zeros during this error to prevent leaks.

     - When a multi-word read completes, the holding register is cleared.

    The latter two features may be disabled within the register file features
    structure to save a small amount of logic.

    `vhdmmio` certainly will *NOT* protect against:

     - Timing attacks on blocking fields. This is impossible to avoid by
       `vhdmmio`, since AXI4L does not support reordering.

     - Denial-of-service and man-in-the-middle style attacks for multi-word
       accesses on the same privilege level. This is impossible to avoid by
       `vhdmmio`, since AXI4L does not support locking.

     - Powerline side-channel attacks, as well as undervolting, overclocking,
       radiation, etc.. Basically, anything that can be used to circumvent the
       semantics of VHDL. This is impossible to avoid in a vendor-agnostic way,
       and would be extremely difficult even for a specific FPGA/ASIC.

    To the best of my knowledge, barring the above, a register file with only
    single-word, non-blocking, non-deferring registers should be fairly secure.
    But please take this statement with a big grain of salt, as I am not a
    security expert."""
    #pylint: disable=E0211,E0213

    @flag
    def user():
        """Whether unprivileged masters (`--0`) can access the field."""
        return True

    @flag
    def privileged():
        """Whether privileged masters (`--1`) can access the field."""
        return True

    @flag
    def secure():
        """Whether secure transactions (`-0-`) can be used to can access the
        field."""
        return True

    @flag
    def nonsecure():
        """Whether nonsecure transactions (`-1-`) can be used to can access the
        field."""
        return True

    @flag
    def data():
        """Whether data transactions (`0--`) can access the field."""
        return True

    @flag
    def instruction():
        """Whether instruction transactions (`1--`) can access the field."""
        return True
