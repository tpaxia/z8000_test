"""Shared verification logic for test results."""

from .flags import get_flag, format_flags


def verify_result(tc, exec_result, actual_regs, actual_fcw, actual_memory, actual_io):
    """Verify test results against expected values.

    Returns list of failure strings (empty = pass).
    """
    failures = []

    # Execution result
    if exec_result != tc.expected_result:
        failures.append(
            f"Execution: expected {tc.expected_result}, got {exec_result}"
        )

    # Registers
    for reg, expected in tc.expected_regs.items():
        actual = actual_regs.get(reg)
        if actual != expected:
            failures.append(
                f"R{reg}: expected 0x{expected:04X}, got "
                f"0x{actual:04X}" if actual is not None else "None"
            )

    # Flags
    if actual_fcw is not None:
        for flag_name in tc.expected_fcw_set:
            if get_flag(actual_fcw, flag_name) != 1:
                failures.append(
                    f"Flag {flag_name}: expected SET, got CLEAR "
                    f"(FCW=0x{actual_fcw:04X} {format_flags(actual_fcw)})"
                )
        for flag_name in tc.expected_fcw_clear:
            if get_flag(actual_fcw, flag_name) != 0:
                failures.append(
                    f"Flag {flag_name}: expected CLEAR, got SET "
                    f"(FCW=0x{actual_fcw:04X} {format_flags(actual_fcw)})"
                )

    # Memory
    for addr, expected in tc.expected_memory.items():
        actual = actual_memory.get(addr)
        if actual != expected:
            failures.append(
                f"Mem[0x{addr:04X}]: expected 0x{expected:04X}, got "
                f"0x{actual:04X}" if actual is not None else "None"
            )

    # I/O ports
    for idx, expected in tc.expected_io.items():
        actual = actual_io.get(idx)
        if actual != expected:
            failures.append(
                f"IO[0x{idx:02X}]: expected 0x{expected:04X}, got "
                f"0x{actual:04X}" if actual is not None else "None"
            )

    return failures
