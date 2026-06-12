"""
Utility / helper functions for FitAI.

Pure functions with no side-effects – safe to call from any layer.
"""

from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# BMI helpers
# ---------------------------------------------------------------------------

def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    """Calculate Body Mass Index from weight (kg) and height (cm).

    Returns the BMI rounded to one decimal place.
    """
    if height_cm <= 0:
        return 0.0
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 1)


def bmi_category(bmi: float) -> str:
    """Return the WHO weight-status category for the given BMI value."""
    if bmi < 18.5:
        return 'Underweight'
    if bmi < 25:
        return 'Normal'
    if bmi < 30:
        return 'Overweight'
    return 'Obese'


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

def format_date(date_str: str, fmt: str = '%b %d, %Y') -> str:
    """Parse an ISO-style date string and return it formatted with *fmt*.

    Supports both ``YYYY-MM-DD`` and ``YYYY-MM-DD HH:MM:SS`` inputs.
    Returns the original string unchanged if parsing fails.
    """
    for pattern in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
        try:
            return datetime.strptime(date_str, pattern).strftime(fmt)
        except (ValueError, TypeError):
            continue
    return date_str


def days_since(date_str: str) -> int:
    """Return the number of whole days between *date_str* and today."""
    for pattern in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
        try:
            past = datetime.strptime(date_str, pattern)
            return (datetime.now() - past).days
        except (ValueError, TypeError):
            continue
    return 0


# ---------------------------------------------------------------------------
# Streak calculation
# ---------------------------------------------------------------------------

def calculate_streak(dates_list: list) -> int:
    """Count consecutive days with activity, working backwards from today.

    *dates_list* may contain ``datetime`` objects or ISO-format date strings.
    Duplicate dates are collapsed before counting.
    """
    if not dates_list:
        return 0

    # Normalise to date objects
    unique_dates = set()
    for d in dates_list:
        if isinstance(d, str):
            for pattern in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
                try:
                    d = datetime.strptime(d, pattern)
                    break
                except (ValueError, TypeError):
                    continue
        if isinstance(d, datetime):
            unique_dates.add(d.date())

    if not unique_dates:
        return 0

    today = datetime.now().date()
    streak = 0
    current_day = today

    while current_day in unique_dates:
        streak += 1
        current_day -= timedelta(days=1)

    return streak


# ---------------------------------------------------------------------------
# Achievement badges
# ---------------------------------------------------------------------------

def generate_achievement_badges(tracking_data: dict) -> list:
    """Generate a list of achievement badges based on the user's tracking data.

    *tracking_data* is expected to contain the following optional keys:

    - ``total_logs``      (int) – total number of log entries across all types
    - ``streak``          (int) – current consecutive-day streak
    - ``water_days``      (int) – number of distinct days with a water log
    - ``sleep_days``      (int) – number of distinct days with a sleep log
    - ``weight_logs``     (int) – total weight-log entries
    - ``total_workouts``  (int) – total workout-log entries
    - ``goals_completed`` (int) – number of goals with status 'completed'

    Returns a list of dicts, each with keys: name, icon, description, earned.
    """

    total_logs = tracking_data.get('total_logs', 0)
    streak = tracking_data.get('streak', 0)
    water_days = tracking_data.get('water_days', 0)
    sleep_days = tracking_data.get('sleep_days', 0)
    weight_logs = tracking_data.get('weight_logs', 0)
    total_workouts = tracking_data.get('total_workouts', 0)
    goals_completed = tracking_data.get('goals_completed', 0)

    badges = [
        {
            'name': 'First Step',
            'icon': '👣',
            'description': 'Logged your very first entry.',
            'earned': total_logs >= 1,
        },
        {
            'name': '7-Day Streak',
            'icon': '🔥',
            'description': 'Maintained a 7-day activity streak.',
            'earned': streak >= 7,
        },
        {
            'name': '30-Day Streak',
            'icon': '💪',
            'description': 'Maintained a 30-day activity streak.',
            'earned': streak >= 30,
        },
        {
            'name': 'Hydration Hero',
            'icon': '💧',
            'description': 'Logged water intake for 7 days.',
            'earned': water_days >= 7,
        },
        {
            'name': 'Early Bird',
            'icon': '🌅',
            'description': 'Logged sleep for 7 days.',
            'earned': sleep_days >= 7,
        },
        {
            'name': 'Weight Warrior',
            'icon': '⚖️',
            'description': 'Recorded 10 weight logs.',
            'earned': weight_logs >= 10,
        },
        {
            'name': 'Century Club',
            'icon': '🏆',
            'description': 'Completed 100 workouts.',
            'earned': total_workouts >= 100,
        },
        {
            'name': 'Goal Crusher',
            'icon': '🎯',
            'description': 'Completed a fitness goal.',
            'earned': goals_completed >= 1,
        },
    ]

    return badges
