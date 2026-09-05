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
    """Generate and download a comprehensive fitness report (PDF or TXT fallback)."""
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
        
        timestamp = datetime.now().strftime('%Y%m%d')
        
        try:
            from fpdf import FPDF
            
            class PDF(FPDF):
                def header(self):
                    self.set_font('Helvetica', 'B', 15)
                    self.set_text_color(41, 128, 185)
                    self.cell(0, 10, 'FitAI - Fitness Analytics Report', 0, 1, 'C')
                    self.ln(5)

                def footer(self):
                    self.set_y(-15)
                    self.set_font('Helvetica', 'I', 8)
                    self.set_text_color(128, 128, 128)
                    self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

                def section_title(self, title):
                    self.set_font('Helvetica', 'B', 12)
                    self.set_text_color(255, 255, 255)
                    self.set_fill_color(52, 73, 94)
                    self.cell(0, 8, f'  {title}', 0, 1, 'L', fill=True)
                    self.ln(2)

                def section_body(self, data_list):
                    self.set_font('Helvetica', '', 11)
                    self.set_text_color(50, 50, 50)
                    for item in data_list:
                        self.cell(0, 6, item, 0, 1)
                    self.ln(5)

            pdf = PDF()
            pdf.add_page()
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 5, f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", 0, 1, 'C')
            pdf.ln(10)

            pdf.section_title('PROFILE')
            pdf.section_body([
                f"Age: {profile.get('age', 'N/A')}", f"Gender: {profile.get('gender', 'N/A')}",
                f"Height: {profile.get('height', 'N/A')} cm", f"Weight: {profile.get('weight', 'N/A')} kg",
                f"Goal Weight: {profile.get('goal_weight', 'N/A')} kg", f"Fitness Goal: {profile.get('fitness_goal', 'N/A')}",
                f"Activity Level: {profile.get('activity_level', 'N/A')}"
            ])

            pdf.section_title('FITNESS SCORE')
            pdf.section_body([f"Overall Score: {fitness_score}/100", f"Current Streak: {streak} days"])

            pdf.section_title("TODAY'S SUMMARY")
            pdf.section_body([
                f"Calories: {today_summary.get('calories_consumed', 0)} kcal in / {today_summary.get('calories_burned', 0)} kcal out",
                f"Water: {today_summary.get('water_ml', 0)} ml", f"Sleep: {today_summary.get('sleep_hours', 0)} hrs",
                f"Steps: {today_summary.get('steps', 0)}", f"Workouts: {today_summary.get('workout_count', 0)}"
            ])

            pdf.section_title('WEEKLY AVERAGES')
            pdf.section_body([
                f"Avg Calories: {weekly_summary.get('avg_calories_consumed', 0)} in / {weekly_summary.get('avg_calories_burned', 0)} out",
                f"Avg Water: {weekly_summary.get('avg_water', 0)} ml", f"Avg Sleep: {weekly_summary.get('avg_sleep', 0)} hrs",
                f"Workouts: {weekly_summary.get('workout_count', 0)}", f"Avg Steps: {weekly_summary.get('avg_steps', 0)}"
            ])

            pdf.section_title('HABIT CONSISTENCY (Last 30 Days)')
            pdf.section_body([
                f"Water: {habits.get('water_consistency', 0)}%", f"Sleep: {habits.get('sleep_consistency', 0)}%",
                f"Workout: {habits.get('workout_consistency', 0)}%", f"Calorie: {habits.get('calorie_consistency', 0)}%",
                f"Overall: {habits.get('overall', 0)}%"
            ])

            pdf.section_title('GOAL PREDICTION')
            pdf.section_body([
                f"Predicted Achievement: {prediction.get('predicted_date', 'N/A')}",
                f"On Track: {'Yes' if prediction.get('on_track') else 'No'}",
                f"Days Remaining: {prediction.get('days_remaining', 'N/A')}"
            ])

            pdf_bytes = bytes(pdf.output())
            filename = f'fitai_report_{timestamp}.pdf'
            
            return Response(pdf_bytes, mimetype='application/pdf', headers={'Content-Disposition': f'attachment; filename={filename}'})
            
        except ImportError:
            # Fallback to Text report if fpdf is not installed
            text_report = f"""FITAI - FITNESS ANALYTICS REPORT
Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
--------------------------------------------------

[ PROFILE ]
Age: {profile.get('age', 'N/A')}
Gender: {profile.get('gender', 'N/A')}
Height: {profile.get('height', 'N/A')} cm
Weight: {profile.get('weight', 'N/A')} kg
Goal Weight: {profile.get('goal_weight', 'N/A')} kg
Fitness Goal: {profile.get('fitness_goal', 'N/A')}
Activity Level: {profile.get('activity_level', 'N/A')}

[ FITNESS SCORE ]
Overall Score: {fitness_score}/100
Current Streak: {streak} days

[ TODAY'S SUMMARY ]
Calories: {today_summary.get('calories_consumed', 0)} kcal in / {today_summary.get('calories_burned', 0)} kcal out
Water: {today_summary.get('water_ml', 0)} ml
Sleep: {today_summary.get('sleep_hours', 0)} hrs
Steps: {today_summary.get('steps', 0)}
Workouts: {today_summary.get('workout_count', 0)}

[ WEEKLY AVERAGES ]
Avg Calories: {weekly_summary.get('avg_calories_consumed', 0)} in / {weekly_summary.get('avg_calories_burned', 0)} out
Avg Water: {weekly_summary.get('avg_water', 0)} ml
Avg Sleep: {weekly_summary.get('avg_sleep', 0)} hrs
Workouts: {weekly_summary.get('workout_count', 0)}
Avg Steps: {weekly_summary.get('avg_steps', 0)}

[ HABIT CONSISTENCY (Last 30 Days) ]
Water: {habits.get('water_consistency', 0)}%
Sleep: {habits.get('sleep_consistency', 0)}%
Workout: {habits.get('workout_consistency', 0)}%
Calorie: {habits.get('calorie_consistency', 0)}%
Overall: {habits.get('overall', 0)}%

[ GOAL PREDICTION ]
Predicted Achievement: {prediction.get('predicted_date', 'N/A')}
On Track: {'Yes' if prediction.get('on_track') else 'No'}
Days Remaining: {prediction.get('days_remaining', 'N/A')}
--------------------------------------------------
"""
            filename = f'fitai_report_{timestamp}.txt'
            return Response(text_report, mimetype='text/plain', headers={'Content-Disposition': f'attachment; filename={filename}'})

    except Exception as e:
        import traceback
        logger.error(f'Error generating report: {traceback.format_exc()}')
        return f'Report generation failed: {traceback.format_exc()}', 500
