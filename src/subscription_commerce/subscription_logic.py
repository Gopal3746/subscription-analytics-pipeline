from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable

from .hash_utils import stable_unit_interval


@dataclass(frozen=True)
class CustomerProfile:
    customer_unique_id: str
    first_order_date: date
    order_count: int
    avg_order_value: float
    total_spend: float
    avg_delivery_delay_days: float
    customer_state: str
    cadence_days: int
    value_segment: str


def enrollment_probability(profile: CustomerProfile) -> float:
    """Model enrollment from observed behavior; value_segment is intentionally not used."""
    spend_signal = min(math.log1p(max(profile.total_spend, 0.0)) / 8.0, 1.0)
    p = 0.16
    p += min(profile.order_count - 1, 3) * 0.07
    p -= max(profile.avg_delivery_delay_days, 0.0) * 0.006
    p += spend_signal * 0.04
    return max(0.08, min(0.65, p))


def renewal_probability(profile: CustomerProfile, cycle_number: int) -> float:
    """Model renewal from continuous observed features, not the analysis segment label."""
    spend_signal = min(math.log1p(max(profile.total_spend, 0.0)) / 8.0, 1.0)
    cadence_signal = (120 - profile.cadence_days) / 90.0
    p = 0.58
    p += min(profile.order_count - 1, 4) * 0.045
    p -= max(profile.avg_delivery_delay_days, 0.0) * 0.008
    p += spend_signal * 0.16
    p += cadence_signal * 0.05
    p -= max(cycle_number - 2, 0) * 0.025
    return max(0.30, min(0.92, p))


def generate_cycles(profile: CustomerProfile, max_cycles: int = 6) -> list[dict]:
    if stable_unit_interval(profile.customer_unique_id, "enroll") >= enrollment_probability(profile):
        return []
    subscription_id = "sub_" + profile.customer_unique_id
    billing_amount = round(max(profile.avg_order_value, 5.0), 2)
    rows = []
    active = True
    for cycle in range(1, max_cycles + 1):
        due_date = profile.first_order_date + timedelta(days=profile.cadence_days * (cycle - 1))
        prior_active = active
        if cycle > 1:
            active = active and (
                stable_unit_interval(profile.customer_unique_id, "renew", cycle)
                < renewal_probability(profile, cycle)
            )
        rows.append({
            "subscription_id": subscription_id,
            "customer_unique_id": profile.customer_unique_id,
            "cycle_number": cycle,
            "billing_date": due_date.isoformat(),
            "billing_amount": billing_amount if active else 0.0,
            "renewed": int(active),
            "churned_this_cycle": int(cycle > 1 and prior_active and not active),
            "customer_state": profile.customer_state,
            "value_segment": profile.value_segment,
            "cadence_days": profile.cadence_days,
        })
        if not active:
            break
    return rows


def generate_all(profiles: Iterable[CustomerProfile], max_cycles: int = 6) -> list[dict]:
    rows = []
    for profile in profiles:
        rows.extend(generate_cycles(profile, max_cycles=max_cycles))
    return rows
