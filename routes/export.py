"""
FitAI - Export Routes
CSV and professional PDF report export functionality.
"""
import io
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, session, Response, request
from database.db import get_db
from services.tracking_service import TrackingService
from services.analytics_service import AnalyticsService
from services.profile_service import ProfileService
from services.ai_engine import AIEngine
from utils.decorators import login_required
from utils.calculations import (
    calculate_bmi, calculate_bmr, calculate_tdee, 
    calculate_macro_targets, parse_workout_volume
)

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
    """Generate and download a comprehensive 8-page fitness report in PDF format."""
    db = get_db()
    user_id = session['user_id']
    username = db.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()['username']

    try:
        # 1. Fetch all data
        profile = ProfileService.get_profile(db, user_id) or {}
        today_summary = TrackingService.get_today_summary(db, user_id)
        weekly_summary = TrackingService.get_weekly_summary(db, user_id)
        fitness_score = AnalyticsService.calculate_fitness_score(db, user_id)
        habits = AnalyticsService.analyze_habits(db, user_id)
        prediction = AnalyticsService.predict_goal_achievement(db, user_id)
        streak = AnalyticsService.get_streak(db, user_id)
        
        # Extended data
        workouts_30d = TrackingService.get_workout_history(db, user_id, days=30)
        weight_30d = TrackingService.get_weight_history(db, user_id, days=30)
        cals_30d = TrackingService.get_calorie_history(db, user_id, days=30)
        
        # 2. Derived Calculations
        weight_kg = profile.get('weight')
        height_cm = profile.get('height')
        age = profile.get('age')
        gender = profile.get('gender')
        activity = profile.get('activity_level', 'moderate')
        goal = profile.get('fitness_goal', 'maintenance')
        
        bmi, bmi_cat = calculate_bmi(weight_kg, height_cm)
        bmr = calculate_bmr(weight_kg, height_cm, age, gender)
        tdee = calculate_tdee(bmr, activity)
        macros = calculate_macro_targets(tdee, weight_kg, goal) if tdee else None
        
        # Calculate Volume
        total_volume = 0
        workout_types = {}
        for w in workouts_30d:
            w_type = w.get('workout_type', 'General')
            workout_types[w_type] = workout_types.get(w_type, 0) + 1
            if w.get('exercises'):
                total_volume += parse_workout_volume(w['exercises'])
                
        # 3. AI Insights
        ai = AIEngine()
        ai_insight = "Insufficient data to generate AI insights."
        if weight_30d or workouts_30d or cals_30d:
            prompt = [
                {"role": "system", "content": "You are a professional fitness coach writing a short, 2-paragraph insight summary for a client's monthly report. Focus on their adherence, volume, and progress. Do not use markdown headers, just plain text paragraphs."},
                {"role": "user", "content": f"Client {username} logged {len(workouts_30d)} workouts, {len(cals_30d)} meal days. Consistency: {fitness_score}%. Volume: {total_volume}kg. Goal: {goal}. Write the insight summary."}
            ]
            ai_insight = ai._call_api(prompt, max_tokens=250)

        # 4. Generate PDF
        try:
            from fpdf import FPDF
            
            class PDF(FPDF):
                def header(self):
                    self.set_font('Helvetica', 'B', 16)
                    self.set_text_color(15, 23, 42)
                    self.cell(0, 15, 'FitAI Fitness Assessment System', 0, 1, 'C')
                    self.set_draw_color(59, 130, 246) # Blue line
                    self.line(10, 25, 200, 25)
                    self.ln(5)

                def footer(self):
                    self.set_y(-15)
                    self.set_font('Helvetica', 'I', 8)
                    self.set_text_color(100, 116, 139)
                    self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

                def page_title(self, title):
                    self.set_font('Helvetica', 'B', 20)
                    self.set_text_color(30, 41, 59)
                    self.cell(0, 12, title, 0, 1, 'C')
                    self.ln(10)

                def section_title(self, title):
                    self.set_font('Helvetica', 'B', 14)
                    self.set_text_color(255, 255, 255)
                    self.set_fill_color(30, 41, 59)
                    self.cell(0, 10, f'  {title}', 0, 1, 'L', fill=True)
                    self.ln(4)
                    
                def sub_title(self, title):
                    self.set_font('Helvetica', 'B', 12)
                    self.set_text_color(15, 23, 42)
                    self.cell(0, 8, title, 0, 1, 'L')
                    self.ln(2)

                def key_value_row(self, key, value, w1=60, w2=130):
                    self.set_font('Helvetica', 'B', 11)
                    self.set_text_color(100, 116, 139)
                    self.cell(w1, 8, key, 0, 0, 'L')
                    self.set_font('Helvetica', '', 11)
                    self.set_text_color(15, 23, 42)
                    self.cell(w2, 8, str(value), 0, 1, 'L')
                    
                def simple_text(self, text):
                    self.set_font('Helvetica', '', 11)
                    self.set_text_color(15, 23, 42)
                    self.multi_cell(0, 7, text)
                    self.ln(4)

            pdf = PDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            
            # --- PAGE 1: OVERVIEW ---
            pdf.add_page()
            pdf.page_title('Monthly Fitness Report')
            pdf.simple_text(f"Client: {username.upper()}")
            pdf.simple_text(f"Report Date: {datetime.now().strftime('%B %d, %Y')}")
            pdf.ln(10)
            
            pdf.section_title('USER PROFILE')
            pdf.key_value_row("Age:", profile.get('age', 'N/A'))
            pdf.key_value_row("Gender:", str(profile.get('gender', 'N/A')).capitalize())
            pdf.key_value_row("Height:", f"{height_cm} cm" if height_cm else "N/A")
            pdf.key_value_row("Weight:", f"{weight_kg} kg" if weight_kg else "N/A")
            pdf.key_value_row("Goal Weight:", f"{profile.get('goal_weight', 'N/A')} kg")
            pdf.key_value_row("Fitness Goal:", str(profile.get('fitness_goal', 'N/A')).title())
            pdf.key_value_row("Activity Level:", str(profile.get('activity_level', 'N/A')).title())
            pdf.ln(10)
            
            pdf.section_title('FITNESS CONSISTENCY')
            pdf.key_value_row("Overall Score:", f"{fitness_score}/100")
            pdf.key_value_row("Current Streak:", f"{streak} Days")
            pdf.key_value_row("Workout Consistency:", f"{habits.get('workout_consistency', 0)}%")
            pdf.key_value_row("Nutrition Tracking:", f"{habits.get('calorie_consistency', 0)}%")
            pdf.key_value_row("Hydration Tracking:", f"{habits.get('water_consistency', 0)}%")
            
            # --- PAGE 2: BODY COMPOSITION ---
            pdf.add_page()
            pdf.page_title('Body Composition & Metabolism')
            
            pdf.section_title('METRIC CALCULATIONS')
            pdf.key_value_row("Body Mass Index (BMI):", f"{bmi} ({bmi_cat})" if bmi else "N/A")
            pdf.key_value_row("Basal Metabolic Rate (BMR):", f"{bmr} kcal/day" if bmr else "N/A")
            pdf.key_value_row("Total Daily Energy Exp. (TDEE):", f"{tdee} kcal/day" if tdee else "N/A")
            pdf.ln(5)
            pdf.simple_text("Note: BMR calculated using Mifflin-St Jeor equation. TDEE is estimated based on reported activity level.")
            pdf.ln(10)
            
            pdf.section_title('WEIGHT PROGRESSION')
            if weight_30d:
                pdf.key_value_row("Starting Weight (30d):", f"{weight_30d[-1]['weight']} kg")
                pdf.key_value_row("Current Weight:", f"{weight_30d[0]['weight']} kg")
                change = weight_30d[0]['weight'] - weight_30d[-1]['weight']
                pdf.key_value_row("Total Change:", f"{change:+.1f} kg")
            else:
                pdf.simple_text("Insufficient weight log data for the past 30 days.")
                
            pdf.ln(10)
            pdf.section_title('GOAL TRACKING')
            pdf.key_value_row("Predicted Achievement:", prediction.get('predicted_date', 'N/A'))
            pdf.key_value_row("On Track:", 'Yes' if prediction.get('on_track') else 'No')
            pdf.key_value_row("Days Remaining:", prediction.get('days_remaining', 'N/A'))
            
            # --- PAGE 3: NUTRITION ---
            pdf.add_page()
            pdf.page_title('Nutrition & Macros')
            
            pdf.section_title('TARGET MACRONUTRIENTS (ESTIMATED)')
            if macros:
                pdf.key_value_row("Target Calories:", f"{macros['target_calories']} kcal/day")
                pdf.key_value_row("Protein:", f"{macros['protein_g']}g  (2.2g/kg bodyweight)")
                pdf.key_value_row("Carbohydrates:", f"{macros['carb_g']}g")
                pdf.key_value_row("Fats:", f"{macros['fat_g']}g")
                pdf.key_value_row("Fiber:", f"{macros['fiber_g']}g")
            else:
                pdf.simple_text("Missing profile data to calculate macros (requires height, weight, age, gender).")
            pdf.ln(10)
            
            pdf.section_title('MONTHLY CALORIE ANALYSIS')
            pdf.key_value_row("Average Consumed:", f"{weekly_summary.get('avg_calories_consumed', 0)} kcal/day")
            pdf.key_value_row("Average Burned:", f"{weekly_summary.get('avg_calories_burned', 0)} kcal/day")
            
            # --- PAGE 4: WORKOUT & VOLUME ---
            pdf.add_page()
            pdf.page_title('Bodybuilding & Performance')
            
            pdf.section_title('MONTHLY WORKOUT SUMMARY')
            pdf.key_value_row("Total Workouts Logged:", f"{len(workouts_30d)}")
            pdf.key_value_row("Estimated Total Volume:", f"{total_volume:,.0f} kg")
            pdf.ln(5)
            pdf.sub_title("Workout Breakdown")
            for wtype, count in workout_types.items():
                pdf.key_value_row(f"  • {wtype}:", f"{count} sessions")
                
            pdf.ln(10)
            pdf.section_title('EXERCISE DETAILS (LAST 5 LOGS)')
            if workouts_30d:
                for w in workouts_30d[:5]:
                    date_str = w['logged_at'][:10] if isinstance(w['logged_at'], str) else w['logged_at'].strftime('%Y-%m-%d')
                    pdf.sub_title(f"{date_str} - {w['workout_type']}")
                    pdf.simple_text(f"Duration: {w.get('duration_minutes', 0)} min | Burned: {w.get('calories_burned', 0)} kcal")
                    if w.get('exercises'):
                        pdf.simple_text(f"Exercises: {w['exercises']}")
                    pdf.ln(3)
            else:
                pdf.simple_text("No workouts logged in the last 30 days.")
                
            # --- PAGE 5: INSIGHTS ---
            pdf.add_page()
            pdf.page_title('AI Fitness Insights')
            pdf.section_title('COACH SUMMARY')
            
            # Clean AI response for PDF (replace fancy quotes, etc)
            insight_clean = ai_insight.replace('"', '"').replace('"', '"').replace('\u2019', "'").replace('\u2014', "-")
            pdf.simple_text(insight_clean)
            pdf.ln(10)
            
            pdf.section_title('DATA COMPLETENESS')
            pdf.key_value_row("Weight Logs:", f"{len(weight_30d)} entries")
            pdf.key_value_row("Nutrition Logs:", f"{len(cals_30d)} entries")
            pdf.key_value_row("Workout Logs:", f"{len(workouts_30d)} entries")

            pdf_bytes = bytes(pdf.output())
            timestamp = datetime.now().strftime('%Y%m%d')
            filename = f'fitai_assessment_{username}_{timestamp}.pdf'
            
            return Response(
                pdf_bytes, 
                mimetype='application/pdf', 
                headers={'Content-Disposition': f'attachment; filename={filename}'}
            )
            
        except ImportError:
            # Group logs by date
            daily_logs = {}
            for w in weight_30d:
                d = str(w['logged_at'])[:10]
                if d not in daily_logs: daily_logs[d] = {}
                daily_logs[d]['weight'] = w['weight']
            for w in workouts_30d:
                d = str(w['logged_at'])[:10]
                if d not in daily_logs: daily_logs[d] = {}
                if 'workouts' not in daily_logs[d]: daily_logs[d]['workouts'] = []
                daily_logs[d]['workouts'].append(w)
            for cal in cals_30d:
                d = str(cal['logged_at'])[:10]
                if d not in daily_logs: daily_logs[d] = {}
                daily_logs[d]['calories'] = cal
            sorted_logs = dict(sorted(daily_logs.items(), reverse=True))

            logger.warning('fpdf2 not installed. Falling back to HTML print report.')
            return render_template('export/export_fallback.html',
                username=username, profile=profile,
                fitness_score=fitness_score, streak=streak, habits=habits,
                bmi=bmi, bmi_cat=bmi_cat, bmr=bmr, tdee=tdee,
                weight_30d=weight_30d, prediction=prediction,
                macros=macros, weekly_summary=weekly_summary,
                workouts_30d=workouts_30d, total_volume=total_volume,
                workout_types=workout_types, ai_insight=ai_insight,
                cals_30d=cals_30d, daily_logs=sorted_logs, now=datetime.now
            )

    except Exception as e:
        import traceback
        logger.error(f'Error generating report: {traceback.format_exc()}')
        return f'Report generation failed: {traceback.format_exc()}', 500
