"""
Dashboard route blueprint for FitAI application.

Provides the main dashboard view with summary metrics, charts,
and AI-generated motivation for authenticated users.
"""

import logging
from datetime import datetime, timedelta

from flask import Blueprint, render_template, session

from database.db import get_db
from services.tracking_service import TrackingService
from services.analytics_service import AnalyticsService
from services.profile_service import ProfileService
from services.ai_engine import AIEngine
from charts.plotly_charts import (
    create_weight_chart,
    create_calories_chart,
    create_workout_chart,
)
from utils.decorators import login_required

logger = logging.getLogger(__name__)

bp = Blueprint('dashboard', __name__)


def format_logged_at(logged_at):
    """Format logged_at timestamp (string or datetime) to YYYY-MM-DD."""
    if not logged_at:
        return ""
    if hasattr(logged_at, 'strftime'):
        return logged_at.strftime('%Y-%m-%d')
    return str(logged_at)[:10]


@bp.route('/dashboard')
@login_required
def dashboard():
    """Render the main dashboard with fitness metrics, charts, and motivation."""
    db = get_db()
    user_id = session['user_id']

    # --- Core profile & daily summary ---
    profile = ProfileService.get_profile(db, user_id)
    today_summary = TrackingService.get_today_summary(db, user_id)

    # --- Analytics data ---
    streak = AnalyticsService.get_streak(db, user_id)
    fitness_score = AnalyticsService.calculate_fitness_score(db, user_id)

    # --- Chart data (30-day weight, 7-day calories, 30-day workouts) ---
    weight_history = TrackingService.get_weight_history(db, user_id, days=30)
    weight_chart_json = None
    if weight_history:
        dates = [format_logged_at(w['logged_at']) for w in weight_history]
        weights = [w['weight'] for w in weight_history]
        goal_w = profile.get('goal_weight') if profile else None
        weight_chart_json = create_weight_chart(dates, weights, goal_w)

    calorie_history = TrackingService.get_calorie_history(db, user_id, days=7)
    calories_chart_json = None
    if calorie_history:
        from collections import defaultdict
        daily_cals = defaultdict(lambda: {'consumed': 0, 'burned': 0})
        for c in calorie_history:
            day = format_logged_at(c['logged_at'])
            daily_cals[day]['consumed'] += c['calories_consumed'] or 0
            daily_cals[day]['burned'] += c['calories_burned'] or 0
        sorted_days = sorted(daily_cals.keys())
        calories_chart_json = create_calories_chart(
            sorted_days,
            [daily_cals[d]['consumed'] for d in sorted_days],
            [daily_cals[d]['burned'] for d in sorted_days]
        )

    workout_history = TrackingService.get_workout_history(db, user_id, days=30)
    workout_chart_json = None
    if workout_history:
        from collections import Counter
        type_counts = Counter(w['workout_type'] for w in workout_history)
        workout_chart_json = create_workout_chart(
            list(type_counts.keys()), list(type_counts.values())
        )

    # --- AI motivation (non-critical – degrade gracefully) ---
    motivation = None
    try:
        ai = AIEngine()
        motivation = ai.generate_motivation()
    except Exception:
        logger.warning("Failed to generate AI motivation for user %s", user_id, exc_info=True)

    return render_template(
        'dashboard/index.html',
        profile=profile,
        today=today_summary,
        now=datetime.now(),
        streak=streak,
        fitness_score=fitness_score,
        weight_chart=weight_chart_json,
        calories_chart=calories_chart_json,
        workout_chart=workout_chart_json,
        motivation=motivation,
    )
