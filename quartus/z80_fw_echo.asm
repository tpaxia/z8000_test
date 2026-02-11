; Z80 Minimal Echo Firmware for Quartus bring-up
; Assembler: pyz80 (pip install pyz80)
;
; Build: pyz80 --obj=z80_fw.bin z80_fw_echo.asm
;
; I/O ports:
;   0x00: UART data (R: read byte, W: send byte)
;   0x01: UART status (bit0=tx_ready, bit1=rx_valid)
;
; Behavior: Print ">" prompt, wait for character, echo it back with CR/LF

        org 0x0000

start:
        ld sp, 0x2000           ; Stack at top of 8KB RAM

main_loop:
        ld a, 0x3E              ; '>'
        call put_char

        call get_char           ; Returns char in A
        call put_char           ; Echo it

        ld a, 0x0D              ; CR
        call put_char
        ld a, 0x0A              ; LF
        call put_char

        jp main_loop

; put_char: Send byte in A to UART
; Preserves A
put_char:
        push af
.wait_tx:
        in a, (0x01)
        and 0x01                ; Check TX ready (bit 0)
        jr z, .wait_tx
        pop af
        out (0x00), a
        ret

; get_char: Wait for and return received byte in A
get_char:
.wait_rx:
        in a, (0x01)
        and 0x02                ; Check RX valid (bit 1)
        jr z, .wait_rx
        in a, (0x00)            ; Read received byte
        ret
