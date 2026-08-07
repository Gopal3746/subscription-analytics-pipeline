from datetime import date

from subscription_commerce.subscription_logic import CustomerProfile, generate_cycles, renewal_probability


def profile(total_spend=375.0):
    return CustomerProfile(
        customer_unique_id="known-customer",
        first_order_date=date(2018, 1, 1),
        order_count=3,
        avg_order_value=125.0,
        total_spend=total_spend,
        avg_delivery_delay_days=0.0,
        customer_state="SP",
        cadence_days=45,
        value_segment="analysis_only",
    )


def test_cycle_generation_is_deterministic():
    assert generate_cycles(profile()) == generate_cycles(profile())


def test_observed_spend_signal_affects_renewal_probability():
    assert renewal_probability(profile(900.0), 2) > renewal_probability(profile(90.0), 2)


def test_cycle_numbers_are_monotonic_if_enrolled():
    rows = generate_cycles(profile())
    assert [r["cycle_number"] for r in rows] == list(range(1, len(rows) + 1))
