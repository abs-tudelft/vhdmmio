import os, re
from vhdmmio.template import TemplateEngine

def _gen_switch_template(num_bits, addresses, optimize=True):
    """Generates a VHDL case/switch template for a vector of the given number
    of bits and the given addresses. The addresses must be any mix of integer
    addresses and two-tuples of base address and bitmask, where a high bit in
    the bitmask indicates that the bit is to be used. If `optimize` is set,
    this function assumes that the action for any address not in the address
    list is don't care. The resulting template uses `$address$` for the
    to-be-matched address, and block markers of the form`$ADDR_0x%x` for the
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

    def gen_template(hi, lo, address_prefix, address_suffix, addresses):
        if not addresses:
            return []
        if hi < lo:
            address = address_prefix + address_suffix
            return [
                '-- $address$ = %s' % address,
                '$ADDR_0x%X' % int(address.replace('-', '0'), 2)]

        common = common_prefix(addresses)
        if common:
            dont_care_count = 0
            for bit in common:
                if bit != '-':
                    break
                dont_care_count += 1
            if dont_care_count:
                common = common[:dont_care_count]
                return gen_template(
                    hi - len(common), lo, address_prefix + common, address_suffix,
                    [a[len(common):] for a in addresses])

            fixed_count = 0
            for bit in common:
                if bit == '-':
                    break
                fixed_count += 1
            if fixed_count:
                common = common[:fixed_count]
                recurse = gen_template(
                    hi - len(common), lo, address_prefix + common, address_suffix,
                    [a[len(common):] for a in addresses])
                if optimize:
                    return recurse
                result = []
                result.append(
                    'if $address$(%d downto %d) = "%s" then'
                    % (hi, hi - len(common) + 1, common))
                result.extend(('  ' + s for s in recurse))
                result.append('end if;')
                return result

            assert False

        common = common_suffix(addresses)
        if common:
            dont_care_count = 0
            for bit in common:
                if bit != '-':
                    break
                dont_care_count += 1
            if dont_care_count:
                common = common[:dont_care_count]
                return gen_template(
                    hi, lo + len(common), address_prefix, common + address_suffix,
                    [a[:len(common)] for a in addresses])

            fixed_count = 0
            for bit in common:
                if bit == '-':
                    break
                fixed_count += 1
            if fixed_count:
                common = common[:fixed_count]
                recurse = gen_template(
                    hi, lo + len(common), address_prefix, common + address_suffix,
                    [a[:len(common)] for a in addresses])
                if optimize:
                    return recurse
                result = []
                result.append(
                    'if $address$(%d downto %d) = "%s" then'
                    % (lo + len(common) - 1, lo, common))
                result.extend(('  ' + s for s in recurse))
                result.append('end if;')
                return result

            assert False

        common = common_prefix((s.replace('1', '0') for s in addresses))
        if common:
            fixed_count = 0
            for bit in common:
                if bit == '-':
                    break
                fixed_count += 1
            if fixed_count:
                common = common[:fixed_count]
                options = set((s[:len(common)] for s in addresses))

                if len(options) == 1:
                    recurse = gen_template(
                        hi - len(common), lo, address_prefix + common, address_suffix,
                        [a[len(common):] for a in addresses])
                    if optimize:
                        return recurse
                    result = []
                    result.append(
                        'if $address$(%d downto %d) = "%s" then'
                        % (hi, hi - len(common) + 1, common))
                    result.extend(('  ' + s for s in recurse))
                    result.append('end if;')
                    return result

                if len(common) == 1:
                    result = []
                    result.append('if $address$(%d) = \'0\' then' % hi)
                    result.extend(('  ' + s for s in gen_template(
                        hi - 1, lo, address_prefix + '0', address_suffix,
                        [a[1:] for a in addresses if a.startswith('0')])))
                    result.append('else')
                    result.extend(('  ' + s for s in gen_template(
                        hi - 1, lo, address_prefix + '1', address_suffix,
                        [a[1:] for a in addresses if a.startswith('1')])))
                    result.append('end if;')
                    return result

                result = []
                result.append(
                    'case $address$(%d downto %d) is'
                    % (hi, hi - len(common) + 1))
                options = sorted(options)
                for index, option in enumerate(options):
                    if optimize and index == len(options) - 1:
                        result.append('  when others => -- "%s"' % option)
                    else:
                        result.append('  when "%s" =>' % option)
                    result.extend(('    ' + s for s in gen_template(
                        hi - len(common), lo, address_prefix + option, address_suffix,
                        [a[len(common):] for a in addresses if a.startswith(option)])))
                if not optimize:
                    result.append('  when others =>')
                    result.append('    null;')
                result.append('end case;')
                return result

        print(hi, lo, address_prefix, address_suffix, addresses)
        assert False

    return '\n'.join((
        re.sub(r'^ ( +)\$', r'$\1', line)
        for line in gen_template(num_bits - 1, 0, '', '', addresses)))

class VhdlGenerator:

    def __init__(self, regfiles, output_dir):
        for regfile in regfiles:
            tple = TemplateEngine()
            tple['r'] = regfile

            # Generate interrupt logic.
            for interrupt in regfile.interrupts:
                comment = interrupt.meta[None].markdown_brief
                assert '\n' not in comment
                if interrupt.can_clear:
                    comment = '@ Edge-sensitive: ' + comment
                else:
                    comment = '@ Level-sensitive: ' + comment
                if interrupt.width is None:
                    tple.append_block('PORTS', comment,
                                      'irq_%s : in std_logic := \'0\';' % interrupt.meta.name)
                    irq_range = '%d' % interrupt.index
                else:
                    tple.append_block('PORTS', comment,
                                      'irq_%s : in std_logic_vector(%d downto 0) '
                                      ':= (others => \'0\');' % (interrupt.meta.name,
                                                                 interrupt.width - 1))
                    irq_range = '%d downto %d' % (interrupt.high, interrupt.low)
                if interrupt.can_clear:
                    tple.append_block('IRQ_LOGIC', comment,
                                      'i_flag({1}) := i_flag({1}) or (irq_{0} and i_enab({1});'
                                      .format(interrupt.meta.name, irq_range))
                else:
                    tple.append_block('IRQ_LOGIC', comment,
                                      'i_flag({1}) := irq_{0} and i_enab({1});'
                                      .format(interrupt.meta.name, irq_range))

            tple.apply_file_to_file(
                os.path.dirname(__file__) + os.sep + 'entity.template.vhd',
                output_dir + os.sep + regfile.meta.name + '.vhd',
                comment='-- ')
            tple.apply_file_to_file(
                os.path.dirname(__file__) + os.sep + 'package.template.vhd',
                output_dir + os.sep + regfile.meta.name + '_pkg.vhd',
                comment='-- ')

        with open(os.path.dirname(__file__) + os.sep + 'vhdmmio_pkg.vhd', 'r') as in_fd:
            vhdmmio_pkg = in_fd.read()
        with open(output_dir + os.sep + 'vhdmmio_pkg.vhd', 'w') as out_fd:
            out_fd.write(vhdmmio_pkg)
