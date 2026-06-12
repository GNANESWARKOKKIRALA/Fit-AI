"""
Profile route blueprint for FitAI application.

Handles user profile management and fitness goal CRUD operations.
"""

import logging
from datetime import datetime

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from database.db import get_db
from services.profile_service import ProfileService
from utils.decorators import login_required

logger = logging.getLogger(__name__)

bp = Blueprint('profile', __name__, url_prefix='/profile')


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

@bp.route('/', methods=['GET', 'POST'])
@login_required
def profile():
    """View or update the user profile."""
    db = get_db()
    user_id = session['user_id']

    if request.method == 'POST':
        profile_data = {
            'age': request.form.get('age', type=int),
            'gender': request.form.get('gender', '').strip(),
            'height': request.form.get('height', type=float),
            'weight': request.form.get('weight', type=float),
            'goal_weight': request.form.get('goal_weight', type=float),
            'activity_level': request.form.get('activity_level', '').strip(),
            'fitness_goal': request.form.get('fitness_goal', '').strip(),
            'workout_preference': request.form.get('workout_preference', '').strip(),
            'diet_preference': request.form.get('diet_preference', '').strip(),
            'medical_notes': request.form.get('medical_notes', '').strip(),
        }

        # Basic validation
        errors = []
        if profile_data['age'] is not None and (profile_data['age'] < 1 or profile_data['age'] > 150):
            errors.append('Please enter a valid age.')
        if profile_data['height'] is not None and profile_data['height'] <= 0:
            errors.append('Please enter a valid height.')
        if profile_data['weight'] is not None and profile_data['weight'] <= 0:
            errors.append('Please enter a valid weight.')
        if profile_data['goal_weight'] is not None and profile_data['goal_weight'] <= 0:
            errors.append('Please enter a valid goal weight.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('profile/profile.html', profile=profile_data)

        try:
            ProfileService.create_or_update_profile(db, user_id, profile_data)
            flash('Profile updated successfully!', 'success')
        except Exception:
            logger.exception("Error updating profile for user %s", user_id)
            flash('An error occurred while saving your profile.', 'error')

        return redirect(url_for('profile.profile'))

    # GET
    user_profile = ProfileService.get_profile(db, user_id)
    return render_template('profile/profile.html', profile=user_profile)


# ---------------------------------------------------------------------------
# Goals
# ---------------------------------------------------------------------------

@bp.route('/goals', methods=['GET', 'POST'])
@login_required
def goals():
    """View all goals or create a new one."""
    db = get_db()
    user_id = session['user_id']

    if request.method == 'POST':
        goal_data = {
            'goal_type': request.form.get('goal_type', '').strip(),
            'target_value': request.form.get('target_value', type=float),
            'current_value': request.form.get('current_value', type=float, default=0),
            'target_date': request.form.get('target_date', '').strip(),
            'description': request.form.get('description', '').strip(),
        }

        if not goal_data['goal_type'] or goal_data['target_value'] is None:
            flash('Goal type and target value are required.', 'error')
            return redirect(url_for('profile.goals'))

        try:
            ProfileService.create_goal(db, user_id, goal_data)
            flash('Goal created successfully!', 'success')
        except Exception:
            logger.exception("Error creating goal for user %s", user_id)
            flash('An error occurred while creating the goal.', 'error')

        return redirect(url_for('profile.goals'))

    # GET
    user_goals = ProfileService.get_goals(db, user_id)
    user_profile = ProfileService.get_profile(db, user_id)
    return render_template('profile/profile.html', profile=user_profile, goals=user_goals)


@bp.route('/goals/<int:goal_id>/delete', methods=['POST'])
@login_required
def delete_goal(goal_id):
    """Delete a fitness goal."""
    db = get_db()
    user_id = session['user_id']

    try:
        ProfileService.delete_goal(db, user_id, goal_id)
        flash('Goal deleted.', 'success')
    except Exception:
        logger.exception("Error deleting goal %s for user %s", goal_id, user_id)
        flash('An error occurred while deleting the goal.', 'error')

    return redirect(url_for('profile.goals'))


@bp.route('/goals/<int:goal_id>/update', methods=['POST'])
@login_required
def update_goal(goal_id):
    """Update progress on a fitness goal."""
    db = get_db()
    user_id = session['user_id']

    current_value = request.form.get('current_value', type=float)
    if current_value is None:
        flash('Please provide a valid progress value.', 'error')
        return redirect(url_for('profile.goals'))

    try:
        ProfileService.update_goal_progress(db, user_id, goal_id, current_value)
        flash('Goal progress updated!', 'success')
    except Exception:
        logger.exception("Error updating goal %s for user %s", goal_id, user_id)
        flash('An error occurred while updating the goal.', 'error')

    return redirect(url_for('profile.goals'))
