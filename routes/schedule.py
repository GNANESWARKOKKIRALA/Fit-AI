import datetime
import calendar
from flask import Blueprint, render_template, request, jsonify, session, g
from utils.decorators import login_required
from database.db import get_db

schedule_bp = Blueprint('schedule', __name__, url_prefix='/schedule')

@schedule_bp.route('/')
@login_required
def schedule_index():
    user_id = session['user_id']
    
    # Get the requested year and month, default to current
    now = datetime.datetime.now()
    year = int(request.args.get('year', now.year))
    month = int(request.args.get('month', now.month))
    
    # Generate calendar matrix
    cal = calendar.Calendar(firstweekday=0) # Monday first
    month_days = cal.monthdatescalendar(year, month)
    
    # Month names for display
    month_name = calendar.month_name[month]
    
    # Calculate prev/next month links
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    # Fetch scheduled workouts for this month (plus a little padding for overlapping weeks)
    db = get_db()
    start_date = month_days[0][0].strftime('%Y-%m-%d')
    end_date = month_days[-1][-1].strftime('%Y-%m-%d')
    
    workouts_data = db.execute('''
        SELECT id, scheduled_date, workout_type, time_of_day, notes, completed 
        FROM workout_schedule 
        WHERE user_id = ? AND scheduled_date BETWEEN ? AND ?
        ORDER BY time_of_day ASC
    ''', (user_id, start_date, end_date)).fetchall()
    
    # Organize workouts by date
    scheduled_workouts = {}
    for w in workouts_data:
        date_str = w['scheduled_date']
        if date_str not in scheduled_workouts:
            scheduled_workouts[date_str] = []
        scheduled_workouts[date_str].append(dict(w))
        
    return render_template(
        'schedule/index.html',
        year=year,
        month=month,
        month_name=month_name,
        month_days=month_days,
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year,
        scheduled_workouts=scheduled_workouts,
        now=now.date()
    )

@schedule_bp.route('/add', methods=['POST'])
@login_required
def add_workout():
    user_id = session['user_id']
    data = request.json
    
    scheduled_date = data.get('date')
    workout_type = data.get('type')
    time_of_day = data.get('time', '')
    notes = data.get('notes', '')
    
    if not scheduled_date or not workout_type:
        return jsonify({'success': False, 'message': 'Date and Workout Type are required.'}), 400
        
    db = get_db()
    cursor = db.execute('''
        INSERT INTO workout_schedule (user_id, scheduled_date, workout_type, time_of_day, notes)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, scheduled_date, workout_type, time_of_day, notes))
    db.commit()
    
    return jsonify({
        'success': True, 
        'message': 'Workout scheduled successfully.',
        'id': cursor.lastrowid
    })

@schedule_bp.route('/<int:workout_id>/toggle', methods=['POST'])
@login_required
def toggle_workout(workout_id):
    user_id = session['user_id']
    data = request.json
    completed = 1 if data.get('completed') else 0
    
    db = get_db()
    db.execute('''
        UPDATE workout_schedule SET completed = ? 
        WHERE id = ? AND user_id = ?
    ''', (completed, workout_id, user_id))
    db.commit()
    
    return jsonify({'success': True})

@schedule_bp.route('/<int:workout_id>', methods=['DELETE'])
@login_required
def delete_workout(workout_id):
    user_id = session['user_id']
    db = get_db()
    db.execute('''
        DELETE FROM workout_schedule 
        WHERE id = ? AND user_id = ?
    ''', (workout_id, user_id))
    db.commit()
    
    return jsonify({'success': True})
