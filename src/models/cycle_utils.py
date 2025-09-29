"""Utilities for menstrual cycle phase calculations."""

from datetime import datetime, timedelta
from typing import Tuple


def calculate_cycle_day(lmp_date: datetime, observation_date: datetime) -> int:
    """
    Calculate cycle day from LMP date.

    Args:
        lmp_date: Last menstrual period start date
        observation_date: Date of observation/survey

    Returns:
        Cycle day (1-28, wrapping if necessary)
    """
    days_since_lmp = (observation_date - lmp_date).days
    # Assume 28-day cycle, wrap around
    return (days_since_lmp % 28) + 1


def get_cycle_phase(cycle_day: int) -> str:
    """
    Determine menstrual cycle phase from cycle day.

    Follicular phase: Days 1-14 (menstruation + follicular)
    Luteal phase: Days 15-28 (ovulation + luteal)

    Args:
        cycle_day: Day of cycle (1-28)

    Returns:
        "follicular" or "luteal"
    """
    if 1 <= cycle_day <= 14:
        return "follicular"
    else:
        return "luteal"


def calculate_phase_from_lmp(lmp_date: datetime, observation_date: datetime) -> str:
    """
    Calculate cycle phase directly from LMP and observation dates.

    Args:
        lmp_date: Last menstrual period start date
        observation_date: Date of observation/survey

    Returns:
        "follicular" or "luteal"
    """
    cycle_day = calculate_cycle_day(lmp_date, observation_date)
    return get_cycle_phase(cycle_day)


def generate_lmp_for_phase(
    observation_date: datetime, target_phase: str, cycle_day_range: Tuple[int, int] = None
) -> datetime:
    """
    Generate an LMP date that results in a specific cycle phase at observation time.

    Args:
        observation_date: Date when survey is taken
        target_phase: "follicular" or "luteal"
        cycle_day_range: Optional tuple (min, max) for cycle day within phase

    Returns:
        LMP date that produces the target phase
    """
    if target_phase == "follicular":
        # Days 1-14: LMP was 0-13 days ago
        min_days, max_days = cycle_day_range or (1, 14)
    else:  # luteal
        # Days 15-28: LMP was 14-27 days ago
        min_days, max_days = cycle_day_range or (15, 28)

    # Random day within phase range
    import random
    days_ago = random.randint(min_days - 1, max_days - 1)

    return observation_date - timedelta(days=days_ago)