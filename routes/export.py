"""
FitAI - Export Routes
CSV and report export functionality.
"""
import io
import logging
from datetime import datetime
from flask import Blueprint, render_template, session, Response
from database.db import get_db
from services.tracking_service import TrackingService
from services.analytics_service import AnalyticsService
from services.profile_service import ProfileService
from utils.decorators import login_required

logger = logging.getLogger(__name__)
bp = Blueprint('export', __name__, url_prefix='/export')


@bp.route('/')
@login_required
def export_page():
    """Render export options page."""
    return render_template('export/export.html')


@bp.route('/csv/<data_type>')
@login_required
def export_csv(data_type):
    """Export tracking data as CSV."""
    db = get_db()
    user_id = session['user_id']

    try:
        import pandas as pd

        data_map = {
            'weight': {
                'fetcher': lambda: TrackingService.get_weight_history(db, user_id, days=365),
                'columns': ['weight', 'logged_at'],
                'headers': ['Weight (kg)', 'Date'],
            },
            'calories': {
                'fetcher': lambda: TrackingService.get_calorie_history(db, user_id, days=365),
                'columns': ['calories_consumed', 'calories_burned', 'meal_details', 'logged_at'],
                'headers': ['Consumed (kcal)', 'Burned (kcal)', 'Meal Details', 'Date'],
            },
            'water': {
                'fetcher': lambda: TrackingService.get_water_history(db, user_id, days=365),
                'columns': ['amount_ml', 'logged_at'],
                'headers': ['Amount (ml)', 'Date'],
            },
            'sleep': {
                'fetcher': lambda: TrackingService.get_sleep_history(db, user_id, days=365),
                'columns': ['sleep_hours', 'sleep_quality', 'logged_at'],
                'headers': ['Hours', 'Quality', 'Date'],
            },
            'workouts': {
                'fetcher': lambda: TrackingService.get_workout_history(db, user_id, days=365),
                'columns': ['workout_type', 'duration_minutes', 'calories_burned', 'exercises', 'notes', 'logged_at'],
                'headers': ['Type', 'Duration (min)', 'Calories Burned', 'Exercises', 'Notes', 'Date'],
            },
            'steps': {
                'fetcher': lambda: TrackingService.get_step_history(db, user_id, days=365),
                'columns': ['steps', 'logged_at'],
                'headers': ['Steps', 'Date'],
            },
        }

        if data_type not in data_map:
            return 'Invalid data type', 400

        config = data_map[data_type]
        data = config['fetcher']()

        if not data:
            df = pd.DataFrame(columns=config['headers'])
        else:
            df = pd.DataFrame(data)
            # Select and rename columns
            available_cols = [c for c in config['columns'] if c in df.columns]
            df = df[available_cols]
            rename_map = dict(zip(available_cols, config['headers'][:len(available_cols)]))
            df = df.rename(columns=rename_map)

        output = io.StringIO()
        df.to_csv(output, index=False)

        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f'fitai_{data_type}_{timestamp}.csv'

        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
    except Exception as e:
        logger.error(f'Error exporting CSV: {e}')
        return 'Export failed', 500


@bp.route('/report/pdf')
@login_required
def export_report():
    """Generate and download a comprehensive fitness report."""
    db = get_db()
    user_id = session['user_id']

    try:
        profile = ProfileService.get_profile(db, user_id) or {}
        today_summary = TrackingService.get_today_summary(db, user_id)
        weekly_summary = TrackingService.get_weekly_summary(db, user_id)
        fitness_score = AnalyticsService.calculate_fitness_score(db, user_id)
        habits = AnalyticsService.analyze_habits(db, user_id)
        prediction = AnalyticsService.predict_goal_achievement(db, user_id)
        streak = AnalyticsService.get_streak(db, user_id)

        # Build comprehensive text report
        report_lines = [
            "=" * 60,
            "FITAI - FITNESS ANALYTICS REPORT",
            f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            "=" * 60,
            "",
            "--- PROFILE ---",
            f"Age: {profile.get('age', 'N/A')}",
            f"Gender: {profile.get('gender', 'N/A')}",
            f"Height: {profile.get('height', 'N/A')} cm",
            f"Weight: {profile.get('weight', 'N/A')} kg",
            f"Goal Weight: {profile.get('goal_weight', 'N/A')} kg",
            f"Fitness Goal: {profile.get('fitness_goal', 'N/A')}",
            f"Activity Level: {profile.get('activity_level', 'N/A')}",
            "",
            "--- FITNESS SCORE ---",
            f"Overall Score: {fitness_score}/100",
            f"Current Streak: {streak} days",
            "",
            "--- TODAY'S SUMMARY ---",
            f"Calories Consumed: {today_summary.get('calories_consumed', 0)} kcal",
            f"Calories Burned: {today_summary.get('calories_burned', 0)} kcal",
            f"Water Intake: {today_summary.get('water_ml', 0)} ml",
            f"Sleep: {today_summary.get('sleep_hours', 0)} hours",
            f"Steps: {today_summary.get('steps', 0)}",
            f"Workouts: {today_summary.get('workout_count', 0)}",
            "",
            "--- WEEKLY AVERAGES ---",
            f"Avg Calories Consumed: {weekly_summary.get('avg_calories_consumed', 0)} kcal",
            f"Avg Calories Burned: {weekly_summary.get('avg_calories_burned', 0)} kcal",
            f"Avg Water Intake: {weekly_summary.get('avg_water', 0)} ml",
            f"Avg Sleep: {weekly_summary.get('avg_sleep', 0)} hours",
            f"Workout Sessions: {weekly_summary.get('workout_count', 0)}",
            f"Avg Steps: {weekly_summary.get('avg_steps', 0)}",
            "",
            "--- HABIT CONSISTENCY (Last 30 Days) ---",
            f"Water Tracking: {habits.get('water_consistency', 0)}%",
            f"Sleep Tracking: {habits.get('sleep_consistency', 0)}%",
            f"Workout Tracking: {habits.get('workout_consistency', 0)}%",
            f"Calorie Tracking: {habits.get('calorie_consistency', 0)}%",
            f"Overall Consistency: {habits.get('overall', 0)}%",
            "",
            "--- GOAL PREDICTION ---",
            f"Predicted Achievement: {prediction.get('predicted_date', 'N/A')}",
            f"On Track: {'Yes' if prediction.get('on_track') else 'No'}",
            f"Days Remaining: {prediction.get('days_remaining', 'N/A')}",
            "",
            "=" * 60,
            "Thank you for using FitAI!",
            "Keep pushing towards your goals! 💪",
            "=" * 60,
        ]

        report_content = "\n".join(report_lines)
        timestamp = datetime.now().strftime('%Y%m%d')
        filename = f'fitai_report_{timestamp}.txt'

        return Response(
            report_content,
            mimetype='text/plain',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
    except Exception as e:
        logger.error(f'Error generating report: {e}')
        return 'Report generation failed', 500
