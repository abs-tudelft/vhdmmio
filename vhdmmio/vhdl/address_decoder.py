"""Module for constructing address decoders."""

import re
from ..template import TemplateEngine

class AddressDecoder:
    """Class for generating VHDL address decoders. That is, based on the value
    of an `std_logic_vector`, execute various actions. This is much like a
    `case-when` statement, but more powerful, because this generator has full
    support for don't cares, and tries to make the decoder nicely
    human-readable as well, using if statements where appropriate. This might
    also help the synthesizer merge address comparators together more than it
    would with a single case statement.

    The address decoder will match the address signal or variable named by
    `address`, which must be an `std_logic_vector(num_bits - 1 downto 0)`. If
    `optimize` is set, the action for any address for which no action is
    specified is interpreted as don't care, versus the default no-operation
    behavior. If `allow_overlap` is set, addresses that partially or fully
    overlap each other due to don't cares (for instance `1--1` and `11--`) do
    not result in an exception. Similarly, if `allow_duplicate` is set,
    multiple actions per address do not result in an exception."""

    def __init__(self, address, num_bits,
                 optimize=False, allow_overlap=False, allow_duplicate=False):
        super().__init__()
        self._num_bits = num_bits
        self._optimize = optimize
        self._allow_overlap = allow_overlap
        self._allow_duplicate = allow_duplicate
        self._tple = TemplateEngine()
        self._tple['address'] = address
        self._addresses = set()

    @staticmethod
    def _common_prefix(items):
        """Returns the prefix common to all strings in `items`."""
        items = iter(items)
        common = next(items)
        for item in items:
            if not common:
                break
            while not item.startswith(common):
                common = common[:-1]
                if not common:
                    break
        return common

    @staticmethod
    def _common_suffix(items):
        """Returns the suffix common to all strings in `items`."""
        items = iter(items)
        common = next(items)
        for item in items:
            if not common:
                break
            while not item.endswith(common):
                common = common[1:]
                if not common:
                    break
        return common

    @staticmethod
    def _count_up_to(iterable, condition):
        """Counts the number of items yielded by `iterator` until the item
        matches the `condition` function."""
        count = 0
        for item in iterable:
            if condition(item):
                break
            count += 1
        return count

    @staticmethod
    def _address_to_key(address):
        """Converts the given address to the key name used within the template
        engine."""
        return 'ADDR_%s' % address.replace('-', '_')

    def _gen_template(self, high, low, address_prefix, address_suffix, addresses):
        """Generates the template recusively.

         - `high`: the address bit index that the first character in the
           `addresses` list maps to.
         - `low`: the address bit index that the last character in the
           `addresses` list maps to.
         - `address_prefix`: previously-conditioned part of the address on
           the MSB side.
         - `address_suffix`: previously-conditioned part of the address on
           the LSB side.
         - `addresses`: list of addresses that still need to be
           matched/discriminated.

        The return value is a list of VHDL template lines.

        Addresses are represented as bit strings with `0`, `1`, and `-`
        characters. `-` represents don't care.

        This function recursively looks for patterns in the list of addresses
        on both the MSB and LSB side, then chooses an appropriate VHDL
        construct to discriminate between the addresses. It can only do one
        of these patterns at a time, so it recursively calls itself with a
        simplified list of addresses. Initially, `high` and `low` should be set
        to the high and low bit indices of the to-be-matched address,
        `address_prefix` and `address_suffix` should be empty strings, and
        `addresses` should contain all the to-be-matched addresses. As the
        function descends, the addresses in `addresses` become narrower (with
        `high` and `low` updated accordingly), and the matched part of the address
        is added to `address_prefix` and/or `address_suffix`, such that
        prefixing/suffixing those to the addresses in the list forms the
        original addresses. Recursion terminates when there are no more bits
        remaining to be discriminated."""

        # Some assertions to make sure that stuff isn't broken.
        assert high - low + 1 + len(address_prefix) + len(address_suffix) == self._num_bits
        if not addresses:
            assert high - low + 1 == self._num_bits
            return []
        for address in addresses:
            assert len(address) == high - low + 1

        # End-of-recursion condition.
        if high < low:

            # There should always be one empty address remaining in the address
            # list. One, because we should have matched all bits at this point
            # and there shouldn't be any duplicates, and empty, because all
            # bits of the address have been transferred to address_prefix and
            # address_suffix during the recursion.
            address = address_prefix + address_suffix
            assert len(addresses) == 1
            assert not addresses[0]
            assert len(address) == self._num_bits
            return [
                '-- $address$ = %s' % address,
                '$%s' % self._address_to_key(address)]

        # Test for precise-match prefixes.
        common = self._common_prefix(addresses)
        if common:

            # Handle the case where we have a common prefix of all don't-cares.
            # We can just call ourselves recursively in this case; no matching
            # needs to be performed.
            dont_care_count = self._count_up_to(common, lambda bit: bit != '-')
            if dont_care_count:
                common = common[:dont_care_count]
                return self._gen_template(
                    high - len(common), low, address_prefix + common, address_suffix,
                    [a[len(common):] for a in addresses])

            # Handle the case where we have a common prefix of something that
            # isn't don't cares. When optimize is set, we just recursively call
            # ourselves without an if statement - after all, none of the bits
            # in the prefix discriminate between address options. If we're not
            # optimizing, we wrap the result of the recursive call in an if
            # statement with a vector match condition.
            fixed_count = self._count_up_to(common, lambda bit: bit == '-')
            assert fixed_count
            common = common[:fixed_count]
            recurse = self._gen_template(
                high - len(common), low, address_prefix + common, address_suffix,
                [a[len(common):] for a in addresses])
            if self._optimize:
                return recurse
            result = []
            result.append(
                'if $address$(%d downto %d) = "%s" then'
                % (high, high - len(common) + 1, common))
            result.extend(('  ' + s for s in recurse))
            result.append('end if;')
            return result

        # Do the same we did above, but for suffixes.
        common = self._common_suffix(addresses)
        if common:

            # Handle the case where we have a common suffix of all don't-cares.
            # We can just call ourselves recursively in this case; no matching
            # needs to be performed.
            dont_care_count = self._count_up_to(reversed(common), lambda bit: bit != '-')
            if dont_care_count:
                common = common[-dont_care_count:]
                return self._gen_template(
                    high, low + len(common), address_prefix, common + address_suffix,
                    [a[:-len(common)] for a in addresses])

            # Handle the case where we have a common suffix of something that
            # isn't don't cares. When optimize is set, we just recursively call
            # ourselves without an if statement - after all, none of the bits
            # in the suffix discriminate between address options. If we're not
            # optimizing, we wrap the result of the recursive call in an if
            # statement with a vector match condition.
            fixed_count = self._count_up_to(reversed(common), lambda bit: bit == '-')
            assert fixed_count
            common = common[-fixed_count:]
            recurse = self._gen_template(
                high, low + len(common), address_prefix, common + address_suffix,
                [a[:-len(common)] for a in addresses])
            if self._optimize:
                return recurse
            result = []
            result.append(
                'if $address$(%d downto %d) = "%s" then'
                % (low + len(common) - 1, low, common))
            result.extend(('  ' + s for s in recurse))
            result.append('end if;')
            return result

        # Look for the longest prefix without don't cares in it in any address.
        # After the above, there must be at least one such bit, otherwise there
        # must be a duplicate address!
        common = self._common_prefix((s.replace('1', '0') for s in addresses))
        if common:
            fixed_count = self._count_up_to(common, lambda bit: bit == '-')
            if fixed_count:
                common = common[:fixed_count]

                # Since we only considered don't-care vs. not don't care,
                # common may not actually be a common prefix. Instead, we can
                # have any number of options. Put all these options in a set.
                # In fact, there HAS to be more than one of these options,
                # otherwise the precise-match prefix would have caught it.
                options = set((s[:len(common)] for s in addresses))

                # If we only have one bit to match, use an if-else statement
                # that just does a scalar match.
                if len(common) == 1:
                    recurse_zero = self._gen_template(
                        high - 1, low, address_prefix + '0', address_suffix,
                        [a[1:] for a in addresses if a.startswith('0')])
                    recurse_one = self._gen_template(
                        high - 1, low, address_prefix + '1', address_suffix,
                        [a[1:] for a in addresses if a.startswith('1')])
                    result = []

                    if recurse_one and recurse_one[0].startswith('if '):
                        result.append('if $address$(%d) = \'0\' then' % high)
                        result.extend(('  ' + s for s in recurse_zero))
                        result.append('els' + recurse_one[0])
                        result.extend(recurse_one[1:])
                        return result

                    if recurse_zero and recurse_zero[0].startswith('if '):
                        result.append('if $address$(%d) = \'1\' then' % high)
                        result.extend(('  ' + s for s in recurse_one))
                        result.append('els' + recurse_zero[0])
                        result.extend(recurse_zero[1:])
                        return result

                    result.append('if $address$(%d) = \'0\' then' % high)
                    result.extend(('  ' + s for s in recurse_zero))
                    result.append('else')
                    result.extend(('  ' + s for s in recurse_one))
                    result.append('end if;')
                    return result

                # If we have more than one bit, use a case statement. If
                # we're optimizing, the "when others" line that would otherwise
                # be no-op will be merged with the final useful when.
                result = []
                result.append(
                    'case $address$(%d downto %d) is'
                    % (high, high - len(common) + 1))
                options = sorted(options)
                for index, option in enumerate(options):
                    if self._optimize and index == len(options) - 1:
                        result.append('  when others => -- "%s"' % option)
                    else:
                        result.append('  when "%s" =>' % option)
                    result.extend(('    ' + s for s in self._gen_template(
                        high - len(common), low, address_prefix + option, address_suffix,
                        [a[len(common):] for a in addresses if a.startswith(option)])))
                if not self._optimize:
                    result.append('  when others =>')
                    result.append('    null;')
                result.append('end case;')
                return result

        # We have overlapping addresses.
        if not self._allow_overlap:
            raise ValueError(
                'addresses overlap at bit {0}: found both {1}-{2}{3} and '
                '{1}0{2}{3} and/or {1}1{2}{3}'.format(
                    high, address_prefix, '#' * (high - low), address_suffix))

        # To handle overlap, split the addresses with don't cares for the next
        # bit from addresses that discriminate based on the next bit, recurse,
        # and just concatenate the results together.
        result = []
        result.extend(self._gen_template(
            high, low, address_prefix, address_suffix,
            [address for address in addresses if address[0] != '-']))
        result.append('')
        result.extend(self._gen_template(
            high, low, address_prefix, address_suffix,
            [address for address in addresses if address[0] == '-']))
        return result

    def add_action(self, masked_address, block):
        """Registers the given code block for execution when the address
        input matches `address`, which should be of type
        `core.address.MaskedAddress`."""
        fmt = '{:0%db}' % self._num_bits
        address = fmt.format(masked_address.address)
        mask = fmt.format(masked_address.mask)
        address = ''.join((a if m == '1' else '-' for a, m in zip(address, mask)))
        if not self._allow_duplicate and address in self._addresses:
            raise ValueError('duplicate address 0b%s' % address)
        self._addresses.add(address)
        self._tple.append_block(self._address_to_key(address), block)

    def __setitem__(self, key, value):
        self.add_action(key, value)

    def generate(self):
        """Generates the address decoder."""
        if not self._addresses:
            return None

        return self._tple.apply_str_to_str(
            '\n'.join((
                re.sub(r'^ ( +)\$', r'$\1', line).rstrip()
                for line in self._gen_template(
                    self._num_bits - 1, 0, '', '', list(self._addresses)))),
            postprocess=False)

    def __str__(self):
        result = self.generate()
        return result if result is not None else ''

    def append_to_template(self, tple, key, comment):
        """Appends this decoder to the given template engine as a block,
        prefixing the given comment."""
        block = self.generate()
        if block is None:
            return
        tple.append_block(key, '@ ' + comment, block)
