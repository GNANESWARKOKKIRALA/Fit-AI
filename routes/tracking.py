"""
Tracking route blueprint for FitAI application.

Handles daily fitness metric logging (weight, water, calories, sleep,
workouts, steps) via AJAX-friendly JSON endpoints, plus history views.
"""

import logging
from datetime import datetime

from flask import Blueprint, jsonify, render_template, request, session

from database.db import get_db
from services.tracking_service import TrackingService
from utils.decorators import login_required

logger = logging.getLogger(__name__)

bp = Blueprint('tracking', __name__, url_prefix='/tracking')


# ---------------------------------------------------------------------------
# Dashboard / overview
# ---------------------------------------------------------------------------

@bp.route('/')
@login_required
def tracking():
    """Show today's tracking summary alongside recent history for all metrics."""
    db = get_db()
    user_id = session['user_id']

    today_summary = TrackingService.get_today_summary(db, user_id)
    recent_weight = TrackingService.get_weight_history(db, user_id, days=7)
    recent_water = TrackingService.get_water_history(db, user_id, days=7)
    recent_calories = TrackingService.get_calorie_history(db, user_id, days=7)
    recent_sleep = TrackingService.get_sleep_history(db, user_id, days=7)
    recent_workouts = TrackingService.get_workout_history(db, user_id, days=7)
    recent_steps = TrackingService.get_step_history(db, user_id, days=7)

    return render_template(
        'tracking/tracking.html',
        today=today_summary,
        weight_history=recent_weight,
        water_history=recent_water,
        calorie_history=recent_calories,
        sleep_history=recent_sleep,
        workout_history=recent_workouts,
        step_history=recent_steps,
    )


# ---------------------------------------------------------------------------
# AJAX logging endpoints (all POST, return JSON)
# ---------------------------------------------------------------------------

@bp.route('/weight', methods=['POST'])
@login_required
def log_weight():
    """Log a weight measurement."""
    db = get_db()
    user_id = session['user_id']

    weight = request.form.get('weight', type=float)
    if weight is None or weight <= 0:
        return jsonify({'success': False, 'message': 'Please enter a valid weight.'}), 400

    try:
        TrackingService.log_weight(db, user_id, weight)
        return jsonify({'success': True, 'message': 'Weight logged successfully.'})
    except Exception:
        logger.exception("Error logging weight for user %s", user_id)
        return jsonify({'success': False, 'message': 'An error occurred while logging weight.'}), 500


@bp.route('/water', methods=['POST'])
@login_required
def log_water():
    """Log water intake."""
    db = get_db()
    user_id = session['user_id']

    amount = request.form.get('amount_ml', type=float)
    if amount is None or amount <= 0:
        return jsonify({'success': False, 'message': 'Please enter a valid water amount.'}), 400

    try:
        TrackingService.log_water(db, user_id, amount)
        return jsonify({'success': True, 'message': 'Water intake logged successfully.'})
    except Exception:
        logger.exception("Error logging water for user %s", user_id)
        return jsonify({'success': False, 'message': 'An error occurred while logging water.'}), 500


@bp.route('/calories', methods=['POST'])
@login_required
def log_calories():
    """Log calorie consumption and burn."""
    db = get_db()
    user_id = session['user_id']

    consumed = request.form.get('consumed', type=float, default=0)
    burned = request.form.get('burned', type=float, default=0)
    meal_details = request.form.get('meal_details', '').strip()

    if consumed < 0 or burned < 0:
        return jsonify({'success': False, 'message': 'Calorie values cannot be negative.'}), 400

    try:
        TrackingService.log_calories(db, user_id, consumed, burned, meal_details)
        return jsonify({'success': True, 'message': 'Calories logged successfully.'})
    except Exception:
        logger.exception("Error logging calories for user %s", user_id)
        return jsonify({'success': False, 'message': 'An error occurred while logging calories.'}), 500


@bp.route('/sleep', methods=['POST'])
@login_required
def log_sleep():
    """Log sleep data."""
    db = get_db()
    user_id = session['user_id']

    hours = request.form.get('hours', type=float)
    quality = request.form.get('quality', 'Good')

    if hours is None or hours < 0 or hours > 24:
        return jsonify({'success': False, 'message': 'Please enter valid sleep hours (0-24).'}), 400
    if quality not in ['Excellent', 'Good', 'Fair', 'Poor']:
        return jsonify({'success': False, 'message': 'Invalid sleep quality rating.'}), 400

    try:
        TrackingService.log_sleep(db, user_id, hours, quality)
        return jsonify({'success': True, 'message': 'Sleep logged successfully.'})
    except Exception:
        logger.exception("Error logging sleep for user %s", user_id)
        return jsonify({'success': False, 'message': 'An error occurred while logging sleep.'}), 500


@bp.route('/workout', methods=['POST'])
@login_required
def log_workout():
    """Log a workout session."""
    db = get_db()
    user_id = session['user_id']

    workout_type = request.form.get('workout_type', '').strip()
    duration = request.form.get('duration', type=int)
    calories_burned = request.form.get('calories_burned', type=float, default=0)
    exercises = request.form.get('exercises', '').strip()
    notes = request.form.get('notes', '').strip()

    if not workout_type:
        return jsonify({'success': False, 'message': 'Workout type is required.'}), 400
    if duration is None or duration <= 0:
        return jsonify({'success': False, 'message': 'Please enter a valid duration in minutes.'}), 400

    try:
        TrackingService.log_workout(db, user_id, workout_type, duration, calories_burned, exercises, notes)
        return jsonify({'success': True, 'message': 'Workout logged successfully.'})
    except Exception:
        logger.exception("Error logging workout for user %s", user_id)
        return jsonify({'success': False, 'message': 'An error occurred while logging the workout.'}), 500


@bp.route('/steps', methods=['POST'])
@login_required
def log_steps():
    """Log daily step count."""
    db = get_db()
    user_id = session['user_id']

    steps = request.form.get('steps', type=int)
    if steps is None or steps < 0:
        return jsonify({'success': False, 'message': 'Please enter a valid step count.'}), 400

    try:
        TrackingService.log_steps(db, user_id, steps)
        return jsonify({'success': True, 'message': 'Steps logged successfully.'})
    except Exception:
        logger.exception("Error logging steps for user %s", user_id)
        return jsonify({'success': False, 'message': 'An error occurred while logging steps.'}), 500


# ---------------------------------------------------------------------------
# Full history view
# ---------------------------------------------------------------------------

@bp.route('/history')
@login_required
def history():
    """Show full tracking history across all metrics."""
    db = get_db()
    user_id = session['user_id']

    weight_history = TrackingService.get_weight_history(db, user_id, days=90)
    water_history = TrackingService.get_water_history(db, user_id, days=90)
    calorie_history = TrackingService.get_calorie_history(db, user_id, days=90)
    sleep_history = TrackingService.get_sleep_history(db, user_id, days=90)
    workout_history = TrackingService.get_workout_history(db, user_id, days=90)
    steps_history = TrackingService.get_step_history(db, user_id, days=90)

    return render_template(
        'tracking/history.html',
        weight_history=weight_history,
        water_history=water_history,
        calorie_history=calorie_history,
        sleep_history=sleep_history,
        workout_history=workout_history,
        step_history=steps_history,
    )
