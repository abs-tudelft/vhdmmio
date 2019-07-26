"""Submodule for `Primitive` configurable."""

import re
from ...config import configurable, Configurable
from .registry import behavior

@behavior(
    'custom', 'allows you to specify the field-specific VHDL code manually.')
@configurable(name='`custom` behavior')
class Custom(Configurable): # TODO
    """NOTE: not yet implemented!

    Fields with `custom` behavior can be programmed to do anything, but you
    have to specify the VHDL code for field access yourself. With great power
    comes great responsibility: you'll need to understand some of `vhdmmio`'s
    internals, and it is in fact possible to execute arbitrary Python code
    using the provided template engine. Because of the latter, you need to
    specify the `--trusted` flag to `vhdmmio`'s command line to use this.

    When a logical register is accessed, each field can independently respond
    to the request by acknowledging it, rejecting it, ignoring it, blocking it,
    or deferring it. The logic that handles the request and generates this
    response is called the field logic. The responses of the individual fields
    are combined into a single action as follows:

     - If any field defers the request, the request is handshaked, but no
       response is sent yet. Instead, the field logic is addressed again later
       to get the response, at which point it must perform any of the following
       actions.
     - If any field blocks the request, the request stays in its holding
       register. Thus, the same request will appear again in the next cycle.
     - Otherwise, if any field rejects the request, the request is handshaked
       and a `slverr` response (`"10"`) is sent.
     - Otherwise, if any field responds with an acknowledgement, the request is
       handshaked an `okay` response (`"00"`) is sent.
     - If zero fields respond, the request is handshaked and a `decerr`
       response (`"11"`) is sent.

    Deferral allows fields such as AXI passthrough fields to handle multiple
    outstanding requests. Such deferral logic (particularly the required FIFO)
    is only generated for register files and logical registers that need it.

    Accesses to addresses that do not map to any fields by default return
    `decerr` responses, since there is no field logic to generate a response.
    `vhdmmio` can however be instructed to "optimize" its address decoder by
    treating accesses that do not map to any field as don't care. This usually
    prevents wide equal-to-constant blocks from being inferred, potentially
    improving timing performance.

    Within an access type (read or write), fields can have characteristics that
    prevent them from sharing a logical register with other fields. These
    characteristics are:

     - Blocking fields: these can block/delay bus access for as long as they
       like. Non-blocking fields always return immediately.

     - Volatile fields: for volatile fields, performing the same operation more
       than once in a row has a different result than performing the operation
       once. Examples of such fields are mmio-to-stream fields, which push data
       into a FIFO for every write, or accumulator fields, which add the
       written value instead of writing it directly.

     - Deferring fields: these can postpone generating a response in a way that
       allows for multiple outstanding requests.

    The rules are:

     - Blocking fields cannot be combined with other blocking fields.
     - Blocking fields cannot be combined with volatile fields.
     - Deferring fields cannot be combined with any other field.

    Fields must also specify how (or if) a master can choose to not access a
    field (or rather, prevent side effects) while still accessing other fields
    in the surrounding logical register. The options are:

     - *always*: all accesses are no-op for the field. This is usually the case for
       reads, but not always.
     - *write zero*: writing zeros to the field is no-op. This is usually the case
       for flag and counter fields.
     - *write current*: first read the register, then write the bits that were read
       to it for no-op.
     - *mask*: bits masked out by the AXI4L byte strobe field are not affected.
     - *write current or mask*: both of the above methods will work. This is
       usually the case for control registers.
     - *never*: it is impossible to access this register without causing side
       effects for this field. This is for instance the case for AXI4L passthrough
       fields.
    """
