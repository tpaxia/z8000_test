// Z8000 Test Harness Controller
// Handles serial protocol for instruction testing

`timescale 1ns / 1ps

module test_harness_ctrl #(
    parameter ADDR_REG_SETUP = 16'h0010,
    parameter ADDR_FCW_SETUP = 16'h0030,
    parameter ADDR_TEST_ADDR = 16'h0032,
    parameter ADDR_REG_DUMP  = 16'h0080,
    parameter ADDR_FCW_DUMP  = 16'h00A0
)(
    input             clk,
    input             rst_n,

    // UART interface
    input      [7:0]  uart_rx_data,
    input             uart_rx_valid,
    output reg        uart_rx_ready,
    output reg [7:0]  uart_tx_data,
    output reg        uart_tx_valid,
    input             uart_tx_ready,

    // CPU control
    output reg        cpu_rst_n,
    input             cpu_halt_n,
    output reg        cpu_busreq_n,
    input             cpu_busack_n,

    // Memory interface
    output reg        mem_we,
    output reg [14:0] mem_addr,
    output reg [15:0] mem_wdata,
    input      [15:0] mem_rdata,
    output reg        mem_byte
);

// States
localparam ST_IDLE      = 5'd0;
localparam ST_CMD1      = 5'd1;
localparam ST_CMD2      = 5'd2;
localparam ST_ARG1      = 5'd3;
localparam ST_ARG2      = 5'd4;
localparam ST_EXEC      = 5'd5;
localparam ST_RESP      = 5'd6;
localparam ST_TX_WAIT   = 5'd7;
localparam ST_CRLF      = 5'd8;
localparam ST_RUN       = 5'd9;
localparam ST_WAIT_HALT = 5'd10;
localparam ST_LOAD_HEX  = 5'd11;
localparam ST_DUMP      = 5'd12;
localparam ST_RESET     = 5'd13;
localparam ST_MEM_READ  = 5'd14;
localparam ST_MEM_READ2 = 5'd15;
localparam ST_RX_WAIT   = 5'd16;  // Wait for UART to clear valid
localparam ST_STARTUP   = 5'd17;  // Initial CPU reset release
localparam ST_MEM_TEST  = 5'd18;  // Memory test state
localparam ST_MEM_TEST2 = 5'd19;  // Memory test read-back state

localparam DONE_FLAG_ADDR = 15'h00B0;  // Address of done flag
localparam DONE_FLAG_VAL  = 16'hDEAD;  // Done flag value

reg [4:0]  state, next_st, after_crlf, after_rx;
reg [15:0] startup_cnt;  // Startup counter for CPU reset release
reg [15:0] poll_cnt;     // Counter for polling interval
reg [7:0]  cmd1, cmd2;
reg [15:0] arg1, arg2;

// Response buffer
reg [7:0]  resp [0:15];
reg [3:0]  resp_len, resp_idx;

// Timeout
reg [23:0] timeout;
localparam TIMEOUT_MAX = 24'd5_000_000;  // ~185ms at 27MHz

// Hex load
reg [15:0] hex_remain;
reg [14:0] hex_addr;
reg [7:0]  hex_hi;
reg        hex_phase;

// Dump state
reg [3:0]  dump_idx;

// Memory test state
reg [2:0]  mt_phase;      // Test phase (0-7)
reg [15:0] mt_expected;   // Expected read value
reg        mt_fail;       // Test failed flag
reg [1:0]  mt_wait;       // Wait counter for BRAM latency

// Reset counter
reg [7:0]  rst_cnt;

// CRLF
reg        send_lf;

// Helpers
function [7:0] to_hex;
    input [3:0] v;
    to_hex = (v < 10) ? (8'h30 + v) : (8'h41 + v - 10);
endfunction

function [3:0] from_hex;
    input [7:0] c;
    if (c >= 8'h30 && c <= 8'h39) from_hex = c - 8'h30;
    else if (c >= 8'h41 && c <= 8'h46) from_hex = c - 8'h41 + 10;
    else if (c >= 8'h61 && c <= 8'h66) from_hex = c - 8'h61 + 10;
    else from_hex = 0;
endfunction

function is_hex;
    input [7:0] c;
    is_hex = (c >= 8'h30 && c <= 8'h39) ||
             (c >= 8'h41 && c <= 8'h46) ||
             (c >= 8'h61 && c <= 8'h66);
endfunction

function is_ws;
    input [7:0] c;
    is_ws = (c == 8'h20) || (c == 8'h09);
endfunction

function is_eol;
    input [7:0] c;
    is_eol = (c == 8'h0D) || (c == 8'h0A);
endfunction

// Main FSM
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        state <= ST_STARTUP;
        next_st <= ST_IDLE;
        after_crlf <= ST_IDLE;
        after_rx <= ST_IDLE;
        cmd1 <= 0; cmd2 <= 0;
        arg1 <= 0; arg2 <= 0;
        resp_len <= 0; resp_idx <= 0;
        timeout <= 0;
        hex_remain <= 0; hex_addr <= 0;
        hex_hi <= 0; hex_phase <= 0;
        dump_idx <= 0;
        rst_cnt <= 0;
        send_lf <= 0;
        startup_cnt <= 16'd1000;  // Hold CPU in reset for 1000 cycles after system reset
        poll_cnt <= 0;

        uart_rx_ready <= 0;
        uart_tx_data <= 0;
        uart_tx_valid <= 0;

        cpu_rst_n <= 0;  // Keep CPU in reset until startup completes
        cpu_busreq_n <= 1;

        mem_we <= 0;
        mem_addr <= 0;
        mem_wdata <= 0;
        mem_byte <= 0;
    end else begin
        // Defaults
        uart_rx_ready <= 0;
        uart_tx_valid <= 0;
        mem_we <= 0;

        case (state)
            ST_STARTUP: begin
                // Hold CPU in reset during startup
                // CPU stays in reset until EX command
                if (startup_cnt > 0) begin
                    startup_cnt <= startup_cnt - 1;
                end else begin
                    // cpu_rst_n stays 0 - harness has memory access
                    state <= ST_IDLE;
                end
            end

            ST_IDLE: begin
                if (uart_rx_valid) begin
                    uart_rx_ready <= 1;
                    if (!is_ws(uart_rx_data) && !is_eol(uart_rx_data)) begin
                        cmd1 <= uart_rx_data;
                        after_rx <= ST_CMD1;
                        state <= ST_RX_WAIT;
                    end
                end
            end

            ST_RX_WAIT: begin
                // Wait for UART to clear valid after we asserted ready
                if (!uart_rx_valid) begin
                    state <= after_rx;
                end
            end

            ST_CMD1: begin
                if (uart_rx_valid) begin
                    uart_rx_ready <= 1;
                    if (is_eol(uart_rx_data)) begin
                        cmd2 <= 0;
                        state <= ST_EXEC;
                    end else if (is_ws(uart_rx_data)) begin
                        cmd2 <= 0;
                        arg1 <= 0;
                        after_rx <= ST_ARG1;
                        state <= ST_RX_WAIT;
                    end else begin
                        cmd2 <= uart_rx_data;
                        after_rx <= ST_CMD2;
                        state <= ST_RX_WAIT;
                    end
                end
            end

            ST_CMD2: begin
                if (uart_rx_valid) begin
                    uart_rx_ready <= 1;
                    if (is_eol(uart_rx_data)) begin
                        state <= ST_EXEC;
                    end else if (is_ws(uart_rx_data)) begin
                        arg1 <= 0;
                        after_rx <= ST_ARG1;
                        state <= ST_RX_WAIT;
                    end else begin
                        // Ignore extra characters
                        after_rx <= ST_CMD2;
                        state <= ST_RX_WAIT;
                    end
                end
            end

            ST_ARG1: begin
                if (uart_rx_valid) begin
                    uart_rx_ready <= 1;
                    if (is_hex(uart_rx_data)) begin
                        arg1 <= {arg1[11:0], from_hex(uart_rx_data)};
                        after_rx <= ST_ARG1;
                        state <= ST_RX_WAIT;
                    end else if (is_ws(uart_rx_data)) begin
                        arg2 <= 0;
                        after_rx <= ST_ARG2;
                        state <= ST_RX_WAIT;
                    end else if (is_eol(uart_rx_data)) begin
                        state <= ST_EXEC;
                    end else begin
                        after_rx <= ST_ARG1;
                        state <= ST_RX_WAIT;
                    end
                end
            end

            ST_ARG2: begin
                if (uart_rx_valid) begin
                    uart_rx_ready <= 1;
                    if (is_hex(uart_rx_data)) begin
                        arg2 <= {arg2[11:0], from_hex(uart_rx_data)};
                        after_rx <= ST_ARG2;
                        state <= ST_RX_WAIT;
                    end else if (is_eol(uart_rx_data)) begin
                        state <= ST_EXEC;
                    end else begin
                        after_rx <= ST_ARG2;
                        state <= ST_RX_WAIT;
                    end
                end
            end

            ST_EXEC: begin
                resp_len <= 0;
                resp_idx <= 0;
                after_crlf <= ST_IDLE;

                case ({cmd1 & 8'hDF, cmd2 & 8'hDF})  // Uppercase
                    // WR nn xxxx
                    16'h5752: begin
                        mem_addr <= ADDR_REG_SETUP[14:0] + {arg1[3:0], 1'b0};
                        mem_wdata <= arg2;
                        mem_we <= 1;
                        mem_byte <= 0;
                        resp[0] <= "O"; resp[1] <= "K";
                        resp_len <= 2;
                        state <= ST_RESP;
                    end

                    // RR nn
                    16'h5252: begin
                        mem_addr <= ADDR_REG_DUMP[14:0] + {arg1[3:0], 1'b0};
                        mem_byte <= 0;
                        next_st <= ST_RESP;
                        state <= ST_MEM_READ;
                    end

                    // WM aaaa xxxx
                    16'h574D: begin
                        mem_addr <= arg1[14:0];
                        mem_wdata <= arg2;
                        mem_we <= 1;
                        mem_byte <= 0;
                        resp[0] <= "O"; resp[1] <= "K";
                        resp_len <= 2;
                        state <= ST_RESP;
                    end

                    // RM aaaa
                    16'h524D: begin
                        mem_addr <= arg1[14:0];
                        mem_byte <= 0;
                        next_st <= ST_RESP;
                        state <= ST_MEM_READ;
                    end

                    // WB aaaa xx
                    16'h5742: begin
                        mem_addr <= arg1[14:0];
                        mem_wdata <= {8'h00, arg2[7:0]};
                        mem_we <= 1;
                        mem_byte <= 1;
                        resp[0] <= "O"; resp[1] <= "K";
                        resp_len <= 2;
                        state <= ST_RESP;
                    end

                    // RB aaaa
                    16'h5242: begin
                        mem_addr <= arg1[14:0];
                        mem_byte <= 1;
                        next_st <= ST_RESP;
                        state <= ST_MEM_READ;
                    end

                    // WF xxxx
                    16'h5746: begin
                        mem_addr <= ADDR_FCW_SETUP[14:0];
                        mem_wdata <= arg1;
                        mem_we <= 1;
                        mem_byte <= 0;
                        resp[0] <= "O"; resp[1] <= "K";
                        resp_len <= 2;
                        state <= ST_RESP;
                    end

                    // RF
                    16'h5246: begin
                        mem_addr <= ADDR_FCW_DUMP[14:0];
                        mem_byte <= 0;
                        next_st <= ST_RESP;
                        state <= ST_MEM_READ;
                    end

                    // WP xxxx
                    16'h5750: begin
                        mem_addr <= ADDR_TEST_ADDR[14:0];
                        mem_wdata <= arg1;
                        mem_we <= 1;
                        mem_byte <= 0;
                        resp[0] <= "O"; resp[1] <= "K";
                        resp_len <= 2;
                        state <= ST_RESP;
                    end

                    // RP
                    16'h5250: begin
                        resp[0] <= "0"; resp[1] <= "0";
                        resp[2] <= "0"; resp[3] <= "0";
                        resp_len <= 4;
                        state <= ST_RESP;
                    end

                    // EX, GO
                    16'h4558, 16'h474F: begin
                        // Clear done flag first
                        mem_addr <= DONE_FLAG_ADDR;
                        mem_wdata <= 16'h0000;
                        mem_we <= 1;
                        mem_byte <= 0;
                        cpu_rst_n <= 0;
                        rst_cnt <= 100;
                        next_st <= ST_RUN;
                        state <= ST_RESET;
                    end

                    // RS - Reset CPU and keep in reset for harness access
                    16'h5253: begin
                        cpu_rst_n <= 0;
                        resp[0] <= "O"; resp[1] <= "K";
                        resp_len <= 2;
                        state <= ST_RESP;  // Stay in reset, don't go through ST_RESET
                    end

                    // ST - Show H if CPU is in reset or halted, R if running
                    16'h5354: begin
                        resp[0] <= (cpu_rst_n && cpu_halt_n) ? "R" : "H";
                        resp_len <= 1;
                        state <= ST_RESP;
                    end

                    // HT
                    16'h4854: begin
                        cpu_rst_n <= 0;
                        rst_cnt <= 10;
                        resp[0] <= "O"; resp[1] <= "K";
                        resp_len <= 2;
                        next_st <= ST_RESP;
                        state <= ST_RESET;
                    end

                    // LH nnnn aaaa
                    16'h4C48: begin
                        hex_remain <= arg1;
                        hex_addr <= arg2[14:0];
                        hex_phase <= 0;
                        if (arg1 > 0) begin
                            state <= ST_LOAD_HEX;
                        end else begin
                            resp[0] <= "O"; resp[1] <= "K";
                            resp_len <= 2;
                            state <= ST_RESP;
                        end
                    end

                    // DA
                    16'h4441: begin
                        dump_idx <= 0;
                        mem_addr <= ADDR_REG_DUMP[14:0];
                        mem_byte <= 0;
                        state <= ST_DUMP;
                    end

                    // MT - Memory Test
                    16'h4D54: begin
                        mt_phase <= 0;
                        mt_fail <= 0;
                        state <= ST_MEM_TEST;
                    end

                    default: begin
                        resp[0] <= "E"; resp[1] <= "R"; resp[2] <= "R";
                        resp_len <= 3;
                        state <= ST_RESP;
                    end
                endcase
            end

            ST_MEM_READ: begin
                state <= ST_MEM_READ2;
            end

            ST_MEM_READ2: begin
                if (mem_byte) begin
                    if (mem_addr[0]) begin
                        resp[0] <= to_hex(mem_rdata[7:4]);
                        resp[1] <= to_hex(mem_rdata[3:0]);
                    end else begin
                        resp[0] <= to_hex(mem_rdata[15:12]);
                        resp[1] <= to_hex(mem_rdata[11:8]);
                    end
                    resp_len <= 2;
                end else begin
                    resp[0] <= to_hex(mem_rdata[15:12]);
                    resp[1] <= to_hex(mem_rdata[11:8]);
                    resp[2] <= to_hex(mem_rdata[7:4]);
                    resp[3] <= to_hex(mem_rdata[3:0]);
                    resp_len <= 4;
                end
                state <= next_st;
            end

            ST_RESET: begin
                if (rst_cnt > 0) begin
                    rst_cnt <= rst_cnt - 1;
                end else begin
                    cpu_rst_n <= 1;
                    state <= next_st;
                end
            end

            ST_RUN: begin
                timeout <= 0;
                poll_cnt <= 0;
                state <= ST_WAIT_HALT;
            end

            ST_WAIT_HALT: begin
                timeout <= timeout + 1;

                // Check if CPU halted (halt_n goes low)
                if (!cpu_halt_n) begin
                    // CPU halted - keep in reset so harness has memory access
                    cpu_rst_n <= 0;
                    resp[0] <= "H"; resp[1] <= "A";
                    resp[2] <= "L"; resp[3] <= "T";
                    resp_len <= 4;
                    state <= ST_RESP;  // Go directly to response, CPU stays in reset
                end else if (timeout >= TIMEOUT_MAX) begin
                    // Timeout - reset CPU and report
                    cpu_rst_n <= 0;
                    resp[0] <= "T"; resp[1] <= "O";
                    resp[2] <= "U"; resp[3] <= "T";
                    resp_len <= 4;
                    state <= ST_RESP;  // Go directly to response, CPU stays in reset
                end
            end

            ST_LOAD_HEX: begin
                if (uart_rx_valid) begin
                    uart_rx_ready <= 1;
                    if (!hex_phase) begin
                        hex_hi <= uart_rx_data;
                        hex_phase <= 1;
                        after_rx <= ST_LOAD_HEX;
                        state <= ST_RX_WAIT;
                    end else begin
                        mem_addr <= hex_addr;
                        mem_wdata <= {hex_hi, uart_rx_data};
                        mem_we <= 1;
                        mem_byte <= 0;
                        hex_phase <= 0;
                        hex_addr <= hex_addr + 2;
                        hex_remain <= hex_remain - 1;
                        if (hex_remain == 1) begin
                            resp[0] <= "O"; resp[1] <= "K";
                            resp_len <= 2;
                            state <= ST_RESP;
                        end else begin
                            after_rx <= ST_LOAD_HEX;
                            state <= ST_RX_WAIT;
                        end
                    end
                end
            end

            ST_DUMP: begin
                if (dump_idx < 16) begin
                    resp[0] <= "R";
                    if (dump_idx < 10) begin
                        resp[1] <= 8'h30 + dump_idx;
                        resp[2] <= "=";
                        resp[3] <= to_hex(mem_rdata[15:12]);
                        resp[4] <= to_hex(mem_rdata[11:8]);
                        resp[5] <= to_hex(mem_rdata[7:4]);
                        resp[6] <= to_hex(mem_rdata[3:0]);
                        resp[7] <= " ";
                        resp_len <= 8;
                    end else begin
                        resp[1] <= "1";
                        resp[2] <= 8'h30 + dump_idx - 10;
                        resp[3] <= "=";
                        resp[4] <= to_hex(mem_rdata[15:12]);
                        resp[5] <= to_hex(mem_rdata[11:8]);
                        resp[6] <= to_hex(mem_rdata[7:4]);
                        resp[7] <= to_hex(mem_rdata[3:0]);
                        resp[8] <= " ";
                        resp_len <= 9;
                    end

                    if (dump_idx < 15) begin
                        after_crlf <= ST_DUMP;
                        dump_idx <= dump_idx + 1;
                        mem_addr <= ADDR_REG_DUMP[14:0] + {(dump_idx + 4'd1), 1'b0};
                    end else begin
                        after_crlf <= ST_IDLE;
                    end
                    state <= ST_RESP;
                end else begin
                    state <= ST_IDLE;
                end
            end

            // Memory Test - writes test patterns and reads them back
            // Phase 0-3: Write patterns, Phase 4-7: Read and verify
            // Use addresses 0x0F00-0x0F06 (within 2K word SDPB range)
            ST_MEM_TEST: begin
                case (mt_phase)
                    // Write phase - write test patterns to addresses 0x0F00-0x0F06
                    3'd0: begin
                        mem_addr <= 15'h0F00;
                        mem_wdata <= 16'h5A5A;
                        mem_we <= 1;
                        mem_byte <= 0;
                        mt_phase <= 3'd1;
                    end
                    3'd1: begin
                        mem_we <= 0;
                        mem_addr <= 15'h0F02;
                        mem_wdata <= 16'hA5A5;
                        mem_we <= 1;
                        mt_phase <= 3'd2;
                    end
                    3'd2: begin
                        mem_we <= 0;
                        mem_addr <= 15'h0F04;
                        mem_wdata <= 16'h1234;
                        mem_we <= 1;
                        mt_phase <= 3'd3;
                    end
                    3'd3: begin
                        mem_we <= 0;
                        mem_addr <= 15'h0F06;
                        mem_wdata <= 16'hFEDC;
                        mem_we <= 1;
                        mt_phase <= 3'd4;
                    end
                    // Read phase - read back and verify
                    3'd4: begin
                        mem_we <= 0;
                        mem_addr <= 15'h0F00;
                        mt_expected <= 16'h5A5A;
                        mt_phase <= 3'd5;
                        mt_wait <= 2'd2;
                        state <= ST_MEM_TEST2;
                    end
                    3'd5: begin
                        mem_addr <= 15'h0F02;
                        mt_expected <= 16'hA5A5;
                        mt_phase <= 3'd6;
                        mt_wait <= 2'd2;
                        state <= ST_MEM_TEST2;
                    end
                    3'd6: begin
                        mem_addr <= 15'h0F04;
                        mt_expected <= 16'h1234;
                        mt_phase <= 3'd7;
                        mt_wait <= 2'd2;
                        state <= ST_MEM_TEST2;
                    end
                    3'd7: begin
                        mem_addr <= 15'h0F06;
                        mt_expected <= 16'hFEDC;
                        mt_phase <= 3'd0;
                        mt_wait <= 2'd2;
                        state <= ST_MEM_TEST2;
                    end
                endcase
            end

            ST_MEM_TEST2: begin
                // Wait for BRAM read latency
                if (mt_wait > 0) begin
                    mt_wait <= mt_wait - 1;
                end else begin
                    // Check read data
                    if (mem_rdata != mt_expected) begin
                        mt_fail <= 1;
                    end

                    if (mt_phase == 3'd0) begin
                        // Done - report result with last read value for debug
                        if (mt_fail || (mem_rdata != mt_expected)) begin
                            // FAIL:xxxx (show last read value)
                            resp[0] <= "F"; resp[1] <= "A"; resp[2] <= "I"; resp[3] <= "L";
                            resp[4] <= ":";
                            resp[5] <= to_hex(mem_rdata[15:12]);
                            resp[6] <= to_hex(mem_rdata[11:8]);
                            resp[7] <= to_hex(mem_rdata[7:4]);
                            resp[8] <= to_hex(mem_rdata[3:0]);
                            resp_len <= 9;
                        end else begin
                            resp[0] <= "P"; resp[1] <= "A"; resp[2] <= "S"; resp[3] <= "S";
                            resp_len <= 4;
                        end
                        state <= ST_RESP;
                    end else begin
                        state <= ST_MEM_TEST;
                    end
                end
            end

            ST_RESP: begin
                if (resp_idx < resp_len) begin
                    uart_tx_data <= resp[resp_idx];
                    uart_tx_valid <= 1;
                    state <= ST_TX_WAIT;
                end else begin
                    send_lf <= 0;
                    state <= ST_CRLF;
                end
            end

            ST_TX_WAIT: begin
                if (uart_tx_ready && !uart_tx_valid) begin
                    resp_idx <= resp_idx + 1;
                    state <= ST_RESP;
                end
            end

            ST_CRLF: begin
                if (!send_lf) begin
                    uart_tx_data <= 8'h0D;
                    uart_tx_valid <= 1;
                    send_lf <= 1;
                end else if (uart_tx_ready && !uart_tx_valid) begin
                    uart_tx_data <= 8'h0A;
                    uart_tx_valid <= 1;
                    state <= after_crlf;
                end
            end

            default: state <= ST_IDLE;
        endcase
    end
end

endmodule
