//============================================================================
// Z8000 Test Harness Testbench
// Simulates the test harness with UART commands
//============================================================================

`timescale 1ns / 1ps

module test_harness_tb;

    // Clock: 27MHz = ~37ns period
    localparam real CLK_PERIOD = 37.037;
    localparam CLK_FRE = 27;  // MHz
    localparam BAUD_RATE = 115200;
    // Calculate bit period in ns (must match DUT calculation)
    localparam BIT_CYCLES = CLK_FRE * 1000000 / BAUD_RATE;  // 234 cycles
    localparam real BIT_PERIOD = BIT_CYCLES * CLK_PERIOD;   // ~8666 ns

    // Signals
    reg         clk;
    reg         rst;
    reg         uart_rx;
    wire        uart_tx;
    wire        led, led2, led3;

    // UART receive buffer
    reg [7:0]   rx_buffer [0:255];
    integer     rx_count;

    // DUT
    test_harness_top dut (
        .clk        (clk),
        .rst        (rst),
        .uart_rx    (uart_rx),
        .uart_tx    (uart_tx),
        .led        (led),
        .led2       (led2),
        .led3       (led3)
    );


    // Clock generation
    initial begin
        clk = 0;
        forever #(CLK_PERIOD/2) clk = ~clk;
    end

    // Debug: trace harness memory writes
    always @(posedge clk) begin
        if (dut.harness_mem_we) begin
            $display("Time %0t: HARNESS WRITE addr=%04X data=%04X",
                     $time, dut.harness_mem_addr, dut.harness_mem_wdata);
        end
    end

    // Debug: trace CPU memory writes (throttled)
    reg [31:0] last_write_time;
    always @(posedge clk) begin
        if (dut.cpu_mem_write && ($time - last_write_time > 100000)) begin
            $display("Time %0t: CPU WRITE addr=%04X data=%04X",
                     $time, dut.latched_addr, dut.ad_bus);
            last_write_time <= $time;
        end
    end

    // Debug: trace harness reads (when controller sets address)
    reg [14:0] prev_harness_addr;
    always @(posedge clk) begin
        if (dut.harness_active && dut.ctrl.mem_addr != prev_harness_addr) begin
            $display("Time %0t: HARNESS READ setup addr=%04X mem_addr=%04X harness_active=%b",
                     $time, dut.ctrl.mem_addr, dut.mem_addr, dut.harness_active);
            prev_harness_addr <= dut.ctrl.mem_addr;
        end
    end

    // Debug: show mem_rdata when controller is in read state
    always @(posedge clk) begin
        if (dut.ctrl.state == 15) begin  // ST_MEM_READ2
            $display("Time %0t: MEM_READ2 harness_active=%b harness_addr=%04X latched=%04X bram_addr=%d rdata=%04X mem[72]=%02X%02X",
                     $time, dut.harness_active, dut.harness_mem_addr, dut.latched_addr,
                     dut.mem_addr, dut.mem_rdata, dut.mem_hi[72], dut.mem_lo[72]);
        end
    end

    // Debug: trace I/O cycles
    reg prev_is_io;
    always @(posedge clk) begin
        if (dut.is_io_cycle && !prev_is_io) begin
            $display("Time %0t: I/O CYCLE START st=%04b addr=%04X ad=%04X ds_n=%b rw_n=%b mreq_n=%b wait_n=%b",
                     $time, dut.cpu_st, dut.latched_addr, dut.ad_bus, dut.cpu.ds_n, dut.cpu.rw_n, dut.cpu.mreq_n, dut.cpu_wait_n);
        end
        if (dut.is_io_cycle && !dut.cpu.ds_n && dut.cpu.rw_n) begin
            $display("Time %0t: I/O READ addr=%04X io_rdata=%04X data_to_cpu=%04X",
                     $time, dut.latched_addr, dut.io_rdata, dut.data_to_cpu);
        end
        prev_is_io <= dut.is_io_cycle;
    end

    // Debug: trace CPU state changes
    reg prev_cpu_rst_n;
    always @(posedge clk) begin
        if (dut.cpu_rst_n != prev_cpu_rst_n) begin
            $display("Time %0t: CPU RST_N changed to %b", $time, dut.cpu_rst_n);
        end
        prev_cpu_rst_n <= dut.cpu_rst_n;
    end

    // Debug: trace CPU execution - show all AS_n falling edges
    reg prev_as_n;
    always @(posedge clk) begin
        // Show AS_n falling edges (address phase)
        if (dut.cpu_rst_n && !dut.cpu.as_n && prev_as_n) begin
            $display("Time %0t: AS st=%04b addr=%04X mreq_n=%b wait_n=%b",
                     $time, dut.cpu_st, dut.ad_bus, dut.cpu.mreq_n, dut.cpu_wait_n);
        end
        prev_as_n <= dut.cpu.as_n;
    end

    // UART transmit task (send byte to DUT)
    task uart_send_byte;
        input [7:0] data;
        integer i;
        begin
            // Start bit
            uart_rx = 1'b0;
            #(BIT_PERIOD);
            // Data bits (LSB first)
            for (i = 0; i < 8; i = i + 1) begin
                uart_rx = data[i];
                #(BIT_PERIOD);
            end
            // Stop bit
            uart_rx = 1'b1;
            #(BIT_PERIOD);
        end
    endtask

    // UART transmit command with CR
    task uart_send_cmd;
        input [255:0] cmd;
        integer i;
        reg [7:0] ch;
        begin
            $write("TX: ");
            for (i = 31; i >= 0; i = i - 1) begin
                ch = cmd[i*8 +: 8];
                if (ch != 0) begin
                    $write("%c", ch);
                    uart_send_byte(ch);
                end
            end
            $display("");
            uart_send_byte(8'h0D);  // CR
        end
    endtask

    // UART receive byte task using time delays
    task uart_recv_byte;
        output [7:0] data;
        output valid;
        integer i;
        begin
            data = 8'h00;
            valid = 0;

            // Wait for falling edge (start bit)
            wait (uart_tx == 1'b0);

            // Wait to middle of start bit
            #(BIT_PERIOD / 2);

            // Verify start bit
            if (uart_tx == 1'b0) begin
                valid = 1;
                // Sample each data bit
                for (i = 0; i < 8; i = i + 1) begin
                    #(BIT_PERIOD);
                    data[i] = uart_tx;
                end
                // Wait through stop bit
                #(BIT_PERIOD);
            end
        end
    endtask

    // Wait for and capture UART response
    task uart_wait_response;
        input integer timeout_ns;
        reg [7:0] byte_val;
        reg byte_valid;
        integer start_time;
        integer done;
        begin
            rx_count = 0;
            done = 0;
            start_time = $time;

            while (!done && ($time - start_time) < timeout_ns) begin
                if (uart_tx == 1'b0) begin
                    uart_recv_byte(byte_val, byte_valid);
                    if (byte_valid) begin
                        rx_buffer[rx_count] = byte_val;
                        rx_count = rx_count + 1;
                        start_time = $time;  // Reset timeout
                        if (byte_val == 8'h0A) done = 1;
                    end
                end else begin
                    #100;  // Small delay
                end
            end
        end
    endtask

    // Print received response
    task print_response;
        integer i;
        begin
            $write("RX: ");
            for (i = 0; i < rx_count; i = i + 1) begin
                if (rx_buffer[i] >= 8'h20 && rx_buffer[i] < 8'h7F)
                    $write("%c", rx_buffer[i]);
                else if (rx_buffer[i] == 8'h0D || rx_buffer[i] == 8'h0A)
                    ; // Skip
                else
                    $write("[%02X]", rx_buffer[i]);
            end
            $display("");
        end
    endtask

    // Main test
    initial begin
        $dumpfile("test_harness.vcd");
        $dumpvars(0, test_harness_tb);

        // Initialize
        rst = 1;
        uart_rx = 1;
        rx_count = 0;

        $display("");
        $display("========================================");
        $display("Z8000 Test Harness Simulation");
        $display("Clock period: %.3f ns", CLK_PERIOD);
        $display("Bit period: %.3f ns (%0d cycles)", BIT_PERIOD, BIT_CYCLES);
        $display("========================================");
        $display("");

        // Reset
        #5000;
        rst = 0;
        #100000;  // Wait for system to stabilize

        $display("Reset complete, starting tests...");
        $display("");

        // Test 1: Status check
        $display("Test 1: Status check (ST) - expect H (in reset)");
        uart_send_cmd("ST");
        uart_wait_response(5000000);  // 5ms timeout
        print_response();
        $display("");

        // Test 1b: Memory test
        $display("Test 1b: Memory test (MT) - expect PASS");
        uart_send_cmd("MT");
        uart_wait_response(5000000);
        print_response();
        $display("");

        // Test 2: Write register R0
        $display("Test 2: Write R0 = 0x1234 (WR 0 1234)");
        uart_send_cmd("WR 0 1234");
        uart_wait_response(5000000);
        print_response();
        $display("");

        // Test 3: Read memory to verify
        $display("Test 3: Read memory 0x0010 (RM 0010) - expect 1234");
        uart_send_cmd("RM 0010");
        uart_wait_response(5000000);
        print_response();
        $display("");

        // Test 4: Write R1
        $display("Test 4: Write R1 = 0x5678 (WR 1 5678)");
        uart_send_cmd("WR 1 5678");
        uart_wait_response(5000000);
        print_response();
        $display("");

        // Test 5: Load test code
        $display("Test 5: Load ADD R0,R1 instruction");
        uart_send_cmd("WM 0200 8110");  // ADD R0, R1 (opcode: 81=ADD, 1=src R1, 0=dst R0)
        uart_wait_response(5000000);
        print_response();
        uart_send_cmd("WM 0202 5E08");  // JP
        uart_wait_response(5000000);
        print_response();
        uart_send_cmd("WM 0204 00C0");  // 0x00C0
        uart_wait_response(5000000);
        print_response();
        $display("");

        // Test 6: Execute
        $display("Test 6: Execute (EX)");
        $display("  R0=0x1234 + R1=0x5678 => expect R0=0x68AC");
        uart_send_cmd("EX");
        uart_wait_response(20000000);  // 20ms timeout
        print_response();
        $display("");

        // Test 7: Read R0 result
        $display("Test 7: Read R0 result (RR 0) - expect 68AC");
        uart_send_cmd("RR 0");
        uart_wait_response(5000000);
        print_response();
        $display("");

        // Test 8: Read R1 result
        $display("Test 8: Read R1 result (RR 1) - expect 5678");
        uart_send_cmd("RR 1");
        uart_wait_response(5000000);
        print_response();
        $display("");

        // Test 9: I/O Port Test - Read from port 0x00 (returns io_data_reg = 0x1234)
        // Reset and setup for I/O test
        $display("Test 9: I/O Port Test - IN R0, port 0x0000 (expect 1234)");
        uart_send_cmd("RS");  // Reset CPU
        uart_wait_response(5000000);
        print_response();
        // IN Rd, port (direct): 0x3Bd4 where d=register, then port address in next word
        // IN R0, port: 0x3B04
        uart_send_cmd("WM 0200 3B04");  // IN R0, port (word, direct addressing)
        uart_wait_response(5000000);
        print_response();
        uart_send_cmd("WM 0202 0000");  // port 0x0000 (io_data_reg = 0x1234)
        uart_wait_response(5000000);
        print_response();
        uart_send_cmd("WM 0204 5E08");  // JP 0x00C0
        uart_wait_response(5000000);
        print_response();
        uart_send_cmd("WM 0206 00C0");
        uart_wait_response(5000000);
        print_response();
        uart_send_cmd("EX");
        uart_wait_response(10000000);
        print_response();
        $display("Read R0 (expect 1234 from io_data_reg):");
        uart_send_cmd("RR 0");
        uart_wait_response(5000000);
        print_response();
        $display("");

        // Test 10: I/O Port Test - Write to port
        $display("Test 10: I/O Port Test - OUT port, R1 (write 0xABCD)");
        uart_send_cmd("RS");  // Reset CPU
        uart_wait_response(5000000);
        print_response();
        uart_send_cmd("WR 1 ABCD");  // R1 = 0xABCD
        uart_wait_response(5000000);
        print_response();
        // OUT port, Rs (direct): 0x3Bd6 where d=source register
        // OUT port, R1: 0x3B16
        uart_send_cmd("WM 0200 3B16");  // OUT port, R1
        uart_wait_response(5000000);
        print_response();
        uart_send_cmd("WM 0202 0000");  // port 0x0000 (io_data_reg)
        uart_wait_response(5000000);
        print_response();
        // Now read it back: IN R0, port 0x0000
        uart_send_cmd("WM 0204 3B04");  // IN R0, port (direct)
        uart_wait_response(5000000);
        print_response();
        uart_send_cmd("WM 0206 0000");  // port 0x0000
        uart_wait_response(5000000);
        print_response();
        uart_send_cmd("WM 0208 5E08");  // JP 0x00C0
        uart_wait_response(5000000);
        print_response();
        uart_send_cmd("WM 020A 00C0");
        uart_wait_response(5000000);
        print_response();
        uart_send_cmd("EX");
        uart_wait_response(10000000);
        print_response();
        $display("Read R0 (expect ABCD - value written to io_data_reg):");
        uart_send_cmd("RR 0");
        uart_wait_response(5000000);
        print_response();
        $display("");

        $display("========================================");
        $display("Simulation complete");
        $display("========================================");

        #100000;
        $finish;
    end

    // Watchdog
    initial begin
        #200000000;  // 200ms
        $display("*** SIMULATION TIMEOUT ***");
        $finish;
    end

endmodule
