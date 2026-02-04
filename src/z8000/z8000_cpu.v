//============================================================================
// Z8000 Microcoded CPU
// File: z8000_cpu.v
//
// A microcoded implementation of a Z8000 CPU subset.
// Designed for 4 MHz operation (250 ns clock period).
//
// Supports both Z8001 (segmented) and Z8002 (non-segmented) modes via
// conditional compilation. Define Z8001_MODE for Z8001, otherwise Z8002.
//
// Key differences:
//   Z8001: Stack pointer is RR14 (R14=segment, R15=offset), segmented
//   Z8002: Stack pointer is R15 only, non-segmented (default)
//
// Supported instructions:
//   - LD (register, immediate, indirect, direct)
//   - ADD (register, immediate, indirect, direct)
//   - SUB (register, immediate)
//   - JP cc, address
//   - JR cc, displacement
//
// Bus timing matches Y8002 specification:
//   - 4 clock cycles per bus transaction (1 µs at 4 MHz)
//   - Multiplexed address/data bus
//   - AS_n/DS_n handshake protocol
//============================================================================

`timescale 1ns / 1ps

// Include auto-generated microcode address definitions
`include "ucode_defs.v"

//=============================================================================
// CPU Mode Configuration
//=============================================================================
`ifdef Z8001_MODE
    // Z8001 (segmented mode) parameters
    `define PSA_SIZE        8       // Program Status Area: 8 bytes (4 words)
    `define STACK_FRAME     4       // CALL pushes 4 bytes (segment:offset)
    `define SEGMENTED_MODE  1       // Segmented addressing enabled
`else
    // Z8002 (non-segmented mode) parameters - DEFAULT
    `define PSA_SIZE        4       // Program Status Area: 4 bytes (2 words)
    `define STACK_FRAME     2       // CALL pushes 2 bytes (offset only)
    `define SEGMENTED_MODE  0       // Non-segmented addressing
`endif

module z8000_cpu (
    // Clock and Reset
    input  wire        clk,           // 4 MHz system clock
    input  wire        rst_n,         // Active low reset
    
    // Multiplexed Address/Data Bus
    inout  wire [15:0] ad,            // Address/Data bus
    
    // Bus Control
    output reg         as_n,          // Address strobe (active low)
    output reg         ds_n,          // Data strobe (active low)
    output reg         rw_n,          // Read/Write (1=read, 0=write)
    output reg         mreq_n,        // Memory request (active low)
    output reg         b_w_n,         // Byte/Word (0=byte, 1=word)
    output reg  [3:0]  st,            // Status (transaction type)
    
    // Bus Handshake
    input  wire        wait_n,        // Wait input (active low)
    input  wire        busreq_n,      // Bus request (active low)
    output reg         busack_n,      // Bus acknowledge (active low)
    
    // Interrupts
    input  wire        nmi_n,         // Non-maskable interrupt
    input  wire        vi_n,          // Vectored interrupt
    input  wire        nvi_n,         // Non-vectored interrupt
    
    // Status
    output wire        n_s,           // Normal/System mode (active low = system)
    output wire        halt_n         // Halt status (active low = halted)
);

    //=========================================================================
    // PARAMETERS
    //=========================================================================
    
    // Bus timing (in clock cycles)
    localparam BUS_CYCLES = 4;        // 4 clocks per bus cycle = 1 µs @ 4 MHz
    
    // Microinstruction field positions (44-bit word)
    // [43:40] ALU_OP   [39:36] SRC_A   [35:32] SRC_B   [31:28] DST
    // [27:25] NEXT     [24:21] BUS_OP  [20:15] COND    [14:4] BRANCH  [3:2] IMM  [1:0] MISC
    // IMM encoding: 00=0, 01=1, 10=2, 11=4
    // MISC: [0]=flags update, [1]=rotate through carry (for SHL/SHR → RLC/RRC)
    
    // ALU Operations (5 bits to support SEXT)
    localparam [4:0] ALU_NOP    = 5'd0;
    localparam [4:0] ALU_PASS_A = 5'd1;
    localparam [4:0] ALU_PASS_B = 5'd2;
    localparam [4:0] ALU_ADD    = 5'd3;
    localparam [4:0] ALU_ADC    = 5'd4;
    localparam [4:0] ALU_SUB    = 5'd5;
    localparam [4:0] ALU_SBC    = 5'd6;
    localparam [4:0] ALU_AND    = 5'd7;
    localparam [4:0] ALU_OR     = 5'd8;
    localparam [4:0] ALU_XOR    = 5'd9;
    localparam [4:0] ALU_SHL    = 5'd10;
    localparam [4:0] ALU_SHR    = 5'd11;
    localparam [4:0] ALU_SAR    = 5'd12;
    localparam [4:0] ALU_ROL    = 5'd13;
    localparam [4:0] ALU_ROR    = 5'd14;
    localparam [4:0] ALU_LATCH  = 5'd15;  // Use latched operation
    localparam [4:0] ALU_SEXTB  = 5'd16;  // Sign extend byte to word (EXTSB)
    localparam [4:0] ALU_SEXTW  = 5'd17;  // Sign extend word (EXTS)
    localparam [4:0] ALU_DAB    = 5'd18;  // Decimal adjust byte (BCD)
    localparam [4:0] ALU_RLDB   = 5'd19;  // Rotate left digit byte (BCD) - new Rbd
    localparam [4:0] ALU_RRDB   = 5'd20;  // Rotate right digit byte (BCD) - new Rbd
    localparam [4:0] ALU_RLDB_SRC = 5'd21;  // RLDB source update - new Rbs
    localparam [4:0] ALU_RRDB_SRC = 5'd22;  // RRDB source update - new Rbs
    localparam [4:0] ALU_MUL      = 5'd23;  // Signed multiply, returns low 16 bits
    localparam [4:0] ALU_MUL_HI   = 5'd24;  // Returns high 16 bits of last multiply
    localparam [4:0] ALU_MULU     = 5'd25;  // Unsigned multiply, returns low 16 bits
    localparam [4:0] ALU_MULU_HI  = 5'd26;  // Returns high 16 bits of last unsigned multiply

    // Source/Destination selects
    localparam [4:0] SEL_ZERO   = 5'd0;
    localparam [4:0] SEL_RS     = 5'd1;   // Rs - size-dependent (byte or word)
    localparam [4:0] SEL_RD     = 5'd2;   // Rd - size-dependent (byte or word)
    localparam [4:0] SEL_RN     = 5'd3;
    localparam [4:0] SEL_PC     = 5'd4;
    localparam [4:0] SEL_SP     = 5'd5;
    localparam [4:0] SEL_MAR    = 5'd6;
    localparam [4:0] SEL_MDR    = 5'd7;
    localparam [4:0] SEL_IR     = 5'd8;
    localparam [4:0] SEL_RSL    = 5'd9;   // Rs+1 (low word for long)
    localparam [4:0] SEL_TEMP   = 5'd10;
    localparam [4:0] SEL_RDL    = 5'd11;  // Rd+1 (low word for long)
    localparam [4:0] SEL_FCW    = 5'd12;
    localparam [4:0] SEL_TEMP2  = 5'd13;
    localparam [4:0] SEL_IMM    = 5'd14;
    localparam [4:0] SEL_SIZE   = 5'd15;
    localparam [4:0] SEL_PTR_RS = 5'd16;  // @Rs - pointer (always word)
    localparam [4:0] SEL_PTR_RD = 5'd17;  // @Rd - pointer (always word)
    localparam [4:0] SEL_INC_VAL = 5'd18; // IR[3:0]+1 for INC/DEC/COM
    localparam [4:0] SEL_JR_OFF = 5'd19;  // JR offset: sign-ext IR[7:0]*2
    localparam [4:0] SEL_CALR_OFF = 5'd20; // CALR offset: sign-ext IR[11:0]*2
    localparam [4:0] SEL_DJNZ_OFF = 5'd21; // DJNZ offset: IR[6:0]*2
    localparam [4:0] SEL_BITMASK = 5'd22;  // 1 << IR[3:0] for BIT/SET/RES
    localparam [4:0] SEL_TRAP_OFF = 5'd23; // (trap_num + 1) << PSA_SHIFT for trap handlers
    localparam [4:0] SEL_SP_SYS = 5'd24;   // System stack pointer (always R15_sys)
    localparam [4:0] SEL_FLAGMASK = 5'd25; // IR[7:4] mask for SETFLG/RESFLG/COMFLG
    localparam [4:0] SEL_SIZE_DIR = 5'd26; // Signed SIZE: +SIZE if dir=INC, -SIZE if dir=DEC
    localparam [4:0] SEL_RSL2   = 5'd27;  // Rs+2 (high word of low long for quad)
    localparam [4:0] SEL_INTMASK = 5'd28;   // IR[1:0] mask for DI/EI: IR[1]->bit11, IR[0]->bit12
    localparam [4:0] SEL_SINGLE_BIT = 5'd29; // TEMP2[3] for single vs repeat block I/O
    localparam [4:0] SEL_RD2    = 5'd30;  // Rd+2 (for quad operations)
    localparam [4:0] SEL_RD3    = 5'd31;  // Rd+3 (for quad operations)

    // Destination-only selects
    localparam [4:0] DST_NONE   = 5'd0;
    localparam [4:0] DST_FLAGS  = 5'd14;
    localparam [4:0] DST_PSAP   = 5'd15;  // PSAP register (also SEL_SIZE for source)
    localparam [4:0] DST_PTR_RS = 5'd16;  // @Rs - pointer dest (always word)
    localparam [4:0] DST_PTR_RD = 5'd17;  // @Rd - pointer dest (always word)
    localparam [4:0] DST_TRAP_NUM = 5'd23; // Trap number latch for PSA offset calculation
    localparam [4:0] DST_SP_SYS = 5'd24;   // System stack pointer (always R15_sys)

    // Operand size constants
    localparam [1:0] SIZE_BYTE = 2'd0;
    localparam [1:0] SIZE_WORD = 2'd1;
    localparam [1:0] SIZE_LONG = 2'd2;

    // Immediate selector constants (imm_sel field)
    localparam [1:0] IMM_ZERO    = 2'd0;  // Constant 0
    localparam [1:0] IMM_ONE     = 2'd1;  // Constant 1
    localparam [1:0] IMM_TWO     = 2'd2;  // Constant 2
    localparam [1:0] IMM_FOUR    = 2'd3;  // Constant 4

    // Next microinstruction control
    localparam [2:0] NEXT_NEXT   = 3'd0;  // Continue to next
    localparam [2:0] NEXT_FETCH  = 3'd1;  // Go to FETCH (uPC = 0)
    localparam [2:0] NEXT_DECODE = 3'd2;  // Decode IR, jump to handler
    localparam [2:0] NEXT_JUMP   = 3'd3;  // Conditional jump
    localparam [2:0] NEXT_CALL   = 3'd4;  // Call subroutine
    localparam [2:0] NEXT_RETURN = 3'd5;  // Return from subroutine
    localparam [2:0] NEXT_WAIT   = 3'd6;  // Wait for condition
    localparam [2:0] NEXT_HALT   = 3'd7;  // Halt processor
    
    // Bus operations
    localparam [3:0] BUS_IDLE    = 4'd0;
    localparam [3:0] BUS_IFETCH  = 4'd1;  // Instruction fetch
    localparam [3:0] BUS_PFETCH  = 4'd2;  // Program data fetch (immediate, displacement, etc.)
    localparam [3:0] BUS_READ    = 4'd3;  // Data read
    localparam [3:0] BUS_WRITE   = 4'd4;  // Data write
    localparam [3:0] BUS_STK_RD  = 4'd5;  // Stack read
    localparam [3:0] BUS_STK_WR  = 4'd6;  // Stack write
    localparam [3:0] BUS_IO_RD   = 4'd7;  // I/O read
    localparam [3:0] BUS_IO_WR   = 4'd8;  // I/O write
    localparam [3:0] BUS_SIO_RD  = 4'd9;  // Special I/O read
    localparam [3:0] BUS_SIO_WR  = 4'd10; // Special I/O write
    localparam [3:0] BUS_AFETCH  = 4'd13; // Address fetch (segmented: 1 or 2 words)

    // Status codes (directly connected to st output)
    localparam [3:0] ST_INTERNAL   = 4'b0000;
    localparam [3:0] ST_REFRESH    = 4'b0001;
    localparam [3:0] ST_IO_REF     = 4'b0010;
    localparam [3:0] ST_SPEC_IO    = 4'b0011;
    localparam [3:0] ST_SEG_TRAP   = 4'b0100;
    localparam [3:0] ST_NMI_ACK    = 4'b0101;
    localparam [3:0] ST_NVI_ACK    = 4'b0110;
    localparam [3:0] ST_VI_ACK     = 4'b0111;
    localparam [3:0] ST_DATA_RD    = 4'b1000;
    localparam [3:0] ST_DATA_WR    = 4'b1001;
    localparam [3:0] ST_STK_RD     = 4'b1010;
    localparam [3:0] ST_STK_WR     = 4'b1011;
    localparam [3:0] ST_PROG_RD    = 4'b1100;
    localparam [3:0] ST_INST_1ST   = 4'b1101;
    localparam [3:0] ST_INST_SUB   = 4'b1110;
    localparam [3:0] ST_EPU_TRAP   = 4'b1111;

    // Bus cycle phases (ucycle states)
    localparam [1:0] UCYC_ADDR     = 2'd0;  // Address phase - drive address, assert AS_n
    localparam [1:0] UCYC_HOLD     = 2'd1;  // Address hold - release AS_n
    localparam [1:0] UCYC_DATA     = 2'd2;  // Data phase - assert DS_n, read/write data
    localparam [1:0] UCYC_COMPLETE = 2'd3;  // Data complete - sample read data, release DS_n

    // FCW (Flags and Control Word) bit positions
    // Standard Z8000 flag layout (bits 7-2)
    localparam FCW_C   = 7;   // Carry flag
    localparam FCW_Z   = 6;   // Zero flag
    localparam FCW_S   = 5;   // Sign flag (negative)
    localparam FCW_V   = 4;   // Overflow flag (signed arithmetic)
    localparam FCW_DA  = 3;   // Decimal adjust flag
    localparam FCW_H   = 2;   // Half carry flag (BCD)
    // Bits 1-0: Reserved
    // Bits 11-15: Control bits
    localparam FCW_VIE = 11;  // Vectored interrupt enable
    localparam FCW_NVIE= 12;  // Non-vectored interrupt enable
    // Bit 13: Reserved
    localparam FCW_SYS = 14;  // System/Normal mode (1=System, 0=Normal)
    localparam FCW_SEG = 15;  // Segmented mode (Z8001 only, always 0 for Z8002)
                              // When SEG=1: 23-bit segmented addressing (7-bit seg + 16-bit offset)
                              // When SEG=0: 16-bit non-segmented addressing
                              // Note: Current implementation uses 16-bit addressing only

    //=========================================================================
    // INTERRUPT PENDING DETECTION
    //=========================================================================

    // Any enabled interrupt is pending (NMI always enabled, VI/NVI check FCW)
    wire int_pending = ~nmi_n ||
                       (~vi_n && FCW[FCW_VIE]) ||
                       (~nvi_n && FCW[FCW_NVIE]);

    //=========================================================================
    // REGISTERS
    //=========================================================================
    
    // General purpose registers R0-R15
    reg [15:0] R [0:15];
    
    // Alternate R15 for system/normal mode (stack pointer offset)
    reg [15:0] R15_sys;
    reg [15:0] R15_nrm;

`ifdef Z8001_MODE
    // Z8001: Alternate R14 for system/normal mode (stack pointer segment)
    // In Z8001, the stack pointer is RR14 (R14=segment, R15=offset)
    // R14 is reserved for stack segment and has separate sys/nrm copies
    reg [15:0] R14_sys;
    reg [15:0] R14_nrm;
`endif
    
    // Program counter and control
    reg [15:0] PC;
    reg [15:0] FCW;            // Flags and Control Word
    reg [15:0] PSAP;           // Program Status Area Pointer
    reg [15:0] REFRESH;        // Refresh counter
    reg [1:0]  trap_num;       // Trap number for PSA offset calculation
    
    // Internal registers
    reg [15:0] MAR;            // Memory Address Register
    reg [15:0] MDR;            // Memory Data Register
    reg [15:0] IR;             // Instruction Register
    reg [15:0] IR2;            // Instruction Register 2 (for long instructions)
    reg [15:0] TEMP;           // Temporary register
    reg [15:0] TEMP2;          // Temporary register 2
    
    // Microsequencer registers
    reg [11:0] uPC;            // Microprogram counter (12-bit for 4096 entries)
    reg [11:0] uPC_stack [0:3];// Microcode return stack
    reg [1:0]  uSP;            // Microcode stack pointer
    reg [1:0]  ucycle;         // Bus cycle counter (0-3)
    
    // Control latches (set by decoder)
    reg [4:0]  op_latch;       // Operation for EXEC_ALU
    reg [1:0]  size_latch;     // BYTE=0, WORD=1, LONG=2
    reg        dir_latch;      // Direction: INC=0, DEC=1
    reg        rep_latch;      // Repeat flag
    reg        priv_latch;     // Privileged instruction
    reg        block_latch;    // Block instruction (LDI): Rd=TEMP2[11:8], Rn=TEMP2[15:12]
    reg        block_cp_latch; // Block instruction (CPI/IO): Rd=TEMP2[7:4], Rn=TEMP2[11:8]
    reg        bx_latch;       // BX addressing: Rn from TEMP2[11:8]
    reg        bx_byte_dest_latch;  // BX with byte destination (dynamic bit byte ops)
    reg        compact_ldb_latch; // Compact LDB: 8-bit immediate from IR[7:0]
    reg        ldk_latch;      // LDK: 4-bit immediate from IR[3:0]
    
    // Status
    reg        halted;
    reg        bus_granted;
    
    //=========================================================================
    // MICROCODE ROM INSTANCE
    //=========================================================================
    
    wire [48:0] uinst;  // 49-bit microinstruction (expanded for 12-bit branch)

    microcode_rom u_ucode (
        .upc(uPC),
        .uinst(uinst)
    );

    //=========================================================================
    // DECODER ROM INSTANCE
    //=========================================================================

    wire [11:0] decode_entry;
    wire [4:0]  decode_op;
    wire [1:0]  decode_size;
    wire        decode_dir;
    wire        decode_rep;
    wire        decode_priv;
    wire        decode_block;
    wire        decode_block_cp;
    wire        decode_bx;
    wire        decode_bx_byte_dest;
    wire        decode_compact_ldb;
    wire        decode_ldk;

    decode_rom u_decode (
        .ir(IR),
        .upc_entry(decode_entry),
        .op_latch(decode_op),
        .size_latch(decode_size),
        .dir_latch(decode_dir),
        .rep_latch(decode_rep),
        .priv_flag(decode_priv),
        .block_latch(decode_block),
        .block_cp_latch(decode_block_cp),
        .bx_latch(decode_bx),
        .bx_byte_dest(decode_bx_byte_dest),
        .compact_ldb(decode_compact_ldb),
        .ldk_flag(decode_ldk)
    );
    
    //=========================================================================
    // MICROINSTRUCTION DECODE
    //=========================================================================

    // 48-bit microinstruction format:
    //   [47:43] ALU_OP (5 bits)
    //   [42:38] SRC_A  (5 bits) - expanded for pointer selectors
    //   [37:33] SRC_B  (5 bits) - expanded for pointer selectors
    //   [32:28] DST    (5 bits) - expanded for pointer selectors
    //   [27:25] NEXT   (3 bits)
    //   [24:21] BUS_OP (4 bits)
    //   [20:15] COND   (6 bits)
    //   [14:4]  BRANCH (11 bits)
    //   [3:2]   IMM    (2 bits)
    //   [1:0]   MISC   (2 bits)
    wire [4:0] alu_op    = uinst[48:44];
    wire [4:0] src_a_sel = uinst[43:39];
    wire [4:0] src_b_sel = uinst[38:34];
    wire [4:0] dst_sel   = uinst[33:29];
    wire [2:0] next_ctrl = uinst[28:26];
    wire [3:0] bus_op    = uinst[25:22];
    wire [5:0] cond_sel  = uinst[21:16];
    wire [11:0] branch_target = uinst[15:4];
    wire [1:0] imm_sel   = uinst[3:2];   // IMM: 00=0, 01=1, 10=2, 11=4
    wire [1:0] misc      = uinst[1:0];

    // Decode immediate value from imm_sel field
    // Simple constants: 0, 1, 2, 4
    wire [15:0] bitmask = 16'h0001 << IR[3:0];  // For SEL_BITMASK source
    // SETFLG/RESFLG/COMFLG: IR[7:4] = CZSV mask
    // Standard Z8000 FCW: bit 7=C, bit 6=Z, bit 5=S, bit 4=V
    // IR[7:4] maps directly to FCW[7:4]
    wire [15:0] flagmask = {8'h00, IR[7:4], 4'h0};
    wire [15:0] single_bit = {15'b0, TEMP2[3]};  // TEMP2[3] for single vs repeat block I/O
    // DI/EI interrupt mask: bits indicate which to SKIP, so invert
    // V=IR[1]: 0=affect VIE(bit11), N=IR[0]: 0=affect NVIE(bit12)
    wire [15:0] intmask = {3'b0, ~IR[0], ~IR[1], 11'b0};
    wire [15:0] imm_value = (imm_sel == IMM_ZERO) ? 16'h0000 :
                            (imm_sel == IMM_ONE)  ? 16'h0001 :
                            (imm_sel == IMM_TWO)  ? 16'h0002 : 16'h0004;

    // PSA offset calculation for trap handlers
    // trap_offset = (trap_num + 1) << PSA_SHIFT
    // Z8002: PSA_SHIFT=2 (entry size 4), Z8001: PSA_SHIFT=3 (entry size 8)
`ifdef Z8001_MODE
    localparam PSA_SHIFT = 3;
`else
    localparam PSA_SHIFT = 2;
`endif
    wire [15:0] trap_offset = ({14'b0, trap_num} + 16'd1) << PSA_SHIFT;

    //=========================================================================
    // REGISTER FILE ACCESS
    //=========================================================================
    
    // Extract register numbers from IR
    wire [3:0] ir_rs = IR[7:4];    // Source register

    // Register field extraction from instruction
    // For non-block instructions: Rd from IR[3:0], Rn from IR[11:8]
    // For block_latch (LDI/LDIR format): second word = 0000_nnnn_dddd_mmmm
    //   Rd (dest pointer) from TEMP2[7:4]
    //   Rn (count) from TEMP2[11:8]
    // For block_cp_latch (CPI/CPIR/block I/O format): second word = 0000_nnnn_dddd_cccc
    //   Rd (compare value reg) from TEMP2[7:4]
    //   Rn (count) from TEMP2[11:8]
    // For BX addressing (base indexed):
    //   Rd from IR[3:0] (unchanged)
    //   Rn (index) from TEMP2[11:8]
    // The latches (set by decoder) select which source to use
    wire [3:0] ir_rd = block_latch    ? TEMP2[7:4] :
                       block_cp_latch ? TEMP2[7:4]  : IR[3:0];
    wire [3:0] ir_rn = block_latch    ? TEMP2[11:8] :
                       block_cp_latch ? TEMP2[11:8]  :
                       bx_latch       ? TEMP2[11:8]  : IR[11:8];
    
    // Current R15 based on mode (stack pointer offset, or full SP in Z8002)
    wire [15:0] current_R15 = FCW[FCW_SYS] ? R15_sys : R15_nrm;

`ifdef Z8001_MODE
    // Current R14 based on mode (stack pointer segment in Z8001)
    // In Z8001, R14 is reserved for stack segment and has separate sys/nrm copies
    wire [15:0] current_R14 = FCW[FCW_SYS] ? R14_sys : R14_nrm;
`endif
    
    // Low word register numbers for long operations (RRn uses Rn:Rn+1)
    wire [3:0] ir_rs_lo = ir_rs | 4'b0001;  // Rs+1 (low word of source pair)
    wire [3:0] ir_rd_lo = ir_rd | 4'b0001;  // Rd+1 (low word of dest pair)
    wire [3:0] ir_rs_lo2 = ir_rs | 4'b0010; // Rs+2 (high word of low long for quad)
    wire [3:0] ir_rd_lo2 = ir_rd | 4'b0010; // Rd+2 (high word of low long for quad)
    wire [3:0] ir_rd_lo3 = ir_rd | 4'b0011; // Rd+3 (low word of low long for quad)

    // Trap handling detection
    // When uPC is in the trap handler range, SEL_SIZE returns PSAP instead of size
    // When uPC is in the trap handler range, SEL_SIZE returns PSAP instead of size
    wire in_trap_handler = (uPC >= `UADDR_TRAP_ILLEGAL) && (uPC <= `UADDR_INT_ENTRY + 12'd32);

    // Privileged instruction violation detection
    // Triggers when a privileged instruction is decoded while in normal mode
    wire priv_violation = decode_priv && !FCW[FCW_SYS];

    // Byte register access (for size_latch=BYTE):
    // Bits [2:0] = register number (R0-R7 only)
    // Bit [3] = 0 for high byte (RHn), 1 for low byte (RLn)
    wire [2:0] ir_rs_byte_reg = ir_rs[2:0];  // Register number for byte ops
    wire [2:0] ir_rd_byte_reg = ir_rd[2:0];
    wire [2:0] ir_rn_byte_reg = ir_rn[2:0];  // Register number for Rn byte ops
    wire       ir_rs_byte_lo = ir_rs[3];      // 1=low byte, 0=high byte
    wire       ir_rd_byte_lo = ir_rd[3];
    wire       ir_rn_byte_lo = ir_rn[3];      // 1=low byte, 0=high byte for Rn

    // Extract byte from word based on high/low selector
    wire [15:0] rs_word = R[{1'b0, ir_rs_byte_reg}];
    wire [15:0] rd_word = R[{1'b0, ir_rd_byte_reg}];
    wire [15:0] rn_word = R[{1'b0, ir_rn_byte_reg}];
    wire [7:0]  rs_byte = ir_rs_byte_lo ? rs_word[7:0] : rs_word[15:8];
    wire [7:0]  rd_byte = ir_rd_byte_lo ? rd_word[7:0] : rd_word[15:8];
    wire [7:0]  rn_byte = ir_rn_byte_lo ? rn_word[7:0] : rn_word[15:8];

    // Source A multiplexer
    reg [15:0] src_a_data;
    always @(*) begin
        case (src_a_sel)
            SEL_ZERO:  src_a_data = 16'h0000;
            // Rs - size-dependent: byte mode uses byte register, word mode uses word
            SEL_RS:    src_a_data = (size_latch == SIZE_BYTE) ? {8'h00, rs_byte} :
                                    (ir_rs == 4'd15) ? current_R15 :
`ifdef Z8001_MODE
                                    (ir_rs == 4'd14) ? current_R14 :
`endif
                                    R[ir_rs];
            // Rd - size-dependent: byte mode uses byte register, word mode uses word
            SEL_RD:    src_a_data = (size_latch == SIZE_BYTE) ? {8'h00, rd_byte} :
                                    (ir_rd == 4'd15) ? current_R15 :
`ifdef Z8001_MODE
                                    (ir_rd == 4'd14) ? current_R14 :
`endif
                                    R[ir_rd];
            // Rn - byte mode when SIZE_BYTE and either: not BX mode, or BX with byte destination
            SEL_RN:    src_a_data = (size_latch == SIZE_BYTE && !block_latch && !block_cp_latch && (!bx_latch || bx_byte_dest_latch)) ? {8'h00, rn_byte} :
                                    (ir_rn == 4'd15) ? current_R15 :
`ifdef Z8001_MODE
                                    (ir_rn == 4'd14) ? current_R14 :
`endif
                                    R[ir_rn];
            SEL_PC:    src_a_data = PC;
            SEL_SP:    src_a_data = current_R15;
            SEL_MAR:   src_a_data = MAR;
            SEL_MDR:   src_a_data = MDR;
            SEL_IR:    src_a_data = compact_ldb_latch ? compact_ldb_imm :
                                    ldk_latch ? ldk_imm : IR;
            SEL_RSL:   src_a_data = (ir_rs_lo == 4'd15) ? current_R15 :
`ifdef Z8001_MODE
                                    (ir_rs_lo == 4'd14) ? current_R14 :
`endif
                                    R[ir_rs_lo];  // Rs+1
            SEL_TEMP:  src_a_data = TEMP;
            SEL_RDL:   src_a_data = (ir_rd_lo == 4'd15) ? current_R15 :
`ifdef Z8001_MODE
                                    (ir_rd_lo == 4'd14) ? current_R14 :
`endif
                                    R[ir_rd_lo];  // Rd+1
            SEL_FCW:   src_a_data = FCW;
            SEL_TEMP2: src_a_data = TEMP2;
            SEL_IMM:   src_a_data = imm_value;  // Immediate from IMM field
            SEL_SIZE:  src_a_data = in_trap_handler ? PSAP :  // Return PSAP when in trap handler
                                    (size_latch == SIZE_BYTE) ? 16'h0001 :
                                    (size_latch == SIZE_WORD) ? 16'h0002 : 16'h0004;
            // Pointer registers - always word (for addresses)
            SEL_PTR_RS: src_a_data = (ir_rs == 4'd15) ? current_R15 :
`ifdef Z8001_MODE
                                     (ir_rs == 4'd14) ? current_R14 :
`endif
                                     R[ir_rs];
            SEL_PTR_RD: src_a_data = (ir_rd == 4'd15) ? current_R15 :
`ifdef Z8001_MODE
                                     (ir_rd == 4'd14) ? current_R14 :
`endif
                                     R[ir_rd];
            SEL_INC_VAL: src_a_data = inc_value;  // IR[3:0]+1 for INC/DEC/COM
            SEL_JR_OFF:  src_a_data = jr_offset;  // JR displacement
            SEL_CALR_OFF: src_a_data = calr_offset; // CALR displacement
            SEL_DJNZ_OFF: src_a_data = djnz_offset; // DJNZ displacement
            SEL_BITMASK: src_a_data = bitmask;    // 1 << IR[3:0] for BIT/SET/RES
            SEL_TRAP_OFF: src_a_data = trap_offset; // (trap_num + 1) << PSA_SHIFT
            SEL_SP_SYS: src_a_data = R15_sys;     // Always system stack
            SEL_FLAGMASK: src_a_data = flagmask;  // IR[7:4] for SETFLG/RESFLG/COMFLG
            SEL_SIZE_DIR: src_a_data = size_dir;  // +SIZE or -SIZE based on dir_latch
            SEL_RSL2:  src_a_data = (ir_rs_lo2 == 4'd15) ? current_R15 :
`ifdef Z8001_MODE
                                    (ir_rs_lo2 == 4'd14) ? current_R14 :
`endif
                                    R[ir_rs_lo2];  // Rs+2 (high word of low long for quad)
            SEL_INTMASK: src_a_data = intmask;    // IR[1:0] for DI/EI interrupt mask
            SEL_SINGLE_BIT: src_a_data = single_bit; // TEMP2[3] for single vs repeat
            SEL_RD2:   src_a_data = (ir_rd_lo2 == 4'd15) ? current_R15 :
`ifdef Z8001_MODE
                                    (ir_rd_lo2 == 4'd14) ? current_R14 :
`endif
                                    R[ir_rd_lo2];  // Rd+2 (for quad operations)
            SEL_RD3:   src_a_data = (ir_rd_lo3 == 4'd15) ? current_R15 :
`ifdef Z8001_MODE
                                    (ir_rd_lo3 == 4'd14) ? current_R14 :
`endif
                                    R[ir_rd_lo3];  // Rd+3 (for quad operations)
            default:   src_a_data = 16'h0000;
        endcase
    end

    // Source B multiplexer
    reg [15:0] src_b_data;
    always @(*) begin
        case (src_b_sel)
            SEL_ZERO:  src_b_data = 16'h0000;
            // Rs - size-dependent: byte mode uses byte register, word mode uses word
            SEL_RS:    src_b_data = (size_latch == SIZE_BYTE) ? {8'h00, rs_byte} :
                                    (ir_rs == 4'd15) ? current_R15 :
`ifdef Z8001_MODE
                                    (ir_rs == 4'd14) ? current_R14 :
`endif
                                    R[ir_rs];
            // Rd - size-dependent: byte mode uses byte register, word mode uses word
            SEL_RD:    src_b_data = (size_latch == SIZE_BYTE) ? {8'h00, rd_byte} :
                                    (ir_rd == 4'd15) ? current_R15 :
`ifdef Z8001_MODE
                                    (ir_rd == 4'd14) ? current_R14 :
`endif
                                    R[ir_rd];
            // Rn - byte mode when SIZE_BYTE and either: not BX mode, or BX with byte destination
            SEL_RN:    src_b_data = (size_latch == SIZE_BYTE && !block_latch && !block_cp_latch && (!bx_latch || bx_byte_dest_latch)) ? {8'h00, rn_byte} :
                                    (ir_rn == 4'd15) ? current_R15 :
`ifdef Z8001_MODE
                                    (ir_rn == 4'd14) ? current_R14 :
`endif
                                    R[ir_rn];
            SEL_PC:    src_b_data = PC;
            SEL_SP:    src_b_data = current_R15;
            SEL_MAR:   src_b_data = MAR;
            SEL_MDR:   src_b_data = MDR;
            SEL_IR:    src_b_data = compact_ldb_latch ? compact_ldb_imm :
                                    ldk_latch ? ldk_imm : IR;
            SEL_RSL:   src_b_data = (ir_rs_lo == 4'd15) ? current_R15 :
`ifdef Z8001_MODE
                                    (ir_rs_lo == 4'd14) ? current_R14 :
`endif
                                    R[ir_rs_lo];  // Rs+1
            SEL_TEMP:  src_b_data = TEMP;
            SEL_RDL:   src_b_data = (ir_rd_lo == 4'd15) ? current_R15 :
`ifdef Z8001_MODE
                                    (ir_rd_lo == 4'd14) ? current_R14 :
`endif
                                    R[ir_rd_lo];  // Rd+1
            SEL_FCW:   src_b_data = FCW;
            SEL_TEMP2: src_b_data = TEMP2;
            SEL_IMM:   src_b_data = imm_value;  // Immediate from IMM field
            SEL_SIZE:  src_b_data = in_trap_handler ? PSAP :  // Return PSAP when in trap handler
                                    (size_latch == SIZE_BYTE) ? 16'h0001 :
                                    (size_latch == SIZE_WORD) ? 16'h0002 : 16'h0004;
            // Pointer registers - always word (for addresses)
            SEL_PTR_RS: src_b_data = (ir_rs == 4'd15) ? current_R15 :
`ifdef Z8001_MODE
                                     (ir_rs == 4'd14) ? current_R14 :
`endif
                                     R[ir_rs];
            SEL_PTR_RD: src_b_data = (ir_rd == 4'd15) ? current_R15 :
`ifdef Z8001_MODE
                                     (ir_rd == 4'd14) ? current_R14 :
`endif
                                     R[ir_rd];
            SEL_INC_VAL: src_b_data = inc_value;  // IR[3:0]+1 for INC/DEC/COM
            SEL_JR_OFF:  src_b_data = jr_offset;  // JR displacement
            SEL_CALR_OFF: src_b_data = calr_offset; // CALR displacement
            SEL_DJNZ_OFF: src_b_data = djnz_offset; // DJNZ displacement
            SEL_BITMASK: src_b_data = bitmask;    // 1 << IR[3:0] for BIT/SET/RES
            SEL_TRAP_OFF: src_b_data = trap_offset; // (trap_num + 1) << PSA_SHIFT
            SEL_SP_SYS: src_b_data = R15_sys;     // Always system stack
            SEL_FLAGMASK: src_b_data = flagmask;  // IR[7:4] for SETFLG/RESFLG/COMFLG
            SEL_SIZE_DIR: src_b_data = size_dir;  // +SIZE or -SIZE based on dir_latch
            SEL_RSL2:  src_b_data = (ir_rs_lo2 == 4'd15) ? current_R15 :
`ifdef Z8001_MODE
                                    (ir_rs_lo2 == 4'd14) ? current_R14 :
`endif
                                    R[ir_rs_lo2];  // Rs+2 (high word of low long for quad)
            SEL_INTMASK: src_b_data = intmask;    // IR[1:0] for DI/EI interrupt mask
            SEL_SINGLE_BIT: src_b_data = single_bit; // TEMP2[3] for single vs repeat
            SEL_RD2:   src_b_data = (ir_rd_lo2 == 4'd15) ? current_R15 :
`ifdef Z8001_MODE
                                    (ir_rd_lo2 == 4'd14) ? current_R14 :
`endif
                                    R[ir_rd_lo2];  // Rd+2 (for quad operations)
            SEL_RD3:   src_b_data = (ir_rd_lo3 == 4'd15) ? current_R15 :
`ifdef Z8001_MODE
                                    (ir_rd_lo3 == 4'd14) ? current_R14 :
`endif
                                    R[ir_rd_lo3];  // Rd+3 (for quad operations)
            default:   src_b_data = 16'h0000;
        endcase
    end

    //=========================================================================
    // ALU
    //=========================================================================
    
    reg [15:0] alu_result;
    reg        alu_carry;
    reg        alu_zero;
    reg        alu_sign;
    reg        alu_overflow;
    reg [7:0]  dab_tmp;     // Temporary for DAB operation
    reg        dab_c;       // Carry for DAB operation
    reg [31:0] mul_result_reg;  // 32-bit result from multiply (sequential register)
    wire [31:0] mul_result_comb; // Combinational multiply result

    // Select actual ALU operation (direct or latched)
    wire [4:0] actual_alu_op = (alu_op == ALU_LATCH) ? op_latch[4:0] : alu_op;

    // Detect shift/rotate operations (for automatic carry update)
    wire is_shift_rotate = (actual_alu_op == ALU_SHL) ||
                           (actual_alu_op == ALU_SHR) ||
                           (actual_alu_op == ALU_SAR) ||
                           (actual_alu_op == ALU_ROL) ||
                           (actual_alu_op == ALU_ROR);
    
    // ALU operation
    always @(*) begin
        alu_carry = 1'b0;
        alu_overflow = 1'b0;
        
        case (actual_alu_op)
            ALU_NOP:    alu_result = 16'h0000;
            ALU_PASS_A: alu_result = src_a_data;
            ALU_PASS_B: alu_result = src_b_data;
            
            ALU_ADD: begin
                {alu_carry, alu_result} = {1'b0, src_a_data} + {1'b0, src_b_data};
                if (size_latch == SIZE_BYTE) begin // BYTE
                    // For byte mode, carry is bit 8 of result (byte overflow)
                    alu_carry = alu_result[8];
                    alu_overflow = (src_a_data[7] == src_b_data[7]) &&
                                   (alu_result[7] != src_a_data[7]);
                end else begin // WORD/LONG
                    alu_overflow = (src_a_data[15] == src_b_data[15]) &&
                                   (alu_result[15] != src_a_data[15]);
                end
            end

            ALU_ADC: begin
                {alu_carry, alu_result} = {1'b0, src_a_data} + {1'b0, src_b_data} +
                                          {16'b0, FCW[FCW_C]};
                if (size_latch == SIZE_BYTE) begin // BYTE
                    // For byte mode, carry is bit 8 of result (byte overflow)
                    alu_carry = alu_result[8];
                    alu_overflow = (src_a_data[7] == src_b_data[7]) &&
                                   (alu_result[7] != src_a_data[7]);
                end else begin // WORD/LONG
                    alu_overflow = (src_a_data[15] == src_b_data[15]) &&
                                   (alu_result[15] != src_a_data[15]);
                end
            end

            ALU_SUB: begin
                {alu_carry, alu_result} = {1'b0, src_a_data} - {1'b0, src_b_data};
                if (size_latch == SIZE_BYTE) begin // BYTE
                    // For byte mode, borrow is bit 8 of result (byte underflow)
                    alu_carry = alu_result[8];
                    alu_overflow = (src_a_data[7] != src_b_data[7]) &&
                                   (alu_result[7] != src_a_data[7]);
                end else begin // WORD/LONG
                    alu_overflow = (src_a_data[15] != src_b_data[15]) &&
                                   (alu_result[15] != src_a_data[15]);
                end
            end

            ALU_SBC: begin
                {alu_carry, alu_result} = {1'b0, src_a_data} - {1'b0, src_b_data} -
                                          {16'b0, FCW[FCW_C]};
                if (size_latch == SIZE_BYTE) begin // BYTE
                    // For byte mode, borrow is bit 8 of result (byte underflow)
                    alu_carry = alu_result[8];
                    alu_overflow = (src_a_data[7] != src_b_data[7]) &&
                                   (alu_result[7] != src_a_data[7]);
                end else begin // WORD/LONG
                    alu_overflow = (src_a_data[15] != src_b_data[15]) &&
                                   (alu_result[15] != src_a_data[15]);
                end
            end
            
            ALU_AND: alu_result = src_a_data & src_b_data;
            ALU_OR:  alu_result = src_a_data | src_b_data;
            ALU_XOR: alu_result = src_a_data ^ src_b_data;
            
            ALU_SHL: begin
                // When misc[1]=1, this becomes RLC (rotate left through carry)
                // Bit out → new carry, old carry → bit in
                if (size_latch == SIZE_BYTE) begin  // BYTE
                    alu_carry = src_a_data[7];
                    alu_result = {8'h00, src_a_data[6:0], misc[1] ? FCW[FCW_C] : 1'b0};
                end else begin  // WORD
                    alu_carry = src_a_data[15];
                    alu_result = {src_a_data[14:0], misc[1] ? FCW[FCW_C] : 1'b0};
                end
            end

            ALU_SHR: begin
                // When misc[1]=1, this becomes RRC (rotate right through carry)
                // Bit out → new carry, old carry → bit in
                if (size_latch == SIZE_BYTE) begin  // BYTE
                    alu_carry = src_a_data[0];
                    alu_result = {8'h00, misc[1] ? FCW[FCW_C] : 1'b0, src_a_data[7:1]};
                end else begin  // WORD
                    alu_carry = src_a_data[0];
                    alu_result = {misc[1] ? FCW[FCW_C] : 1'b0, src_a_data[15:1]};
                end
            end

            ALU_SAR: begin
                if (size_latch == SIZE_BYTE) begin  // BYTE - sign extend from bit 7
                    alu_carry = src_a_data[0];
                    alu_result = {8'h00, src_a_data[7], src_a_data[7:1]};
                end else begin  // WORD
                    {alu_result, alu_carry} = {src_a_data[15], src_a_data};
                end
            end

            ALU_ROL: begin
                if (size_latch == SIZE_BYTE) begin  // BYTE
                    alu_carry = src_a_data[7];
                    alu_result = {8'h00, src_a_data[6:0], src_a_data[7]};
                end else begin  // WORD
                    {alu_carry, alu_result} = {src_a_data, src_a_data[15]};
                end
            end

            ALU_ROR: begin
                if (size_latch == SIZE_BYTE) begin  // BYTE
                    alu_carry = src_a_data[0];
                    alu_result = {8'h00, src_a_data[0], src_a_data[7:1]};
                end else begin  // WORD
                    {alu_result, alu_carry} = {src_a_data[0], src_a_data};
                end
            end

            ALU_SEXTB: begin
                // EXTSB: Sign extend byte to word (bit 7 fills bits 8-15)
                alu_carry = 1'b0;
                alu_result = {{8{src_a_data[7]}}, src_a_data[7:0]};
            end

            ALU_SEXTW: begin
                // EXTS: Fill all 16 bits with sign bit 15 (for high word of long)
                alu_carry = 1'b0;
                alu_result = {16{src_a_data[15]}};
            end

            ALU_DAB: begin
                // Decimal Adjust Byte (BCD) - src_a is the byte to adjust
                // Uses C (carry) and H (half-carry) flags from previous operation
                // D flag indicates subtract mode (FCW[FCW_DA])
                dab_tmp = src_a_data[7:0];
                dab_c = FCW[FCW_C];

                if (FCW[FCW_DA]) begin
                    // Subtract mode (previous was SUB/SBC)
                    if (FCW[FCW_H] || (dab_tmp[3:0] > 4'h9))
                        dab_tmp = dab_tmp - 8'h06;
                    if (dab_c || (dab_tmp[7:4] > 4'h9)) begin
                        dab_tmp = dab_tmp - 8'h60;
                        dab_c = 1'b1;
                    end
                end else begin
                    // Add mode (previous was ADD/ADC)
                    if (FCW[FCW_H] || (dab_tmp[3:0] > 4'h9)) begin
                        dab_tmp = dab_tmp + 8'h06;
                    end
                    if (dab_c || (dab_tmp[7:4] > 4'h9)) begin
                        dab_tmp = dab_tmp + 8'h60;
                        dab_c = 1'b1;
                    end
                end

                alu_result = {8'h00, dab_tmp};
                alu_carry = dab_c;
            end

            ALU_RLDB: begin
                // Rotate Left Digit Byte (matches Z8000 emulator behavior)
                // Microcode: Rd <- Rd RLDB Rs => src_a = Rd, src_b = Rs
                // New Rbd = {Rbd[7:4], Rbs[7:4]} = {src_a[7:4], src_b[7:4]}
                alu_result = {8'h00, src_a_data[7:4], src_b_data[7:4]};
                alu_carry = 1'b0;
            end

            ALU_RRDB: begin
                // Rotate Right Digit Byte (matches Z8000 emulator behavior)
                // Note: In RRDB, destination register is UNCHANGED
                // This ALU op is not used; RRDB only modifies source register
                alu_result = src_a_data;  // Pass through unchanged
                alu_carry = 1'b0;
            end

            ALU_RLDB_SRC: begin
                // RLDB source register update (matches Z8000 emulator behavior)
                // Microcode: Rs <- Rs RLDB_SRC TEMP => src_a = Rs, src_b = TEMP (original Rd)
                // New Rbs = {Rbs[3:0], Rbd[3:0]} = {src_a[3:0], src_b[3:0]}
                alu_result = {8'h00, src_a_data[3:0], src_b_data[3:0]};
                alu_carry = 1'b0;
            end

            ALU_RRDB_SRC: begin
                // RRDB source register update (matches Z8000 emulator behavior)
                // Microcode: Rs <- Rs RRDB_SRC TEMP => src_a = Rs, src_b = TEMP (original Rd)
                // New Rbs = {Rbd[3:0], Rbs[7:4]} = {src_b[3:0], src_a[7:4]}
                alu_result = {8'h00, src_b_data[3:0], src_a_data[7:4]};
                alu_carry = 1'b0;
            end

            ALU_MUL: begin
                // Signed 16x16 -> 32 multiply, return low 16 bits
                // src_a and src_b are treated as signed 16-bit values
                // mul_result_comb is computed below, use registered value for high word
                alu_result = mul_result_comb[15:0];
                alu_carry = 1'b0;
                // Set sign from high word bit 15 (sign of 32-bit result)
                alu_sign = mul_result_comb[31];
                // Set zero if entire 32-bit result is zero
                alu_zero = (mul_result_comb == 32'h0);
            end

            ALU_MUL_HI: begin
                // Return high 16 bits from last multiply (from registered result)
                alu_result = mul_result_reg[31:16];
                alu_carry = 1'b0;
            end

            ALU_MULU: begin
                // Unsigned 16x16 -> 32 multiply, return low 16 bits
                // mul_result_comb is computed below
                alu_result = mul_result_comb[15:0];
                alu_carry = 1'b0;
            end

            ALU_MULU_HI: begin
                // Return high 16 bits from last unsigned multiply (from registered result)
                alu_result = mul_result_reg[31:16];
                alu_carry = 1'b0;
            end

            default: alu_result = 16'h0000;
        endcase
    end

    // Combinational multiply result computation
    // Sign-extend to 32 bits for signed multiply, zero-extend for unsigned
    assign mul_result_comb = (actual_alu_op == ALU_MUL) ?
                             ({{16{src_a_data[15]}}, src_a_data} * {{16{src_b_data[15]}}, src_b_data}) :
                             ({16'b0, src_a_data} * {16'b0, src_b_data});

    // Size-aware flags computation (moved outside the case for clarity)
    always @(*) begin
        // Size-aware flags
        case (size_latch)
            SIZE_BYTE: begin
                alu_zero = (alu_result[7:0] == 8'h00);
                alu_sign = alu_result[7];
            end
            SIZE_WORD: begin
                alu_zero = (alu_result == 16'h0000);
                alu_sign = alu_result[15];
            end
            default: begin  // SIZE_LONG (flags from high word)
                alu_zero = (alu_result == 16'h0000);
                alu_sign = alu_result[15];
            end
        endcase
    end
    
    //=========================================================================
    // CONDITION EVALUATION
    //=========================================================================
    
    // Z8000 condition codes
    wire cc_z  = FCW[FCW_Z];
    wire cc_nz = ~FCW[FCW_Z];
    wire cc_c  = FCW[FCW_C];
    wire cc_nc = ~FCW[FCW_C];
    wire cc_s  = FCW[FCW_S];   // Minus
    wire cc_ns = ~FCW[FCW_S];  // Plus
    wire cc_v  = FCW[FCW_V];   // Overflow
    wire cc_nv = ~FCW[FCW_V];
    
    // Signed comparisons
    wire cc_lt = FCW[FCW_S] ^ FCW[FCW_V];           // Less than
    wire cc_ge = ~(FCW[FCW_S] ^ FCW[FCW_V]);        // Greater or equal
    wire cc_le = FCW[FCW_Z] | (FCW[FCW_S] ^ FCW[FCW_V]);  // Less or equal
    wire cc_gt = ~FCW[FCW_Z] & ~(FCW[FCW_S] ^ FCW[FCW_V]); // Greater than
    
    // Unsigned comparisons
    wire cc_ult = FCW[FCW_C];                       // Unsigned less than (carry)
    wire cc_uge = ~FCW[FCW_C];                      // Unsigned greater or equal
    wire cc_ule = FCW[FCW_C] | FCW[FCW_Z];          // Unsigned less or equal
    wire cc_ugt = ~FCW[FCW_C] & ~FCW[FCW_Z];        // Unsigned greater than
    
    // Z8000 condition code sources
    wire [3:0] ir_cc = IR[3:0];       // For JP: condition in low nibble
    wire [3:0] ir_cc_jr = IR[11:8];   // For JR: condition in high byte
    wire [3:0] t2_cc = TEMP2[3:0];    // For block compare: condition in TEMP2

    // Select condition code based on microcode condition selector
    // CC (5'd16) uses IR[3:0], CC_JR (5'd19) uses IR[11:8], CC_T2 (5'd22) uses TEMP2[3:0]
    wire [3:0] cc_select = (cond_sel[4:0] == 5'd16) ? ir_cc :
                        (cond_sel[4:0] == 5'd19) ? ir_cc_jr :
                        (cond_sel[4:0] == 5'd22) ? t2_cc : 4'h0;

    // Single Z8000 condition code evaluator
    reg cc_result;
    always @(*) begin
        case (cc_select)
            4'h0: cc_result = 1'b0;      // F - Never (false)
            4'h1: cc_result = cc_lt;     // LT
            4'h2: cc_result = cc_le;     // LE
            4'h3: cc_result = cc_ule;    // ULE
            4'h4: cc_result = cc_v;      // OV (overflow)
            4'h5: cc_result = cc_s;      // MI (minus)
            4'h6: cc_result = cc_z;      // Z (zero)
            4'h7: cc_result = cc_c;      // C (carry)
            4'h8: cc_result = 1'b1;      // T - Always (true)
            4'h9: cc_result = cc_ge;     // GE
            4'hA: cc_result = cc_gt;     // GT
            4'hB: cc_result = cc_ugt;    // UGT
            4'hC: cc_result = cc_nv;     // NOV
            4'hD: cc_result = cc_ns;     // PL (plus)
            4'hE: cc_result = cc_nz;     // NZ
            4'hF: cc_result = cc_nc;     // NC
            default: cc_result = 1'b0;
        endcase
    end
    
    // Microcode condition evaluation
    reg ucond_true;
    always @(*) begin
        case (cond_sel[4:0])  // Lower 5 bits select condition
            5'd0:  ucond_true = cc_z;
            5'd1:  ucond_true = cc_nz;
            5'd2:  ucond_true = cc_c;
            5'd3:  ucond_true = cc_nc;
            5'd4:  ucond_true = cc_s;
            5'd5:  ucond_true = cc_ns;
            5'd6:  ucond_true = cc_v;
            5'd7:  ucond_true = cc_nv;
            5'd8:  ucond_true = cc_lt;
            5'd9:  ucond_true = cc_ge;
            5'd10: ucond_true = cc_le;
            5'd11: ucond_true = cc_gt;
            5'd12: ucond_true = cc_ult;
            5'd13: ucond_true = cc_uge;
            5'd14: ucond_true = cc_ule;
            5'd15: ucond_true = cc_ugt;
            5'd16: ucond_true = cc_result;    // CC - instruction condition (IR[3:0])
            5'd17: ucond_true = FCW[FCW_SYS];     // SYS - system mode
            5'd18: ucond_true = ~FCW[FCW_SYS];    // NRM - normal mode
            5'd19: ucond_true = cc_result;    // CC_JR - JR condition (IR[11:8])
            5'd20: ucond_true = FCW[FCW_SEG];     // SEG - segmented mode
            5'd21: ucond_true = ~FCW[FCW_SEG];    // NSEG - non-segmented mode
            5'd22: ucond_true = cc_result;    // CC_T2 - block compare condition (TEMP2[3:0])
            // Interrupt conditions (active low inputs)
            5'd24: ucond_true = int_pending;      // INT - any enabled interrupt pending
            5'd25: ucond_true = ~nmi_n;           // NMI - non-maskable interrupt
            5'd26: ucond_true = ~vi_n && FCW[FCW_VIE];   // VI - vectored interrupt (if enabled)
            5'd27: ucond_true = ~nvi_n && FCW[FCW_NVIE]; // NVI - non-vectored interrupt (if enabled)
            5'd31: ucond_true = 1'b1;             // ALWAYS - unconditional
            default: ucond_true = 1'b0;
        endcase
        
        // Negate if bit 5 is set
        if (cond_sel[5])
            ucond_true = ~ucond_true;
    end
    
    //=========================================================================
    // BUS STATE MACHINE
    //=========================================================================
    
    // Bus cycle timing:
    // ucycle 0: Address phase - drive address, assert AS_n
    // ucycle 1: Address hold - release AS_n
    // ucycle 2: Data phase - assert DS_n, read/write data
    // ucycle 3: Data complete - sample read data, release DS_n
    
    wire bus_active = (bus_op != BUS_IDLE);
    wire bus_is_write = (bus_op == BUS_WRITE) || (bus_op == BUS_STK_WR) ||
                        (bus_op == BUS_IO_WR) || (bus_op == BUS_SIO_WR);
    wire bus_cycle_done = (ucycle == UCYC_COMPLETE) || (!bus_active && ucycle == UCYC_ADDR);
    
    // Address/Data bus control
    reg [15:0] ad_out;
    reg        ad_oe;
    
    assign ad = ad_oe ? ad_out : 16'bz;
    
    // Status code generation
    always @(*) begin
        case (bus_op)
            BUS_IFETCH: st = ST_INST_1ST;
            BUS_PFETCH: st = ST_PROG_RD;
            BUS_AFETCH: st = ST_PROG_RD;   // Address fetch (same status as PFETCH)
            BUS_READ:   st = ST_DATA_RD;
            BUS_WRITE:  st = ST_DATA_WR;
            BUS_STK_RD: st = ST_STK_RD;
            BUS_STK_WR: st = ST_STK_WR;
            BUS_IO_RD:  st = ST_IO_REF;    // Standard I/O read
            BUS_IO_WR:  st = ST_IO_REF;    // Standard I/O write
            BUS_SIO_RD: st = ST_SPEC_IO;   // Special I/O read
            BUS_SIO_WR: st = ST_SPEC_IO;   // Special I/O write
            default:    st = ST_INTERNAL;
        endcase
    end
    
    //=========================================================================
    // JR/CALR OFFSET CALCULATION
    //=========================================================================

    // JR displacement is in IR[7:0], sign-extended and doubled
    // JR format: 0xEcdd where c=condition, dd=8-bit displacement
    wire [15:0] jr_offset = {{7{IR[7]}}, IR[7:0], 1'b0};

    // CALR displacement is in IR[11:0], sign-extended and doubled
    // CALR format: 0xDddd where ddd=12-bit displacement
    // Note: CALR uses subtraction (target = PC - offset) unlike JR which adds
    wire [15:0] calr_offset = {{3{IR[11]}}, IR[11:0], 1'b0};

    // INC/DEC value is in IR[3:0], needs +1 (0-15 means 1-16)
    // INC instruction: 0xA9 rrrr_cccc where r = register, c = count-1
    // DEC instruction: 0xAB rrrr_cccc where r = register, c = count-1
    // COM instruction: 0x8Dd0 - IR[3:0]=0, so inc_value=1 (used to compute ~X = X XOR (0-1))
    wire [15:0] inc_value = {12'h000, IR[3:0]} + 16'h0001;

    // Compact LDB immediate (0xCxxx): 8-bit immediate from IR[7:0]
    // Format: 1100_dddd_iiii_iiii where dddd=dest reg, iiii_iiii=byte immediate
    wire [15:0] compact_ldb_imm = {8'h00, IR[7:0]};  // Zero-extended immediate byte

    // LDK immediate (0xBDxx): 4-bit constant from IR[3:0]
    // Format: 10111101_Rddd_dddd where Rd=dest reg (IR[7:4]), d=4-bit constant (IR[3:0])
    wire [15:0] ldk_imm = {12'h000, IR[3:0]};  // Zero-extended 4-bit immediate

    // DJNZ displacement is in IR[6:0], unsigned, doubled
    // DJNZ format: 0xFr8d where r=register, d=7-bit displacement
    // Target = PC - (IR[6:0] * 2), always backward jump
    wire [15:0] djnz_offset = {8'h00, IR[6:0], 1'b0};

    // Size value based on size_latch: BYTE=1, WORD=2, LONG=4
    wire [15:0] size_value = (size_latch == SIZE_BYTE) ? 16'h0001 :
                             (size_latch == SIZE_WORD) ? 16'h0002 : 16'h0004;

    // Signed size value: +SIZE if dir_latch=0 (INC), -SIZE if dir_latch=1 (DEC)
    wire [15:0] size_dir = dir_latch ? -size_value : size_value;

    //=========================================================================
    // MAIN STATE MACHINE
    //=========================================================================
    
    // Destination write enable
    wire dst_write = bus_cycle_done && (dst_sel != DST_NONE);
    
    // Flags write enable
    wire flags_write = bus_cycle_done && (dst_sel == DST_FLAGS || misc[0]);
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Reset state
            uPC <= 9'h000;
            uSP <= 2'd0;
            ucycle <= UCYC_ADDR;
            
            PC <= 16'h0000;
            FCW <= 16'h0000;
            PSAP <= 16'h0000;
            trap_num <= 2'b0;
            MAR <= 16'h0000;
            MDR <= 16'h0000;
            IR <= 16'h0000;
            TEMP <= 16'h0000;
            TEMP2 <= 16'h0000;
            
            R15_sys <= 16'h0000;
            R15_nrm <= 16'h0000;
`ifdef Z8001_MODE
            R14_sys <= 16'h0000;
            R14_nrm <= 16'h0000;
`endif

            mul_result_reg <= 32'h0;

            op_latch <= 5'd0;
            size_latch <= SIZE_WORD;
            dir_latch <= 1'b0;
            rep_latch <= 1'b0;
            priv_latch <= 1'b0;
            block_latch <= 1'b0;
            block_cp_latch <= 1'b0;
            bx_latch <= 1'b0;
            bx_byte_dest_latch <= 1'b0;
            compact_ldb_latch <= 1'b0;
            ldk_latch <= 1'b0;

            halted <= 1'b0;
            bus_granted <= 1'b0;
            
            as_n <= 1'b1;
            ds_n <= 1'b1;
            rw_n <= 1'b1;
            mreq_n <= 1'b1;
            b_w_n <= 1'b1;
            busack_n <= 1'b1;
            
            ad_oe <= 1'b0;
            ad_out <= 16'h0000;
            
        end else if (halted) begin
            // Halted - wait for interrupt or reset
            if (!nmi_n || (!vi_n && FCW[FCW_VIE]) || (!nvi_n && FCW[FCW_NVIE])) begin
                halted <= 1'b0;
                uPC <= 9'h000;  // Go to FETCH (will be interrupted)
            end
            
        end else if (!busreq_n && !bus_granted) begin
            // Bus request - grant bus
            bus_granted <= 1'b1;
            busack_n <= 1'b0;
            ad_oe <= 1'b0;
            as_n <= 1'b1;
            ds_n <= 1'b1;
            mreq_n <= 1'b1;
            
        end else if (bus_granted && busreq_n) begin
            // Bus released
            bus_granted <= 1'b0;
            busack_n <= 1'b1;
            
        end else if (!bus_granted) begin
            //=================================================================
            // NORMAL EXECUTION
            //=================================================================
            
            // Bus timing state machine
            if (bus_active) begin
                case (ucycle)
                    UCYC_ADDR: begin
                        // T1: Address phase
                        ad_oe <= 1'b1;
                        ad_out <= MAR;
                        as_n <= 1'b0;
                        mreq_n <= 1'b0;
                        rw_n <= ~bus_is_write;
                        b_w_n <= (size_latch != SIZE_BYTE);  // 0=byte, 1=word/long
                        ucycle <= UCYC_HOLD;
                    end

                    UCYC_HOLD: begin
                        // T2: Address hold, prepare for data
                        as_n <= 1'b1;
                        if (bus_is_write) begin
                            // Byte write routing: place byte in correct bus lane
                            // Even address: byte in AD[15:8], Odd address: byte in AD[7:0]
                            if (size_latch == SIZE_BYTE)
                                ad_out <= MAR[0] ? {8'h00, MDR[7:0]} : {MDR[7:0], 8'h00};
                            else
                                ad_out <= MDR;
                        end else begin
                            ad_oe <= 1'b0;  // Tristate for read
                        end
                        ds_n <= 1'b0;
                        ucycle <= UCYC_DATA;
                    end

                    UCYC_DATA: begin
                        // T3: Data phase (wait for WAIT_n if needed)
                        if (wait_n) begin
                            ucycle <= UCYC_COMPLETE;
                        end
                        // else stay in T3 (wait state)
                    end

                    UCYC_COMPLETE: begin
                        // T4: Complete cycle
                        if (!bus_is_write) begin
                            // For byte DATA/IO reads (not PFETCH/AFETCH), extract the correct byte
                            // Z8000 is big-endian: even addr = high byte, odd addr = low byte
                            if ((bus_op == BUS_READ || bus_op == BUS_IO_RD || bus_op == BUS_SIO_RD) &&
                                size_latch == SIZE_BYTE)
                                MDR <= MAR[0] ? {8'h00, ad[7:0]} : {8'h00, ad[15:8]};
                            else
                                MDR <= ad;  // Word read or PFETCH/AFETCH
                        end
                        ds_n <= 1'b1;
                        mreq_n <= 1'b1;
                        ad_oe <= 1'b0;
                        ucycle <= UCYC_ADDR;
`ifdef Z8001_MODE
                        // TODO: Z8001 segmented mode address fetch handling
                        // When bus_op == BUS_AFETCH and FCW[FCW_SEG]:
                        //   1. Check if MDR indicates long-form segmented address
                        //   2. If so, auto-fetch second word (segment offset)
                        //   3. Combine into full segmented address
                        // For now, AFETCH behaves like PFETCH (single word)
`endif
                    end
                endcase
            end else begin
                // No bus operation - complete in one cycle
                ucycle <= UCYC_ADDR;
            end
            
            //=================================================================
            // REGISTER WRITEBACK (on bus cycle done)
            //=================================================================
            
            if (bus_cycle_done) begin
                // Update multiply result register when MUL or MULU is executed
                if (actual_alu_op == ALU_MUL || actual_alu_op == ALU_MULU) begin
                    mul_result_reg <= mul_result_comb;
                end

                // Write ALU result to destination
                if (dst_sel != DST_NONE && dst_sel != DST_FLAGS) begin
                    case (dst_sel)
                        SEL_RS:    if (size_latch == SIZE_BYTE) begin  // BYTE mode
                                       if (ir_rs_byte_lo)
                                           R[{1'b0, ir_rs_byte_reg}][7:0] <= alu_result[7:0];
                                       else
                                           R[{1'b0, ir_rs_byte_reg}][15:8] <= alu_result[7:0];
                                   end else if (ir_rs == 4'd15)
                                       if (FCW[FCW_SYS]) R15_sys <= alu_result;
                                       else R15_nrm <= alu_result;
`ifdef Z8001_MODE
                                   else if (ir_rs == 4'd14)
                                       if (FCW[FCW_SYS]) R14_sys <= alu_result;
                                       else R14_nrm <= alu_result;
`endif
                                   else R[ir_rs] <= alu_result;
                        SEL_RD:    if (size_latch == SIZE_BYTE) begin  // BYTE mode
                                       if (ir_rd_byte_lo)
                                           R[{1'b0, ir_rd_byte_reg}][7:0] <= alu_result[7:0];
                                       else
                                           R[{1'b0, ir_rd_byte_reg}][15:8] <= alu_result[7:0];
                                   end else if (ir_rd == 4'd15)
                                       if (FCW[FCW_SYS]) R15_sys <= alu_result;
                                       else R15_nrm <= alu_result;
`ifdef Z8001_MODE
                                   else if (ir_rd == 4'd14)
                                       if (FCW[FCW_SYS]) R14_sys <= alu_result;
                                       else R14_nrm <= alu_result;
`endif
                                   else R[ir_rd] <= alu_result;
                        // Rn - byte mode when SIZE_BYTE and either: not BX mode, or BX with byte destination
                        SEL_RN:    if (size_latch == SIZE_BYTE && !block_latch && !block_cp_latch && (!bx_latch || bx_byte_dest_latch)) begin
                                       if (ir_rn_byte_lo)
                                           R[{1'b0, ir_rn_byte_reg}][7:0] <= alu_result[7:0];
                                       else
                                           R[{1'b0, ir_rn_byte_reg}][15:8] <= alu_result[7:0];
                                   end else if (ir_rn == 4'd15)
                                       if (FCW[FCW_SYS]) R15_sys <= alu_result;
                                       else R15_nrm <= alu_result;
`ifdef Z8001_MODE
                                   else if (ir_rn == 4'd14)
                                       if (FCW[FCW_SYS]) R14_sys <= alu_result;
                                       else R14_nrm <= alu_result;
`endif
                                   else R[ir_rn] <= alu_result;
                        SEL_PC:    PC <= alu_result;
                        SEL_SP:    if (FCW[FCW_SYS]) R15_sys <= alu_result;
                                   else R15_nrm <= alu_result;
                        SEL_MAR:   MAR <= alu_result;
                        SEL_MDR:   MDR <= alu_result;
                        SEL_IR:    IR <= alu_result;
                        SEL_RSL:   if (ir_rs_lo == 4'd15)  // Rs+1 (low word)
                                       if (FCW[FCW_SYS]) R15_sys <= alu_result;
                                       else R15_nrm <= alu_result;
`ifdef Z8001_MODE
                                   else if (ir_rs_lo == 4'd14)
                                       if (FCW[FCW_SYS]) R14_sys <= alu_result;
                                       else R14_nrm <= alu_result;
`endif
                                   else R[ir_rs_lo] <= alu_result;
                        SEL_TEMP:  // For byte memory operations, extract correct byte based on address
                                   // MAR[0]=0 (even): byte in high position [15:8]
                                   // MAR[0]=1 (odd): byte in low position [7:0]
                                   // Note: Byte extraction from MDR is now done when MDR is
                                   // loaded from memory (in UCYC_COMPLETE for BUS_READ).
                                   // No additional extraction needed here.
                                   TEMP <= alu_result;
                        SEL_RDL:   if (ir_rd_lo == 4'd15)  // Rd+1 (low word)
                                       if (FCW[FCW_SYS]) R15_sys <= alu_result;
                                       else R15_nrm <= alu_result;
`ifdef Z8001_MODE
                                   else if (ir_rd_lo == 4'd14)
                                       if (FCW[FCW_SYS]) R14_sys <= alu_result;
                                       else R14_nrm <= alu_result;
`endif
                                   else R[ir_rd_lo] <= alu_result;
                        SEL_FCW:   FCW <= alu_result;
                        SEL_TEMP2: TEMP2 <= alu_result;
                        DST_PSAP:  PSAP <= alu_result;
                        DST_TRAP_NUM: trap_num <= alu_result[1:0];
                        DST_SP_SYS: R15_sys <= alu_result;  // Always system stack
                        // Pointer registers - ALWAYS write full word (used for addresses)
                        DST_PTR_RS: if (ir_rs == 4'd15)
                                       if (FCW[FCW_SYS]) R15_sys <= alu_result;
                                       else R15_nrm <= alu_result;
`ifdef Z8001_MODE
                                   else if (ir_rs == 4'd14)
                                       if (FCW[FCW_SYS]) R14_sys <= alu_result;
                                       else R14_nrm <= alu_result;
`endif
                                   else R[ir_rs] <= alu_result;
                        DST_PTR_RD: if (ir_rd == 4'd15)
                                       if (FCW[FCW_SYS]) R15_sys <= alu_result;
                                       else R15_nrm <= alu_result;
`ifdef Z8001_MODE
                                   else if (ir_rd == 4'd14)
                                       if (FCW[FCW_SYS]) R14_sys <= alu_result;
                                       else R14_nrm <= alu_result;
`endif
                                   else R[ir_rd] <= alu_result;
                        SEL_RD2:   if (ir_rd_lo2 == 4'd15)  // Rd+2 (for quad operations)
                                       if (FCW[FCW_SYS]) R15_sys <= alu_result;
                                       else R15_nrm <= alu_result;
`ifdef Z8001_MODE
                                   else if (ir_rd_lo2 == 4'd14)
                                       if (FCW[FCW_SYS]) R14_sys <= alu_result;
                                       else R14_nrm <= alu_result;
`endif
                                   else R[ir_rd_lo2] <= alu_result;
                        SEL_RD3:   if (ir_rd_lo3 == 4'd15)  // Rd+3 (for quad operations)
                                       if (FCW[FCW_SYS]) R15_sys <= alu_result;
                                       else R15_nrm <= alu_result;
`ifdef Z8001_MODE
                                   else if (ir_rd_lo3 == 4'd14)
                                       if (FCW[FCW_SYS]) R14_sys <= alu_result;
                                       else R14_nrm <= alu_result;
`endif
                                   else R[ir_rd_lo3] <= alu_result;
                    endcase
                end
                
                // Update flags if requested
                if (dst_sel == DST_FLAGS || misc[0]) begin
                    // Only update C for actual arithmetic/shift operations,
                    // not for pass-through operations (used by FLAGS <- TEMP in shift loops)
                    if (actual_alu_op != ALU_NOP && actual_alu_op != ALU_PASS_A && actual_alu_op != ALU_PASS_B) begin
                        FCW[FCW_C] <= alu_carry;
                    end
                    FCW[FCW_Z] <= alu_zero;
                    FCW[FCW_S] <= alu_sign;
                    FCW[FCW_V] <= alu_overflow;

                    // D flag (Decimal Adjust): Set by byte arithmetic only
                    // ADDB/ADCB set D=0, SUBB/SBCB set D=1
                    // D flag tells DAB whether to adjust for add or subtract
                    if (size_latch == SIZE_BYTE) begin  // Byte operation
                        case (actual_alu_op)
                            ALU_ADD, ALU_ADC: FCW[FCW_DA] <= 1'b0;
                            ALU_SUB, ALU_SBC: FCW[FCW_DA] <= 1'b1;
                            // Other byte ops (AND, OR, XOR, etc.) don't change D
                        endcase
                    end
                end
                // For shift/rotate operations, always update carry even when
                // writing to a register (not FLAGS). This ensures the carry
                // reflects the last bit shifted out, not the loop counter.
                else if (is_shift_rotate && dst_sel != DST_NONE) begin
                    FCW[FCW_C] <= alu_carry;
                end
                
                //=============================================================
                // MICROSEQUENCER CONTROL
                //=============================================================
                
                case (next_ctrl)
                    NEXT_NEXT: begin
                        uPC <= uPC + 1;
                    end
                    
                    NEXT_FETCH: begin
                        uPC <= `UADDR_FETCH;  // From ucode_defs.v
                    end
                    
                    NEXT_DECODE: begin
                        // Load decoder outputs into latches
                        op_latch <= decode_op;
                        size_latch <= decode_size;
                        dir_latch <= decode_dir;
                        rep_latch <= decode_rep;
                        priv_latch <= decode_priv;
                        block_latch <= decode_block;
                        block_cp_latch <= decode_block_cp;
                        bx_latch <= decode_bx;
                        bx_byte_dest_latch <= decode_bx_byte_dest;
                        compact_ldb_latch <= decode_compact_ldb;
                        ldk_latch <= decode_ldk;
                        // Check for privileged instruction violation
                        // If privileged instruction in normal mode, redirect to trap
                        if (decode_priv && !FCW[FCW_SYS]) begin
                            uPC <= `UADDR_TRAP_PRIV;
                        end else begin
                            // Jump to instruction handler
                            uPC <= decode_entry;
                        end
                    end
                    
                    NEXT_JUMP: begin
                        if (ucond_true)
                            uPC <= branch_target;
                        else
                            uPC <= uPC + 1;
                    end
                    
                    NEXT_CALL: begin
                        uPC_stack[uSP] <= uPC + 1;
                        uSP <= uSP + 1;
                        uPC <= branch_target;
                    end
                    
                    NEXT_RETURN: begin
                        uSP <= uSP - 1;
                        uPC <= uPC_stack[uSP - 1];
                    end
                    
                    NEXT_WAIT: begin
                        // Stay at current uPC until condition true
                        if (ucond_true)
                            uPC <= uPC + 1;
                    end
                    
                    NEXT_HALT: begin
                        halted <= 1'b1;
                    end
                endcase
            end
        end
    end
    
    //=========================================================================
    // STATUS OUTPUTS
    //=========================================================================
    
    assign n_s = ~FCW[FCW_SYS];   // Active low = system mode
    assign halt_n = ~halted;
    
    //=========================================================================
    // DEBUG (optional - remove for synthesis)
    //=========================================================================
    
    `ifdef DEBUG
    always @(posedge clk) begin
        if (bus_cycle_done && !halted) begin
            $display("Time %0t: uPC=%03X ucycle=%d bus_op=%d next=%d",
                     $time, uPC, ucycle, bus_op, next_ctrl);
            if (next_ctrl == NEXT_DECODE)
                $display("  DECODE: IR=%04X -> entry=%03X op=%d", IR, decode_entry, decode_op);
            // Debug when a test fails (increment r1)
            // INC R1, #1 is 0xA910
            if (IR == 16'hA910 && next_ctrl == NEXT_DECODE) begin
                $display("  TEST FAIL: r1++ at PC=%04X r2=%04X r0=%04X", PC, R[2], R[0]);
            end
        end
    end
    `endif

endmodule
