from subscription_commerce.hash_utils import stable_unit_interval


def test_stable_unit_interval_is_deterministic():
    assert stable_unit_interval("abc", 1) == stable_unit_interval("abc", 1)


def test_stable_unit_interval_range():
    value = stable_unit_interval("customer-1", "renew", 3)
    assert 0.0 <= value < 1.0
