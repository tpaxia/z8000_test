; Z80 Test Runner Firmware for Z8001 External Bus Test
; Assembler: pyz80 (pip install pyz80)
;
; Self-contained test: writes Z8001 program to BRAM, releases CPU,
; monitors execution, dumps bus trace buffer over UART.
;
; Build: pyz80 --obj=z80_fw.bin z80_fw_echo.asm
;
; I/O ports (Z80 harness):
;   0x00: UART data (R: read byte, W: send byte)
;   0x01: UART status (bit0=tx_ready, bit1=rx_valid)
;   0x10-0x11: Z8K mem addr (low, high)
;   0x12-0x13: Z8K mem data (low, high)
;   0x14: Z8K control (bit0=rst_n, bit1=mem_write)
;   0x15: Z8K status (bit0=halt_n, bit1=bus_active, bit2=timeout)
;   0x16-0x19: Cycle count (32-bit LE)
;   0x1A-0x1B: Fetch count (16-bit LE)
;   0x1C-0x1F: Cycle limit (32-bit LE, write)
;   0x20-0x21: Trace read addr (10-bit, R/W)
;   0x22-0x26: Trace data (36-bit, R)
;   0x27-0x28: Trace write count (10-bit, R)

        org 0x0000

start:
        ld sp, 0x2000           ; Stack at top of 8KB RAM

        ; Print banner
        ld hl, str_banner
        call print_str

        ; Ensure Z8001 is in reset
        xor a
        out (0x14), a

        ; ---- Write Z8001 reset vectors (segmented 4-word format) ----
        ; 0x0000: reserved
        ld de, 0x0000
        ld hl, 0x0000
        call z8kw
        ; 0x0002: FCW = 0x4000 (system mode, non-segmented)
        ld de, 0x0002
        ld hl, 0x4000
        call z8kw
        ; 0x0004: PC segment = 0 (segment 0)
        ld de, 0x0004
        ld hl, 0x0000
        call z8kw
        ; 0x0006: PC offset = 0x0200 (test code area, matches trace gate)
        ld de, 0x0006
        ld hl, 0x0200
        call z8kw

        ; ---- Write test program at 0x0200 ----
        ; LD R1, #1
        ld de, 0x0200
        ld hl, 0x2101           ; LD R1, #imm16 opcode
        call z8kw
        ld de, 0x0202
        ld hl, 0x0001           ; immediate value: 1
        call z8kw
        ; OUT DA, R1 (word)
        ld de, 0x0204
        ld hl, 0x3B16           ; OUT DA, R1 opcode
        call z8kw
        ld de, 0x0206
        ld hl, 0x00FE           ; port address
        call z8kw
        ; HALT
        ld de, 0x0208
        ld hl, 0x7A00           ; HALT opcode
        call z8kw

        ; ---- Set cycle limit = 4,000,000 = 0x003D0900 ----
        xor a
        out (0x1C), a           ; byte 0 = 0x00
        ld a, 0x09
        out (0x1D), a           ; byte 1 = 0x09
        ld a, 0x3D
        out (0x1E), a           ; byte 2 = 0x3D
        xor a
        out (0x1F), a           ; byte 3 = 0x00

; ============================================================
; Main test loop: release CPU, wait for halt, dump results
; ============================================================
run_test:
        ; Release Z8001 (write 0x01 to port 0x14: bit 0 = rst_n = 1)
        ld a, 0x01
        out (0x14), a

        ; Phase 1: Wait for bus activity (bit 1 of port 0x15)
        ; Fixed timeout: ~4096 iterations
        ld bc, 0x1000
.poll_start:
        in a, (0x15)
        and 0x02                ; bus_active?
        jr nz, .bus_ok
        dec bc
        ld a, b
        or c
        jr nz, .poll_start
        ; No bus activity - Z8001 didn't start
        xor a
        out (0x14), a           ; Reset CPU
        ld hl, str_nrst
        call print_str
        jp .wait_key

.bus_ok:
        ; Phase 2: Wait for halt_n=0 (bit 0) or cycle_timeout (bit 2)
.poll_halt:
        in a, (0x15)
        bit 0, a
        jr z, .halted           ; halt_n=0 -> CPU halted
        bit 2, a
        jr nz, .timed_out       ; timeout=1 -> cycle limit reached
        jr .poll_halt

.halted:
        ld hl, str_halt
        call print_str
        jr .show_counts

.timed_out:
        ld hl, str_tout
        call print_str

.show_counts:
        ; Print cycle count: CC=xxxxxxxx
        ld a, 0x43              ; 'C'
        call put_char
        ld a, 0x43              ; 'C'
        call put_char
        ld a, 0x3D              ; '='
        call put_char
        in a, (0x19)
        call phex2
        in a, (0x18)
        call phex2
        in a, (0x17)
        call phex2
        in a, (0x16)
        call phex2
        call put_crlf

        ; Print fetch count: FC=xxxx
        ld a, 0x46              ; 'F'
        call put_char
        ld a, 0x43              ; 'C'
        call put_char
        ld a, 0x3D              ; '='
        call put_char
        in a, (0x1B)
        call phex2
        in a, (0x1A)
        call phex2
        call put_crlf

        ; Read trace count into DE
        in a, (0x28)
        and 0x03
        ld d, a                 ; D = high byte of count
        in a, (0x27)
        ld e, a                 ; DE = trace count (10-bit)

        ; Print trace count: TC=xxx
        ld a, 0x54              ; 'T'
        call put_char
        ld a, 0x43              ; 'C'
        call put_char
        ld a, 0x3D              ; '='
        call put_char
        ld a, d
        call phex1
        ld a, e
        call phex2
        call put_crlf

        ; If count == 0, skip trace dump
        ld a, d
        or e
        jr z, .done

        ; Dump all trace entries (index 0 to count-1)
        ld bc, 0x0000           ; BC = current index
.trace_loop:
        push de                 ; Save count
        push bc                 ; Save index

        ; Set trace read address
        ld a, c
        out (0x20), a           ; addr low
        ld a, b
        out (0x21), a           ; addr high
        nop                     ; Wait for BRAM read
        nop

        ; Print trace entry: AAAA DDDD RBM
        call print_trace

        pop bc                  ; Restore index
        pop de                  ; Restore count

        ; Next entry
        inc bc

        ; Compare BC with DE (done when BC == DE)
        ld a, c
        cp e
        jr nz, .trace_loop
        ld a, b
        cp d
        jr nz, .trace_loop

.done:
        ld hl, str_done
        call print_str

.wait_key:
        ; Wait for keypress
        call get_char

        ; Reset Z8001, then re-run
        xor a
        out (0x14), a
        jp run_test

; ============================================================
; print_trace: Print one trace entry from ports 0x22-0x26
; Format: AAAA DDDD RBM\r\n
; ============================================================
print_trace:
        ; Address (big-endian: high byte first)
        in a, (0x23)
        call phex2
        in a, (0x22)
        call phex2
        ld a, 0x20              ; ' '
        call put_char
        ; Data (big-endian)
        in a, (0x25)
        call phex2
        in a, (0x24)
        call phex2
        ld a, 0x20              ; ' '
        call put_char
        ; Flags byte (port 0x26)
        in a, (0x26)
        ld b, a
        ; R/W flag (bit 0): 1=read, 0=write
        bit 0, b
        jr z, .wr
        ld a, 0x52              ; 'R'
        jr .rw_out
.wr:
        ld a, 0x57              ; 'W'
.rw_out:
        call put_char
        ; B/W flag (bit 1): 1=word, 0=byte
        bit 1, b
        jr z, .byte
        ld a, 0x57              ; 'W'
        jr .bw_out
.byte:
        ld a, 0x42              ; 'B'
.bw_out:
        call put_char
        ; I/O flag (bit 2): 1=I/O, 0=memory
        bit 2, b
        jr z, .mem
        ld a, 0x49              ; 'I'
        jr .io_out
.mem:
        ld a, 0x4D              ; 'M'
.io_out:
        call put_char
        jp put_crlf             ; Tail call (returns to caller)

; ============================================================
; Core Subroutines
; ============================================================

; put_char: Send byte in A to UART. Preserves A.
put_char:
        push af
.wait_tx:
        in a, (0x01)
        and 0x01                ; TX ready?
        jr z, .wait_tx
        pop af
        out (0x00), a
        ret

; get_char: Wait for and return received byte in A.
get_char:
.wait_rx:
        in a, (0x01)
        and 0x02                ; RX valid?
        jr z, .wait_rx
        in a, (0x00)
        ret

; put_crlf: Print CR/LF
put_crlf:
        ld a, 0x0D
        call put_char
        ld a, 0x0A
        jp put_char

; print_str: Print null-terminated string at HL. Clobbers A, HL.
print_str:
        ld a, (hl)
        or a
        ret z
        call put_char
        inc hl
        jr print_str

; phex1: Print low nibble of A as hex digit
phex1:
        and 0x0F
        cp 10
        jr c, .digit
        add a, 0x37             ; 'A' - 10 = 0x41 - 0x0A = 0x37
        jp put_char
.digit:
        add a, 0x30             ; '0' = 0x30
        jp put_char

; phex2: Print A as 2 hex digits (high nibble first)
phex2:
        push af
        rrca
        rrca
        rrca
        rrca
        call phex1
        pop af
        jp phex1

; z8kw: Write word HL to Z8000 memory address DE.
; CPU must be in reset (bit 0 of port 0x14 stays 0).
z8kw:
        ld a, e
        out (0x10), a           ; addr low
        ld a, d
        out (0x11), a           ; addr high
        ld a, l
        out (0x12), a           ; data low
        ld a, h
        out (0x13), a           ; data high
        ld a, 0x02              ; bit 1 = mem_write, bit 0 = 0 (keep in reset)
        out (0x14), a
        xor a
        out (0x14), a           ; clear write pulse
        ret

; ============================================================
; String Constants
; ============================================================
str_banner:
        defm "Z8001 Bus Test"
        defb 0x0D, 0x0A, 0x00
str_halt:
        defm "HALT"
        defb 0x0D, 0x0A, 0x00
str_tout:
        defm "TOUT"
        defb 0x0D, 0x0A, 0x00
str_nrst:
        defm "NRST"
        defb 0x0D, 0x0A, 0x00
str_done:
        defm "DONE"
        defb 0x0D, 0x0A, 0x00
