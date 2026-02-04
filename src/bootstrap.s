# Z8000 Test Harness Bootstrap and Dump Routines
# Assembler: z8k-coff-as -z8002

        .text
        .global _start

# Reset vectors at 0x0000
        .org    0x0000
        .word   0x0000          ! Reserved
        .word   0x4000          ! FCW = System mode
        .word   bootstrap       ! PC = bootstrap entry

# Padding to register setup area
        .org    0x0010
reg_setup:
        .space  32              ! R0-R15 initial values (0x0010-0x002F)

# FCW setup at 0x0030
        .org    0x0030
fcw_setup:
        .word   0x4000          ! Initial FCW

# Bootstrap code at 0x0040
        .org    0x0040
bootstrap:
_start:
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
        jp      0x0200          ! Jump to test code

# Register dump area at 0x0090
        .org    0x0090
reg_dump:
        .space  32              ! R0-R15 final values (0x0090-0x00AF)

# Done flag at 0x00B0
        .org    0x00B0
done_flag:
        .word   0x0000

# Dump routine at 0x00C0
        .org    0x00C0
dump_routine:
        ld      reg_dump+0, r0
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

# Default test code at 0x0200
        .org    0x0200
test_code:
        jp      dump_routine    ! Default: just jump to dump

        .end
