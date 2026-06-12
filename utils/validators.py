"""
Input validation functions for FitAI.

Every validator returns a tuple ``(is_valid: bool, error_message: str)``.
When *is_valid* is ``True``, *error_message* is an empty string.
"""

import re


def validate_registration(
    username: str,
    email: str,
    password: str,
    confirm_password: str,
) -> tuple[bool, str]:
    """Validate new-user registration fields."""

    if not username or not username.strip():
        return False, 'Username is required.'

    username = username.strip()
    if len(username) < 3 or len(username) > 30:
        return False, 'Username must be between 3 and 30 characters.'

    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, 'Username may only contain letters, numbers, and underscores.'

    if not email or not email.strip():
        return False, 'Email is required.'

    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email.strip()):
        return False, 'Please enter a valid email address.'

    if not password:
        return False, 'Password is required.'

    if len(password) < 8:
        return False, 'Password must be at least 8 characters long.'

    if password != confirm_password:
        return False, 'Passwords do not match.'

    return True, ''


def validate_login(username: str, password: str) -> tuple[bool, str]:
    """Validate login form fields (presence checks only)."""

    if not username or not username.strip():
        return False, 'Username or Email is required.'

    if not password:
        return False, 'Password is required.'

    return True, ''


def validate_profile(data: dict) -> tuple[bool, str]:
    """Validate user-profile fields.

    *data* should contain optional keys such as ``age``, ``height``,
    ``weight``, ``goal_weight``, ``activity_level``, ``fitness_goal``, etc.
    """

    # Age
    age = data.get('age')
    if age is not None and age != '':
        try:
            age_val = int(age)
            if age_val < 13 or age_val > 120:
                return False, 'Age must be between 13 and 120.'
        except (ValueError, TypeError):
            return False, 'Age must be a valid number.'

    # Height (cm)
    height = data.get('height')
    if height is not None and height != '':
        try:
            height_val = float(height)
            if height_val < 50 or height_val > 300:
                return False, 'Height must be between 50 and 300 cm.'
        except (ValueError, TypeError):
            return False, 'Height must be a valid number.'

    # Weight (kg)
    weight = data.get('weight')
    if weight is not None and weight != '':
        try:
            weight_val = float(weight)
            if weight_val < 20 or weight_val > 500:
                return False, 'Weight must be between 20 and 500 kg.'
        except (ValueError, TypeError):
            return False, 'Weight must be a valid number.'

    # Goal weight (kg)
    goal_weight = data.get('goal_weight')
    if goal_weight is not None and goal_weight != '':
        try:
            gw_val = float(goal_weight)
            if gw_val < 20 or gw_val > 500:
                return False, 'Goal weight must be between 20 and 500 kg.'
        except (ValueError, TypeError):
            return False, 'Goal weight must be a valid number.'

    # Activity level
    valid_levels = {'sedentary', 'lightly_active', 'moderately_active', 'very_active', 'extra_active'}
    activity_level = data.get('activity_level')
    if activity_level and activity_level not in valid_levels:
        return False, 'Please select a valid activity level.'

    # Fitness goal
    valid_goals = {'lose_weight', 'gain_muscle', 'maintain', 'improve_endurance', 'flexibility'}
    fitness_goal = data.get('fitness_goal')
    if fitness_goal and fitness_goal not in valid_goals:
        return False, 'Please select a valid fitness goal.'

    # Gender
    valid_genders = {'male', 'female', 'other', 'prefer_not_to_say'}
    gender = data.get('gender')
    if gender and gender not in valid_genders:
        return False, 'Please select a valid gender option.'

    return True, ''


def validate_tracking_input(
    value,
    field_name: str,
    min_val: float = 0,
    max_val: float | None = None,
) -> tuple[bool, str]:
    """Validate a single numeric tracking input.

    Returns ``(True, '')`` when *value* is a valid number within the
    specified range, or ``(False, error_message)`` otherwise.
    """

    if value is None or (isinstance(value, str) and not value.strip()):
        return False, f'{field_name} is required.'

    try:
        num = float(value)
    except (ValueError, TypeError):
        return False, f'{field_name} must be a valid number.'

    if num < min_val:
        return False, f'{field_name} must be at least {min_val}.'

    if max_val is not None and num > max_val:
        return False, f'{field_name} must be at most {max_val}.'

    return True, ''
