"""I/O instruction tests: IN, OUT (verified via I/O port registers and trace)."""

from .defs import TestCase
from .flags import FCW_SYS

FCW_SEG_SYS = FCW_SYS | 0x8000

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
        instruction="OUT 0x0106, R0",
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
        instruction="OUT 0x0102, R1",
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
        instruction="IN R0, 0x010A",
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
        instruction="IN R2, 0x0102",
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
        instruction="OUT 0x0102, R0; IN R1, 0x0102",
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
        instruction="OUTB 0x0104, RH0",
        description="OUTB 0x0104, RH0: write byte to output byte reg",
        tags=["io", "byte", "DA_mode"],
        # OUTB port, Rbs: 00111010_Rbss_0110 + port; RH0=0000
        code=[0x3A06, 0x0104],
        regs={0: 0xAB00},  # RH0 = 0xAB
        io_preloads={2: 0x00BC},
        expected_regs={0: 0xAB00},
        expected_io={2: 0xABBC},  # High byte written, low byte preserved
    ),

    # =========================================================================
    # INB Rbd, port - input byte
    # =========================================================================
    TestCase(
        name="inb_port_byte",
        mnemonic="INB",
        instruction="INB RH0, 0x0108",
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
        instruction="OUT @R1, R0",
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
        instruction="IN R0, @R1",
        description="IN R0, @R1: read from port addressed by R1",
        tags=["io", "word", "IR_mode"],
        # IN R0, @R1: 0x3D10
        code=[0x3D10],
        regs={0: 0x0000, 1: 0x010A},
        io_preloads={5: 0xFACE},  # Reg 5 = standard input word
        expected_regs={0: 0xFACE, 1: 0x010A},
    ),

    TestCase(
        name="io_normal_special_word_select",
        mnemonic="IN",
        instruction="IN R0, #0x0106; SIN R1, #0x0106",
        description="Normal and special word input use separate I/O banks",
        tags=["io", "word", "special_io"],
        code=[0x3B04, 0x0106, 0x3B15, 0x0106],
        regs={0: 0x0000, 1: 0x0000},
        io_preloads={3: 0x1111, 9: 0x9999},
        expected_regs={0: 0x1111, 1: 0x9999},
    ),

    TestCase(
        name="io_normal_special_word_output",
        mnemonic="OUT",
        instruction="OUT #0x0106, R0; SOUT #0x0106, R1",
        description="Normal and special word output use separate I/O banks",
        tags=["io", "word", "special_io"],
        code=[0x3B06, 0x0106, 0x3B17, 0x0106],
        regs={0: 0x2222, 1: 0xAAAA},
        expected_io={3: 0x2222, 9: 0xAAAA},
    ),

    TestCase(
        name="io_byte_lanes_input_normal_special",
        mnemonic="INB",
        instruction="INB RH0, #0x0104; INB RL0, #0x0105; SINB RH1, #0x0104; SINB RL1, #0x0105",
        description="Normal/special byte input reads high and low I/O byte lanes",
        tags=["io", "byte", "special_io"],
        code=[0x3A04, 0x0104, 0x3A84, 0x0105, 0x3A15, 0x0104, 0x3A95, 0x0105],
        regs={0: 0x0000, 1: 0x0000},
        io_preloads={2: 0xA1B2, 8: 0xC3D4},
        expected_regs={0: 0xA1B2, 1: 0xC3D4},
    ),

    TestCase(
        name="io_byte_lanes_output_normal_special",
        mnemonic="OUTB",
        instruction="OUTB #0x0104, RH0; OUTB #0x0105, RL0; SOUTB #0x0104, RH1; SOUTB #0x0105, RL1",
        description="Normal/special byte output writes high and low I/O byte lanes",
        tags=["io", "byte", "special_io"],
        code=[0x3A06, 0x0104, 0x3A86, 0x0105, 0x3A17, 0x0104, 0x3A97, 0x0105],
        regs={0: 0xA1B2, 1: 0xC3D4},
        io_preloads={2: 0x1122, 8: 0x3344},
        expected_io={2: 0xA1B2, 8: 0xC3D4},
    ),

    TestCase(
        name="io_fifo_in_word_standard",
        mnemonic="IN",
        instruction="IN R0, #0x0106; IN R2, #0x0106; IN R3, #0x0106",
        description="Standard input consumes multiple FIFO values from one port",
        tags=["io", "word", "fifo"],
        code=[0x3B04, 0x0106, 0x3B24, 0x0106, 0x3B34, 0x0106],
        regs={0: 0x0000, 2: 0x0000, 3: 0x0000},
        io_sequences={3: [0x1111, 0x2222, 0x3333]},
        expected_regs={0: 0x1111, 2: 0x2222, 3: 0x3333},
    ),

    TestCase(
        name="io_fifo_sin_word_special",
        mnemonic="SIN",
        instruction="SIN R0, #0x0106; SIN R2, #0x0106; SIN R3, #0x0106",
        description="Special input consumes multiple FIFO values from one port",
        tags=["io", "word", "fifo", "special_io"],
        code=[0x3B05, 0x0106, 0x3B25, 0x0106, 0x3B35, 0x0106],
        regs={0: 0x0000, 2: 0x0000, 3: 0x0000},
        io_sequences={9: [0xAAAA, 0xBBBB, 0xCCCC]},
        expected_regs={0: 0xAAAA, 2: 0xBBBB, 3: 0xCCCC},
    ),

    TestCase(
        name="seg_io_normal_special_word_select",
        mnemonic="IN",
        target="z8001-seg",
        instruction="IN R0, #0x0106; SIN R1, #0x0106",
        description="Segmented mode normal and special word input use separate I/O banks",
        tags=["io", "word", "special_io"],
        code=[0x3B04, 0x0106, 0x3B15, 0x0106],
        regs={0: 0x0000, 1: 0x0000},
        fcw=FCW_SEG_SYS,
        io_preloads={3: 0x1111, 9: 0x9999},
        expected_regs={0: 0x1111, 1: 0x9999},
    ),

    TestCase(
        name="seg_out_port_word",
        mnemonic="OUT",
        target="z8001-seg",
        instruction="OUT 0x0106, R0",
        description="Segmented OUT 0x0106, R0: write R0 to output word reg",
        tags=["io", "word", "DA_mode"],
        code=[0x3B06, 0x0106],
        regs={0: 0xABCD},
        fcw=FCW_SEG_SYS,
        expected_regs={0: 0xABCD},
        expected_io={3: 0xABCD},
    ),

    TestCase(
        name="seg_out_port_loopback",
        mnemonic="OUT",
        target="z8001-seg",
        instruction="OUT 0x0102, R1",
        description="Segmented OUT 0x0102, R1: write R1 to loopback word reg",
        tags=["io", "word", "DA_mode"],
        code=[0x3B16, 0x0102],
        regs={1: 0x1234},
        fcw=FCW_SEG_SYS,
        expected_regs={1: 0x1234},
        expected_io={1: 0x1234},
    ),

    TestCase(
        name="seg_in_port_word",
        mnemonic="IN",
        target="z8001-seg",
        instruction="IN R0, 0x010A",
        description="Segmented IN R0, 0x010A: read from input word reg",
        tags=["io", "word", "DA_mode"],
        code=[0x3B04, 0x010A],
        regs={0: 0x0000},
        fcw=FCW_SEG_SYS,
        io_preloads={5: 0xBEEF},
        expected_regs={0: 0xBEEF},
    ),

    TestCase(
        name="seg_in_port_loopback",
        mnemonic="IN",
        target="z8001-seg",
        instruction="IN R2, 0x0102",
        description="Segmented IN R2, 0x0102: read from loopback word reg",
        tags=["io", "word", "DA_mode"],
        code=[0x3B24, 0x0102],
        regs={2: 0x0000},
        fcw=FCW_SEG_SYS,
        io_preloads={1: 0xCAFE},
        expected_regs={2: 0xCAFE},
    ),

    TestCase(
        name="seg_out_in_loopback",
        mnemonic="OUT",
        target="z8001-seg",
        instruction="OUT 0x0102, R0; IN R1, 0x0102",
        description="Segmented OUT 0x0102, R0; IN R1, 0x0102: loopback roundtrip",
        tags=["io", "word", "DA_mode"],
        code=[0x3B06, 0x0102, 0x3B14, 0x0102],
        regs={0: 0x5A5A, 1: 0x0000},
        fcw=FCW_SEG_SYS,
        expected_regs={0: 0x5A5A, 1: 0x5A5A},
        expected_io={1: 0x5A5A},
    ),

    TestCase(
        name="seg_outb_port_byte",
        mnemonic="OUTB",
        target="z8001-seg",
        instruction="OUTB 0x0104, RH0",
        description="Segmented OUTB 0x0104, RH0: high byte write preserves low byte",
        tags=["io", "byte", "DA_mode"],
        code=[0x3A06, 0x0104],
        regs={0: 0xAB00},
        fcw=FCW_SEG_SYS,
        io_preloads={2: 0x00BC},
        expected_regs={0: 0xAB00},
        expected_io={2: 0xABBC},
    ),

    TestCase(
        name="seg_inb_port_byte",
        mnemonic="INB",
        target="z8001-seg",
        instruction="INB RH0, 0x0108",
        description="Segmented INB RH0, 0x0108: read byte from input byte reg",
        tags=["io", "byte", "DA_mode"],
        code=[0x3A04, 0x0108],
        regs={0: 0x0000},
        fcw=FCW_SEG_SYS,
        io_preloads={4: 0x42FF},
        expected_regs={0: 0x4200},
    ),

    TestCase(
        name="seg_out_indirect",
        mnemonic="OUT",
        target="z8001-seg",
        instruction="OUT @R1, R0",
        description="Segmented OUT @R1, R0: write R0 to port addressed by R1",
        tags=["io", "word", "IR_mode"],
        code=[0x3F10],
        regs={0: 0xDEAD, 1: 0x0106},
        fcw=FCW_SEG_SYS,
        expected_regs={0: 0xDEAD, 1: 0x0106},
        expected_io={3: 0xDEAD},
    ),

    TestCase(
        name="seg_in_indirect",
        mnemonic="IN",
        target="z8001-seg",
        instruction="IN R0, @R1",
        description="Segmented IN R0, @R1: read from port addressed by R1",
        tags=["io", "word", "IR_mode"],
        code=[0x3D10],
        regs={0: 0x0000, 1: 0x010A},
        fcw=FCW_SEG_SYS,
        io_preloads={5: 0xFACE},
        expected_regs={0: 0xFACE, 1: 0x010A},
    ),

    TestCase(
        name="seg_io_normal_special_word_output",
        mnemonic="OUT",
        target="z8001-seg",
        instruction="OUT #0x0106, R0; SOUT #0x0106, R1",
        description="Segmented mode normal and special word output use separate I/O banks",
        tags=["io", "word", "special_io"],
        code=[0x3B06, 0x0106, 0x3B17, 0x0106],
        regs={0: 0x2222, 1: 0xAAAA},
        fcw=FCW_SEG_SYS,
        expected_io={3: 0x2222, 9: 0xAAAA},
    ),

    TestCase(
        name="seg_io_byte_lanes_input_normal_special",
        mnemonic="INB",
        target="z8001-seg",
        instruction="INB RH0, #0x0104; INB RL0, #0x0105; SINB RH1, #0x0104; SINB RL1, #0x0105",
        description="Segmented mode normal/special byte input reads high and low I/O byte lanes",
        tags=["io", "byte", "special_io"],
        code=[0x3A04, 0x0104, 0x3A84, 0x0105, 0x3A15, 0x0104, 0x3A95, 0x0105],
        regs={0: 0x0000, 1: 0x0000},
        fcw=FCW_SEG_SYS,
        io_preloads={2: 0xA1B2, 8: 0xC3D4},
        expected_regs={0: 0xA1B2, 1: 0xC3D4},
    ),

    TestCase(
        name="seg_io_byte_lanes_output_normal_special",
        mnemonic="OUTB",
        target="z8001-seg",
        instruction="OUTB #0x0104, RH0; OUTB #0x0105, RL0; SOUTB #0x0104, RH1; SOUTB #0x0105, RL1",
        description="Segmented mode normal/special byte output writes both I/O byte lanes",
        tags=["io", "byte", "special_io"],
        code=[0x3A06, 0x0104, 0x3A86, 0x0105, 0x3A17, 0x0104, 0x3A97, 0x0105],
        regs={0: 0xA1B2, 1: 0xC3D4},
        fcw=FCW_SEG_SYS,
        io_preloads={2: 0x1122, 8: 0x3344},
        expected_io={2: 0xA1B2, 8: 0xC3D4},
    ),

    TestCase(
        name="seg_io_fifo_in_word_standard",
        mnemonic="IN",
        target="z8001-seg",
        instruction="IN R0, #0x0106; IN R2, #0x0106; IN R3, #0x0106",
        description="Segmented mode standard input consumes FIFO values from one port",
        tags=["io", "word", "fifo"],
        code=[0x3B04, 0x0106, 0x3B24, 0x0106, 0x3B34, 0x0106],
        regs={0: 0x0000, 2: 0x0000, 3: 0x0000},
        fcw=FCW_SEG_SYS,
        io_sequences={3: [0x1111, 0x2222, 0x3333]},
        expected_regs={0: 0x1111, 2: 0x2222, 3: 0x3333},
    ),

    TestCase(
        name="seg_io_fifo_sin_word_special",
        mnemonic="SIN",
        target="z8001-seg",
        instruction="SIN R0, #0x0106; SIN R2, #0x0106; SIN R3, #0x0106",
        description="Segmented mode special input consumes FIFO values from one port",
        tags=["io", "word", "fifo", "special_io"],
        code=[0x3B05, 0x0106, 0x3B25, 0x0106, 0x3B35, 0x0106],
        regs={0: 0x0000, 2: 0x0000, 3: 0x0000},
        fcw=FCW_SEG_SYS,
        io_sequences={9: [0xAAAA, 0xBBBB, 0xCCCC]},
        expected_regs={0: 0xAAAA, 2: 0xBBBB, 3: 0xCCCC},
    ),
]

# =============================================================================
# Word I/O at odd port addresses
# =============================================================================
# Discovery tests: what the CPU does with A0 and the data lanes when a word
# I/O instruction addresses an odd port.  The harness decodes the register
# from addr[3:1], so 0x0107 reaches reg 3 like 0x0106 and 0x010B reaches
# reg 5 like 0x010A.  Word writes store all 16 driven bits and word reads
# return the whole register, so the readback shows any lane swap.  The bus
# trace (--save-traces) shows whether A0 is driven.  No expected values for
# the odd-port cases: the physical Z8001 capture is the reference.
#
# ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8002)
#   3b06 0106    out  #0x106,r0
#   3b06 0107    out  #0x107,r0
#   3f10         out  @r1,r0
#   3b04 010a    in   r0,#0x10a
#   3b04 010b    in   r0,#0x10b
#   3d10         in   r0,@r1
#   3b17 0107    sout #0x107,r1
#   3b15 010b    sin  r1,#0x10b
#   3b22 0318    outi @r1,@r2,r3
#   3b10 0328    ini  @r2,@r1,r3
#   3a86 0107    outb #0x107,rl0
#   3a06 0106    outb #0x106,rh0
#
# ASSEMBLER-VERIFIED LISTING (z8k-coff-as -z8001, linked at .text=0x200)
#   7608 8000 0800    lda  rr8,0x800
#   3b82 0318         outi @r1,@rr8,r3
#   3b10 0388         ini  @rr8,@r1,r3

TESTS += [
    TestCase(
        name="io_odd_out_word_even",
        mnemonic="OUT",
        instruction="OUT #0x0106, R0",
        description="Odd-port baseline: word OUT to even port 0x0106",
        tags=["io", "word", "odd_port", "DA_mode"],
        code=[0x3B06, 0x0106],
        regs={0: 0xA1B2},
        io_preloads={3: 0x5555},
        observe_io=[3],
    ),

    TestCase(
        name="io_odd_out_word_da",
        mnemonic="OUT",
        instruction="OUT #0x0107, R0",
        description="Word OUT to odd port 0x0107: A0 on the bus and lane order",
        tags=["io", "word", "odd_port", "DA_mode"],
        code=[0x3B06, 0x0107],
        regs={0: 0xA1B2},
        io_preloads={3: 0x5555},
        observe_io=[3],
    ),

    TestCase(
        name="io_odd_out_word_ir",
        mnemonic="OUT",
        instruction="OUT @R1, R0",
        description="Word OUT @R1 with R1=0x0107: indirect odd port",
        tags=["io", "word", "odd_port", "IR_mode"],
        code=[0x3F10],
        regs={0: 0xA1B2, 1: 0x0107},
        io_preloads={3: 0x5555},
        observe_io=[3],
    ),

    TestCase(
        name="io_odd_in_word_even",
        mnemonic="IN",
        instruction="IN R0, #0x010A",
        description="Odd-port baseline: word IN from even port 0x010A",
        tags=["io", "word", "odd_port", "DA_mode"],
        code=[0x3B04, 0x010A],
        regs={0: 0x0000},
        io_preloads={5: 0xC3D4},
    ),

    TestCase(
        name="io_odd_in_word_da",
        mnemonic="IN",
        instruction="IN R0, #0x010B",
        description="Word IN from odd port 0x010B: A0 on the bus and lane order",
        tags=["io", "word", "odd_port", "DA_mode"],
        code=[0x3B04, 0x010B],
        regs={0: 0x0000},
        io_preloads={5: 0xC3D4},
    ),

    TestCase(
        name="io_odd_in_word_ir",
        mnemonic="IN",
        instruction="IN R0, @R1",
        description="Word IN R0, @R1 with R1=0x010B: indirect odd port",
        tags=["io", "word", "odd_port", "IR_mode"],
        code=[0x3D10],
        regs={0: 0x0000, 1: 0x010B},
        io_preloads={5: 0xC3D4},
    ),

    TestCase(
        name="io_odd_sout_sin_word",
        mnemonic="SOUT",
        instruction="SOUT #0x0107, R1; SIN R1, #0x010B",
        description="Special word OUT to 0x0107 and IN from 0x010B",
        tags=["io", "word", "odd_port", "special_io"],
        code=[0x3B17, 0x0107, 0x3B15, 0x010B],
        regs={1: 0xA1B2},
        io_preloads={9: 0x5555, 11: 0xC3D4},
        observe_io=[9, 11],
    ),

    TestCase(
        name="io_odd_outi_word",
        mnemonic="OUTI",
        instruction="OUTI @R1, @R2, R3",
        description="Block word OUTI to odd port 0x0107 from memory 0x0F00",
        tags=["io", "word", "odd_port", "block"],
        code=[0x3B22, 0x0318],
        regs={1: 0x0107, 2: 0x0F00, 3: 0x0001},
        memory={0x0F00: 0xA1B2},
        io_preloads={3: 0x5555},
        observe_io=[3],
    ),

    TestCase(
        name="io_odd_ini_word",
        mnemonic="INI",
        instruction="INI @R2, @R1, R3",
        description="Block word INI from odd port 0x010B to memory 0x0F00",
        tags=["io", "word", "odd_port", "block"],
        code=[0x3B10, 0x0328],
        regs={1: 0x010B, 2: 0x0F00, 3: 0x0001},
        memory={0x0F00: 0x5555},
        io_preloads={5: 0xC3D4},
        observe_memory=[0x0F00],
    ),

    TestCase(
        name="io_odd_outb_lanes",
        mnemonic="OUTB",
        instruction="OUTB #0x0107, RL0; OUTB #0x0106, RH0",
        description="Byte OUT to odd and even ports: trace shows lane duplication",
        tags=["io", "byte", "odd_port"],
        code=[0x3A86, 0x0107, 0x3A06, 0x0106],
        regs={0: 0xA1B2},
        io_preloads={3: 0x5555},
        observe_io=[3],
    ),
]

TESTS += [
    TestCase(
        name="seg_io_odd_out_word_even",
        mnemonic="OUT",
        target="z8001-seg",
        instruction="OUT #0x0106, R0",
        description="Segmented odd-port baseline: word OUT to even port 0x0106",
        tags=["io", "word", "odd_port", "DA_mode"],
        code=[0x3B06, 0x0106],
        regs={0: 0xA1B2},
        fcw=FCW_SEG_SYS,
        io_preloads={3: 0x5555},
        observe_io=[3],
    ),

    TestCase(
        name="seg_io_odd_out_word_da",
        mnemonic="OUT",
        target="z8001-seg",
        instruction="OUT #0x0107, R0",
        description="Segmented word OUT to odd port 0x0107",
        tags=["io", "word", "odd_port", "DA_mode"],
        code=[0x3B06, 0x0107],
        regs={0: 0xA1B2},
        fcw=FCW_SEG_SYS,
        io_preloads={3: 0x5555},
        observe_io=[3],
    ),

    TestCase(
        name="seg_io_odd_out_word_ir",
        mnemonic="OUT",
        target="z8001-seg",
        instruction="OUT @R1, R0",
        description="Segmented word OUT @R1 with R1=0x0107",
        tags=["io", "word", "odd_port", "IR_mode"],
        code=[0x3F10],
        regs={0: 0xA1B2, 1: 0x0107},
        fcw=FCW_SEG_SYS,
        io_preloads={3: 0x5555},
        observe_io=[3],
    ),

    TestCase(
        name="seg_io_odd_in_word_even",
        mnemonic="IN",
        target="z8001-seg",
        instruction="IN R0, #0x010A",
        description="Segmented odd-port baseline: word IN from even port 0x010A",
        tags=["io", "word", "odd_port", "DA_mode"],
        code=[0x3B04, 0x010A],
        regs={0: 0x0000},
        fcw=FCW_SEG_SYS,
        io_preloads={5: 0xC3D4},
    ),

    TestCase(
        name="seg_io_odd_in_word_da",
        mnemonic="IN",
        target="z8001-seg",
        instruction="IN R0, #0x010B",
        description="Segmented word IN from odd port 0x010B",
        tags=["io", "word", "odd_port", "DA_mode"],
        code=[0x3B04, 0x010B],
        regs={0: 0x0000},
        fcw=FCW_SEG_SYS,
        io_preloads={5: 0xC3D4},
    ),

    TestCase(
        name="seg_io_odd_in_word_ir",
        mnemonic="IN",
        target="z8001-seg",
        instruction="IN R0, @R1",
        description="Segmented word IN R0, @R1 with R1=0x010B",
        tags=["io", "word", "odd_port", "IR_mode"],
        code=[0x3D10],
        regs={0: 0x0000, 1: 0x010B},
        fcw=FCW_SEG_SYS,
        io_preloads={5: 0xC3D4},
    ),

    TestCase(
        name="seg_io_odd_sout_sin_word",
        mnemonic="SOUT",
        target="z8001-seg",
        instruction="SOUT #0x0107, R1; SIN R1, #0x010B",
        description="Segmented special word OUT to 0x0107 and IN from 0x010B",
        tags=["io", "word", "odd_port", "special_io"],
        code=[0x3B17, 0x0107, 0x3B15, 0x010B],
        regs={1: 0xA1B2},
        fcw=FCW_SEG_SYS,
        io_preloads={9: 0x5555, 11: 0xC3D4},
        observe_io=[9, 11],
    ),

    TestCase(
        name="seg_io_odd_outi_word",
        mnemonic="OUTI",
        target="z8001-seg",
        instruction="LDA RR8, 0x800; OUTI @R1, @RR8, R3",
        description="Segmented block word OUTI to odd port 0x0107 from seg 0 offset 0x0800",
        tags=["io", "word", "odd_port", "block"],
        code=[0x7608, 0x8000, 0x0800, 0x3B82, 0x0318],
        regs={1: 0x0107, 3: 0x0001},
        fcw=FCW_SEG_SYS,
        memory={0x0800: 0xA1B2},
        io_preloads={3: 0x5555},
        observe_io=[3],
    ),

    TestCase(
        name="seg_io_odd_ini_word",
        mnemonic="INI",
        target="z8001-seg",
        instruction="LDA RR8, 0x800; INI @RR8, @R1, R3",
        description="Segmented block word INI from odd port 0x010B to seg 0 offset 0x0800",
        tags=["io", "word", "odd_port", "block"],
        code=[0x7608, 0x8000, 0x0800, 0x3B10, 0x0388],
        regs={1: 0x010B, 3: 0x0001},
        fcw=FCW_SEG_SYS,
        memory={0x0800: 0x5555},
        io_preloads={5: 0xC3D4},
        observe_memory=[0x0800],
    ),

    TestCase(
        name="seg_io_odd_outb_lanes",
        mnemonic="OUTB",
        target="z8001-seg",
        instruction="OUTB #0x0107, RL0; OUTB #0x0106, RH0",
        description="Segmented byte OUT to odd and even ports: lane duplication",
        tags=["io", "byte", "odd_port"],
        code=[0x3A86, 0x0107, 0x3A06, 0x0106],
        regs={0: 0xA1B2},
        fcw=FCW_SEG_SYS,
        io_preloads={3: 0x5555},
        observe_io=[3],
    ),
]
