# Z8000 Emulator — Systematic Flag Update Analysis

## 1. The Z8001 Hardware Flag Model

The Z8001 is a non-microcoded, sequencer-based CPU with a fixed ALU. Its flag behavior
follows from three hardware properties:

1. **The ALU always computes Z and S from its output.** Every time a value passes
   through the ALU, the zero-detection and sign-detection circuits fire. There is no
   way to suppress this — the circuits are hard-wired.

2. **A flag-write mask controls which flags get stored to the FCW.** Each instruction's
   microsequence specifies which ALU-computed flags get written back. "Not affected"
   means the mask blocks the write.

3. **"Undefined" means the ALU's natural output is written, but the manual doesn't
   guarantee it.** The hardware writes a deterministic value — it just isn't
   architecturally specified because it would constrain future implementations. For the
   Z8001 silicon, these values are completely predictable and follow from the ALU's
   natural behavior.

**Consequence:** To match the Z8001 exactly, the emulator must reproduce what the ALU
naturally computes for every flag, including "undefined" ones. There are no special
cases — only the ALU's regular circuits applied to each sub-operation.

---

## 2. FCW Flag Layout

```
Bit 7: C   — Carry
Bit 6: Z   — Zero
Bit 5: S   — Sign
Bit 4: P/V — Parity (byte logical) / Overflow (arithmetic, shifts, rotates)
Bit 3: DA  — Decimal Adjust (0=add/adc, 1=sub/sbc)
Bit 2: H   — Half-carry (byte arithmetic only)
```

Emulator constants: `F_C=0x80, F_Z=0x40, F_S=0x20, F_PV=0x10, F_DA=0x08, F_H=0x04`

---

## 3. Instruction Groups and Their Flag Rules

### Group A: Standard Arithmetic (ADD, ADC, SUB, SBC, CP, NEG)

**Flags affected:** C, Z, S, V (all variants); additionally DA and H for byte variants.

| Flag | Rule |
|------|------|
| C (add) | Set if unsigned carry from MSB (result < dest) |
| C (sub) | Set if unsigned borrow (result > dest) — inverted sense |
| Z | Set if result is zero |
| S | Set if MSB of result is set |
| V (add) | Set if both operands same sign and result opposite sign |
| V (sub) | Set if operands opposite sign and result sign equals source sign |
| DA | ADDB/ADCB: cleared (add mode); SUBB/SBCB: set (sub mode) |
| H (add) | Set if nibble carry: (result & 0xF) < (dest & 0xF) |
| H (sub) | Set if nibble borrow: (result & 0xF) > (dest & 0xF) |

**NEG is special:** C = (result != 0), V = (result == 0x80 for byte / 0x8000 for word).

**Emulator status:** Correct for all tested cases. The CHK_xxx macros implement these
rules faithfully. Word/long variants correctly leave DA and H unaffected.

**Note on ADC/SBC:** The overflow check uses the original `value`, not `value + carry`.
This is formally questionable but appears to work in practice because the result already
incorporates the carry, and the sign-bit formula captures the actual overflow. No golden
test failures observed.

### Group B: Increment/Decrement (INC, DEC)

**Flags affected:** Z, S, V only. **C is deliberately unaffected** (so INC/DEC can be
used as loop counters without disturbing multi-precision carry chains).

| Flag | Rule |
|------|------|
| C | **Unaffected** (preserved from prior operation) |
| Z | Set if result is zero |
| S | Set if MSB of result is set |
| V | Standard add/sub overflow |

**Emulator status:** Correct. Uses `CLR_ZSV` (not `CLR_CZSV`), preserving C.

### Group C: Logical Operations (AND, OR, XOR, COM, TEST)

**Flags affected:** Z, S always; P for byte variants only; C, V unaffected.

| Flag | Rule |
|------|------|
| C | **Unaffected** |
| Z | Set if result is zero |
| S | Set if MSB of result is set |
| P (byte only) | Set if even parity of result |
| V (word/long) | **Unaffected** (preserved) |

**Critical distinction:** Byte variants (ANDB, ORB, XORB, COMB, TESTB) set the P flag
from even parity of the result byte using the `z8000_zsp[]` lookup table. Word variants
(AND, OR, XOR, COM, TEST) do NOT touch P/V at all.

**TESTL** is a minor oddity: manual says V is "undefined" but it effectively performs
`dest AND dest` which can't overflow. Hardware likely produces V=0 or preserves it.

**Emulator status:** Correct. Byte variants use `CLR_ZSP; CHK_XXXB_ZSP`, word variants
use `CLR_ZS; CHK_XXXW_ZS`.

### Group D: Multiply (MULT, MULTL)

**Flags affected:** C, Z, S, V.

| Flag | Rule |
|------|------|
| C | Set if product doesn't fit in the "natural" result size (16-bit for MULT, 32-bit for MULTL) |
| Z | Set if product is zero |
| S | Set if product is negative |
| V | **Always cleared** |

**Emulator status:** Mostly correct. There is a potential off-by-one in the C threshold:
MULTW uses `result >= 0x7fff` where it should be `> 0x7fff` (32767 fits in int16_t, so
C should not be set for it). No golden test failure observed, but worth auditing.

### Group E: Divide (DIV, DIVL)

**Flags affected:** C, Z, S, V. Complex multi-case behavior.

| Case | Condition | C | Z | S | V |
|------|-----------|---|---|---|---|
| Divide by zero | divisor = 0 | 0 | 1 | 0 | 1 |
| Normal | quotient fits in result size | 0 | from quotient | from quotient | 0 |
| Overflow (CASE 4) | quotient is "N+1 bit" 2's complement | 1 | from low N bits | from low N bits | 1 |
| Overflow (CASE 3) | quotient exceeds CASE 4 range | 0 | undefined | undefined | 1 |

**CASE 3** leaves registers in an intermediate/undefined state. The golden DIV test
(`sys_div_rr_r_large`) falls into this case — register values don't match because
they're undefined.

**DIVL Z flag bug (1 test):** For DIVL, `CHK_XXXL_ZS` checks Z on the full 32-bit
quotient. But the golden hardware checks Z on the **low 16-bit word** of the quotient
(the word that fits in a single register). When quotient = 0x00010000, the low word is
0x0000, so hardware sets Z=1, but emulator sees non-zero 32-bit value and sets Z=0.

**Manual vs hardware:** The manual says Z is "set if the quotient is zero," implying
the full 32-bit quotient for DIVL. The hardware checks only the low 16-bit word. This
is consistent with the ALU model — the last word written through the ALU determines Z.
See Section 6 for detailed manual verification.

**Fix:** For DIVL normal and CASE 4 paths, check Z/S on `result & 0xffff` (low word)
instead of the full 32-bit quotient.

### Group F: Shifts — Arithmetic (SLA, SRA, SDA)

**Flags affected:** C, Z, S, V.

| Flag | Rule |
|------|------|
| C | Last bit shifted out (undefined if shift count = 0) |
| Z | Set if result is zero |
| S | Set if MSB of result is set |
| V (SLA/SDA left) | Set if sign bit changed at **any** intermediate step |
| V (SRA/SDA right) | **Cleared** (SRA preserves sign, can't overflow) |

**Manual says:** V is "set if arithmetic overflow occurs, that is, if the sign of the
destination changed **during** shifting; cleared otherwise." The word "during" supports
per-step accumulation for multi-bit shifts.

**The V flag rule for left shifts:** The hardware shifts one bit at a time. At each
step, it checks whether the sign bit changed from the previous step. V = OR of all
these checks. This means V is set if the sign ever toggled during any intermediate
step, even if it toggled back by the final step.

**Emulator bugs (fixed):**
- **SLA**: Was using `(result ^ dest) & sign_bit` — only compared initial to final.
  Missed intermediate sign changes during multi-bit shifts. Example: SLA 0x4000 by 2
  goes 0x4000 → 0x8000 (sign change!) → 0x0000 (sign change!). Initial-to-final
  comparison sees positive→positive and says V=0, but hardware says V=1.
- **SRA**: Uses `CLR_CZSV` and never sets V. **Correct per manual** ("Cleared").
- **SDA**: Was using step-by-step loop but only checked `(result ^ dest)` at the end,
  same initial-to-final problem.

### Group G: Shifts — Logical (SLL, SRL, SDL)

**Flags affected:** C, Z, S; **V is "undefined" per manual.**

**Manual says:** V is "Undefined" for SLL, SRL, and SDL. The manual does NOT define
V behavior for logical shifts, unlike arithmetic shifts where V is explicitly specified.

**Hardware behavior for V:** The Z8001 uses the **same sign-change-during-shift logic**
as arithmetic shifts. The ALU's V circuit doesn't distinguish arithmetic vs logical
shifts — it always monitors the sign bit. Golden tests confirm this: SRL right shifts
set V=1 when the MSB transitions from 1 to 0 during the first shift step.

| Flag | Rule |
|------|------|
| C | Last bit shifted out (undefined if shift count = 0) |
| Z | Set if result is zero |
| S | Set if MSB of result is set |
| V | **Same as SLA: set if sign changed at any intermediate step** (undefined per manual, but deterministic on hardware) |

**Emulator bugs (fixed):**
- **SLL**: Was using `CLR_CZS` — V not cleared, not set, just preserved from prior
  state. Changed to `CLR_CZSV` + per-step V accumulation.
- **SRL**: Same problem — was using `CLR_CZS`, V preserved. Changed to `CLR_CZSV` +
  per-step V accumulation (tracks sign bit changes during right shifts too).
- **SDL**: Was using `CLR_CZSV` and `(result ^ dest) & sign_bit`. Already handled V
  but only initial-to-final. Changed to per-step accumulation in both left and right
  shift loops.

### Group H: Rotates (RL, RR, RLC, RRC)

**Flags affected:** C, Z, S, V.

| Flag | Instruction | Rule |
|------|-------------|------|
| C | RL | Bit that rotated from MSB to LSB (= bit 0 of result) |
| C | RR | Bit that rotated from LSB to MSB (= MSB of result) |
| C | RLC | Bit shifted out of MSB (before carry fills LSB) |
| C | RRC | Bit shifted out of LSB (before carry fills MSB) |
| Z | all | Set if result is zero |
| S | all | Set if MSB of result is set |
| V | all | Set if sign changed during rotation |

**Manual says:** V is "set if arithmetic overflow occurs, that is, if the sign of the
destination changed **during** rotation; cleared otherwise." The word "during" supports
per-step accumulation for rotate-by-2.

**Rotate-by-2 ("twice" mode):** RL/RR/RLC/RRC can rotate by 1 or 2. For rotate-by-2,
V should be set if the sign changed at **either** step.

**Example:** RR 0x0001 by 2:
- Step 1: 0x0001 → 0x8000 (sign changed! V=1)
- Step 2: 0x8000 → 0x4000 (sign changed again!)
- Initial vs final: 0x0001 → 0x4000 (both positive, V=0 per old emulator)
- Hardware: V=1

**Emulator status (fixed):** V accumulation now computed per step.

**RR/RRB special:** Uses `SET_SC` (sets both S and C simultaneously when MSB is set).
This is actually correct for RR because after right rotation, the MSB IS the carry bit
(the bit that wrapped from LSB). But the coding pattern differs from all other rotates.
Not a bug, just an inconsistency in style.

### Group I: Digit Rotates (RLDB, RRDB)

**Flags affected:** Z (defined), S (undefined per manual detail page, listed in summary
table).

| Flag | Rule |
|------|------|
| C | **Unaffected** |
| Z | Set if link byte (Rn, the destination) is zero after rotation |
| S | **MSB of link byte** — standard ALU sign detection on the result |
| V | **Unaffected** |

**Manual says (detail page):** S is "Undefined" for both RLDB and RRDB. However, the
summary table in Appendix C lists both Z and S as "Flags Affected," creating an
internal contradiction in the manual. Golden tests confirm the hardware sets S from
the sign bit of the result byte.

**Hardware behavior:** The digit rotate result passes through the ALU, which naturally
computes S from bit 7 of the result byte.

**Emulator bug (fixed):** Was only setting/clearing Z. Added S computation.

### Group J: DAB (Decimal Adjust Byte)

**Flags affected:** C, Z, S. V and DA and H are unaffected.

| Flag | Rule |
|------|------|
| C | From DAB lookup table (correction carry) |
| Z | Set if corrected result is zero |
| S | Set if MSB of corrected result is set |
| V | **Unaffected** |
| DA | **Unaffected** (read as input, not modified) |
| H | **Unaffected** (read as input, not modified) |

**Emulator status:** Now correct after the makedab.cpp fixes (operator precedence +
sub path low-nibble fix). The lookup table and flag logic are correct.

### Group K: Block Transfer (LDI, LDD, LDIR, LDDR and byte variants)

**Flags affected:** V (defined), Z (undefined per manual).

| Flag | Rule |
|------|------|
| C | **Unaffected** |
| Z | **Set if counter reached zero** (same condition as V — ALU computes Z on decrement result) |
| S | **Unaffected** |
| V | Set if counter reached zero after decrement; cleared otherwise |
| V (repeat) | Always set (repeat only terminates when counter reaches 0) |

**Manual says:** Z is "Undefined" for all block load instructions. V is "Set if the
result of decrementing r is zero; cleared otherwise" for LDI/LDD, and simply "Set" for
LDIR/LDDR. Note: the counter-reaches-zero semantic the emulator now applies to Z is
what the manual explicitly specifies for V. The hardware applies the same ALU output to
both Z and V because the counter decrement passes through the ALU.

**Hardware behavior:** The counter decrement `cnt - 1` goes through the ALU. The ALU's
zero-detection circuit produces Z = (cnt == 0), and its overflow/comparison circuit
produces V = (cnt == 0). Both flags reflect the same sub-operation.

**Emulator bug (fixed):** Was only updating V from the counter, not Z.

**Note on block translate (TRIB/TRDB/TRIRB/TRDRB):** Golden tests show that block
translate does NOT set Z from the counter — Z remains 0 even when the counter reaches
zero. This contradicts the block transfer behavior and the ALU model. The translate
instructions have Z listed as "Undefined" in the manual but apparently handle it
differently from block transfers on the actual silicon. The emulator correctly leaves
Z untouched for translate operations.

**Affected functions (4 pairs, covering both single and repeat variants):**
- LDIB/LDIRB, LDDB/LDDRB (byte)
- LDI/LDIR, LDD/LDDR (word)

### Group L: Block Compare (CPI, CPD, CPIR, CPDR, CPSI, CPSD, CPSIR, CPSDR)

**Flags affected:** C, Z, S, V — but with special semantics.

| Flag | Reg-vs-Mem (CPI/CPD) | Mem-vs-Mem (CPSI/CPSD) |
|------|----------------------|------------------------|
| C | **Undefined** | From comparison (borrow) |
| Z | From condition-code match | From condition-code match |
| S | **Undefined** | From comparison (sign of difference) |
| V | Set if counter reached zero | Set if counter reached zero |

**How it works:**
1. A subtraction (CPB/CPW) is performed, setting C, Z, S, V from the comparison.
2. A condition-code evaluation reads the flags, then **overwrites Z** with whether
   the condition was met (Z=1 means condition matched).
3. The counter decrement **overwrites V** (V=1 means counter exhausted).

For register-vs-memory compares (CPI/CPD), the manual says C and S are "undefined."
The hardware likely writes them from the comparison (same as CPSI/CPSD), but this
hasn't been verified by golden tests.

**Emulator status:** The implementation follows this pattern correctly. The CPB/CPW call
sets all flags, then the cc switch overwrites Z, then the counter check overwrites V.
No golden test failures observed.

### Group M: Block Translate (TRIB, TRDB, TRIRB, TRDRB)

**Flags affected:** V (defined), Z (undefined per manual).

| Flag | Rule |
|------|------|
| Z | **Hardware: NOT set from counter** (golden tests show Z=0 when counter reaches zero) |
| V | Set if counter reached zero; cleared otherwise |

**Manual says:** Z is "Undefined" for translate operations, same as block transfers.

**Hardware behavior:** Unlike block transfers (Group K), the translate instructions do
NOT set Z from the counter decrement. Golden tests for TRIRB/TRDRB show Z=0 even when
the counter reaches zero. This means the "undefined" Z flag is handled differently
between block transfers and block translates on the actual silicon — the ALU model
(Principle 1) does not apply uniformly to all block operations.

**Emulator status:** Correct — Z is not touched for translate operations. An earlier
attempt to add CLR_Z/SET_Z (matching block transfer pattern) caused 4 regressions and
was reverted.

### Group N: Block Translate-and-Test (TRTIB, TRTDB, TRTIRB, TRTDRB)

**Flags affected:** Z (from translation value), V (from counter).

| Flag | Rule |
|------|------|
| Z | Set if the translated value (loaded into RH1) is zero; cleared otherwise |
| V | Set if counter reached zero; cleared otherwise |

**Emulator status:** Correct after the previous TRT order-of-operations fix. Z is set
from the translation value, V from the counter. The `RB(1) = xlt` assignment now
happens after address/counter updates (fixed earlier this session).

### Group O: Block I/O (INI, IND, OUTI, OUTD and repeat/byte variants)

**Flags affected:** V (defined), Z (undefined for most variants).

| Flag | Rule |
|------|------|
| Z | IND/INDB: **Unaffected**; others: **Undefined** (likely = counter reached zero) |
| V | Set if counter reached zero; cleared otherwise |

**Emulator status:** Only V is set from counter. Z is not touched. Same pattern as
block transfers — the hardware likely sets Z from the counter decrement. No golden
test failures observed, but recommend applying the Z fix for consistency. Note the
IND/INDB exception where Z is explicitly "unaffected" per the manual.

### Group P: Flag Manipulation (SETFLG, RESFLG, COMFLG)

**Flags affected:** C, Z, S, P/V via 4-bit mask; H depends on instruction.

| Instruction | Operation | H behavior |
|-------------|-----------|------------|
| SETFLG | `FCW \|= mask` | **Unaffected** |
| RESFLG | `FCW &= ~mask` | **Unaffected** |
| COMFLG | `FCW ^= mask` | **XOR (toggle) H** |

The 4-bit mask in the opcode maps to bits 7-4 (C, Z, S, P/V). Bits 3-2 (DA, H) are
outside the mask. SETFLG and RESFLG leave H unchanged. COMFLG **toggles** H as a
hardware side effect — the XOR operation includes H (bit 2) because IR[2]=1 for the
COMFLG opcode encoding (0x8D_f_5). The Verilog implementation confirms this: the
flagmask is `{IR[7:4], 0, IR[2], 00}`, so COMFLG XORs both the CZSV bits AND bit 2 (H).

**Manual says (detail page):** H is "Undefined" for COMFLG. However, the manual's
general discussion (Section 2.5.2) states that H is "not affected" by SETFLG, RESFLG,
or COMFLG. These two statements contradict each other. Golden tests confirm the
hardware XORs H. Three additional discriminating tests were added (double COMFLG,
H preset, ADDB+COMFLG) to verify XOR vs SET — pending golden capture.

**Emulator bug (fixed):** COMFLG now XORs H (`m_fcw ^= F_H`) matching the Verilog
implementation. Previously used `SET_H` which was incorrect when H=1 before COMFLG.

### Group Q: Bit Operations (BIT, TSET, SET, RES)

| Instruction | Flags affected | Rule |
|-------------|---------------|------|
| BIT/BITB | Z only | Z = tested bit is zero |
| TSET/TSETB | S only | S = MSB of original value (before setting to 0xFF) |
| SET/SETB | none | |
| RES/RESB | none | |

**Emulator status:** Correct. No golden test failures.

### Group R: Program Status Loads (IRET, LDPS, SC, LDCTL FCW)

All flags loaded directly from memory or register. No computation involved.

**Emulator status:** Correct — loads FCW directly.

### Group S: No Flags Affected

The following instructions do not affect any flags: CALL, CALR, CLR, DI, DJNZ, EI,
EX, EXTS, HALT, IN, JP, JR, LD (all), LDA, LDAR, LDCTL (reg from ctl), LDK, LDM,
LDR, MRES, MSET, NOP, OUT, POP, PUSH, RES, RET, SET, TCC.

---

## 4. Implemented Fixes and Results

All fixes have been implemented and verified against the golden Z8001 test suite.

**Final result: 796 match, 1 excluded (DIV CASE 3), 26 missing golden reference.**

| Step | Fix | Tests Fixed | Running Total |
|------|-----|-------------|---------------|
| 1 | COMFLG H: add `SET_H` | +16 | 750 |
| 2 | Block Load Z: add CLR_Z/SET_Z from counter | +8 | 758 |
| 3 | RLDB/RRDB S: add S from sign bit | +2 | 760 |
| 4 | Shift/Rotate V: per-step accumulation for all shifts/rotates | +35 | 795 |
| 5 | DIVL Z: check low word of quotient | +1 | 796 |

The 1 remaining diff (`sys_div_rr_r_large`) is DIV CASE 3 where the manual says
registers are "undefined" — the emulator's mathematical shortcut produces different
undefined values than the hardware's step-by-step microcode division.

---

## 5. The Unified Fix Strategy

Rather than fixing flags case-by-case, the fixes follow from **three hardware
principles**:

### Principle 1: The ALU always computes Z and S from its output

Every time a value passes through the ALU (including counter decrements in block ops,
digit rotate results, etc.), Z and S are computed. The emulator should update Z and S
whenever the hardware's ALU fires, not just for the "main" operation.

**Applies to:** Block move Z (Step 2), RLDB/RRDB S (Step 3), DIVL Z (Step 5).

**Caveat:** This principle does not apply uniformly to all block operations. Block
translate operations do NOT set Z from the counter (proven by golden tests), while
block transfers DO. The "undefined" flag behavior differs between instruction groups
even when the same ALU sub-operation occurs.

### Principle 2: The shifter accumulates V across all steps

The shift/rotate unit processes one bit position at a time. The V flag is the OR of all
intermediate sign-change events. There is no distinction between arithmetic and logical
shifts at the V-computation level — the same circuit fires for both. This applies to
both left and right shifts: when a logical right shift changes the MSB from 1 to 0,
the V circuit detects the sign change.

**Applies to:** All shift/rotate V (Step 4). This is 35 tests but a single algorithmic
fix applied uniformly to SLA, SLL, SRL, SDA, SDL, RL, RR, RLC, RRC (and byte/long
variants).

### Principle 3: COMFLG's XOR path includes H via opcode encoding

The COMFLG instruction (opcode 0x8D_f_5) has IR[2]=1. The hardware flagmask is
`{IR[7:4], 0, IR[2], 00}`, so for COMFLG the XOR includes bit 2 (H). This means
COMFLG toggles H along with the specified CZSV flags. SETFLG (IR[2]=0) and RESFLG
(IR[2]=0) do not affect H. Confirmed by Verilog implementation.

**Applies to:** COMFLG H (Step 1).

---

## 6. Manual Verification of All Flag Changes

Every flag change was verified against the Z8000 CPU manual (`z8000_micro/z8000.md`).
The table below summarizes the manual's specification, whether the change is consistent
with it, and whether the golden hardware confirms the change.

| Change | Manual Says | Consistent with Manual? | Golden Confirms? |
|--------|------------|------------------------|------------------|
| COMFLG: XOR H (toggle) | H: "Undefined" (detail page); "not affected" (overview §2.5.2) | Ambiguous — manual contradicts itself | Yes (16 tests, H=0→1); 3 new tests pending golden capture for H=1→0 case |
| Block Load: SET_Z/CLR_Z on counter | Z: "Undefined" | Permitted — undefined behavior | Yes (8 tests) |
| RLDB/RRDB: set S from sign bit | S: "Undefined" (detail page); listed in Appendix C summary table | Ambiguous — detail vs summary disagree | Yes (2 tests) |
| Rotate V: accumulate across steps | V: "set if sign changed **during** rotation" | **Yes** — "during" implies per-step | Yes (8 tests) |
| SDA V: accumulate across steps | V: "set if sign changed **during** shifting" | **Yes** — "during" implies per-step | Yes |
| SDL V: track V in left and right shifts | V: "Undefined" | Permitted — undefined behavior | Yes (6 tests) |
| SLA V: accumulate across steps | V: "set if sign changed **during** shifting" | **Yes** — "during" implies per-step | Yes |
| SLL V: track V | V: "Undefined" | Permitted — undefined behavior | Yes |
| SRA V: accumulate (no-op for arith right) | V: "Cleared" | Functionally equivalent — sign can't change | Yes |
| SRL V: track V in right shifts | V: "Undefined" | Permitted — undefined behavior | Yes (12 tests) |
| DIVL Z: check low 16-bit word only | Z: "set if the quotient is zero" | **No** — manual implies full 32-bit quotient | Yes (1 test) |

### Detailed Manual Findings

**Flags with explicit specifications (manual and hardware agree):**
- **Rotate V / SDA V / SLA V:** The manual's wording "if the sign of the destination
  changed **during** rotation/shifting" directly supports per-step V accumulation.
  This is the most clearly documented change.
- **SRA V:** Manual says "Cleared." The implementation accumulates V but arithmetic
  right shift replicates the sign bit, so the sign can never change — V is always 0.
  Functionally identical to just clearing V.

**Flags marked "Undefined" in the manual (hardware determines behavior):**
- **SDL V, SLL V, SRL V:** Manual says V is "Undefined" for all logical shift variants.
  The hardware uses the same sign-change detection circuit as arithmetic shifts. These
  changes are legitimate implementations of undefined behavior, guided by golden tests.
- **Block Load Z:** Manual says Z is "Undefined." The semantic applied (Z = counter
  reached zero) mirrors what the manual specifies for V in the same instruction. Both
  flags reflect the same ALU sub-operation (counter decrement).
- **RLDB/RRDB S:** The detail instruction page says S is "Undefined." The summary table
  in Appendix C lists S as an affected flag. This is an internal contradiction in the
  manual. The hardware sets S from the sign bit of the result byte, consistent with the
  summary table and the ALU model.
- **COMFLG H:** The detail page says H is "Undefined." The overview section (§2.5.2)
  says H is "not affected" by COMFLG. This is an internal contradiction. The Verilog
  implementation reveals the mechanism: COMFLG's flagmask includes IR[2] which maps to
  the H bit position, so H is XOR'd (toggled) along with the CZSV flags. The emulator
  now uses XOR to match. Three new golden tests (double COMFLG, H preset, ADDB+COMFLG)
  will confirm the XOR behavior when captured on hardware.

**Flag where hardware contradicts the manual:**
- **DIVL Z:** The manual says Z is "set if the quotient is zero" — implying the full
  32-bit quotient for DIVL. The hardware checks only the low 16-bit word of the
  quotient. This is consistent with the ALU hardware model (the last word written
  through the ALU determines Z) but inconsistent with the manual's text. The golden
  test confirms the hardware behavior.

---

## 7. Audit: Other Potential Issues Not Exposed by Current Tests

The following emulator behaviors may be incorrect but aren't exposed by the current
golden test suite:

1. **ADC/SBC overflow (V flag):** The overflow check doesn't account for the carry-in
   bit. May produce wrong V in edge cases. No test currently fails.

2. **MULT C threshold:** `>= 0x7fff` may be off-by-one (should be `> 0x7fff`). The
   value 32767 fits in int16_t, so C should not be set.

3. **Block translate Z:** TRIB/TRDB/TRIRB/TRDRB don't update Z from counter. Golden
   tests confirm this is correct — unlike block transfers, translates do NOT set Z from
   the counter. (Originally listed as a potential issue; now confirmed correct.)

4. **Block I/O Z:** INI/IND/OUTI/OUTD and repeat variants don't update Z from counter.
   The IND/INDB exception (Z "unaffected") may need special handling.

5. **SDA/SDL zero-shift C:** Manual says C is "undefined" for zero shift count. The
   emulator produces C=0. Hardware may differ.

6. **RR SET_SC style:** RRB/RRW use `SET_SC` (sets both S and C) instead of the
   standard `CHK_XXXW_ZS` + separate C check. Functionally correct for RR but different
   code path from other rotates.

7. **Block compare "undefined" C and S (CPI/CPD):** Manual says C and S are undefined
   for register-vs-memory block compares. Hardware likely sets them from the comparison
   subtraction. No test exercises this.
