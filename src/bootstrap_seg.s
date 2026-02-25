# Z8000 Test Harness Bootstrap and Dump Routines (Segmented Mode)
# Assembler: z8k-coff-as -z8001
#
# In segmented mode, all DA (direct address) instructions encode as 3 words
# (opcode + segment word + offset word), making the code larger than the
# non-segmented version. The bootstrap code extends from 0x0040 to ~0x00AD,
# so the register dump area is placed at 0x0140 (after the dump routine)
# instead of 0x0090 as in the non-segmented version.
#
# Memory layout:
#   0x0000-0x0007  Reset vectors (segmented: 4 words)
#   0x0010-0x002F  Register initial values (loaded by bootstrap)
#   0x0030-0x0031  FCW setup word
#   0x0040-0x00AD  Bootstrap code (loads regs, jumps to test code)
#   0x00C0-0x0133  Dump routine (saves regs after test)
#   0x0140-0x015F  Register dump area (R0-R15 saved here)
#   0x0160-0x0161  Done flag
#   0x0162-0x0163  FCW dump
#   0x0200+        Test code
#
# FCW = 0xC000 (System + Segmented mode)

        segm
        .text
        .global _start

# Reset vectors at 0x0000 (segmented format: 4 words)
        .org    0x0000
        .word   0x0000          ! Reserved
        .word   0xC000          ! FCW = System mode + Segmented
        .word   0x0000          ! PC segment number = 0
        .word   0x0040          ! PC offset = bootstrap entry

# Register initial values (loaded to R0-R15 by bootstrap)
        .org    0x0010
reg_setup:
        .space  32              ! R0-R15 initial values (0x0010-0x002F)

# FCW setup at 0x0030
        .org    0x0030
fcw_setup:
        .word   0xC000          ! Initial FCW (System + Segmented)

# Bootstrap code at 0x0040
        .org    0x0040
bootstrap:
_start:
        ld      r0, fcw_setup       ! Load desired FCW value
        ldctl   fcw, r0             ! Set FCW (LD doesn't affect flags)
        ld      r0, reg_setup+0
        ld      r1, reg_setup+2
        ld      r2, reg_setup+4
        ld      r3, reg_setup+6
        ld      r4, reg_setup+8
        ld      r5, reg_setup+10
        ld      r6, reg_setup+12
        ld      r7, reg_setup+14
        ld      r8, reg_setup+16
        ld      r9, reg_setup+18
        ld      r10, reg_setup+20
        ld      r11, reg_setup+22
        ld      r12, reg_setup+24
        ld      r13, reg_setup+26
        ld      r14, reg_setup+28
        ld      r15, reg_setup+30
        jp      test_code           ! Jump to test code (0x0200)
# Bootstrap code ends at 0x00AE

# Dump routine at 0x00C0
# Saves R0-R15 to reg_dump (0x0140-0x015F), FCW to fcw_dump (0x0162)
        .org    0x00C0
dump_routine:
        ld      reg_dump+0, r0      ! Save R0 first (before clobbering)
        ldctl   r0, fcw             ! Read FCW into R0
        ld      fcw_dump, r0        ! Save FCW at 0x0162
        ld      reg_dump+2, r1
        ld      reg_dump+4, r2
        ld      reg_dump+6, r3
        ld      reg_dump+8, r4
        ld      reg_dump+10, r5
        ld      reg_dump+12, r6
        ld      reg_dump+14, r7
        ld      reg_dump+16, r8
        ld      reg_dump+18, r9
        ld      reg_dump+20, r10
        ld      reg_dump+22, r11
        ld      reg_dump+24, r12
        ld      reg_dump+26, r13
        ld      reg_dump+28, r14
        ld      reg_dump+30, r15
        ld      r0, #0xDEAD
        ld      done_flag, r0
        halt
# Dump routine ends at 0x0134

# Register dump area at 0x0140 (moved from 0x0090 due to larger code)
        .org    0x0140
reg_dump:
        .space  32              ! R0-R15 final values (0x0140-0x015F)

# Done flag at 0x0160
        .org    0x0160
done_flag:
        .word   0x0000

# FCW dump area at 0x0162
        .org    0x0162
fcw_dump:
        .word   0x0000

# Default test code at 0x0200
        .org    0x0200
test_code:
        jp      dump_routine        ! Default: just jump to dump

        .end
