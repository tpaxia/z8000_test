; Z80 Test Harness Firmware - z80asm compatible syntax
; I/O: 0=UART_DATA, 1=UART_STAT, 0x10-0x15=Z8K control
;      0x16-0x19=cycle count, 0x1A-0x1B=fetch count
;      0x1C-0x1F=cycle limit (write)
;
; Commands:
;   ST - Status (returns H or R)
;   RS - Reset Z8000
;   EX - Execute until halt (with cycle-based timeout)
;   WRnxxxx - Write register n
;   RRn - Read register n
;   WMaaaaxxxx - Write memory
;   RMaaaa - Read memory
;   DA - Dump all registers
;   MT - Memory test
;   DB - Toggle debug mode
;   DP - Dump I/O ports (debug)
;   TOxxxxxxxx - Set cycle timeout (32-bit, 0=no timeout)
;   CC - Read cycle count
;   FC - Read fetch count

        org 0x0000

; Variables in RAM at 0x1F00 (before stack at 0x2000)
; 0x1F00: debug_flag (0=off, 1=on)
; 0x1F02-0x1F05: cycle_limit (32-bit, little-endian)

start:
        ld sp, 0x2000   ; Initialize stack pointer to top of RAM
        ; Initialize variables
        xor a
        ld (0x1F00), a  ; debug_flag = 0
        ; Default cycle_limit = 4,000,000 (1 second at 4MHz) = 0x003D0900
        ld (0x1F02), a  ; cycle_limit byte 0 = 0x00
        ld a, 0x09
        ld (0x1F03), a  ; cycle_limit byte 1 = 0x09
        ld a, 0x3D
        ld (0x1F04), a  ; cycle_limit byte 2 = 0x3D
        xor a
        ld (0x1F05), a  ; cycle_limit byte 3 = 0x00

main:
        call get_char
        call to_upper
        cp 'S'
        jp z, cmd_st
        cp 'R'
        jp z, cmd_r
        cp 'W'
        jp z, cmd_w
        cp 'E'
        jp z, cmd_ex
        cp 'D'
        jp z, cmd_d
        cp 'M'
        jp z, cmd_mt
        cp 'I'
        jp z, cmd_in
        cp 'T'
        jp z, cmd_t
        cp 'C'
        jp z, cmd_c
        cp 'F'
        jp z, cmd_f
        jp cmd_err

cmd_t:
        call get_char
        call to_upper
        cp 'O'
        jp z, do_to
        jp cmd_err

cmd_c:
        call get_char
        call to_upper
        cp 'C'
        jp z, do_cc_eol
        jp cmd_err

do_cc_eol:
        call skip_eol
        jp do_cc

cmd_f:
        call get_char
        call to_upper
        cp 'C'
        jp z, do_fc_eol
        jp cmd_err

do_fc_eol:
        call skip_eol
        jp do_fc

; TO xxxxxxxx - Set cycle timeout (32-bit, 0 = no timeout)
do_to:
        ; Read 8 hex digits into 0x1F02-0x1F05 (big-endian input, little-endian storage)
        call ghex4              ; Get high word into HL
        push hl
        call ghex4              ; Get low word into HL
        call skip_eol
        ; Store low word (HL) to bytes 0-1
        ld a, l
        ld (0x1F02), a          ; Byte 0 (LSB)
        ld a, h
        ld (0x1F03), a          ; Byte 1
        ; Store high word to bytes 2-3
        pop hl
        ld a, l
        ld (0x1F04), a          ; Byte 2
        ld a, h
        ld (0x1F05), a          ; Byte 3 (MSB)
        ; Print OK
        ld a, 'O'
        call put_char
        ld a, 'K'
        call put_char
        call put_crlf
        jp main

cmd_in:
        call get_char
        call to_upper
        cp 'N'
        jp nz, cmd_err
        call get_char
        call to_upper
        cp 'I'
        jp nz, cmd_err
        call get_char
        call to_upper
        cp 'T'
        jp nz, cmd_err
        call skip_eol
        jp do_init

cmd_st:
        call get_char
        call to_upper
        cp 'T'
        jp nz, cmd_err
        call skip_eol
        jp do_st

cmd_r:
        call get_char
        call to_upper
        cp 'S'
        jp z, do_rs_eol
        cp 'R'
        jp z, do_rr
        cp 'M'
        jp z, do_rm
        jp cmd_err

do_rs_eol:
        call skip_eol
        jp do_rs

cmd_w:
        call get_char
        call to_upper
        cp 'R'
        jp z, do_wr
        cp 'M'
        jp z, do_wm
        jp cmd_err

cmd_ex:
        call get_char
        call to_upper
        cp 'X'
        jp nz, cmd_err
        call skip_eol
        jp do_ex

cmd_d:
        call get_char
        call to_upper
        cp 'A'
        jp z, do_da_eol
        cp 'B'
        jp z, do_db_eol
        cp 'P'
        jp z, do_dp_eol
        jp cmd_err

do_da_eol:
        call skip_eol
        jp do_da

do_db_eol:
        call skip_eol
        jp do_db

do_dp_eol:
        call skip_eol
        jp do_dp

cmd_mt:
        call get_char
        call to_upper
        cp 'T'
        jp nz, cmd_err
        call skip_eol
        jp do_mt

cmd_err:
        call skip_eol
        ld a, 'E'
        call put_char
        ld a, 'R'
        call put_char
        ld a, 'R'
        call put_char
        call put_crlf
        jp main

; DB - Toggle debug mode
do_db:
        ld a, (0x1F00)
        xor 1
        ld (0x1F00), a
        ; Print status
        ld a, 'D'
        call put_char
        ld a, 'B'
        call put_char
        ld a, '='
        call put_char
        ld a, (0x1F00)
        add a, '0'
        call put_char
        call put_crlf
        jp main

; DP - Dump all I/O ports (diagnostic)
do_dp:
        ; Port 0x00 - UART data (don't read, would consume byte)
        ld a, 'P'
        call put_char
        ld a, '0'
        call put_char
        ld a, '1'
        call put_char
        ld a, '='
        call put_char
        in a, (0x01)
        call phex2
        call put_crlf

        ; Port 0x10 - Z8K addr low
        ld a, 'P'
        call put_char
        ld a, '1'
        call put_char
        ld a, '0'
        call put_char
        ld a, '='
        call put_char
        in a, (0x10)
        call phex2
        call put_crlf

        ; Port 0x11 - Z8K addr high
        ld a, 'P'
        call put_char
        ld a, '1'
        call put_char
        ld a, '1'
        call put_char
        ld a, '='
        call put_char
        in a, (0x11)
        call phex2
        call put_crlf

        ; Port 0x12 - Z8K data low
        ld a, 'P'
        call put_char
        ld a, '1'
        call put_char
        ld a, '2'
        call put_char
        ld a, '='
        call put_char
        in a, (0x12)
        call phex2
        call put_crlf

        ; Port 0x13 - Z8K data high
        ld a, 'P'
        call put_char
        ld a, '1'
        call put_char
        ld a, '3'
        call put_char
        ld a, '='
        call put_char
        in a, (0x13)
        call phex2
        call put_crlf

        ; Port 0x14 - Z8K control
        ld a, 'P'
        call put_char
        ld a, '1'
        call put_char
        ld a, '4'
        call put_char
        ld a, '='
        call put_char
        in a, (0x14)
        call phex2
        call put_crlf

        ; Port 0x15 - Z8K status
        ld a, 'P'
        call put_char
        ld a, '1'
        call put_char
        ld a, '5'
        call put_char
        ld a, '='
        call put_char
        in a, (0x15)
        call phex2
        call put_crlf

        jp main

; ST - Status
do_st:
        call dbg_st_enter
        in a, (0x14)
        call dbg_port14
        and 1
        jp z, st_h
        in a, (0x15)
        call dbg_port15
        and 1
        jp z, st_h
        ld a, 'R'
        jp st_out
st_h:
        ld a, 'H'
st_out:
        call put_char
        call put_crlf
        jp main

; RS - Reset
do_rs:
        xor a
        out (0x14), a
        ld a, 'O'
        call put_char
        ld a, 'K'
        call put_char
        call put_crlf
        jp main

; EX - Execute
; Phase 1: Release reset and verify Z8000 starts (bus_active goes HIGH)
; Phase 2: Wait for Z8000 to halt (halt_n goes LOW) or cycle timeout
do_ex:
        ; Debug: show cycle limit
        call dbg_ex_limit

        ; Write cycle_limit to hardware ports 0x1C-0x1F before releasing reset
        ld a, (0x1F02)
        out (0x1C), a           ; Cycle limit byte 0
        ld a, (0x1F03)
        out (0x1D), a           ; Cycle limit byte 1
        ld a, (0x1F04)
        out (0x1E), a           ; Cycle limit byte 2
        ld a, (0x1F05)
        out (0x1F), a           ; Cycle limit byte 3

        ld a, 1
        out (0x14), a           ; Release reset

        ; Debug: show reset released
        call dbg_ex_start

        ; Phase 1: Wait for Z8000 bus activity (bit 1 of port 0x15)
        ; Fixed timeout: 4096 iterations (~200us)
        ld bc, 0x1000
ex_startup:
        in a, (0x15)
        and 2                   ; Check bit 1 = bus_active
        jp nz, ex_running       ; bus_active = 1 means Z8000 started OK
        dec bc
        ld a, b
        or c
        jp nz, ex_startup
        ; Timeout - Z8000 didn't start (no bus activity)
        xor a
        out (0x14), a           ; Assert reset
        ld a, 'N'
        call put_char
        ld a, 'R'
        call put_char
        ld a, 'S'
        call put_char
        ld a, 'T'
        call put_char
        call put_crlf
        jp main

ex_running:
        ; Phase 2: Z8000 is running, wait for halt or cycle timeout
        ; Port 0x15: bit 0 = halt_n (0=halted), bit 2 = cycle_timeout (1=timeout)
ex_lp:
        in a, (0x15)
        bit 0, a
        jp z, ex_ok             ; halt_n = 0 means halted
        bit 2, a
        jp nz, ex_tout          ; cycle_timeout = 1 means timeout
        jp ex_lp

ex_tout:
        ; Cycle timeout
        call dbg_ex_status      ; Debug: show final status
        call dbg_ex_cycles      ; Debug: show cycle count (before reset clears it!)
        xor a
        out (0x14), a           ; Assert reset
        ld a, 'T'
        call put_char
        ld a, 'O'
        call put_char
        ld a, 'U'
        call put_char
        ld a, 'T'
        call put_char
        call put_crlf
        jp main

ex_ok:
        call dbg_ex_status      ; Debug: show final status
        call dbg_ex_cycles      ; Debug: show cycle count (before reset clears it!)
        xor a
        out (0x14), a           ; Assert reset
        ld a, 'H'
        call put_char
        ld a, 'A'
        call put_char
        ld a, 'L'
        call put_char
        ld a, 'T'
        call put_char
        call put_crlf
        jp main

; WR n xxxx
do_wr:
        call ghex1
        push af
        call ghex4
        call skip_eol
        pop af
        add a, a
        ld e, a
        ld d, 0
        ld bc, 0x0010
        ex de, hl
        add hl, bc
        ex de, hl
        call z8kw
        ld a, 'O'
        call put_char
        ld a, 'K'
        call put_char
        call put_crlf
        jp main

; RR n
do_rr:
        call ghex1
        call skip_eol
        add a, a
        ld e, a
        ld d, 0
        ld hl, 0x0090
        add hl, de
        ex de, hl
        call dbg_rr_addr
        call z8kr
        call dbg_rr_data
        call phex4
        call put_crlf
        jp main

; WM aaaa xxxx
do_wm:
        call ghex4
        push hl
        call ghex4
        pop de
        call skip_eol
        call z8kw
        ld a, 'O'
        call put_char
        ld a, 'K'
        call put_char
        call put_crlf
        jp main

; RM aaaa
do_rm:
        call ghex4
        ex de, hl
        call skip_eol
        call z8kr
        call phex4
        call put_crlf
        jp main

; DA - Dump all registers
do_da:
        call dbg_da_enter
        ld b, 0
da_lp:
        call dbg_da_loop     ; Debug: show loop iteration
        ld a, 'R'
        call put_char
        ld a, b
        cp 10
        jp c, da_1d
        ld a, '1'
        call put_char
        ld a, b
        sub 10
        add a, '0'
        call put_char
        jp da_eq
da_1d:
        add a, '0'
        call put_char
da_eq:
        ld a, '='
        call put_char
        ; Calculate address: 0x0090 + b*2
        ld a, b
        add a, a
        ld e, a
        ld d, 0
        ld hl, 0x0090
        add hl, de
        ex de, hl
        call dbg_da_addr     ; Debug: show address
        push bc
        call z8kr
        call dbg_da_read     ; Debug: show read value
        call phex4
        pop bc
        call dbg_da_popped   ; Debug: show B after pop
        call put_crlf
        inc b
        ld a, b
        cp 16
        jp nz, da_lp
        call dbg_da_done
        jp main

; MT - Memory test
do_mt:
        ld de, 0x0F00
        ld hl, 0x5A5A
        call z8kw
        ld de, 0x0F00
        call z8kr
        ld a, h
        cp 0x5A
        jp nz, mt_f
        ld a, l
        cp 0x5A
        jp nz, mt_f
        ld de, 0x0F02
        ld hl, 0xA5A5
        call z8kw
        ld de, 0x0F02
        call z8kr
        ld a, h
        cp 0xA5
        jp nz, mt_f
        ld a, l
        cp 0xA5
        jp nz, mt_f
        ld a, 'P'
        call put_char
        ld a, 'A'
        call put_char
        ld a, 'S'
        call put_char
        ld a, 'S'
        call put_char
        call put_crlf
        jp main
mt_f:
        ld a, 'F'
        call put_char
        ld a, 'A'
        call put_char
        ld a, 'I'
        call put_char
        ld a, 'L'
        call put_char
        call put_crlf
        jp main

; INIT - Initialize Z8000 memory with bootstrap code
; Loads bootstrap_data (from bootstrap.inc) to Z8000 memory starting at 0x0000
; Bootstrap contains: reset vectors, register init, dump routines
do_init:
        ; Assert reset first
        xor a
        out (0x14), a

        ; Copy bootstrap data to Z8000 memory
        ; Use IX as source pointer, DE as Z8000 dest address
        ld ix, bootstrap_data
        ld de, 0x0000           ; Z8000 start address
        ld bc, bootstrap_len    ; Word count

init_loop:
        ; Check if done (BC = 0)
        ld a, b
        or c
        jp z, init_done

        ; Read word from bootstrap_data (Z80 dw stores little-endian: low, high)
        ld l, (ix+0)            ; Low byte
        ld h, (ix+1)            ; High byte
        inc ix
        inc ix

        ; Write HL to Z8000 address DE
        call z8kw

        ; Next Z8000 address
        inc de
        inc de

        ; Decrement count
        dec bc
        jp init_loop

init_done:
        ; Print OK
        ld a, 'O'
        call put_char
        ld a, 'K'
        call put_char
        call put_crlf
        jp main

; CC - Read cycle count (32-bit, 8 hex digits)
do_cc:
        ; Read 4 bytes from ports 0x16-0x19 and print as hex
        ; Print high byte first (big endian output)
        in a, (0x19)
        call phex2
        in a, (0x18)
        call phex2
        in a, (0x17)
        call phex2
        in a, (0x16)
        call phex2
        call put_crlf
        jp main

; FC - Read fetch count (16-bit, 4 hex digits)
do_fc:
        ; Read 2 bytes from ports 0x1A-0x1B and print as hex
        in a, (0x1B)
        call phex2
        in a, (0x1A)
        call phex2
        call put_crlf
        jp main

; === Debug output routines ===
; These check debug_flag and output diagnostic info

; Debug: ST command enter
dbg_st_enter:
        ld a, (0x1F00)
        or a
        ret z
        push af
        ld a, '['
        call put_char
        ld a, 'S'
        call put_char
        ld a, 'T'
        call put_char
        ld a, ']'
        call put_char
        pop af
        ret

; Debug: show port 0x14 value
dbg_port14:
        push af
        ld a, (0x1F00)
        or a
        jp z, dbg_p14_skip
        ld a, '<'
        call put_char
        ld a, '1'
        call put_char
        ld a, '4'
        call put_char
        ld a, '='
        call put_char
        pop af
        push af
        call phex2
        ld a, '>'
        call put_char
dbg_p14_skip:
        pop af
        ret

; Debug: show port 0x15 value
dbg_port15:
        push af
        ld a, (0x1F00)
        or a
        jp z, dbg_p15_skip
        ld a, '<'
        call put_char
        ld a, '1'
        call put_char
        ld a, '5'
        call put_char
        ld a, '='
        call put_char
        pop af
        push af
        call phex2
        ld a, '>'
        call put_char
dbg_p15_skip:
        pop af
        ret

; Debug: DA command enter
dbg_da_enter:
        ld a, (0x1F00)
        or a
        ret z
        ld a, '['
        call put_char
        ld a, 'D'
        call put_char
        ld a, 'A'
        call put_char
        ld a, ']'
        call put_char
        call put_crlf
        ret

; Debug: DA loop iteration (B = loop counter)
dbg_da_loop:
        ld a, (0x1F00)
        or a
        ret z
        push bc
        ld a, '#'
        call put_char
        ld a, b
        call phex2
        ld a, ' '
        call put_char
        pop bc
        ret

; Debug: DA address (DE = address)
dbg_da_addr:
        ld a, (0x1F00)
        or a
        ret z
        push de
        push hl
        ld a, '@'
        call put_char
        ex de, hl
        call phex4
        ld a, ' '
        call put_char
        pop hl
        pop de
        ret

; Debug: DA read value (HL = value from z8kr)
dbg_da_read:
        ld a, (0x1F00)
        or a
        ret z
        push hl
        ld a, '='
        call put_char
        call phex4
        ld a, ' '
        call put_char
        pop hl
        ret

; Debug: DA after pop (show B value)
dbg_da_popped:
        ld a, (0x1F00)
        or a
        ret z
        push bc
        ld a, 'B'
        call put_char
        ld a, '='
        call put_char
        ld a, b
        call phex2
        ld a, ' '
        call put_char
        pop bc
        ret

; Debug: DA done
dbg_da_done:
        ld a, (0x1F00)
        or a
        ret z
        ld a, '['
        call put_char
        ld a, 'O'
        call put_char
        ld a, 'K'
        call put_char
        ld a, ']'
        call put_char
        call put_crlf
        ret

; Debug: RR address
dbg_rr_addr:
        ld a, (0x1F00)
        or a
        ret z
        push de
        push hl
        ld a, '['
        call put_char
        ld a, '@'
        call put_char
        ex de, hl
        call phex4
        ld a, ']'
        call put_char
        pop hl
        pop de
        ret

; Debug: RR data
dbg_rr_data:
        ld a, (0x1F00)
        or a
        ret z
        push hl
        ld a, '['
        call put_char
        ld a, '='
        call put_char
        call phex4
        ld a, ']'
        call put_char
        pop hl
        ret

; Debug: EX show cycle limit
dbg_ex_limit:
        ld a, (0x1F00)
        or a
        ret z
        ld a, '['
        call put_char
        ld a, 'L'
        call put_char
        ld a, '='
        call put_char
        ; Print 32-bit limit as 8 hex digits (big endian)
        ld a, (0x1F05)
        call phex2
        ld a, (0x1F04)
        call phex2
        ld a, (0x1F03)
        call phex2
        ld a, (0x1F02)
        call phex2
        ld a, ']'
        call put_char
        ret

; Debug: EX reset released
dbg_ex_start:
        ld a, (0x1F00)
        or a
        ret z
        ld a, '['
        call put_char
        ld a, 'R'
        call put_char
        ld a, 'U'
        call put_char
        ld a, 'N'
        call put_char
        ld a, ']'
        call put_char
        ret

; Debug: EX show port 0x15 status
dbg_ex_status:
        ld a, (0x1F00)
        or a
        ret z
        ld a, '['
        call put_char
        ld a, 'S'
        call put_char
        ld a, '='
        call put_char
        in a, (0x15)
        call phex2
        ld a, ']'
        call put_char
        ret

; Debug: EX show cycle count
dbg_ex_cycles:
        ld a, (0x1F00)
        or a
        ret z
        ld a, '['
        call put_char
        ld a, 'C'
        call put_char
        ld a, '='
        call put_char
        ; Print 32-bit count as 8 hex digits (big endian)
        in a, (0x19)
        call phex2
        in a, (0x18)
        call phex2
        in a, (0x17)
        call phex2
        in a, (0x16)
        call phex2
        ld a, ']'
        call put_char
        ret

; === Core Subroutines ===

; Convert character in A to uppercase
to_upper:
        cp 'a'
        ret c               ; < 'a', return unchanged
        cp 'z'+1
        ret nc              ; > 'z', return unchanged
        sub 0x20            ; Convert lowercase to uppercase
        ret

get_char:
        in a, (0x01)
        and 2
        jp z, get_char
        in a, (0x00)
        ret

put_char:
        push af
pc_w:
        in a, (0x01)
        and 1
        jp z, pc_w
        pop af
        out (0x00), a
        ret

put_crlf:
        ld a, 0x0D
        call put_char
        ld a, 0x0A
        call put_char
        ret

skip_eol:
        in a, (0x01)
        and 2
        jp z, skip_eol
        in a, (0x00)
        cp 0x0D
        ret z
        cp 0x0A
        ret z
        jp skip_eol

ghex1:
        call get_char
        cp '0'
        jp c, gh1_0
        cp '9'+1
        jp c, gh1_d
        cp 'A'
        jp c, gh1_0
        cp 'F'+1
        jp c, gh1_u
        cp 'a'
        jp c, gh1_0
        cp 'f'+1
        jp c, gh1_l
gh1_0:
        xor a
        ret
gh1_d:
        sub '0'
        ret
gh1_u:
        sub 'A'-10
        ret
gh1_l:
        sub 'a'-10
        ret

ghex2:
        call ghex1
        rlca
        rlca
        rlca
        rlca
        ld b, a
        call ghex1
        or b
        ret

ghex4:
        call ghex2
        ld h, a
        call ghex2
        ld l, a
        ret

phex1:
        and 0x0F
        cp 10
        jp c, ph1_d
        add a, 'A'-10
        jp put_char
ph1_d:
        add a, '0'
        jp put_char

phex2:
        push af
        rrca
        rrca
        rrca
        rrca
        call phex1
        pop af
        jp phex1

phex4:
        ld a, h
        call phex2
        ld a, l
        jp phex2

z8kw:
        ld a, e
        out (0x10), a
        ld a, d
        out (0x11), a
        ld a, l
        out (0x12), a
        ld a, h
        out (0x13), a
        ld a, 0x02
        out (0x14), a
        xor a
        out (0x14), a
        ret

z8kr:
        ld a, e
        out (0x10), a
        ld a, d
        out (0x11), a
        nop
        nop
        in a, (0x12)
        ld l, a
        in a, (0x13)
        ld h, a
        ret

; ==============================================
; Z8000 Bootstrap Data
; ==============================================
        include "bootstrap.inc"

        end
