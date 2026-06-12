"""
FitAI - Analytics Routes
Fitness analytics dashboard with charts, reports, and insights.
"""
import logging
from flask import Blueprint, render_template, request, jsonify, session
from database.db import get_db
from services.analytics_service import AnalyticsService
from services.tracking_service import TrackingService
from services.profile_service import ProfileService
from services.ai_engine import AIEngine
from charts.plotly_charts import (
    create_weight_chart, create_bmi_chart, create_calories_chart,
    create_workout_chart, create_sleep_chart, create_water_chart,
    create_steps_chart, create_goal_progress_chart, create_fitness_score_gauge
)
from utils.decorators import login_required

logger = logging.getLogger(__name__)
bp = Blueprint('analytics', __name__, url_prefix='/analytics')


def format_logged_at(logged_at):
    """Format logged_at timestamp (string or datetime) to YYYY-MM-DD."""
    if not logged_at:
        return ""
    if hasattr(logged_at, 'strftime'):
        return logged_at.strftime('%Y-%m-%d')
    return str(logged_at)[:10]


@bp.route('/')
@login_required
def analytics():
    """Full analytics dashboard."""
    db = get_db()
    user_id = session['user_id']

    profile = ProfileService.get_profile(db, user_id)
    fitness_score = AnalyticsService.calculate_fitness_score(db, user_id)
    habits = AnalyticsService.analyze_habits(db, user_id)
    prediction = AnalyticsService.predict_goal_achievement(db, user_id)
    achievements = AnalyticsService.get_achievements(db, user_id)
    goals = ProfileService.get_goals(db, user_id)

    # Build charts
    charts = {}

    # Weight chart
    weight_history = TrackingService.get_weight_history(db, user_id, days=30)
    if weight_history:
        dates = [format_logged_at(w['logged_at']) for w in weight_history]
        weights = [w['weight'] for w in weight_history]
        goal_w = profile.get('goal_weight') if profile else None
        charts['weight_chart'] = create_weight_chart(dates, weights, goal_w)

    # BMI chart
    bmi_history = AnalyticsService.calculate_bmi_history(db, user_id)
    if bmi_history:
        charts['bmi_chart'] = create_bmi_chart(
            [b['date'] for b in bmi_history],
            [b['bmi'] for b in bmi_history]
        )

    # Calories chart
    calorie_history = TrackingService.get_calorie_history(db, user_id, days=14)
    if calorie_history:
        from collections import defaultdict
        daily_cals = defaultdict(lambda: {'consumed': 0, 'burned': 0})
        for c in calorie_history:
            day = format_logged_at(c['logged_at'])
            daily_cals[day]['consumed'] += c['calories_consumed'] or 0
            daily_cals[day]['burned'] += c['calories_burned'] or 0
        sorted_days = sorted(daily_cals.keys())
        charts['calories_chart'] = create_calories_chart(
            sorted_days,
            [daily_cals[d]['consumed'] for d in sorted_days],
            [daily_cals[d]['burned'] for d in sorted_days]
        )

    # Workout chart
    workout_history = TrackingService.get_workout_history(db, user_id, days=30)
    if workout_history:
        from collections import Counter
        type_counts = Counter(w['workout_type'] for w in workout_history)
        charts['workout_chart'] = create_workout_chart(
            list(type_counts.keys()), list(type_counts.values())
        )

    # Sleep chart
    sleep_history = TrackingService.get_sleep_history(db, user_id, days=14)
    if sleep_history:
        charts['sleep_chart'] = create_sleep_chart(
            [format_logged_at(s['logged_at']) for s in sleep_history],
            [s['sleep_hours'] for s in sleep_history],
            [s.get('sleep_quality', 'Good') for s in sleep_history]
        )

    # Water chart
    water_history = TrackingService.get_water_history(db, user_id, days=14)
    if water_history:
        from collections import defaultdict
        daily_water = defaultdict(float)
        for w in water_history:
            daily_water[format_logged_at(w['logged_at'])] += w['amount_ml']
        sorted_days = sorted(daily_water.keys())
        charts['water_chart'] = create_water_chart(
            sorted_days, [daily_water[d] for d in sorted_days]
        )

    # Steps chart
    step_history = TrackingService.get_step_history(db, user_id, days=14)
    if step_history:
        from collections import defaultdict
        daily_steps = defaultdict(int)
        for s in step_history:
            daily_steps[format_logged_at(s['logged_at'])] += s['steps']
        sorted_days = sorted(daily_steps.keys())
        charts['steps_chart'] = create_steps_chart(
            sorted_days, [daily_steps[d] for d in sorted_days]
        )

    # Goal progress chart
    if goals:
        charts['goal_chart'] = create_goal_progress_chart(goals)

    # Fitness score gauge
    charts['fitness_gauge'] = create_fitness_score_gauge(fitness_score)

    return render_template('analytics/analytics.html',
                           fitness_score=fitness_score,
                           habits=habits,
                           prediction=prediction,
                           achievements=achievements,
                           **charts)


@bp.route('/report', methods=['POST'])
@login_required
def generate_report():
    """Generate AI weekly report."""
    db = get_db()
    user_id = session['user_id']

    try:
        profile = ProfileService.get_profile(db, user_id)
        weekly_data = TrackingService.get_weekly_summary(db, user_id)

        ai = AIEngine()
        report = ai.generate_weekly_report(profile or {}, weekly_data)

        # Save report
        db.execute(
            'INSERT INTO ai_reports (user_id, report_type, content) VALUES (?, ?, ?)',
            (user_id, 'weekly', report)
        )
        db.commit()

        return jsonify({'success': True, 'content': report})
    except Exception as e:
        logger.error(f'Error generating report: {e}')
        return jsonify({'success': False, 'message': 'Failed to generate report.'})


@bp.route('/reports')
@login_required
def view_reports():
    """View saved AI reports."""
    db = get_db()
    reports = db.execute(
        'SELECT * FROM ai_reports WHERE user_id = ? ORDER BY created_at DESC LIMIT 20',
        (session['user_id'],)
    ).fetchall()
    return jsonify({'reports': [dict(r) for r in reports]})
