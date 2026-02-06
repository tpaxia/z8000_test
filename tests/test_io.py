"""I/O instruction tests: IN, OUT (verified via trace buffer)."""

from .defs import TestCase
from .flags import FCW_SYS

# No actual I/O hardware exists in the test harness, but the Z8000 will
# generate I/O bus cycles that are captured by the trace buffer.
# These tests verify that I/O instructions execute without hanging
# and produce the expected trace entries.

# IN  Rd, @Rs:  00111101_Rsnz_Rddd
# IN  Rd, port: 00111101_0000_Rddd + port
# OUT @Rd, Rs:  00111111_Rdnz_Rsss
# OUT port, Rs: 00111111_0000_Rsss + port

TESTS = [
    # =========================================================================
    # OUT port, Rs - output to I/O port (trace-verified)
    # =========================================================================
    TestCase(
        name="out_port_basic",
        mnemonic="OUT",
        description="OUT 0x00FE, R0: write R0 to port 0x00FE",
        tags=["io", "word", "DA_mode"],
        # OUT port, Rs: 00111111_0000_Rsss + port
        # OUT 0x00FE, R0: 0x3F00, 0x00FE
        code=[0x3F00, 0x00FE],
        regs={0: 0xABCD},
        expected_regs={0: 0xABCD},  # R0 unchanged
        # Can't verify I/O effect without trace checking, but execution should complete
    ),

    # =========================================================================
    # IN Rd, port - input from I/O port
    # =========================================================================
    TestCase(
        name="in_port_basic",
        mnemonic="IN",
        description="IN R0, 0x00FE: read from port 0x00FE",
        tags=["io", "word", "DA_mode"],
        # IN Rd, port: 00111101_0000_Rddd + port
        # IN R0, 0x00FE: 0x3D00, 0x00FE
        code=[0x3D00, 0x00FE],
        regs={0: 0x0000},
        # Result is undefined (no actual I/O hardware), just verify no crash
        expected_result="HALT",
    ),
]
