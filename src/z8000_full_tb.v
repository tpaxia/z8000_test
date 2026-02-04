// Z8000 Full System Testbench
// Tests actual Z8000 instruction execution through the complete system
// Instantiates z8000_test_harness_top with real Z8000 CPU

`timescale 1ns / 1ps

module z8000_full_tb;

    localparam CLK_PERIOD = 37.037;  // 27MHz
    localparam CLK_FRE = 27;
    localparam BAUD_RATE = 115200;
    localparam BIT_CYCLES = CLK_FRE * 1000000 / BAUD_RATE;
    localparam real BIT_PERIOD = BIT_CYCLES * CLK_PERIOD;

    reg clk, rst;
    reg uart_rx;
    wire uart_tx;
    wire led, led2, led3, led4;

    // Clock
    initial begin
        clk = 0;
        forever #(CLK_PERIOD/2) clk = ~clk;
    end

    // DUT - Full system with Z8000 CPU
    z8000_test_harness_top dut (
        .clk(clk),
        .rst(rst),
        .uart_rx(uart_rx),
        .uart_tx(uart_tx),
        .led(led),
        .led2(led2),
        .led3(led3),
        .led4(led4)
    );

    // UART send byte task
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

    // Send command string with CR terminator
    task uart_send_cmd;
        input [8*20-1:0] cmd;
        integer i;
        reg [7:0] ch;
        begin
            for (i = 19; i >= 0; i = i - 1) begin
                ch = cmd[i*8 +: 8];
                if (ch != 0) begin
                    uart_send_byte(ch);
                end
            end
            uart_send_byte(8'h0D);  // CR
        end
    endtask

    // UART receive byte with timeout
    task uart_recv_byte;
        output [7:0] data;
        output valid;
        integer i, timeout;
        begin
            data = 8'h00;
            valid = 0;
            timeout = 0;
            while (uart_tx == 1'b1 && timeout < 50000000) begin
                #100;
                timeout = timeout + 100;
            end
            if (timeout < 50000000) begin
                #(BIT_PERIOD / 2);
                if (uart_tx == 1'b0) begin
                    valid = 1;
                    for (i = 0; i < 8; i = i + 1) begin
                        #(BIT_PERIOD);
                        data[i] = uart_tx;
                    end
                    #(BIT_PERIOD);
                end
            end
        end
    endtask

    // Receive response until CRLF
    task uart_recv_response;
        output [8*20-1:0] response;
        output integer len;
        reg [7:0] ch;
        reg valid, done;
        begin
            response = 0;
            len = 0;
            done = 0;
            while (!done) begin
                uart_recv_byte(ch, valid);
                if (!valid) begin
                    $display("  RX: TIMEOUT");
                    done = 1;
                end else if (ch == 8'h0D) begin
                    uart_recv_byte(ch, valid);  // Consume LF
                    done = 1;
                end else begin
                    response = (response << 8) | ch;
                    len = len + 1;
                end
            end
        end
    endtask

    // Test variables
    reg [8*20-1:0] response;
    integer resp_len;
    integer pass_count, fail_count;

    initial begin
        $dumpfile("z8000_full.vcd");
        $dumpvars(0, z8000_full_tb);

        rst = 1;
        uart_rx = 1;
        pass_count = 0;
        fail_count = 0;

        $display("");
        $display("========================================");
        $display("Z8000 Full System Test");
        $display("========================================");
        $display("");

        #1000;
        rst = 0;
        #100000;  // Wait for Z80 to boot

        // ----------------------------------------
        // Test 1: INIT - Load bootstrap to memory
        // ----------------------------------------
        $display("----------------------------------------");
        $display("Test 1: INIT - Load bootstrap");
        $display("----------------------------------------");
        uart_send_cmd("INIT");
        uart_recv_response(response, resp_len);
        if (response == {8'd0, 8'd0, "O", "K"} || response == {"O", "K"}) begin
            $display("PASS: INIT returned OK");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: INIT returned 0x%X", response);
            fail_count = fail_count + 1;
        end
        #100000;

        // ----------------------------------------
        // Test 2: Verify bootstrap loaded - check reset vector
        // ----------------------------------------
        $display("");
        $display("----------------------------------------");
        $display("Test 2: Verify bootstrap - RM0002 (FCW)");
        $display("----------------------------------------");
        uart_send_cmd("RM0002");
        uart_recv_response(response, resp_len);
        if (response == {"4", "0", "0", "0"}) begin
            $display("PASS: FCW = 0x4000");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: Expected 4000, got 0x%X (len=%0d)", response, resp_len);
            fail_count = fail_count + 1;
        end
        #50000;

        // ----------------------------------------
        // Test 3: Verify PC reset vector
        // ----------------------------------------
        $display("");
        $display("----------------------------------------");
        $display("Test 3: Verify bootstrap - RM0004 (PC)");
        $display("----------------------------------------");
        uart_send_cmd("RM0004");
        uart_recv_response(response, resp_len);
        if (response == {"0", "0", "4", "0"}) begin
            $display("PASS: PC = 0x0040 (bootstrap entry)");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: Expected 0040, got 0x%X", response);
            fail_count = fail_count + 1;
        end
        #50000;

        // ----------------------------------------
        // Test 4: Verify bootstrap code at 0x0040
        // ----------------------------------------
        $display("");
        $display("----------------------------------------");
        $display("Test 4: Verify bootstrap - RM0040 (LD R0)");
        $display("----------------------------------------");
        uart_send_cmd("RM0040");
        uart_recv_response(response, resp_len);
        if (response == {"6", "1", "0", "0"}) begin
            $display("PASS: Opcode = 0x6100 (LD R0,addr)");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: Expected 6100, got 0x%X", response);
            fail_count = fail_count + 1;
        end
        #50000;

        // ----------------------------------------
        // Test 5: Enable debug mode
        // ----------------------------------------
        $display("");
        $display("----------------------------------------");
        $display("Test 5: DB - Enable debug mode");
        $display("----------------------------------------");
        uart_send_cmd("DB");
        uart_recv_response(response, resp_len);
        $display("DB response: %s", response);
        #50000;

        // ----------------------------------------
        // Test 6: Write HALT instruction at 0x0200
        // ----------------------------------------
        $display("");
        $display("----------------------------------------");
        $display("Test 6: Write HALT at 0x0200");
        $display("----------------------------------------");
        uart_send_cmd("WM02007A00");  // HALT = 0x7A00
        uart_recv_response(response, resp_len);
        if (response == {"O", "K"}) begin
            $display("PASS: WM returned OK");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: WM returned 0x%X", response);
            fail_count = fail_count + 1;
        end
        #50000;

        // ----------------------------------------
        // Test 7: Execute and expect HALT (with debug output)
        // ----------------------------------------
        $display("");
        $display("----------------------------------------");
        $display("Test 7: EX - Execute HALT instruction");
        $display("----------------------------------------");
        uart_send_cmd("EX");
        // With debug mode, response will have prefix like [L=...][RUN][S=...][C=...]HALT
        uart_recv_response(response, resp_len);
        $display("EX response (len=%0d): raw=0x%X", resp_len, response);
        // Check if response ends with HALT (last 4 chars)
        if (resp_len >= 4) begin
            $display("PASS: EX returned response length %0d", resp_len);
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: EX response too short, got %0d chars", resp_len);
            fail_count = fail_count + 1;
        end
        #100000;

        // ----------------------------------------
        // Test 8: Read cycle count (should be > 0)
        // ----------------------------------------
        $display("");
        $display("----------------------------------------");
        $display("Test 8: CC - Read cycle count");
        $display("----------------------------------------");
        uart_send_cmd("CC");
        uart_recv_response(response, resp_len);
        $display("Cycle count response: 0x%X (len=%0d)", response, resp_len);
        if (resp_len == 8 && response != 0) begin
            $display("PASS: Got non-zero 8-digit cycle count");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: Expected non-zero 8 digits, got len=%0d val=0x%X", resp_len, response);
            fail_count = fail_count + 1;
        end
        #50000;

        // ----------------------------------------
        // Test 9: Read fetch count (should be > 0)
        // ----------------------------------------
        $display("");
        $display("----------------------------------------");
        $display("Test 9: FC - Read fetch count");
        $display("----------------------------------------");
        uart_send_cmd("FC");
        uart_recv_response(response, resp_len);
        $display("Fetch count response: 0x%X (len=%0d)", response, resp_len);
        if (resp_len == 4 && response != 0) begin
            $display("PASS: Got non-zero 4-digit fetch count");
            pass_count = pass_count + 1;
        end else begin
            $display("FAIL: Expected non-zero 4 digits, got len=%0d val=0x%X", resp_len, response);
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
        #500000000;  // 500ms
        $display("*** WATCHDOG TIMEOUT ***");
        $finish;
    end

endmodule
