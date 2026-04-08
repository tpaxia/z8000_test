"""FCW flag bit definitions and reference flag computation."""

# Z8000 FCW flag bit positions (from rtl/z8000_cpu.v)
FLAG_BITS = {
    'C':  7,   # Carry
    'Z':  6,   # Zero
    'S':  5,   # Sign (negative)
    'V':  4,   # Overflow (signed)
    'DA': 3,   # Decimal adjust
    'H':  2,   # Half carry (BCD)
}

# Control bits
CTL_BITS = {
    'VIE':  12,  # Vectored interrupt enable
    'NVIE': 11,  # Non-vectored interrupt enable
    'SYS':  14,  # System/Normal mode
    'SEG':  15,  # Segmented mode (Z8001 only)
}

# Common FCW values
FCW_SYS = 0x4000       # System mode, all flags clear
FCW_SYS_CARRY = 0x4080 # System mode + carry flag set


ALL_BITS = {**FLAG_BITS, **CTL_BITS}


def flag_mask(flag_name):
    """Return bitmask for a flag."""
    return 1 << FLAG_BITS[flag_name]


def fcw_with_flags(base=FCW_SYS, **flags):
    """Build FCW value with specified flags set.

    Example: fcw_with_flags(C=1, Z=0) -> 0x4080
    """
    val = base
    for name, set_flag in flags.items():
        bit = FLAG_BITS[name]
        if set_flag:
            val |= (1 << bit)
        else:
            val &= ~(1 << bit)
    return val


def get_flag(fcw, flag_name):
    """Extract a flag or control bit value from FCW."""
    return (fcw >> ALL_BITS[flag_name]) & 1


def format_flags(fcw):
    """Format FCW flags as readable string like 'C=1 Z=0 S=0 V=0 DA=0 H=0'."""
    parts = []
    for name in ('C', 'Z', 'S', 'V', 'DA', 'H'):
        parts.append(f"{name}={get_flag(fcw, name)}")
    return ' '.join(parts)


def compute_add_flags(a, b, size=16, carry_in=0):
    """Compute flags for ADD/ADC result."""
    mask = (1 << size) - 1
    sign_bit = size - 1
    result = a + b + carry_in
    carry = 1 if result > mask else 0
    result &= mask
    zero = 1 if result == 0 else 0
    sign = (result >> sign_bit) & 1
    # Overflow: both operands same sign, result different sign
    a_sign = (a >> sign_bit) & 1
    b_sign = (b >> sign_bit) & 1
    r_sign = sign
    overflow = 1 if (a_sign == b_sign and r_sign != a_sign) else 0
    # Half carry: carry out of bit 3
    half = 1 if ((a & 0xF) + (b & 0xF) + carry_in) > 0xF else 0
    return result, {'C': carry, 'Z': zero, 'S': sign, 'V': overflow, 'H': half}


def compute_sub_flags(a, b, size=16, carry_in=0):
    """Compute flags for SUB/SBC result."""
    mask = (1 << size) - 1
    sign_bit = size - 1
    result = a - b - carry_in
    carry = 1 if result < 0 else 0
    result &= mask
    zero = 1 if result == 0 else 0
    sign = (result >> sign_bit) & 1
    # Overflow: operands different sign, result sign matches subtrahend
    a_sign = (a >> sign_bit) & 1
    b_sign = (b >> sign_bit) & 1
    r_sign = sign
    overflow = 1 if (a_sign != b_sign and r_sign == b_sign) else 0
    # Half carry (borrow from bit 4)
    half = 1 if ((a & 0xF) - (b & 0xF) - carry_in) < 0 else 0
    return result, {'C': carry, 'Z': zero, 'S': sign, 'V': overflow, 'H': half}


def compute_logic_flags(result, size=16):
    """Compute flags for AND/OR/XOR result (C=0, V=0)."""
    mask = (1 << size) - 1
    sign_bit = size - 1
    result &= mask
    zero = 1 if result == 0 else 0
    sign = (result >> sign_bit) & 1
    return {'C': 0, 'Z': zero, 'S': sign, 'V': 0}
