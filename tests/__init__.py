"""Z8000 Instruction Test Package.

Collects all test cases from test definition modules.
"""

from .defs import TestCase, TestResult


def collect_all_tests():
    """Collect all test cases from all test modules."""
    all_tests = []

    # Import each test module and collect its TESTS list
    test_modules = []

    try:
        from . import test_arithmetic
        test_modules.append(test_arithmetic)
    except ImportError:
        pass

    try:
        from . import test_logical
        test_modules.append(test_logical)
    except ImportError:
        pass

    try:
        from . import test_load
        test_modules.append(test_load)
    except ImportError:
        pass

    try:
        from . import test_compare
        test_modules.append(test_compare)
    except ImportError:
        pass

    try:
        from . import test_bit
        test_modules.append(test_bit)
    except ImportError:
        pass

    try:
        from . import test_shift
        test_modules.append(test_shift)
    except ImportError:
        pass

    try:
        from . import test_branch
        test_modules.append(test_branch)
    except ImportError:
        pass

    try:
        from . import test_stack
        test_modules.append(test_stack)
    except ImportError:
        pass

    try:
        from . import test_block
        test_modules.append(test_block)
    except ImportError:
        pass

    try:
        from . import test_exchange
        test_modules.append(test_exchange)
    except ImportError:
        pass

    try:
        from . import test_control
        test_modules.append(test_control)
    except ImportError:
        pass

    try:
        from . import test_io
        test_modules.append(test_io)
    except ImportError:
        pass

    try:
        from . import test_cpu_bugs
        test_modules.append(test_cpu_bugs)
    except ImportError:
        pass

    try:
        from . import test_z8001_golden
        test_modules.append(test_z8001_golden)
    except ImportError:
        pass

    for mod in test_modules:
        if hasattr(mod, 'TESTS'):
            all_tests.extend(mod.TESTS)

    return all_tests
