"""Module for the `match_template` function."""

import re

def match_template(num_bits, addresses, optimize=False):
    """Generates a VHDL case/switch template for a vector of the given number
    of bits and the given addresses. The addresses must be any mix of integer
    addresses and two-tuples of base address and bitmask, where a high bit in
    the bitmask indicates that the bit is to be used. If `optimize` is set,
    this function assumes that the action for any address not in the address
    list is don't care. The resulting template uses `$address$` for the
    to-be-matched address, and block markers of the form `$ADDR_0x%X` for the
    to-be-inserted blocks."""

    def conv_address(address):
        """Converts the incoming addresses into std_match-style strings."""
        if isinstance(address, int):
            mask = 0
            address = int(address)
        else:
            mask = int(address[1])
            address = int(address[0])
        mask = ~mask & (1 << num_bits) - 1
        fmt = '{:0%db}' % num_bits
        address = fmt.format(address)
        mask = fmt.format(mask)
        return ''.join((a if m == '1' else '-' for a, m in zip(address, mask)))

    addresses = [conv_address(a) for a in addresses]

    def common_prefix(items):
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

    def common_suffix(items):
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

    def count_up_to(iterable, condition):
        """Counts the number of items yielded by `iterator` until the item
        matches the `condition` function."""
        count = 0
        for item in iterable:
            if condition(item):
                break
            count += 1
        return count

    def gen_template(high, low, address_prefix, address_suffix, addresses):
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
        assert high - low + 1 + len(address_prefix) + len(address_suffix) == num_bits
        if not addresses:
            assert high - low + 1 == num_bits
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
            if len(addresses) > 1:
                raise ValueError('duplicate address %s' % address)
            assert not addresses[0]
            assert len(address) == num_bits
            return [
                '-- $address$ = %s' % address,
                '$ADDR_0x%X' % int(address.replace('-', '0'), 2)]

        # Test for precise-match prefixes.
        common = common_prefix(addresses)
        if common:

            # Handle the case where we have a common prefix of all don't-cares.
            # We can just call ourselves recursively in this case; no matching
            # needs to be performed.
            dont_care_count = count_up_to(common, lambda bit: bit != '-')
            if dont_care_count:
                common = common[:dont_care_count]
                return gen_template(
                    high - len(common), low, address_prefix + common, address_suffix,
                    [a[len(common):] for a in addresses])

            # Handle the case where we have a common prefix of something that
            # isn't don't cares. When optimize is set, we just recursively call
            # ourselves without an if statement - after all, none of the bits
            # in the prefix discriminate between address options. If we're not
            # optimizing, we wrap the result of the recursive call in an if
            # statement with a vector match condition.
            fixed_count = count_up_to(common, lambda bit: bit == '-')
            assert fixed_count
            common = common[:fixed_count]
            recurse = gen_template(
                high - len(common), low, address_prefix + common, address_suffix,
                [a[len(common):] for a in addresses])
            if optimize:
                return recurse
            result = []
            result.append(
                'if $address$(%d downto %d) = "%s" then'
                % (high, high - len(common) + 1, common))
            result.extend(('  ' + s for s in recurse))
            result.append('end if;')
            return result

        # Do the same we did above, but for suffixes.
        common = common_suffix(addresses)
        if common:

            # Handle the case where we have a common suffix of all don't-cares.
            # We can just call ourselves recursively in this case; no matching
            # needs to be performed.
            dont_care_count = count_up_to(reversed(common), lambda bit: bit != '-')
            if dont_care_count:
                common = common[-dont_care_count:]
                return gen_template(
                    high, low + len(common), address_prefix, common + address_suffix,
                    [a[:-len(common)] for a in addresses])

            # Handle the case where we have a common suffix of something that
            # isn't don't cares. When optimize is set, we just recursively call
            # ourselves without an if statement - after all, none of the bits
            # in the suffix discriminate between address options. If we're not
            # optimizing, we wrap the result of the recursive call in an if
            # statement with a vector match condition.
            fixed_count = count_up_to(reversed(common), lambda bit: bit == '-')
            assert fixed_count
            common = common[-fixed_count:]
            recurse = gen_template(
                high, low + len(common), address_prefix, common + address_suffix,
                [a[:-len(common)] for a in addresses])
            if optimize:
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
        common = common_prefix((s.replace('1', '0') for s in addresses))
        if common:
            fixed_count = count_up_to(common, lambda bit: bit == '-')
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
                    recurse_zero = gen_template(
                        high - 1, low, address_prefix + '0', address_suffix,
                        [a[1:] for a in addresses if a.startswith('0')])
                    recurse_one = gen_template(
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
                    if optimize and index == len(options) - 1:
                        result.append('  when others => -- "%s"' % option)
                    else:
                        result.append('  when "%s" =>' % option)
                    result.extend(('    ' + s for s in gen_template(
                        high - len(common), low, address_prefix + option, address_suffix,
                        [a[len(common):] for a in addresses if a.startswith(option)])))
                if not optimize:
                    result.append('  when others =>')
                    result.append('    null;')
                result.append('end case;')
                return result

        # We have a duplicate address.
        raise ValueError(
            'addresses overlap at bit {0}: found both {1}-{2}{3} and '
            '{1}0{2}{3} and/or {1}1{2}{3}'.format(
                high, address_prefix, '#' * (high - low), address_suffix))

    # Fix the $ position of the block references and join the lines together to
    # finish the template.
    return '\n'.join((
        re.sub(r'^ ( +)\$', r'$\1', line)
        for line in gen_template(num_bits - 1, 0, '', '', addresses)))
