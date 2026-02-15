"""Test case and result dataclass definitions."""

from dataclasses import dataclass, field


@dataclass
class TestCase:
    name: str                                        # "add_r_r_basic"
    mnemonic: str                                    # "ADD"
    description: str                                 # "ADD R0, R1: 0x1234+0x5678"
    tags: list[str]                                  # ["arithmetic", "word", "R_mode"]
    instruction: str = ""                            # "ADD R0, R1"
    target: str = "common"                           # "common" | "z8001" | "z8002"
    issues: list[str] = field(default_factory=list)  # Known discrepancies vs real silicon

    # Initial state
    code: list[int] = field(default_factory=list)    # [0x8110]
    regs: dict[int, int] = field(default_factory=dict)
    fcw: int = 0x4000                                # Initial FCW (system mode)
    memory: dict[int, int] = field(default_factory=dict)  # {addr: word}
    io_preloads: dict[int, int] = field(default_factory=dict)  # {reg_index: word}

    # Expected results
    expected_regs: dict[int, int] = field(default_factory=dict)
    expected_fcw_set: list[str] = field(default_factory=list)    # Flags that must be 1
    expected_fcw_clear: list[str] = field(default_factory=list)  # Flags that must be 0
    expected_memory: dict[int, int] = field(default_factory=dict)
    expected_io: dict[int, int] = field(default_factory=dict)  # {reg_index: word}
    expected_trace: list[dict] | None = None         # Optional trace pattern
    expected_result: str = "HALT"                    # Expected EX result


@dataclass
class TestResult:
    test: TestCase
    passed: bool
    exec_result: str = ""                # "HALT", "TOUT", "NRST"
    failures: list[str] = field(default_factory=list)
    actual_regs: dict[int, int] = field(default_factory=dict)
    actual_fcw: int | None = None
    actual_memory: dict[int, int] = field(default_factory=dict)
    actual_io: dict[int, int] = field(default_factory=dict)
    cycle_count: int | None = None
    fetch_count: int | None = None
    instr_cycle_count: int | None = None
    trace: list[dict] = field(default_factory=list)  # Bus trace entries
