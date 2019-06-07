


Parameters of all fields
========================

 - address: <address>[/<size=2>][:[<high-bit=31/63>..]<low-bit=0>]
    - the register is addressed if the incoming address & mask == address.
    - if high-bit > 31, the register becomes multi-word. the necessary amount
      of subsequent registers then become in/out holding registers. read
      actions are performed and held when the first register is read, write
      actions are performed when the last register is written and held until
      then.

 - mnemonic: <identifier=name>
    - name used to refer to the field in documentation and C constants
    - must be unique within enclosed register only
    - when field is repeated, the index is suffixed where appropriate

 - name: <identifier>
    - name used for the field in VHDL
    - must be unique within register file
    - when field is repeated, the index is suffixed where appropriate

 - brief: <single-paragraph markdown=None>
    - single-line markdown documentation for the field
    - when field is repeated, {index} is replaced with the field index where
      appropriate, or "*<0..N>*" when summary is printed for all repetitions

 - doc: <multiline markdown=None>
    - multi-line markdown documentation for the field
    - when field is repeated, {index} is replaced with the field index where
      appropriate, or "*<0..N>*" when summary is printed for all repetitions

 - register-mnemonic: <identifier=name>

 - register-name: <identifier=name>
    - name used to refer to the register in documentation and C constants
    - when multiple fields are associated with a register, only one may carry
      this tag. if none of the registers carry the tag, the name is inherited
      from the lowest-indexed read field, or if the register is write-only, the
      lowest-indexed write field
    - only a singular value is accepted regardless of repetition
    - when field is repeated, the index is suffixed where appropriate

 - register-brief: <single-paragraph markdown=None>
    - combination of register-name and brief

 - register-doc: <multiline markdown=None>
    - combination of register-name and doc

 - repeat: <num=1>
    - number of times to repeat the field
    - all generics and ports releated to this fieldset become arrays
    - parameters specified in the spec file can be specified either as a single
      value (which is used for all) or as a comma-separated array of sufficient
      length within [] unless otherwise specified
    - if only a single address is specified, it specifies the address for the
      first field (index 0). the rest is calculated using field-repeat, stride,
      and field-stride.

 - field-repeat: <num=repeat>
    - number of times to repeat the field within a logical register before
      advancing to the next register
    - only used when only the first field's address is specified
    - only a singular value is accepted regardless of repetition

 - stride: <num=min-stride-pow2>
    - number of 32-bit words to increment the address by when advancing to the
      next register
    - only used when only the first field's address is specified
    - only a singular value is accepted regardless of repetition

 - field-stride: <num=min-bits>
    - number of bits to increment high-bit/low-bit by when advancing to the
      next field
    - only used when only the first field's address is specified
    - only a singular value is accepted regardless of repetition

 - type: <field type, see below>
    - determines the behavior of the register
    - note that some field types are read-only and some are write-only. two
      different fields, one being read-only and one being write-only, can
      have overlapping addresses/bit ranges.
    - only a singular value is accepted regardless of repetition


Types of fields
===============

Primitive
---------

 - primitive
    - bus-read-mode = read: specifies action of bus reads (no/read/clear/increment/decrement) [singular]
    - bus-write-mode = none: specifies action of bus writes (none/write/accumulate/clear/increment/decrement/set/reset/toggle) [singular]
    - hw-read-enable = no: specifies hardware read interface (no/yes) [singular]
    - hw-write-mode = none: specifies hardware write interface (none/transparent/write/accumulate) [singular]
    - hw-response-enable = no: allows updating the bus response (no/yes) [singular]
    - hw-clear-enable = no: specifies existence of clear signal (no/yes) [singular]
    - hw-increment-enable = no: specifies existence of increment signal (no/yes) [singular]
    - hw-decrement-enable = no: specifies existence of decrement signal (no/yes) [singular]
    - hw-set-enable = no: specifies existence of bit-set signal (no/yes) [singular]
    - hw-reset-enable = no: specifies existence of bit-reset signal (no/yes) [singular]
    - hw-toggle-enable = no: specifies existence of bit-toggle signal (no/yes) [singular]
    - reset-value = 0: value to set when block is reset [const/generic/signal]
    - reset-response = ok: read response to send between reset and first write (ok/slave-error/decode-error/block) [const/generic/signal]

 - control: synonym for primitive with the following defaults overridden:
    - bus-read-mode = read
    - bus-write-mode = write
    - hw-read-enable = yes

 - constant: synonym for primitive with the following defaults overridden:
    - bus-read-mode = read
    - hw-write-mode = none

 - status: synonym for primitive with the following defaults overridden:
    - bus-read-mode = read
    - hw-write-mode = transparent

 - latching: synonym for primitive with the following defaults overridden:
    - bus-read-mode = read
    - hw-write-mode = write

 - flag: synonym for primitive with the following defaults overridden:
    - bus-read-mode = read
    - bus-write-mode = reset
    - hw-set-enable = yes

 - flag-volatile: synonym for primitive with the following defaults overridden:
    - bus-read-mode = clear
    - hw-set-enable = yes

 - counter: synonym for primitive with the following defaults overridden:
    - bus-read-mode = read
    - bus-write-mode = write
    - hw-increment-enable = yes

 - counter-volatile: synonym for primitive with the following defaults overridden:
    - bus-read-mode = clear
    - hw-increment-enable = yes

Interrupts
----------

Interrupts are special inputs that each have up to three internal registers
associated with them:

 - flag (default 0)
 - mask (default 1)
 - enable (default 1)

An incoming strobe signal is used to set the flag bit iff the enable bit is
set. If both the flag bit and the mask bits are set for any interrupt, the
block's combined interrupt output is asserted.

 - irq-flag: works the same as flag register but operates on the interrupt
   flag register
    - irq = mnemonic: name of the interrupt to operate on
    - hw-set-enable = no

 - irq-mask: works the same as control register but operates on the interrupt mask
    - irq = mnemonic: name of the interrupt to operate on
    - hw-read-enable = no

 - irq-enable: works the same as control register but operates on the interrupt enable
    - irq = mnemonic: name of the interrupt to operate on
    - hw-read-enable = no

Atomic flags
------------

Atomic flags are like flag primitives, but use two field bits per internal
register bit (so the width of the field must be divisible by 2). When read,
0b01 is returned when the respective bit is set, and 0b10 when it is cleared.
When written, the operation performed is no-op for 0b00, set for 0b01, clear
for 0b10, or toggle for 0b11. The practical upshot of which is that the bits
within a logical register can be unaffected/set/cleared/toggled/restored using
a single atomic write.

 - atomic-flag:
    - hw-read-enable = yes: specifies hardware read interface (no/yes) [singular]
    - hw-write-enable = no: specifies existence of hardware write interface (no/yes) [singular]
    - hw-clear-enable = no: specifies existence of clear signal (no/yes) [singular]
    - hw-set-enable = no: specifies existence of bit-set signal (no/yes) [singular]
    - hw-reset-enable = no: specifies existence of bit-reset signal (no/yes) [singular]
    - hw-toggle-enable = no: specifies existence of bit-toggle signal (no/yes) [singular]
    - reset-value = 0: value to set when block is reset [const/generic/signal]

Embedded memories
-----------------

Like ram-iface, but with the memory embedded within the register block using a
behavioral description. Only a subset of ram-iface's features are supported (no
byte-enables for instance). However, this is good enough when you just need a
no-nonsense quick-and-dirty memory. The portedness of the inferred memory is
configurable; if not enough ports are available, they are shared using
configurable priority between the bus and hardware interfaces.

 - ram:
    - bus-write-enable=yes: (no/yes)
    - bus-read-enable=yes: (no/yes)
    - hw-write-enable=yes: (no/yes) [singular]
    - hw-read-enable=yes: (no/yes) [singular]
    - mode=1r1w: (1rw/2rw/1r1w/2r1w/2r2w/1r1rw)
    - priority=hw: (hw/bus/rr)

AXI-lite passthrough
--------------------

This "field" type passes the AXI-lite requests through to a child bus, thereby
allowing nesting. The /mask in the address specification for the field is used
to specify the size of the passthrough block, the inverse of which is by
default applied to the address reported to the child (so its addresses
seemingly start at zero). The upper bits that therefore cannot be set by the
master bus can be taken from a register defined through a primitive field
to facilitate paging. Multiple outstanding requests are supported through a
FIFO inferred within the block, the size of which being set to at least the
maximum of the min-outstanding keys of all axi fields. If min-outstanding is 0
(the default), multiple outstanding requests are disabled for the specified
interface (i.e. new requests will block if there are any outstanding requests).

 - axi:
    - min-outstanding = 0: minimum number of outstanding requests that must be supported
    - output-address-mask = ~address-mask: value and'ed with incoming address
    - output-address-base = 0: value added to incoming address
    - page-field = None: name of the primitive field used to control the upper bits of the output bus
    - connects-to = None: name of the register file block that this bus connects to (used for documentation output)

Memory passthrough
------------------

This field is sort of like axi, but uses a simplified single-cycle-write,
single-or-more-cycle-read interface similar to what's used for block RAMs.

 - ram-iface:
    - write-mode=word: (none/slave-error/decode-error/word/byte) [singular]
    - read-mode=1: (none/slave-error/decode-error/<cycle count>/handshake) [singular]

Stream interface
----------------

These field types allow direct interfacing with streams. stream-source is
write-only, stream-sink is read-only.

 - stream-source:
    - overflow: (ignore/block/slave-error/decode-error)

 - stream-sink:
    - underflow: (ignore/block/slave-error/decode-error)
    - underflow-value: [const/generic/signal]

