// Z8000 Emulator Test Driver
// Reads a test spec file, executes one test, prints results.
// Supports both Z8002 (non-segmented) and Z8001 (segmented) modes.
// Used by tests/emu_runner.py as a subprocess (same pattern as vvp).

#include <z8000/z8000.h>
#include "memory.h"
#include "test_io_ports.h"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <map>
#include <memory>

static constexpr uint16_t CODE_BASE = 0x0200;
static constexpr uint16_t DUMP_ROUTINE = 0x00C0;
static constexpr uint16_t HALT_OPCODE = 0x7A00;
static constexpr int MAX_CYCLES = 100000;

struct TestSpec {
    std::vector<uint16_t> code;
    std::map<int, uint16_t> regs;
    uint16_t fcw = 0x4000;
    std::map<uint16_t, uint16_t> mem_preloads;
    std::map<int, uint16_t> io_preloads;
    std::vector<uint16_t> verify_mem;
    std::vector<int> verify_io;
    bool z8001_mode = false;
};

static uint16_t parse_hex16(const std::string& s) {
    return static_cast<uint16_t>(strtoul(s.c_str(), nullptr, 16));
}

// Translate flat BRAM address to Z8001 segmented emulator address.
// Mirrors FPGA BRAM mapping: {sn[0], addr[11:0]}
//   flat 0x0000-0x0FFF -> segment 0, offset 0x0000-0x0FFF (emu 0x000000-0x000FFF)
//   flat 0x1000-0x1FFF -> segment 1, offset 0x0000-0x0FFF (emu 0x010000-0x010FFF)
static uint32_t flat_to_seg(uint16_t flat) {
    return (static_cast<uint32_t>(flat >> 12) << 16) | (flat & 0x0FFF);
}

static bool parse_spec(const char* path, TestSpec& spec) {
    std::ifstream f(path);
    if (!f.is_open()) {
        fprintf(stderr, "Cannot open spec file: %s\n", path);
        return false;
    }

    std::string line;
    while (std::getline(f, line)) {
        // Strip comments
        auto hash = line.find('#');
        if (hash != std::string::npos)
            line = line.substr(0, hash);

        // Strip whitespace
        while (!line.empty() && (line.back() == ' ' || line.back() == '\t' || line.back() == '\r'))
            line.pop_back();
        if (line.empty())
            continue;

        if (line.substr(0, 5) == "CODE:") {
            std::istringstream iss(line.substr(5));
            std::string word;
            while (iss >> word)
                spec.code.push_back(parse_hex16(word));

        } else if (line.substr(0, 4) == "REG:") {
            // REG:n:val
            auto first = line.find(':', 4);
            if (first == std::string::npos) continue;
            int reg = std::stoi(line.substr(4, first - 4));
            uint16_t val = parse_hex16(line.substr(first + 1));
            spec.regs[reg] = val;

        } else if (line.substr(0, 4) == "FCW:") {
            spec.fcw = parse_hex16(line.substr(4));

        } else if (line.substr(0, 4) == "MEM:") {
            // MEM:addr:val
            auto first = line.find(':', 4);
            if (first == std::string::npos) continue;
            uint16_t addr = parse_hex16(line.substr(4, first - 4));
            uint16_t val = parse_hex16(line.substr(first + 1));
            spec.mem_preloads[addr] = val;

        } else if (line.substr(0, 3) == "IO:") {
            // IO:index:val
            auto first = line.find(':', 3);
            if (first == std::string::npos) continue;
            int idx = std::stoi(line.substr(3, first - 3));
            uint16_t val = parse_hex16(line.substr(first + 1));
            spec.io_preloads[idx] = val;

        } else if (line.substr(0, 11) == "VERIFY_MEM:") {
            spec.verify_mem.push_back(parse_hex16(line.substr(11)));

        } else if (line.substr(0, 10) == "VERIFY_IO:") {
            spec.verify_io.push_back(std::stoi(line.substr(10)));

        } else if (line.substr(0, 5) == "MODE:") {
            std::string mode = line.substr(5);
            // Trim leading whitespace
            while (!mode.empty() && mode[0] == ' ') mode.erase(0, 1);
            spec.z8001_mode = (mode == "z8001");

        } else if (line == "RUN") {
            // Marker; parsing stops here
            break;
        }
    }
    return true;
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <spec_file>\n", argv[0]);
        return 1;
    }

    TestSpec spec;
    if (!parse_spec(argv[1], spec))
        return 1;

    // Address translation: identity for Z8002, flat-to-seg for Z8001
    auto addr_xlat = [&](uint16_t flat) -> uint32_t {
        return spec.z8001_mode ? flat_to_seg(flat) : flat;
    };

    // Create memory
    // Z8002: 64KB flat.  Z8001: 128KB (covers segments 0 and 1)
    MemoryRegion memory(spec.z8001_mode ? 0x20000 : 0x10000);

    // Create I/O ports
    TestIOPorts io;

    // Place HALT at dump routine address (0x00C0) so tests with
    // explicit JP 0x00C0 (e.g. call_ret_basic) halt cleanly
    memory.write_word(addr_xlat(DUMP_ROUTINE), HALT_OPCODE);

    // Write test code at CODE_BASE, append HALT
    uint32_t code_base = addr_xlat(CODE_BASE);
    for (size_t i = 0; i < spec.code.size(); i++) {
        memory.write_word(code_base + i * 2, spec.code[i]);
    }
    memory.write_word(code_base + spec.code.size() * 2, HALT_OPCODE);

    // Write memory preloads (translate flat addresses for Z8001)
    for (auto& [addr, val] : spec.mem_preloads) {
        memory.write_word(addr_xlat(addr), val);
    }

    // Set I/O preloads
    for (auto& [idx, val] : spec.io_preloads) {
        io.preload(idx, val);
    }

    // Create CPU (Z8001 segmented or Z8002 non-segmented)
    std::unique_ptr<z8002_device> cpu;
    if (spec.z8001_mode) {
        cpu = std::make_unique<z8001_device>();
    } else {
        cpu = std::make_unique<z8002_device>();
    }
    cpu->set_memory(&memory);
    cpu->set_io(&io);

    // Initialize state: FCW, PC=CODE_BASE, no PSAP/NSP needed
    cpu->init_state(spec.fcw, code_base, 0, 0, 0, 0);

    // Set registers (after init_state so R14/R15 override works)
    for (auto& [reg, val] : spec.regs) {
        cpu->set_reg(reg, val);
    }

    // Run
    cpu->run(MAX_CYCLES);

    // Print results
    if (cpu->is_halted()) {
        printf("RESULT:HALT\n");
    } else {
        printf("RESULT:TOUT\n");
    }

    // All 16 registers
    for (int i = 0; i < 16; i++) {
        printf("REG:%d:%04X\n", i, cpu->get_reg(i));
    }

    // FCW
    printf("FCW:%04X\n", cpu->get_fcw());

    // Requested memory readbacks (translate addresses, report as flat)
    for (uint16_t flat_addr : spec.verify_mem) {
        printf("MEM:%04X:%04X\n", flat_addr, memory.read_word(addr_xlat(flat_addr)));
    }

    // Requested I/O readbacks
    for (int idx : spec.verify_io) {
        printf("IO:%02X:%04X\n", idx, io.get_reg(idx));
    }

    // Cycle count
    printf("CYCLES:%08X\n", cpu->get_cycles());

    return 0;
}
