"""Memory layout constants and common test helpers."""

# Memory map
CODE_BASE = 0x0200       # Test code area start
CODE_END = 0x03FF        # Test code area end
OPERAND_BASE = 0x0400    # Memory operand area (for DA/IR/X mode)
OPERAND_END = 0x05FF
SRC_BUF = 0x0600         # Block operation source buffer
SRC_BUF_END = 0x06FF
DST_BUF = 0x0700         # Block operation destination buffer
DST_BUF_END = 0x07FF
STACK_BASE = 0x0F00      # Stack base (grows downward)

# Bootstrap addresses
REG_SETUP = 0x0010       # R0-R15 initial values (0x0010-0x002F)
FCW_SETUP = 0x0030       # FCW setup word
FCW_DUMP = 0x00B2        # FCW dump area (after execution)
REG_DUMP = 0x0090        # R0-R15 dump area (0x0090-0x00AF)
DONE_FLAG = 0x00B0       # Done flag
DUMP_ROUTINE = 0x00C0    # Dump routine entry

# Jump to dump routine instruction words
JP_DUMP = [0x5E08, DUMP_ROUTINE]  # JP 0x00C0


def stack_regs(sp=STACK_BASE):
    """Return register dict with R15 set as stack pointer."""
    return {15: sp}


def block_regs(src=SRC_BUF, dst=DST_BUF, count=0, src_reg=1, dst_reg=2, cnt_reg=0):
    """Return register dict for block operations."""
    return {src_reg: src, dst_reg: dst, cnt_reg: count}


def preload_buffer(base, words):
    """Create memory dict to preload a buffer with word values."""
    mem = {}
    for i, w in enumerate(words):
        mem[base + i * 2] = w
    return mem
