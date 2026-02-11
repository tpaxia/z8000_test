// Z8000 Test Harness Testbench
// Tests firmware command protocol

`timescale 1ns / 1ps

module z8000_test_harness_tb;

    localparam CLK_PERIOD = 37.037;  // 27MHz
    localparam CLK_FRE = 27;
    localparam BAUD_RATE = 115200;
    localparam BIT_CYCLES = CLK_FRE * 1000000 / BAUD_RATE;
    localparam real BIT_PERIOD = BIT_CYCLES * CLK_PERIOD;

    reg clk, rst_n;
    reg uart_rx;
    wire uart_tx;

    // UART signals between modules
    wire [7:0] uart_rx_data, uart_tx_data;
    wire uart_rx_valid, uart_rx_ready;
    wire uart_tx_valid, uart_tx_ready;

    // Z8000 signals
    wire z8k_rst_n;
    reg  z8k_halt_n;
    wire z8k_mem_we;
    wire [14:0] z80_addr;
    wire [15:0] z8k_mem_wdata;
    reg [15:0] z8k_mem_rdata;

    // Instrumentation (simulated values for testbench)
    reg        z8k_bus_active;
    reg [31:0] z8k_cycle_count;
    reg [15:0] z8k_fetch_count;
    wire [31:0] z8k_cycle_limit;
    wire       z8k_cycle_timeout;

    // Trace buffer (stub for testbench)
    wire [9:0]  trace_rd_addr;
    reg  [35:0] trace_rd_data;
    reg  [9:0]  trace_wr_count;

    // I/O port registers (stub for testbench)
    wire [3:0]  io_port_reg_sel;
    wire [7:0]  io_port_wbyte;
    reg  [15:0] io_port_rdata;
    wire        io_port_wr_lo;
    wire        io_port_wr_hi;

    // Simulate cycle timeout: timeout when cycle_count >= cycle_limit (if limit != 0)
    assign z8k_cycle_timeout = (z8k_cycle_limit != 32'd0) && (z8k_cycle_count >= z8k_cycle_limit);

    // Simple memory for testing
    reg [15:0] test_mem [0:16383];

    // Clock
    initial begin
        clk = 0;
        forever #(CLK_PERIOD/2) clk = ~clk;
    end

    // UART TX
    uart_tx #(.CLK_FRE(CLK_FRE), .BAUD_RATE(BAUD_RATE)) u_uart_tx (
        .clk(clk), .rst_n(rst_n),
        .tx_data(uart_tx_data), .tx_data_valid(uart_tx_valid),
        .tx_data_ready(uart_tx_ready), .tx_pin(uart_tx)
    );

    // UART RX
    uart_rx #(.CLK_FRE(CLK_FRE), .BAUD_RATE(BAUD_RATE)) u_uart_rx (
        .clk(clk), .rst_n(rst_n),
        .rx_data(uart_rx_data), .rx_data_valid(uart_rx_valid),
        .rx_data_ready(uart_rx_ready), .rx_pin(uart_rx)
    );

    // Z80 Harness
    z80_harness dut (
        .clk(clk), .rst_n(rst_n),
        .uart_rx_data(uart_rx_data), .uart_rx_valid(uart_rx_valid),
        .uart_rx_ready(uart_rx_ready),
        .uart_tx_data(uart_tx_data), .uart_tx_valid(uart_tx_valid),
        .uart_tx_ready(uart_tx_ready),
        .z8k_rst_n(z8k_rst_n), .z8k_halt_n(z8k_halt_n),
        .z8k_st(4'b0000),
        .z8k_mem_we(z8k_mem_we), .z80_addr(z80_addr),
        .z8k_mem_wdata(z8k_mem_wdata), .z8k_mem_rdata(z8k_mem_rdata),
        .z8k_bus_active(z8k_bus_active),
        .z8k_cycle_count(z8k_cycle_count),
        .z8k_fetch_count(z8k_fetch_count),
        .z8k_cycle_limit(z8k_cycle_limit),
        .z8k_cycle_timeout(z8k_cycle_timeout),
        .trace_rd_addr(trace_rd_addr),
        .trace_rd_data(trace_rd_data),
        .trace_wr_count(trace_wr_count),
        .io_port_reg_sel(io_port_reg_sel),
        .io_port_wbyte(io_port_wbyte),
        .io_port_rdata(io_port_rdata),
        .io_port_wr_lo(io_port_wr_lo),
        .io_port_wr_hi(io_port_wr_hi),
        .z80_alive()
    );

    // Memory read/write handling
    always @(posedge clk) begin
        if (z8k_mem_we)
            test_mem[z80_addr[13:0]] <= z8k_mem_wdata;
        z8k_mem_rdata <= test_mem[z80_addr[13:0]];
    end

    // UART send task
    task uart_send_byte;
        input [7:0] data;
        integer i;
        begin
            uart_rx = 1'b0;  // Start bit
            #(BIT_PERIOD);
            for (i = 0; i < 8; i = i + 1) begin
                uart_rx = data[i];
                #(BIT_PERIOD);
            end
            uart_rx = 1'b1;  // Stop bit
            #(BIT_PERIOD);
        end
    endtask

    // Send a string with CR terminator
    task uart_send_cmd;
        input [8*20-1:0] cmd;  // Up to 20 chars
        integer i, len;
        reg [7:0] ch;
        begin
            // Find length (non-zero chars from MSB)
            len = 0;
            for (i = 19; i >= 0; i = i - 1) begin
                ch = cmd[i*8 +: 8];
                if (ch != 0) len = len + 1;
            end
            // Send chars from MSB to LSB
            for (i = 19; i >= 0; i = i - 1) begin
                ch = cmd[i*8 +: 8];
                if (ch != 0) begin
                    $display("  TX: '%c' (0x%02X)", ch, ch);
                    uart_send_byte(ch);
                end
            end
            // Send CR
            $display("  TX: <CR> (0x0D)");
            uart_send_byte(8'h0D);
        end
    endtask

    // UART receive task with timeout
    task uart_recv_byte;
        output [7:0] data;
        output valid;
        integer i;
        integer timeout;
        begin
            data = 8'h00;
            valid = 0;
            timeout = 0;
            // Wait for start bit with timeout
            while (uart_tx == 1'b1 && timeout < 2000000) begin
                #100;
                timeout = timeout + 100;
            end
            if (timeout < 2000000) begin
                #(BIT_PERIOD / 2);  // Middle of start bit
                if (uart_tx == 1'b0) begin
                    valid = 1;
                    for (i = 0; i < 8; i = i + 1) begin
                        #(BIT_PERIOD);
                        data[i] = uart_tx;
                    end
                    #(BIT_PERIOD);  // Stop bit
                end
            end
        end
    endtask

    // Receive until CRLF
    reg recv_done;
    task uart_recv_response;
        output [8*20-1:0] response;
        output integer len;
        reg [7:0] ch;
        reg valid;
        begin
            response = 0;
            len = 0;
            recv_done = 0;
            while (!recv_done) begin
                uart_recv_byte(ch, valid);
                if (!valid) begin
                    $display("  RX: TIMEOUT");
                    recv_done = 1;
                end else if (ch == 8'h0D) begin
                    $display("  RX: <CR> (0x0D)");
                    // Expect LF next
                    uart_recv_byte(ch, valid);
                    if (valid && ch == 8'h0A)
                        $display("  RX: <LF> (0x0A)");
                    recv_done = 1;
                end else begin
                    $display("  RX: '%c' (0x%02X)", ch, ch);
                    response = (response << 8) | ch;
                    len = len + 1;
                end
            end
        end
    endtask

    // Test
    reg [8*20-1:0] response;
    integer resp_len;
    integer pass_count, fail_count;

    initial begin
        $dumpfile("z8000_harness.vcd");
        $dumpvars(0, z8000_test_harness_tb);

        rst_n = 0;
        uart_rx = 1;
        z8k_halt_n = 1;  // Not halted initially
        z8k_bus_active = 1;  // Simulate bus active for testing
        z8k_cycle_count = 32'h00001234;  // Test value
        z8k_fetch_count = 16'h0042;  // Test value
        trace_rd_data = 36'd0;
        trace_wr_count = 10'd0;
        io_port_rdata = 16'd0;
        pass_count = 0;
        fail_count = 0;

        // Initialize test memory
        test_mem[14'h0000] = 16'h1234;
        test_mem[14'h0001] = 16'h5678;

        $display("");
        $display("========================================");
        $display("Z80 Harness Firmware Test");
        $display("========================================");
        $display("");

        #1000;
        rst_n = 1;
        #10000;

        // ----------------------------------------
        // Test 1: ST (Status) - should return 'H' (halted due to z8k_rst_n=0)
        // ----------------------------------------
        $display("----------------------------------------");
        $display("Test 1: ST (Status) - Z8000 in reset");
        $display("----------------------------------------");
        uart_send_cmd("ST");
        uart_recv_response(response, resp_len);
        if (response[7:0] == "H") begin
            $display("PASS: Got 'H' (halted/reset)");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: Expected 'H', got response=0x%X len=%d", response, resp_len);
            fail_count = fail_count + 1;
        end
        #50000;

        // ----------------------------------------
        // Test 2: RS (Reset) - should return 'OK'
        // ----------------------------------------
        $display("");
        $display("----------------------------------------");
        $display("Test 2: RS (Reset Z8000)");
        $display("----------------------------------------");
        uart_send_cmd("RS");
        uart_recv_response(response, resp_len);
        if (response == {"O", "K"}) begin
            $display("PASS: Got 'OK'");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: Expected 'OK', got 0x%X", response);
            fail_count = fail_count + 1;
        end
        #50000;

        // ----------------------------------------
        // Test 3: Invalid command - should return 'ERR'
        // ----------------------------------------
        $display("");
        $display("----------------------------------------");
        $display("Test 3: Invalid command 'XX'");
        $display("----------------------------------------");
        uart_send_cmd("XX");
        uart_recv_response(response, resp_len);
        if (response == {"E", "R", "R"}) begin
            $display("PASS: Got 'ERR'");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: Expected 'ERR', got 0x%X", response);
            fail_count = fail_count + 1;
        end
        #50000;

        // ----------------------------------------
        // Test 4: WM (Write Memory) - write 0xABCD to addr 0x0100
        // ----------------------------------------
        $display("");
        $display("----------------------------------------");
        $display("Test 4: WM0100ABCD (Write Memory)");
        $display("----------------------------------------");
        uart_send_cmd("WM0100ABCD");
        uart_recv_response(response, resp_len);
        if (response == {"O", "K"}) begin
            $display("PASS: Got 'OK'");
            // Address 0x0100 word address = test_mem[0x0100]
            if (test_mem[14'h0100] == 16'hABCD) begin
                $display("PASS: Memory[0x0100] = 0x%04X", test_mem[14'h0100]);
                pass_count = pass_count + 1;
            end else begin
                $display("FAIL: Memory[0x0100] = 0x%04X, expected 0xABCD", test_mem[14'h0100]);
                fail_count = fail_count + 1;
            end
        end else begin
            $display("FAIL: Expected 'OK', got 0x%X", response);
            fail_count = fail_count + 1;
        end
        #50000;

        // ----------------------------------------
        // Test 5: RM (Read Memory) - read back from 0x0100
        // ----------------------------------------
        $display("");
        $display("----------------------------------------");
        $display("Test 5: RM0100 (Read Memory)");
        $display("----------------------------------------");
        uart_send_cmd("RM0100");
        uart_recv_response(response, resp_len);
        if (response == {"A", "B", "C", "D"}) begin
            $display("PASS: Got 'ABCD'");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: Expected 'ABCD', got 0x%X len=%d", response, resp_len);
            fail_count = fail_count + 1;
        end
        #50000;

        // ----------------------------------------
        // Test 6: MT (Memory Test) - should pass
        // ----------------------------------------
        $display("");
        $display("----------------------------------------");
        $display("Test 6: MT (Memory Test)");
        $display("----------------------------------------");
        uart_send_cmd("MT");
        uart_recv_response(response, resp_len);
        if (response == {"P", "A", "S", "S"}) begin
            $display("PASS: Got 'PASS'");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: Expected 'PASS', got 0x%X len=%d", response, resp_len);
            fail_count = fail_count + 1;
        end
        #50000;

        // ----------------------------------------
        // Summary
        // ----------------------------------------
        $display("");
        $display("========================================");
        $display("Test Summary: %0d PASS, %0d FAIL", pass_count, fail_count);
        $display("========================================");

        #100000;
        $finish;
    end

    // Watchdog
    initial begin
        #200000000;  // 200ms
        $display("*** WATCHDOG TIMEOUT ***");
        $finish;
    end

    // Debug: Show RAM contents at start
    initial begin
        #2000;  // After reset
        $display("RAM[0x00-0x0F]: %02X %02X %02X %02X %02X %02X %02X %02X  %02X %02X %02X %02X %02X %02X %02X %02X",
            dut.ram[0], dut.ram[1], dut.ram[2], dut.ram[3],
            dut.ram[4], dut.ram[5], dut.ram[6], dut.ram[7],
            dut.ram[8], dut.ram[9], dut.ram[10], dut.ram[11],
            dut.ram[12], dut.ram[13], dut.ram[14], dut.ram[15]);
    end

    // Debug: trace CPU instruction fetches after command received
    // Track when we've received full command (CR)
    reg cmd_received = 0;
    integer post_cmd_fetches = 0;
    always @(posedge clk) begin
        if (uart_rx_valid && uart_rx_data == 8'h0D)
            cmd_received <= 1;
        if (rst_n && !dut.cpu_m1_n && !dut.cpu_mreq_n && !dut.cpu_rd_n && cmd_received) begin
            if (post_cmd_fetches < 100) begin
                $display("Time %0t: FETCH PC=%04X opcode=%02X", $time, dut.cpu_addr, dut.cpu_din);
                post_cmd_fetches = post_cmd_fetches + 1;
            end
        end
    end

    // Debug: trace I/O operations - all after CR received
    integer io_post_cmd = 0;
    always @(posedge clk) begin
        if (rst_n && !dut.cpu_iorq_n && dut.cpu_m1_n) begin
            if (cmd_received && io_post_cmd < 50) begin
                if (!dut.cpu_rd_n)
                    $display("Time %0t: IO RD port=%02X data=%02X", $time, dut.cpu_addr[7:0], dut.io_dout);
                if (!dut.cpu_wr_n)
                    $display("Time %0t: IO WR port=%02X data=%02X", $time, dut.cpu_addr[7:0], dut.cpu_dout);
                io_post_cmd = io_post_cmd + 1;
            end else if (!cmd_received) begin
                // Before cmd received, only show non-status and writes
                if (!dut.cpu_rd_n && dut.cpu_addr[7:0] != 8'h01)
                    $display("Time %0t: IO RD port=%02X data=%02X", $time, dut.cpu_addr[7:0], dut.io_dout);
                if (!dut.cpu_wr_n)
                    $display("Time %0t: IO WR port=%02X data=%02X", $time, dut.cpu_addr[7:0], dut.cpu_dout);
            end
        end
    end

    // Debug: trace UART RX valid transitions
    reg prev_rx_valid = 0;
    always @(posedge clk) begin
        if (uart_rx_valid != prev_rx_valid) begin
            $display("Time %0t: uart_rx_valid = %b, data = 0x%02X", $time, uart_rx_valid, uart_rx_data);
            prev_rx_valid <= uart_rx_valid;
        end
    end

    // Debug: trace UART RX state machine
    reg [2:0] prev_rx_state = 0;
    always @(posedge clk) begin
        if (u_uart_rx.state != prev_rx_state) begin
            $display("Time %0t: UART_RX state = %d (1=IDLE,2=START,3=REC,4=STOP,5=DATA)", $time, u_uart_rx.state);
            prev_rx_state <= u_uart_rx.state;
        end
    end

    // Debug: trace uart_rx pin transitions (unlimited)
    reg prev_uart_rx = 1;
    always @(posedge clk) begin
        if (uart_rx != prev_uart_rx) begin
            $display("Time %0t: uart_rx = %b", $time, uart_rx);
            prev_uart_rx <= uart_rx;
        end
    end

endmodule
