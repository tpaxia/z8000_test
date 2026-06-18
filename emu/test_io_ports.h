// Test I/O Ports for Z8000 Test Driver
// Replicates z8k_io_ports.v behavior: 12 x 16-bit registers
// Standard I/O (mode=0) -> regs[0-5], Special I/O (mode=1) -> regs[6-11]
// Address decode: reg_index = addr[3:1] + (mode ? 6 : 0)
// Only responds to addresses 0x0100-0x010A

#ifndef TEST_IO_PORTS_H
#define TEST_IO_PORTS_H

#include <z8000/z8000_intf.h>
#include <cstdio>
#include <cstring>
#include <vector>

class TestIOPorts : public z8000_io_bus {
public:
    TestIOPorts() {
        clear();
    }

    void clear() {
        memset(m_regs, 0, sizeof(m_regs));
        memset(m_seq_count, 0, sizeof(m_seq_count));
        memset(m_seq_pos, 0, sizeof(m_seq_pos));
        memset(m_seq, 0, sizeof(m_seq));
    }

    void preload(int index, uint16_t val) {
        if (index >= 0 && index < 12)
            m_regs[index] = val;
    }

    uint16_t get_reg(int index) const {
        if (index >= 0 && index < 12)
            return m_regs[index];
        return 0;
    }

    void preload_sequence(int index, const std::vector<uint16_t>& values) {
        if (index < 0 || index >= 12)
            return;
        int count = values.size() > 4 ? 4 : static_cast<int>(values.size());
        for (int i = 0; i < count; i++)
            m_seq[index][i] = values[i];
        m_seq_count[index] = count;
        m_seq_pos[index] = 0;
    }

    // z8000_io_bus interface

    uint8_t read_byte(uint16_t addr, int mode) override {
        if (!addr_match(addr))
            return 0xFF;
        int idx = reg_index(addr, mode);
        uint16_t val = read_value(idx);
        advance_sequence(idx);
        // addr[0]: 0=high byte, 1=low byte (matches z8k_io_ports.v)
        if (addr & 1)
            return val & 0xFF;
        else
            return (val >> 8) & 0xFF;
    }

    uint16_t read_word(uint16_t addr, int mode) override {
        if (!addr_match(addr))
            return 0xFFFF;
        int idx = reg_index(addr, mode);
        uint16_t val = read_value(idx);
        advance_sequence(idx);
        return val;
    }

    void write_byte(uint16_t addr, uint8_t val, int mode) override {
        if (!addr_match(addr))
            return;
        int idx = reg_index(addr, mode);
        // addr[0]: 0=high byte, 1=low byte (matches z8k_io_ports.v lines 52-61)
        if (addr & 1)
            m_regs[idx] = (m_regs[idx] & 0xFF00) | val;
        else
            m_regs[idx] = (m_regs[idx] & 0x00FF) | (static_cast<uint16_t>(val) << 8);
    }

    void write_word(uint16_t addr, uint16_t val, int mode) override {
        if (!addr_match(addr))
            return;
        m_regs[reg_index(addr, mode)] = val;
    }

private:
    uint16_t m_regs[12];
    uint16_t m_seq[12][4];
    int m_seq_count[12];
    int m_seq_pos[12];

    uint16_t read_value(int index) const {
        if (m_seq_count[index] > 0) {
            int pos = m_seq_pos[index];
            if (pos >= m_seq_count[index])
                pos = m_seq_count[index] - 1;
            return m_seq[index][pos];
        }
        return m_regs[index];
    }

    void advance_sequence(int index) {
        if (m_seq_count[index] > 0 && m_seq_pos[index] < m_seq_count[index])
            m_seq_pos[index]++;
    }

    // Address 0x0100-0x010A only
    static bool addr_match(uint16_t addr) {
        return (addr & 0xFFF0) == 0x0100 && (addr & 0x000E) <= 0x000A;
    }

    // reg_index = addr[3:1] + (mode ? 6 : 0)
    static int reg_index(uint16_t addr, int mode) {
        return ((addr >> 1) & 0x07) + (mode ? 6 : 0);
    }
};

#endif // TEST_IO_PORTS_H
