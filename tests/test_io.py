"""I/O instruction tests: IN, OUT (verified via I/O port registers and trace)."""

from .defs import TestCase
from .flags import FCW_SYS

# I/O Port Register Map:
# Standard I/O (ST=0010): regs 0-5 at Z8000 addr 0x0100-0x010A
# Special I/O  (ST=0100): regs 6-11 at Z8000 addr 0x0100-0x010A
#
# Reg 0 (0x0100): Loopback byte  (standard)
# Reg 1 (0x0102): Loopback word  (standard)
# Reg 2 (0x0104): Output byte    (standard)
# Reg 3 (0x0106): Output word    (standard)
# Reg 4 (0x0108): Input byte     (standard)
# Reg 5 (0x010A): Input word     (standard)
# Reg 6 (0x0100): Loopback byte  (special)
# Reg 7 (0x0102): Loopback word  (special)
# Reg 8 (0x0104): Output byte    (special)
# Reg 9 (0x0106): Output word    (special)
# Reg 10(0x0108): Input byte     (special)
# Reg 11(0x010A): Input word     (special)

# IR (indirect register) mode - single word:
# IN  Rd, @Rs:    00111101_Rsnz_Rddd
# INB  Rbd, @Rs:  00111100_Rsnz_Rbdd
# OUT @Rd, Rs:    00111111_Rdnz_Rsss
# OUTB @Rd, Rbs:  00111110_Rdnz_Rbss
#
# DA (direct address) mode - two words (opcode + port):
# IN  Rd, port:   00111011_Rddd_0100 + port
# INB  Rbd, port: 00111010_Rbdd_0100 + port
# OUT port, Rs:   00111011_Rsss_0110 + port
# OUTB port, Rbs: 00111010_Rbss_0110 + port

TESTS = [
    # =========================================================================
    # OUT port, Rs - output word to I/O port (register-verified)
    # =========================================================================
    TestCase(
        name="out_port_word",
        mnemonic="OUT",
        description="OUT 0x0106, R0: write R0 to output word reg",
        tags=["io", "word", "DA_mode"],
        # OUT port, Rs: 00111011_Rsss_0110 + port; R0=0000
        code=[0x3B06, 0x0106],
        regs={0: 0xABCD},
        expected_regs={0: 0xABCD},
        expected_io={3: 0xABCD},  # Reg 3 = standard output word
    ),

    TestCase(
        name="out_port_loopback",
        mnemonic="OUT",
        description="OUT 0x0102, R1: write R1 to loopback word reg",
        tags=["io", "word", "DA_mode"],
        # OUT port, Rs: 00111011_Rsss_0110 + port; R1=0001
        code=[0x3B16, 0x0102],
        regs={1: 0x1234},
        expected_regs={1: 0x1234},
        expected_io={1: 0x1234},  # Reg 1 = standard loopback word
    ),

    # =========================================================================
    # IN Rd, port - input word from I/O port (register-verified)
    # =========================================================================
    TestCase(
        name="in_port_word",
        mnemonic="IN",
        description="IN R0, 0x010A: read from input word reg",
        tags=["io", "word", "DA_mode"],
        # IN Rd, port: 00111011_Rddd_0100 + port; R0=0000
        code=[0x3B04, 0x010A],
        regs={0: 0x0000},
        io_preloads={5: 0xBEEF},  # Reg 5 = standard input word
        expected_regs={0: 0xBEEF},
    ),

    TestCase(
        name="in_port_loopback",
        mnemonic="IN",
        description="IN R2, 0x0102: read from loopback word reg",
        tags=["io", "word", "DA_mode"],
        # IN Rd, port: 00111011_Rddd_0100 + port; R2=0010
        code=[0x3B24, 0x0102],
        regs={2: 0x0000},
        io_preloads={1: 0xCAFE},  # Reg 1 = standard loopback word
        expected_regs={2: 0xCAFE},
    ),

    # =========================================================================
    # OUT/IN loopback roundtrip
    # =========================================================================
    TestCase(
        name="out_in_loopback",
        mnemonic="OUT",
        description="OUT 0x0102, R0; IN R1, 0x0102: loopback roundtrip",
        tags=["io", "word", "DA_mode"],
        # OUT port, Rs: 00111011_0000_0110 + port (R0)
        # IN  Rd, port: 00111011_0001_0100 + port (R1)
        code=[0x3B06, 0x0102, 0x3B14, 0x0102],
        regs={0: 0x5A5A, 1: 0x0000},
        expected_regs={0: 0x5A5A, 1: 0x5A5A},
        expected_io={1: 0x5A5A},  # Loopback reg should have final value
    ),

    # =========================================================================
    # OUTB port, Rbs - output byte
    # =========================================================================
    TestCase(
        name="outb_port_byte",
        mnemonic="OUTB",
        description="OUTB 0x0104, RH0: write byte to output byte reg",
        tags=["io", "byte", "DA_mode"],
        # OUTB port, Rbs: 00111010_Rbss_0110 + port; RH0=0000
        code=[0x3A06, 0x0104],
        regs={0: 0xAB00},  # RH0 = 0xAB
        expected_regs={0: 0xAB00},
        expected_io={2: 0xAB00},  # Reg 2 = standard output byte, high byte written
    ),

    # =========================================================================
    # INB Rbd, port - input byte
    # =========================================================================
    TestCase(
        name="inb_port_byte",
        mnemonic="INB",
        description="INB RH0, 0x0108: read byte from input byte reg",
        tags=["io", "byte", "DA_mode"],
        # INB Rbd, port: 00111010_Rbdd_0100 + port; RH0=0000
        code=[0x3A04, 0x0108],
        regs={0: 0x0000},
        io_preloads={4: 0x42FF},  # Reg 4 = standard input byte, high byte = 0x42
        expected_regs={0: 0x4200},  # RH0 = high byte of port read
    ),

    # =========================================================================
    # OUT @Rd, Rs - indirect output
    # =========================================================================
    TestCase(
        name="out_indirect",
        mnemonic="OUT",
        description="OUT @R1, R0: write R0 to port addressed by R1",
        tags=["io", "word", "IR_mode"],
        # OUT @R1, R0: 0x3F10, R1=port addr
        code=[0x3F10],
        regs={0: 0xDEAD, 1: 0x0106},
        expected_regs={0: 0xDEAD, 1: 0x0106},
        expected_io={3: 0xDEAD},  # Reg 3 = standard output word
    ),

    # =========================================================================
    # IN Rd, @Rs - indirect input
    # =========================================================================
    TestCase(
        name="in_indirect",
        mnemonic="IN",
        description="IN R0, @R1: read from port addressed by R1",
        tags=["io", "word", "IR_mode"],
        # IN R0, @R1: 0x3D10
        code=[0x3D10],
        regs={0: 0x0000, 1: 0x010A},
        io_preloads={5: 0xFACE},  # Reg 5 = standard input word
        expected_regs={0: 0xFACE, 1: 0x010A},
    ),
]
