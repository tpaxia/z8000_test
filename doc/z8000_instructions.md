# Z8000 Instruction Set Reference

## Instruction Format

The Z8000 architecture uses a regular instruction format with the following structure:

### General Instruction Format (First Word)

```
Bit:  15 14 | 13 12 11 10 9 8 | 7 6 5 4 | 3 2 1 0
      ------+------------------+---------+---------
Byte: ad mode|     opcode     0 |  src/dst |  src/dst
Word: ad mode|     opcode     1 |  src/dst |  src/dst
Long: ad mode|        opcode    |  src/dst |  src/dst
```

### Addressing Mode Field (bits 15-14)

| Bits | Mode |
|------|------|
| 00 | Immediate (IM) or Indirect Register (IR) |
| 01 | Direct Address (DA) or Index (X) |
| 10 | Register (R) |
| 11 | Compact format (special instructions) |

The choice between IM/IR or DA/X is determined by bits 7-4. Register R0 cannot be used with IR or X modes.

### Compact Format Instructions

```
Bit:  15 14 13 12 | 11 10 9 8 | 7 6 5 4 3 2 1 0
      ------------+-----------+-----------------
LDB:   1  1  0  0 | destination|    byte data
CALR:  1  1  0  1 |        offset (12-bit)
JR:    1  1  1  0 |  cond code |  offset (8-bit)
DJNZ:  1  1  1  1 |  register W|  offset (7-bit)
```

### Second Word Format (for multi-word instructions)

Used for: immediate data, addresses, displacements, or extended operands.

```
Bit:  15 14 13 12 | 11 10 9 8 | 7 6 5 4 | 3 2 1 0
      ------------+-----------+---------+---------
      0  0  0  0  |  register |  register| cond code
      0  0  0  0  |  register | 0 0 0 0 | identifier
EPU:   EPU data   |     EPU data        | iter count
```

---

## Addressing Modes

| Mode | Symbol | Description | Example |
|------|--------|-------------|---------|
| R | Register | Operand in register | `ADD Rd, Rs` |
| IR | Indirect Register | Address in register | `ADD Rd, @Rs` |
| IM | Immediate | Data in instruction | `ADD Rd, #data` |
| DA | Direct Address | Address in instruction | `ADD Rd, address` |
| X | Index | Base address + register | `ADD Rd, addr(Rs)` |
| RA | Relative Address | PC + displacement | `JR cc, address` |
| BA | Base Address | Register + displacement | `LD Rd, Rs(#disp)` |
| BX | Base Index | Register + index register | `LD Rd, Rs(Rx)` |

---

## Encoding Field Legend

| Field | Description |
|-------|-------------|
| `Rddd` | Destination register (R0-R15) |
| `Rsss` | Source register (R0-R15) |
| `Rbdd` | Destination byte register (RL0-RH7) |
| `Rbss` | Source byte register (RL0-RH7) |
| `RRdd` | Destination register pair (RR0-RR14) |
| `RRss` | Source register pair (RR0-RR14) |
| `RQdd` | Destination quad register (RQ0-RQ12) |
| `Rdnz` | Register, non-zero (R1-R15, R0 not allowed) |
| `Rsnz` | Source register, non-zero (R1-R15) |
| `cccc` | Condition code (0-15) |
| `bbbb` | Bit number (0-15 for word, 0-7 for byte) |
| `dddd...` | Displacement/offset bits |
| `xxxx` | Don't care / ignored bits |


---

## Condition Codes

| Code | Mnemonic | Meaning | Flags |
|------|----------|---------|-------|
| 0000 | F | Always False | - |
| 0001 | LT | Less Than | (S XOR V) = 1 |
| 0010 | LE | Less or Equal | (Z OR (S XOR V)) = 1 |
| 0011 | ULE | Unsigned LE | (C OR Z) = 1 |
| 0100 | OV | Overflow | V = 1 |
| 0101 | MI | Minus | S = 1 |
| 0110 | Z/EQ | Zero/Equal | Z = 1 |
| 0111 | C/ULT | Carry/Unsigned LT | C = 1 |
| 1000 | T | Always True | - |
| 1001 | GE | Greater or Equal | (S XOR V) = 0 |
| 1010 | GT | Greater Than | (Z OR (S XOR V)) = 0 |
| 1011 | UGT | Unsigned GT | (C OR Z) = 0 |
| 1100 | NOV | No Overflow | V = 0 |
| 1101 | PL | Plus | S = 0 |
| 1110 | NZ/NE | Not Zero/Not Equal | Z = 0 |
| 1111 | NC/UGE | No Carry/Unsigned GE | C = 0 |

---

## General Column

The **General** column indicates whether the instruction follows the General Instruction Format:
- **1** = Instruction uses General Format (bits 15-14 match expected addressing mode pattern)
- **0** = Instruction uses special/compact format (RA, BA, BX modes, or no addressing mode)

---

## Instruction Reference

### ADC

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `ADC Rd, Rs` | `10110101_Rsss_Rddd` |

### ADCB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `ADCB Rbd, Rbs` | `10110100_Rbss_Rbdd` |

### ADD

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `ADD Rd, Rs` | `10000001_Rsss_Rddd` |
| 1 | IM | `ADD Rd, #data` | `00000001_0000_Rddd + #data` |
| 1 | IR | `ADD Rd, @Rs` | `00000001_Rsnz_Rddd` |
| 1 | DA | `ADD Rd, address` | `01000001_0000_Rddd + address` |
| 1 | X | `ADD Rd, addr(Rs)` | `01000001_Rsnz_Rddd + address` |

### ADDB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `ADDB Rbd, Rbs` | `10000000_Rbss_Rbdd` |
| 1 | IM | `ADDB Rbd, #data` | `00000000_0000_Rbdd + #data | #data` |
| 1 | IR | `ADDB Rbd, @Rs` | `00000000_Rsnz_Rbdd` |
| 1 | DA | `ADDB Rbd, address` | `01000000_0000_Rbdd + address` |
| 1 | X | `ADDB Rbd, addr(Rs)` | `01000000_Rsnz_Rbdd + address` |

### ADDL

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `ADDL RRd, RRs` | `10010110_RRss_RRdd` |
| 1 | IM | `ADDL RRd, #data` | `00010110_0000_RRdd + #data (high) + #data (low)` |
| 1 | IR | `ADDL RRd, @Rs` | `00010110_Rsnz_RRdd` |
| 1 | DA | `ADDL RRd, address` | `01010110_0000_RRdd + address` |
| 1 | X | `ADDL RRd, addr(Rs)` | `01010110_Rsnz_RRdd + address` |

### AND

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `AND Rd, Rs` | `10000111_Rsss_Rddd` |
| 1 | IM | `AND Rd, #data` | `00000111_0000_Rddd + #data` |
| 1 | IR | `AND Rd, @Rs` | `00000111_Rsnz_Rddd` |
| 1 | DA | `AND Rd, address` | `01000111_0000_Rddd + address` |
| 1 | X | `AND Rd, addr(Rs)` | `01000111_Rsnz_Rddd + address` |

### ANDB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `ANDB Rbd, Rbs` | `10000110_Rbss_Rbdd` |
| 1 | IM | `ANDB Rbd, #data` | `00000110_0000_Rbdd + #data | #data` |
| 1 | IR | `ANDB Rbd, @Rs` | `00000110_Rsnz_Rbdd` |
| 1 | DA | `ANDB Rbd, address` | `01000110_0000_Rbdd + address` |
| 1 | X | `ANDB Rbd, addr(Rs)` | `01000110_Rsnz_Rbdd + address` |

### BIT

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `BIT Rd, #b` | `10100111_Rddd_bbbb` |
| 1 | IR | `BIT @Rd, #b` | `00100111_Rdnz_bbbb` |
| 1 | DA | `BIT address, #b` | `01100111_0000_bbbb + address` |
| 1 | X | `BIT addr(Rd), #b` | `01100111_Rdnz_bbbb + address` |
| 0 | R | `BIT Rd, Rs` | `00100111_0000_Rsss + 0000_Rddd_0000_0000` |

### BITB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `BITB Rbd, #b` | `10100110_Rbdd_0bbb` |
| 1 | IR | `BITB @Rd, #b` | `00100110_Rdnz_0bbb` |
| 1 | DA | `BITB address, #b` | `01100110_0000_0bbb + address` |
| 1 | X | `BITB addr(Rd), #b` | `01100110_Rdnz_0bbb + address` |
| 0 | R | `BITB Rbd, Rs` | `00100110_0000_Rsss + 0000_Rbdd_0000_0000` |

### CALL

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `CALL @Rd` | `00011111_Rdnz_0000` |
| 1 | DA | `CALL address` | `01011111_0000_0000 + address` |
| 1 | X | `CALL address(Rd)` | `01011111_Rdnz_0000 + address` |

### CALR

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | RA | `CALR address` | `1101dddd_dddd_dddd` |

### CLR

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `CLR Rd` | `10001101_Rddd_1000` |
| 1 | IR | `CLR @Rd` | `00001101_Rdnz_1000` |
| 1 | DA | `CLR address` | `01001101_0000_1000 + address` |
| 1 | X | `CLR addr(Rd)` | `01001101_Rdnz_1000 + address` |

### CLRB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `CLRB Rbd` | `10001100_Rbdd_1000` |
| 1 | IR | `CLRB @Rd` | `00001100_Rdnz_1000` |
| 1 | DA | `CLRB address` | `01001100_0000_1000 + address` |
| 1 | X | `CLRB addr(Rd)` | `01001100_Rdnz_1000 + address` |

### COM

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `COM Rd` | `10001101_Rddd_0000` |
| 1 | IR | `COM @Rd` | `00001101_Rdnz_0000` |
| 1 | DA | `COM address` | `01001101_0000_0000 + address` |
| 1 | X | `COM addr(Rd)` | `01001101_Rdnz_0000 + address` |

### COMB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `COMB Rbd` | `10001100_Rbdd_0000` |
| 1 | IR | `COMB @Rd` | `00001100_Rdnz_0000` |
| 1 | DA | `COMB address` | `01001100_0000_0000 + address` |
| 1 | X | `COMB addr(Rd)` | `01001100_Rdnz_0000 + address` |

### COMFLG

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | - | `COMFLG flags` | `10001101_CZSV_0101` |

### CP

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `CP Rd, Rs` | `10001011_Rsss_Rddd` |
| 1 | IM | `CP Rd, #data` | `00001011_0000_Rddd + #data` |
| 1 | IR | `CP Rd, @Rs` | `00001011_Rsnz_Rddd` |
| 1 | DA | `CP Rd, address` | `01001011_0000_Rddd + address` |
| 1 | X | `CP Rd, addr(Rs)` | `01001011_Rsnz_Rddd + address` |
| 1 | IR | `CP @Rd, #data` | `00001101_Rdnz_0001 + #data` |
| 1 | DA | `CP address, #data` | `01001101_0000_0001 + address + #data` |
| 1 | X | `CP (addr)Rd, #data` | `01001101_Rdnz_0001 + address + #data` |

### CPB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `CPB Rbd, Rbs` | `10001010_Rbss_Rbdd` |
| 1 | IM | `CPB Rbd, #data` | `00001010_0000_Rbdd + #data | #data` |
| 1 | IR | `CPB Rbd, @Rs` | `00001010_Rsnz_Rbdd` |
| 1 | DA | `CPB Rbd, address` | `01001010_0000_Rbdd + address` |
| 1 | X | `CPB Rbd, addr(Rs)` | `01001010_Rsnz_Rbdd + address` |
| 1 | IR | `CPB @Rd, #data` | `00001100_Rdnz_0001 + #data | #data` |
| 1 | DA | `CPB address, #data` | `01001100_0000_0001 + address + #data | #data` |
| 1 | X | `CPB (addr)Rd, #data` | `01001100_Rdnz_0001 + address + #data | #data` |

### CPD

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | IR | `CPD Rd, @Rs, r, cc` | `10111011_Rsnz_1000 + 0000_Rrrr_Rddd_cccc` |

### CPDB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | IR | `CPDB Rd, @Rs, r, cc` | `10111010_Rsnz_1000 + 0000_Rrrr_Rddd_cccc` |

### CPDR

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | IR | `CPDR Rd, @Rs, r, cc` | `10111011_Rsnz_1100 + 0000_Rrrr_Rddd_cccc` |

### CPDRB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | IR | `CPDRB Rd, @Rs, r, cc` | `10111010_Rsnz_1100 + 0000_Rrrr_Rddd_cccc` |

### CPI

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | IR | `CPI Rd, @Rs, r, cc` | `10111011_Rsnz_0000 + 0000_Rrrr_Rddd_cccc` |

### CPIB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | IR | `CPIB Rd, @Rs, r, cc` | `10111010_Rsnz_0000 + 0000_Rrrr_Rddd_cccc` |

### CPIR

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | IR | `CPIR Rd, @Rs, r, cc` | `10111011_Rsnz_0100 + 0000_Rrrr_Rddd_cccc` |

### CPIRB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | IR | `CPIRB Rd, @Rs, r, cc` | `10111010_Rsnz_0100 + 0000_Rrrr_Rddd_cccc` |

### CPL

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `CPL RRd, RRs` | `10010000_RRss_RRdd` |
| 1 | IM | `CPL RRd, #data` | `00010000_0000_RRdd + #data (high) + #data (low)` |
| 1 | IR | `CPL RRd, @Rs` | `00010000_Rsnz_RRdd` |
| 1 | DA | `CPL RRd, address` | `01010000_0000_RRdd + address` |
| 1 | X | `CPL RRd, addr(Rs)` | `01010000_Rsnz_RRdd + address` |

### CPSD

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | IR | `CPSD @Rd, @Rs, r, cc` | `10111011_Rsnz_1010 + 0000_Rrrr_Rdnz_cccc` |

### CPSDB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | IR | `CPSDB @Rd, @Rs, r, cc` | `10111010_Rsnz_1010 + 0000_Rrrr_Rdnz_cccc` |

### CPSDR

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | IR | `CPSDR @Rd, @Rs, r, cc` | `10111011_Rsnz_1110 + 0000_Rrrr_Rdnz_cccc` |

### CPSDRB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | IR | `CPSDRB @Rd, @Rs, r, cc` | `10111010_Rsnz_1110 + 0000_Rrrr_Rdnz_cccc` |

### CPSI

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | IR | `CPSI @Rd, @Rs, r, cc` | `10111011_Rsnz_0010 + 0000_Rrrr_Rdnz_cccc` |

### CPSIB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | IR | `CPSIB @Rd, @Rs, r, cc` | `10111010_Rsnz_0010 + 0000_Rrrr_Rdnz_cccc` |

### CPSIR

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | IR | `CPSIR @Rd, @Rs, r, cc` | `10111011_Rsnz_0110 + 0000_Rrrr_Rdnz_cccc` |

### CPSIRB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | IR | `CPSIRB @Rd, @Rs, r, cc` | `10111010_Rsnz_0110 + 0000_Rrrr_Rdnz_cccc` |

### DAB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `DAB Rbd` | `10110000_Rbdd_0000` |

### DBJNZ

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | RA | `DBJNZ Rb, address` | `1111Rrrr_0ddd_dddd` |

### DEC

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `DEC Rd, #n` | `10101011_Rddd_nnnn` |
| 1 | IR | `DEC @Rd, #n` | `00101011_Rdnz_nnnn` |
| 1 | DA | `DEC address, #n` | `01101011_0000_nnnn + address` |
| 1 | X | `DEC addr(Rd), #n` | `01101011_Rdnz_nnnn + address` |

### DECB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `DECB Rbd, #n` | `10101010_Rbdd_nnnn` |
| 1 | IR | `DECB @Rd, #n` | `00101010_Rdnz_nnnn` |
| 1 | DA | `DECB address, #n` | `01101010_0000_nnnn + address` |
| 1 | X | `DECB addr(Rd), #n` | `01101010_Rdnz_nnnn + address` |

### DI

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | - | `DI int` | `01111100_0000_00VN` |

### DIV

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| - | R | `DIV RRd, Rs` | `10011011_Rsss_RRdd` |
| - | IM | `DIV RRd, #data` | `00011011_0000_RRdd + #data` |
| - | IR | `DIV RRd, @Rs` | `00011011_Rsnz_RRdd` |
| - | DA | `DIV RRd, address` | `01011011_0000_RRdd + #address` |
| - | X | `DIV RRd, addr(Rs)` | `01011011_Rsnz_RRdd + #address` |

### DIVL

| - | 1R | `DIVL RQd, RRs` | `10011010_RRss_RQdd` |
| - | IM | `DIVL RQd, #data ` | `00011010_0000_RQdd + #data (high) + #data (low)` |
| - | IR | `DIVL RQd, @Rs ` | `00011010_Rsnz_RQdd` |
| - | DA | `DIVL RQd, address ` | `01011010_0000_RQdd + #address` |
| - | X | `DIVL RQd, addr(Rs)` | `01011010_Rsnz_RQdd + #address` |

### DJNZ

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | RA | `DJNZ R, address` | `1111Rrrr_1ddd_dddd` |

### EI

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | - | `EI int` | `01111100_0000_01VN` |

### EPUI

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `EPUI #n` | `10001110_xxxx_01xx` |
| 0 | - | `EPUI` | `10001110_xxxx_01xx` |

### EX

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `EX Rd, Rs` | `10101101_Rsss_Rddd` |
| 1 | IR | `EX Rd, @Rs` | `00101101_Rsnz_Rddd` |
| 1 | DA | `EX Rd, address` | `01101101_0000_Rddd + address` |
| 1 | X | `EX, Rd, addr(Rs)` | `01101101_Rsnz_Rddd + address` |

### EXB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `EXB Rbd, Rbs` | `10101100_Rbss_Rbdd` |
| 1 | IR | `EXB Rbd, @Rs` | `00101100_Rsnz_Rbdd` |
| 1 | DA | `EXB Rbd, address` | `01101100_0000_Rbdd + address` |
| 1 | X | `EXB Rbd, addr(Rs)` | `01101100_Rsnz_Rbdd + address` |

### EXTS

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `EXTS RRd` | `10110001_RRdd_1010` |

### EXTSB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `EXTSB Rd` | `10110001_Rddd_0000` |

### EXTSL

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `EXTSL RQd` | `10110001_RQdd_0111` |



### HALT

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | - | `HALT` | `01111010_0000_0000` |

### IN

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | R | `IN Rd, @Rs` | `00111101_Rsnz_Rddd` |
| 0 | DA | `IN Rd, port` | `00111011_Rddd_0100` |

### INB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | R | `INB Rbd, @Rs` | `00111100_Rsnz_Rbdd` |
| 0 | DA | `INB Rbd, port` | `00111010_Rbdd_0100` |

### INC

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `INC Rd, #n` | `10101001_Rddd_nnnn` |
| 1 | IR | `INC @Rd, #n` | `00101001_Rdnz_nnnn` |
| 1 | DA | `INC address, #n` | `01101001_0000_nnnn + address` |
| 1 | X | `INC addr(Rd), #n` | `01101001_Rdnz_nnnn + address` |

### INCB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `INCB Rbd, #n` | `10101000_Rbdd_nnnn` |
| 1 | IR | `INCB @Rd, #n` | `00101000_Rdnz_nnnn` |
| 1 | DA | `INCB address, #n` | `01101000_0000_nnnn + address` |
| 1 | X | `INCB addr(Rd), #n` | `01101000_Rdnz_nnnn + address` |

### IND

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `IND @Rd, @Rs, r` | `00111011_Rsnz_1000 + 0000_Rrrr_Rdnz_1000` |

### INDB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `INDB @Rd, @Rs, r` | `00111011_Rsnz_1000 + 0000_Rrrr_Rdnz_1000` |

### INDR

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `INDR @Rd, @Rs, r` | `00111011_Rsnz_1000 + 0000_Rrrr_Rdnz_0000` |

### INDRB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `INDRB @Rd, @Rs, r` | `00111011_Rsnz_1000 + 0000_Rrrr_Rdnz_0000` |

### INI

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `INI @Rd, @Rs, r` | `00111011_Rsnz_0000 + 0000_Rrrr_Rdnz_1000` |

### INIB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `INIB @Rd, @Rs, r` | `00111011_Rsnz_0000 + 0000_Rrrr_Rdnz_1000` |

### INIR

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `INIR @Rd, @Rs, r` | `00111011_Rsnz_0000 + 0000_Rrrr_Rdnz_0000` |

### INIRB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `INIRB @Rd, @Rs, r` | `00111011_Rsnz_0000 + 0000_Rrrr_Rdnz_0000` |

### IRET

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | - | `IRET` | `01111011_0000_0000` |

### JP

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | DA | `JP cc, address` | `01011110_0000_cccc + address` |
| 1 | X | `JP cc, address(Rd)` | `01011110_Rdnz_cccc + address` |

### JR

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | RA | `JR cc, address` | `1110cccc_dddd_dddd` |

### LD

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `LD Rd, Rs` | `10100001_Rsss_Rddd` |
| 1 | IR | `LD Rd, @Rs` | `00100001_Rsnz_Rddd` |
| 1 | DA | `LD Rd, address` | `01100001_0000_Rddd + address` |
| 1 | X | `LD Rd, addr(Rs)` | `01100001_Rsnz_Rddd + address` |
| 0 | BA | `LD Rd, Rs(#disp)` | `00110001_Rsnz_Rddd + displacement` |
| 0 | BX | `LD Rd, Rs(Rx)` | `01110001_Rsnz_Rddd + 0000_Rxxx_0000_0000` |
| 1 | IR | `LD @Rd, Rs` | `00101111_Rdnz_Rsss` |
| 1 | DA | `LD address, Rs` | `01101111_0000_Rsss + address` |
| 1 | X | `LD addr(Rd), Rs` | `01101111_Rdnz_Rsss + address` |
| 0 | BA | `LD Rd(#disp), Rs` | `00110011_Rdnz_Rsss + displacement` |
| 0 | BX | `LD Rd(Rx), Rs` | `01110011_Rdnz_Rsss + 0000_Rxxx_0000_0000` |
| 0 | R | `LD Rd, #data` | `00100001_0000_Rddd + #data` |
| 0 | R | `LD Rbd, #data` | `00100000_0000_Rbdd + #data | #data` |
| 1 | IR | `LD @Rd, #data` | `00001101_Rdnz_0101 + #data` |
| 1 | DA | `LD address, Rs` | `01001101_0000_0101 + address + #data` |
| 1 | X | `LD addr(Rd), Rs` | `01001101_Rdnz_0101 + address + #data` |
| 1 | R | `LD Rd, EPU, #n` | `10001111_0xxx_00xx` |
| 1 | IR | `LD @Rd, EPU, #n` | `00001111_Rdnz_11xx` |
| 1 | DA | `LD address, EPU, #n` | `01001111_0000_11xx` |
| 1 | X | `LD addr(Rd), EPU, #n` | `01001111_Rdnz_11xx` |
| 1 | R | `LD EPU, Rs, #n` | `10001111_0xxx_10xx` |
| 1 | IR | `LD EPU, @Rs, #n` | `00001111_Rsnz_01xx` |
| 1 | DA | `LD EPU, address, #n` | `01001111_0000_01xx` |
| 1 | X | `LD EPU, addr(Rs), #n` | `01001111_Rsnz_01xx` |
| 0 | - | `LD @Rd, EPU` | `00001111_Rdnz_11xx` |
| 0 | - | `LD address, EPU` | `01001111_0000_11xx` |
| 0 | - | `LD addr(Rd), EPU` | `01001111_Rdnz_11xx` |
| 0 | - | `LD EPU, @Rs` | `00001111_Rsnz_01xx` |
| 0 | - | `LD EPU, address` | `01001111_0000_01xx` |
| 0 | - | `LD EPU, addr(Rs)` | `01001111_Rsnz_01xx` |
| 0 | - | `LD Rd, EPU` | `10001111_0xxx_00xx` |
| 0 | - | `LD EPU, Rs` | `10001111_0xxx_10xx` |
| 0 | - | `LD FCW, EPU` | `10001110_xxxx_00xx` |
| 0 | - | `LD EPU, FCW` | `10001110_xxxx_10xx` |

### LDA

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | DA | `LDA Rd, address` | `01110110_0000_Rddd + address` |
| 1 | X | `LDA Rd, addr(Rs)` | `01110110_Rsnz_Rddd + address` |
| 0 | BA | `LDA Rd, Rs(#disp)` | `00110100_Rsnz_Rddd + displacement` |
| 0 | BX | `LDA Rd, Rs(Rx)` | `01110100_Rsnz_Rddd + 0000_Rxxx_0000_0000` |

### LDAR

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | RA | `LDAR Rd, address` | `00110100_0000_Rddd + displacement` |

### LDB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `LDB Rbd, Rbs` | `10100000_Rbss_Rbdd` |
| 1 | IR | `LDB Rbd, @Rs` | `00100000_Rsnz_Rbdd` |
| 1 | DA | `LDB Rbd, address` | `01100000_0000_Rbdd + address` |
| 1 | X | `LDB Rbd, addr(Rs)` | `01100000_Rsnz_Rbdd + address` |
| 0 | BA | `LDB Rbd, Rs(#disp)` | `00110000_Rsnz_Rbdd + displacement` |
| 0 | BX | `LDB Rbd, Rs(Rx)` | `01110000_Rsnz_Rddd + 0000_Rxxx_0000_0000` |
| 1 | IR | `LDB @Rd, Rbs` | `00101110_Rdnz_Rbss` |
| 1 | DA | `LDB address, Rbs` | `01101110_0000_Rbss + address` |
| 1 | X | `LDB addr(Rd), Rbs` | `01101110_Rdnz_Rbss + address` |
| 0 | BA | `LDB Rd(#disp), Rbs` | `00110010_Rdnz_Rbss + displacement` |
| 0 | BX | `LDB Rd(Rx), Rbs` | `01110010_Rdnz_Rbss + 0000_Rxxx_0000_0000` |
| 1 | IR | `LDB @Rd, #data` | `00001100_Rdnz_0101 + #data | #data` |
| 1 | DA | `LDB address, Rbs` | `01001100_0000_0101 + address + #data | #data` |
| 1 | X | `LDB addr(Rd), Rbs` | `01001100_Rdnz_0101 + address + #data | #data` |
| 1 | R | `LDB FCW, EPU` | `10001110_xxxx_00xx` |
| 1 | R | `LDB EPU, FCW` | `10001110_xxxx_10xx` |

### LDCTLB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `LDCTLB Rbd, FLAGS` | `10001100_Rbdd_0001` |

### LDCTL

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | R | `LDCTL FCW, Rs` | `01111101_Rsss_1010` |
| 0 | R | `LDCTL REFRESH, Rs` | `01111101_Rsss_1011` |
| 0 | R | `LDCTL NSP, Rs` | `01111101_Rsss_1111` |
| 0 | R | `LDCTL PSAP, Rs` | `01111101_Rsss_1101` |
| 0 | R | `LDCTL Rd, FCW` | `01111101_Rddd_0010` |
| 0 | R | `LDCTL Rd, REFRESH` | `01111101_Rddd_0011` |
| 0 | R | `LDCTL Rd, NSP` | `01111101_Rddd_0111` |
| 0 | R | `LDCTL Rd, PSAP` | `01111101_Rddd_0101` |

### LDCTLB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `LDCTLB FCW, Rbs` | `10001100_Rbss_1001` |

### LDD

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | IR | `LDD @Rd, @Rs, r` | `10111011_Rsnz_1001 + 0000_Rrrr_Rdnz_1000` |

### LDDB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | IR | `LDDB @Rd, @Rs, r` | `10111010_Rsnz_1001 + 0000_Rrrr_Rdnz_1000` |

### LDDR

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | IR | `LDDR @Rd, @Rs, r` | `10111011_Rsnz_1001 + 0000_Rrrr_Rdnz_0000` |

### LDDRB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | IR | `LDDRB @Rd, @Rs, r` | `10111010_Rsnz_1001 + 0000_Rrrr_Rdnz_0000` |

### LDI

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | IR | `LDI @Rd, @Rs, r` | `10111011_Rsnz_0001 + 0000_Rrrr_Rdnz_1000` |

### LDIB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | IR | `LDIB @Rd, @Rs, r` | `10111010_Rsnz_0001 + 0000_Rrrr_Rdnz_1000` |

### LDIR

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | IR | `LDIR @Rd, @Rs, r` | `10111011_Rsnz_0001 + 0000_Rrrr_Rdnz_0000` |

### LDIRB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | IR | `LDIRB @Rd, @Rs, r` | `10111010_Rsnz_0001 + 0000_Rrrr_Rdnz_0000` |

### LDK

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `LDK Rd, #data` | `10111101_Rddd_dddd` |

### LDL

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `LDL RRd, RRs` | `10010100_RRss_RRdd` |
| 1 | IR | `LDL RRd, @Rs` | `00010100_Rsnz_RRdd` |
| 1 | DA | `LDL RRd, address` | `01010100_0000_RRdd + address` |
| 1 | X | `LDL RRd, addr(Rs)` | `01010100_Rsnz_RRdd + address` |
| 0 | BA | `LDL RRd, Rs(#disp)` | `00110101_Rsnz_RRdd + displacement` |
| 0 | BX | `LDL RRd, Rs(Rx)` | `01110101_Rsnz_RRdd + 0000_Rxxx_0000_0000` |
| 1 | IR | `LDL @Rd, RRs` | `00011101_Rdnz_RRss` |
| 1 | DA | `LDL address, RRs` | `01011101_0000_RRss + address` |
| 1 | X | `LDL addr(Rd), RRs` | `01011101_Rdnz_RRss + address` |
| 0 | BA | `LDL Rd(#disp), RRs` | `00110111_Rdnz_RRss + displacement` |
| 0 | BX | `LDL Rd(Rx), RRs` | `01110111_Rdnz_RRss + 0000_Rxxx_0000_0000` |
| 0 | R | `LDL RRd, #data` | `00010100_0000_RRdd + #data (high) + #data (low)` |

### LDM

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `LDM Rd, @Rs, #n` | `00011100_Rsnz_0001 + 0000_Rddd_0000_nnnn` |
| 1 | DA | `LDM Rd, address, #n` | `01011100_0000_0001 + 0000_Rddd_0000_nnnn + address` |
| 1 | X | `LDM Rd, addr(Rs), #n` | `01011100_Rsnz_0001 + 0000_Rddd_0000_nnnn + address` |
| 1 | IR | `LDM @Rd, Rs, #n` | `00011100_Rdnz_1001 + 0000_Rsss_0000_nnnn` |
| 1 | DA | `LDM address, Rs, #n` | `01011100_0000_1001 + 0000_Rsss_0000_nnnn + address` |
| 1 | X | `LDM addr(Rd), Rs, #n` | `01011100_Rdnz_1001 + 0000_Rsss_0000_nnnn + address` |

### LDPS

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `LDPS @Rs` | `00111001_Rsnz_0000` |
| 1 | DA | `LDPS address` | `01111001_0000_0000 + address` |
| 1 | X | `LDPS addr(Rs)` | `01111001_Rsnz_0000 + address` |

### LDR

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | RA | `LDR Rd, address` | `00110001_0000_Rddd + displacement` |
| 0 | RA | `LDR address, Rs` | `00110011_0000_Rsss + displacement` |

### LDRB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | RA | `LDRB Rbd, address` | `00110000_0000_Rbdd + displacement` |
| 0 | RA | `LDRB address, Rbs` | `00110010_0000_Rbss + displacement` |

### LDRL

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | RA | `LDRL RRd, address` | `00110101_0000_RRdd + displacement` |
| 0 | RA | `LDRL address, RRs` | `00110111_0000_RRss + displacement` |

### MBIT

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | - | `MBIT` | `01111011_0000_1010` |

### MREQ

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | - | `MREQ Rd` | `01111011_Rddd_1101` |

### MRES

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | - | `MRES` | `01111011_0000_1001` |

### MSET

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | - | `MSET` | `01111011_0000_1000` |

### MULT

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| - | R | `MULT RRd, Rs` | `10011001_Rsss_RRdd` |
| - | IM | `MULT RRd, #data` | `00011001_0000_RRdd + #data` |
| - | IR | `MULT RRd, @Rs` | `00011001_Rsnz_RRdd` |
| - | DA | `MULT RRd, address` | `01011001_0000_RRdd + #address` |
| - | X | `MULT RRd, addr(Rs)` | `01011001_Rsnz_RRdd + #address` |

### MULTL

| - | 1R | `MULTL RQd, RRs` | `10011000_RRss_RQdd` |
| - | IM | `MULTL RQd, #data ` | `00011000_0000_RQdd + #data (high) + #data (low)` |
| - | IR | `MULTL RQd, @Rs ` | `00011000_Rsnz_RQdd` |
| - | DA | `MULTL RQd, address ` | `01011000_0000_RQdd + #address` |
| - | X | `MULTL RQd, addr(Rs)` | `01011000_Rsnz_RQdd + #address` |

### NEG

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `NEG Rd` | `10001101_Rddd_0010` |
| 1 | IR | `NEG @Rd` | `00001101_Rdnz_0010` |
| 1 | DA | `NEG address` | `01001101_0000_0010 + address` |
| 1 | X | `NEG addr(Rd)` | `01001101_Rdnz_0010 + address` |

### NEGB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `NEGB Rbd` | `10001100_Rbdd_0010` |
| 1 | IR | `NEGB @Rd` | `00001100_Rdnz_0010` |
| 1 | DA | `NEGB address` | `01001100_0000_0010 + address` |
| 1 | X | `NEGB addr(Rd)` | `01001100_Rdnz_0010 + address` |

### NOP

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | - | `NOP` | `10001101_0000_0111` |

### OR

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `OR Rd, Rs` | `10000101_Rsss_Rddd` | 
| 1 | IM | `OR Rd, #data` | `00000101_0000_Rddd + #data` |
| 1 | IR | `OR Rd, @Rs` | `00000101_Rsnz_Rddd` |
| 1 | DA | `OR Rd, address` | `01000101_0000_Rddd + address` |
| 1 | X | `OR Rd, addr(Rs)` | `01000101_Rsnz_Rddd + address` |

### ORB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `ORB Rbd, Rbs` | `10000100_Rbss_Rbdd` |
| 1 | IM | `ORB Rbd, #data` | `00000100_0000_Rbdd + #data | #data` |
| 1 | IR | `ORB Rbd, @Rs` | `00000100_Rsnz_Rbdd` |
| 1 | DA | `ORB Rbd, address` | `01000100_0000_Rbdd + address` |
| 1 | X | `ORB Rbd, addr(Rs)` | `01000100_Rsnz_Rbdd + address` |

### OTDR

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `OTDR @Rd, @Rs, r` | `00111011_Rsnz_1010 + 0000_Rrrr_Rdnz_0000` |

### OTDRB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `OTDRB @Rd, @Rs, r` | `00111010_Rsnz_1010 + 0000_Rrrr_Rdnz_0000` |

### OTIR

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `OTIR @Rd, @Rs, r` | `00111011_Rsnz_0010 + 0000_Rrrr_Rdnz_0000` |

### OTIRB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `OTIRB @Rd, @Rs, r` | `00111010_Rsnz_0010 + 0000_Rrrr_Rdnz_0000` |

### OUT

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | R | `OUT @Rd, Rs` | `00111111_Rdnz_Rsss` |
| 0 | DA | `OUT port, Rst` | `00111011_Rsss_0110` |

### OUTB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | R | `OUTB @Rd, Rbs` | `00111110_Rdnz_Rbss` |
| 0 | DA | `OUTB port, Rbs` | `00111010_Rsss_0110` |

### OUTD

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `OUTD @Rd, @Rs, r` | `00111011_Rsnz_1010 + 0000_Rrrr_Rdnz_1000` |

### OUTDB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `OUTDB @Rd, @Rs, r` | `00111010_Rsnz_1010 + 0000_Rrrr_Rdnz_1000` |

### OUTI

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `OUTI @Rd, @Rs, r` | `00111011_Rsnz_0010 + 0000_Rrrr_Rdnz_1000` |

### OUTIB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `OUTIB @Rd, @Rs, r` | `00111010_Rsnz_0010 + 0000_Rrrr_Rdnz_1000` |

### POP

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `POP Rd, @Rs` | `10010111_Rsnz_Rddd` |
| 1 | IR | `POP @Rd, @Rs` | `00010111_Rsnz_Rdnz` |
| 1 | DA | `POP address, @Rs` | `01010111_Rsnz_0000 + address` |
| 1 | X | `POP addr(Rd), @Rs` | `01010111_Rsnz_Rdnz + address` |

### POPL

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `POPL RRd, @Rs` | `10010101_Rsnz_RRdd` |
| 1 | IR | `POPL @Rd, @Rs` | `00010101_Rsnz_Rdnz` |
| 1 | DA | `POPL address, @Rs` | `01010101_Rsnz_0000 + address` |
| 1 | X | `POPL addr(Rd), @Rs` | `01010101_Rsnz_Rdnz + address` |

### PUSH

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `PUSH @Rd, Rs` | `10010011_Rdnz_Rsss` |
| 1 | IM | `PUSH @Rd, #data` | `00001101_Rdnz_1001 + #data` |
| 1 | IR | `PUSH @Rd, @Rs` | `00010011_Rdnz_Rsnz` |
| 1 | DA | `PUSH @Rd, address` | `01010011_Rdnz_0000 + address` |
| 1 | X | `PUSH @Rd, addr(Rs)` | `01010011_Rdnz_Rsnz + address` |

### PUSHL

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `PUSHL @Rd, RRs` | `10010001_Rdnz_RRss` |
| 1 | IR | `PUSHL @Rd, @Rs` | `00010001_Rdnz_Rsnz` |
| 1 | DA | `PUSHL @Rd, address` | `01010001_Rdnz_0000 + address` |
| 1 | X | `PUSHL @Rd, addr(Rs)` | `01010001_Rdnz_Rsnz + address` |

### RES

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `RES Rd, #b` | `10100011_Rddd_bbbb` |
| 1 | IR | `RES @Rd, #b` | `00100011_Rdnz_bbbb` |
| 1 | DA | `RES address, #b` | `01100011_0000_bbbb + address` |
| 1 | X | `RES addr(Rd), #b` | `01100011_Rdnz_bbbb + address` |
| 0 | R | `RES Rd, Rs` | `00100011_0000_Rsss + 0000_Rddd_0000_0000` |

### RESB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `RESB Rbd, #b` | `10100010_Rbdd_0bbb` |
| 1 | IR | `RESB @Rd, #b` | `00100010_Rdnz_0bbb` |
| 1 | DA | `RESB address, #b` | `01100010_0000_0bbb + address` |
| 1 | X | `RESB addr(Rd), #b` | `01100010_Rdnz_0bbb + address` |
| 0 | R | `RESB Rbd, Rs` | `00100010_0000_Rsss + 0000_Rbdd_0000_0000` |

### RESFLG

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | - | `RESFLG flags` | `10001101_CZSV_0011` |

### RET

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | - | `RET` | `10011110_0000_cccc` |

### RL

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `RL Rd, #1` | `10110011_Rddd_0000` |
| 1 | R | `RL Rd, #2` | `10110011_Rddd_0010` |

### RLB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `RLB Rbd, #1` | `10110010_Rbdd_0000` |
| 1 | R | `RLB Rbd, #2` | `10110010_Rbdd_0010` |

### RLC

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `RLC Rd, #1` | `10110011_Rddd_1000` |
| 1 | R | `RLC Rd, #2` | `10110011_Rddd_1010` |

### RLCB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `RLCB Rbd, #1` | `10110010_Rbdd_1000` |
| 1 | R | `RLCB Rbd, #2` | `10110010_Rbdd_1010` |

### RLDB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `RLDB Rbd, Rbs` | `10111110_Rbss_Rbdd` |

### RR

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `RR Rd, #1` | `10110011_Rddd_0100` |
| 1 | R | `RR Rd, #2` | `10110011_Rddd_0110` |

### RRB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `RRB Rbd, #1` | `10110010_Rbdd_0100` |
| 1 | R | `RRB Rbd, #2` | `10110010_Rbdd_0110` |

### RRC

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `RRC Rd, #1` | `10110011_Rddd_1100` |
| 1 | R | `RRC Rd, #2` | `10110011_Rddd_1110` |

### RRCB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `RRCB Rbd, #1` | `10110010_Rbdd_1100` |
| 1 | R | `RRCB Rbd, #2` | `10110010_Rbdd_1110` |

### RRDB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `RRDB Rbd, Rbs` | `10111100_Rbss_Rbdd` |

### SBC

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `SBC Rd, Rs` | `10110111_Rsss_Rddd` |

### SBCB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `SBCB Rbd, Rbs` | `10110110_Rbss_Rbdd` |

### SC

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | IM | `SC #src` | `01111111_ssssrccc` |

### SDA

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `SDA Rd, Rs` | `10110011_Rddd_1011 + 0000_Rsss_0000_0000` |

### SDAB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `SDAB Rbd, Rs` | `10110010_Rbdd_1011 + 0000_Rsss_0000_0000` |

### SDAL

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `SDAL RRd, Rs` | `10110011_RRdd_1111 + 0000_Rsss_0000_0000` |

### SDL

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `SDL Rd, Rs` | `10110011_Rddd_0011 + 0000_Rsss_0000_0000` |

### SDLB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `SDLB Rbd, Rs` | `10110010_Rbdd_0011 + 0000_Rsss_0000_0000` |

### SDLL

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `SDLL RRd, Rs` | `10110011_RRdd_0111 + 0000_Rsss_0000_0000` |

### SET

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `SET Rd, #b` | `10100101_Rddd_bbbb` |
| 1 | IR | `SET @Rd, #b` | `00100101_Rdnz_bbbb` |
| 1 | DA | `SET address, #b` | `01100101_0000_bbbb + address` |
| 1 | X | `SET addr(Rd), #b` | `01100101_Rdnz_bbbb + address` |
| 0 | R | `SET Rd, Rs` | `00100101_0000_Rsss + 0000_Rddd_0000_0000` |

### SETB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `SETB Rbd, #b` | `10100100_Rbdd_0bbb` |
| 1 | IR | `SETB @Rd, #b` | `00100100_Rdnz_0bbb` |
| 1 | DA | `SETB address, #b` | `01100100_0000_0bbb + address` |
| 1 | X | `SETB addr(Rd), #b` | `01100100_Rdnz_0bbb + address` |
| 0 | R | `SETB Rbd, Rs` | `00100100_0000_Rsss + 0000_Rbdd_0000_0000` |

### SETFLG

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | - | `SETFLG flags` | `10001101_CZSV_0001` |

### SIN

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | DA | `SIN Rd, port` | `00111011_Rddd_0101` |

### SINB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | DA | `SINB Rbd, port` | `00111010_Rbdd_0101` |

### SIND

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `SIND @Rd, @Rs, r` | `00111011_Rsnz_1001 + 0000_Rrrr_Rdnz_1000` |

### SINDB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `SINDB @Rd, @Rs, r` | `00111010_Rsnz_1001 + 0000_Rrrr_Rdnz_1000` |

### SINDR

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `SINDR @Rd, @Rs, r` | `00111011_Rsnz_1001 + 0000_Rrrr_Rdnz_0000` |

### SINDRB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `SINDRB @Rd, @Rs, r` | `00111010_Rsnz_1001 + 0000_Rrrr_Rdnz_0000` |

### SINI

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `SINI @Rd, @Rs, r` | `00111011_Rsnz_0001 + 0000_Rrrr_Rdnz_1000` |

### SINIB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `SINIB @Rd, @Rs, r` | `00111010_Rsnz_0001 + 0000_Rrrr_Rdnz_1000` |

### SINIR

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `SINIR @Rd, @Rs, r` | `00111011_Rsnz_0001 + 0000_Rrrr_Rdnz_0000` |

### SINIRB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `SINIRB @Rd, @Rs, r` | `00111010_Rsnz_0001 + 0000_Rrrr_Rdnz_0000` |

### SLA

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `SLA Rd, #b` | `10110011_Rddd_1001 + bbbbbbbb` |

### SLAB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `SLAB Rbd, #b` | `10110010_Rbdd_1001 + 0000_bbbb` |

### SLAL

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `SLAL RRd, #b` | `10110011_RRdd_1101 + bbbbbbbb` |

### SLL

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `SLL Rd, #b` | `10110011_Rddd_0001 + bbbbbbbb` |

### SLLB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `SLLB Rbd, #b` | `10110010_Rbdd_0001 + 0000_bbbb` |

### SLLL

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `SLLL RRd, #b` | `10110011_RRdd_0101 + bbbbbbbb` |

### SOTDR

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `SOTDR @Rd, @Rs, r` | `00111011_Rsnz_1011 + 0000_Rrrr_Rdnz_0000` |

### SOTDRB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `SOTDRB @Rd, @Rs, r` | `00111010_Rsnz_1011 + 0000_Rrrr_Rdnz_0000` |

### SOTIR

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `SOTIR @Rd, @Rs, r` | `00111011_Rsnz_0011 + 0000_Rrrr_Rdnz_0000` |

### SOTIRB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `SOTIRB @Rd, @Rs, r` | `00111010_Rsnz_0011 + 0000_Rrrr_Rdnz_0000` |

### SOUT

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | DA | `SOUT port, Rst` | `00111011_Rsss_0111` |

### SOUTB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | DA | `SOUTB port, Rbs` | `00111010_Rsss_0111` |

### SOUTD

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `SOUTD @Rd, @Rs, r` | `00111011_Rsnz_1011 + 0000_Rrrr_Rdnz_1000` |

### SOUTDB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `SOUTDB @Rd, @Rs, r` | `00111010_Rsnz_1011 + 0000_Rrrr_Rdnz_1000` |

### SOUTI

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `SOUTI @Rd, @Rs, r` | `00111011_Rsnz_0011 + 0000_Rrrr_Rdnz_1000` |

### SOUTIB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | IR | `SOUTIB @Rd, @Rs, r` | `00111010_Rsnz_0011 + 0000_Rrrr_Rdnz_1000` |

### SRA

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `SRA Rd, #b` | `10110011_Rddd_1001 + bbbbbbbb` |

### SRAB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `SRAB Rbd, #b` | `10110010_Rbdd_1001 + 0000_bbbb` |

### SRAL

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `SRAL RRd, #b` | `10110011_RRdd_1101 + bbbbbbbb` |

### SRL

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `SRL Rd, #b` | `10110011_Rddd_0001 + bbbbbbbb` |

### SRLB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `SRLB Rbd, #b` | `10110010_Rbdd_0001 + 0000_bbbb` |

### SRLL

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `SRLL RRd, #b` | `10110011_RRdd_0101 + bbbbbbbb` |

### SUB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `SUB Rd, Rs` | `10000011_Rsss_Rddd` |
| 1 | IM | `SUB Rd, #data` | `00000011_0000_Rddd + #data` |
| 1 | IR | `SUB Rd, @Rs` | `00000011_Rsnz_Rddd` |
| 1 | DA | `SUB Rd, address` | `01000011_0000_Rddd + address` |
| 1 | X | `SUB Rd, addr(Rs)` | `01000011_Rsnz_Rddd + address` |

### SUBB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `SUBB Rbd, Rbs` | `10000010_Rbss_Rbdd` |
| 1 | IM | `SUBB Rbd, #data` | `00000010_0000_Rbdd + #data | #data` |
| 1 | IR | `SUBB Rbd, @Rs` | `00000010_Rsnz_Rbdd` |
| 1 | DA | `SUBB Rbd, address` | `01000010_0000_Rbdd + address` |
| 1 | X | `SUBB Rbd, addr(Rs)` | `01000010_Rsnz_Rbdd + address` |

### SUBL

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `SUBL RRd, RRs` | `10010010_RRss_RRdd` |
| 1 | IM | `SUBL RRd, #data` | `00010010_0000_RRdd + #data (high) + #data (low)` |
| 1 | IR | `SUBL RRd, @Rs` | `00010010_Rsnz_RRdd` |
| 1 | DA | `SUBL RRd, address` | `01010010_0000_RRdd + address` |
| 1 | X | `SUBL RRd, addr(Rs)` | `01010010_Rsnz_RRdd + address` |

### TCC

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `TCC cc, Rd` | `10101111_Rddd_cccc` |

### TCCB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `TCCB cc, Rbd` | `10101110_Rbdd_cccc` |

### TEST

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `TEST Rd` | `10001101_Rddd_0100` |
| 1 | IR | `TEST @Rd` | `00001101_Rdnz_0100` |
| 1 | DA | `TEST address` | `01001101_0000_0100 + address` |
| 1 | X | `TEST addr(Rd)` | `01001101_Rdnz_0100 + address` |

### TESTB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `TESTB Rbd` | `10001100_Rbdd_0100` |
| 1 | IR | `TESTB @Rd` | `00001100_Rdnz_0100` |
| 1 | DA | `TESTB address` | `01001100_0000_0100 + address` |
| 1 | X | `TESTB addr(Rd)` | `01001100_Rdnz_0100 + address` |

### TESTL

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `TESTL RRd` | `10011100_RRdd_1000` |
| 1 | IR | `TESTL @Rd` | `00011100_Rdnz_1000` |
| 1 | DA | `TESTL address` | `01011100_0000_1000 + address` |
| 1 | X | `TESTL addr(Rd)` | `01011100_Rddd_1000 + address` |

### TRDB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | IR | `TRDB @Rd, @Rs, r` | `10111000_Rdnz_1000 + 0000_Rrrr_Rsnz_0000` |

### TRDRB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | IR | `TRDRB @Rd, @Rs, r` | `10111000_Rdnz_1100 + 0000_Rrrr_Rsnz_0000` |

### TRIB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | IR | `TRIB @Rd, @Rs, r` | `10111000_Rdnz_0000 + 0000_Rrrr_Rsnz_0000` |

### TRIRB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | IR | `TRIRB @Rd, @Rs, r` | `10111000_Rdnz_0100 + 0000_Rrrr_Rsnz_0000` |

### TRTDB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | IR | `TRTDB @Rs1, @Rs2, r` | `10111000_R1nz_1010 + 0000_Rrrr_R2nz_0000` |

### TRTDRB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | IR | `TRTDRB @Rs1, @Rs2, r` | `10111000_R1nz_1110 + 0000_Rrrr_R2nz_1110` |

### TRTIB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | IR | `TRTIB @Rs1, @Rs2, r` | `10111000_R1nz_0010 + 0000_Rrrr_R2nz_0000` |

### TRTIRB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 0 | IR | `TRTIRB @Rs1, @Rs2, r` | `10111000_R1nz_0110 + 0000_Rrrr_R2nz_1110` |

### TSET

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `TSET Rd` | `10001101_Rddd_0110` |
| 1 | IR | `TSET @Rd` | `00001101_Rdnz_0110` |
| 1 | DA | `TSET address` | `01001101_0000_0110 + address` |
| 1 | X | `TSET addr(Rd)` | `01001101_Rdnz_0110 + address` |

### TSETB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `TSETB Rbd` | `10001100_Rbdd_0110` |
| 1 | IR | `TSETB @Rd` | `00001100_Rdnz_0110` |
| 1 | DA | `TSETB address` | `01001100_0000_0110 + address` |
| 1 | X | `TSETB addr(Rd)` | `01001100_Rdnz_0110 + address` |

### XOR

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `XOR Rd, Rs` | `10001001_Rsss_Rddd` |
| 1 | IM | `XOR Rd, #data` | `00001001_0000_Rddd + #data` |
| 1 | IR | `XOR Rd, @Rs` | `00001001_Rsnz_Rddd` |
| 1 | DA | `XOR Rd, address` | `01001001_0000_Rddd + address` |
| 1 | X | `XOR Rd, addr(Rs)` | `01001001_Rsnz_Rddd + address` |

### XORB

| General | Mode | Syntax | Encoding |
|---------|------|--------|----------|
| 1 | R | `XORB Rbd, Rbs` | `10001000_Rbss_Rbdd` |
| 1 | IM | `XORB Rbd, #data` | `00001000_0000_Rddd + #data | #data` |
| 1 | IR | `XORB Rbd, @Rs` | `00001000_Rsnz_Rbdd` |
| 1 | DA | `XORB Rbd, address` | `01001000_0000_Rbdd + address` |
| 1 | X | `XORB Rbd, addr(Rs)` | `01001000_Rsnz_Rbdd + address` |

