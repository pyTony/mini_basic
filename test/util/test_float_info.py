
from mini_basic.util.float_info import discover_machine_epsilon

def test_discover_machine_epsilon():
    eps = discover_machine_epsilon()
    assert isinstance(eps, float)
    assert eps > 0.0
    # It should correctly identify epsilon via loop
    assert 1.0 + eps != 1.0
    assert 1.0 + (eps / 2.0) == 1.0
