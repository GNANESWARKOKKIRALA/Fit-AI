"""
FitAI - Tracking Service
CRUD operations for all fitness tracking log tables.
"""
from datetime import datetime, timedelta


class TrackingService:
    """Service class for fitness tracking data operations."""

    @staticmethod
    def log_weight(db, user_id, weight):
        """Log a weight entry."""
        db.execute(
            'INSERT INTO weight_logs (user_id, weight) VALUES (?, ?)',
            (user_id, float(weight))
        )
        db.commit()

    @staticmethod
    def log_water(db, user_id, amount_ml):
        """Log water intake."""
        db.execute(
            'INSERT INTO water_logs (user_id, amount_ml) VALUES (?, ?)',
            (user_id, float(amount_ml))
        )
        db.commit()

    @staticmethod
    def log_calories(db, user_id, consumed, burned=0, meal_details=''):
        """Log calorie intake and burn."""
        db.execute(
            'INSERT INTO calorie_logs (user_id, calories_consumed, calories_burned, meal_details) VALUES (?, ?, ?, ?)',
            (user_id, float(consumed), float(burned), meal_details)
        )
        db.commit()

    @staticmethod
    def log_sleep(db, user_id, hours, quality='Good'):
        """Log sleep data."""
        db.execute(
            'INSERT INTO sleep_logs (user_id, sleep_hours, sleep_quality) VALUES (?, ?, ?)',
            (user_id, float(hours), quality)
        )
        db.commit()

    @staticmethod
    def log_workout(db, user_id, workout_type, duration, calories_burned=0, exercises='', notes=''):
        """Log a workout session."""
        db.execute(
            '''INSERT INTO workout_logs (user_id, workout_type, duration_minutes, calories_burned, exercises, notes)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (user_id, workout_type, int(duration), float(calories_burned), exercises, notes)
        )
        db.commit()

    @staticmethod
    def log_steps(db, user_id, steps):
        """Log step count."""
        db.execute(
            'INSERT INTO step_logs (user_id, steps) VALUES (?, ?)',
            (user_id, int(steps))
        )
        db.commit()

    @staticmethod
    def get_weight_history(db, user_id, days=30):
        """Get weight history for the specified number of days."""
        cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        rows = db.execute(
            '''SELECT weight, logged_at FROM weight_logs
               WHERE user_id = ? AND DATE(logged_at) >= ?
               ORDER BY logged_at ASC''',
            (user_id, cutoff)
        ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_water_history(db, user_id, days=30):
        """Get water intake history."""
        cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        rows = db.execute(
            '''SELECT amount_ml, logged_at FROM water_logs
               WHERE user_id = ? AND DATE(logged_at) >= ?
               ORDER BY logged_at ASC''',
            (user_id, cutoff)
        ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_calorie_history(db, user_id, days=30):
        """Get calorie history."""
        cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        rows = db.execute(
            '''SELECT calories_consumed, calories_burned, meal_details, logged_at
               FROM calorie_logs WHERE user_id = ? AND DATE(logged_at) >= ?
               ORDER BY logged_at ASC''',
            (user_id, cutoff)
        ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_sleep_history(db, user_id, days=30):
        """Get sleep history."""
        cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        rows = db.execute(
            '''SELECT sleep_hours, sleep_quality, logged_at FROM sleep_logs
               WHERE user_id = ? AND DATE(logged_at) >= ?
               ORDER BY logged_at ASC''',
            (user_id, cutoff)
        ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_workout_history(db, user_id, days=30):
        """Get workout history."""
        cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        rows = db.execute(
            '''SELECT workout_type, duration_minutes, calories_burned, exercises, notes, logged_at
               FROM workout_logs WHERE user_id = ? AND DATE(logged_at) >= ?
               ORDER BY logged_at ASC''',
            (user_id, cutoff)
        ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_step_history(db, user_id, days=30):
        """Get step count history."""
        cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        rows = db.execute(
            '''SELECT steps, logged_at FROM step_logs
               WHERE user_id = ? AND DATE(logged_at) >= ?
               ORDER BY logged_at ASC''',
            (user_id, cutoff)
        ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_today_summary(db, user_id):
        """Get today's tracking summary."""
        today = datetime.now().strftime('%Y-%m-%d')

        # Today's calories
        cal = db.execute(
            '''SELECT COALESCE(SUM(calories_consumed), 0) as consumed,
                      COALESCE(SUM(calories_burned), 0) as burned
               FROM calorie_logs WHERE user_id = ? AND DATE(logged_at) = ?''',
            (user_id, today)
        ).fetchone()

        # Today's water
        water = db.execute(
            'SELECT COALESCE(SUM(amount_ml), 0) as total FROM water_logs WHERE user_id = ? AND DATE(logged_at) = ?',
            (user_id, today)
        ).fetchone()

        # Today's sleep
        sleep = db.execute(
            'SELECT COALESCE(SUM(sleep_hours), 0) as total FROM sleep_logs WHERE user_id = ? AND DATE(logged_at) = ?',
            (user_id, today)
        ).fetchone()

        # Today's steps
        steps = db.execute(
            'SELECT COALESCE(SUM(steps), 0) as total FROM step_logs WHERE user_id = ? AND DATE(logged_at) = ?',
            (user_id, today)
        ).fetchone()

        # Today's workouts
        workouts = db.execute(
            '''SELECT COUNT(*) as count, COALESCE(SUM(duration_minutes), 0) as duration
               FROM workout_logs WHERE user_id = ? AND DATE(logged_at) = ?''',
            (user_id, today)
        ).fetchone()

        # Latest weight
        weight = db.execute(
            'SELECT weight FROM weight_logs WHERE user_id = ? ORDER BY logged_at DESC LIMIT 1',
            (user_id,)
        ).fetchone()

        return {
            'calories_consumed': cal['consumed'] if cal else 0,
            'calories_burned': cal['burned'] if cal else 0,
            'water_ml': water['total'] if water else 0,
            'sleep_hours': sleep['total'] if sleep else 0,
            'steps': steps['total'] if steps else 0,
            'workout_count': workouts['count'] if workouts else 0,
            'workout_duration': workouts['duration'] if workouts else 0,
            'current_weight': weight['weight'] if weight else None,
        }

    @staticmethod
    def get_weekly_summary(db, user_id):
        """Get this week's aggregated data."""
        week_start = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

        avg_calories = db.execute(
            '''SELECT COALESCE(AVG(calories_consumed), 0) as avg_consumed,
                      COALESCE(AVG(calories_burned), 0) as avg_burned
               FROM calorie_logs WHERE user_id = ? AND DATE(logged_at) >= ?''',
            (user_id, week_start)
        ).fetchone()

        avg_water = db.execute(
            '''SELECT COALESCE(AVG(daily_total), 0) as avg FROM
               (SELECT DATE(logged_at) as day, SUM(amount_ml) as daily_total
                FROM water_logs WHERE user_id = ? AND DATE(logged_at) >= ?
                GROUP BY DATE(logged_at))''',
            (user_id, week_start)
        ).fetchone()

        avg_sleep = db.execute(
            'SELECT COALESCE(AVG(sleep_hours), 0) as avg FROM sleep_logs WHERE user_id = ? AND DATE(logged_at) >= ?',
            (user_id, week_start)
        ).fetchone()

        workout_count = db.execute(
            'SELECT COUNT(*) as count FROM workout_logs WHERE user_id = ? AND DATE(logged_at) >= ?',
            (user_id, week_start)
        ).fetchone()

        avg_steps = db.execute(
            '''SELECT COALESCE(AVG(daily_total), 0) as avg FROM
               (SELECT DATE(logged_at) as day, SUM(steps) as daily_total
                FROM step_logs WHERE user_id = ? AND DATE(logged_at) >= ?
                GROUP BY DATE(logged_at))''',
            (user_id, week_start)
        ).fetchone()

        return {
            'avg_calories_consumed': round(avg_calories['avg_consumed'], 0) if avg_calories else 0,
            'avg_calories_burned': round(avg_calories['avg_burned'], 0) if avg_calories else 0,
            'avg_water': round(avg_water['avg'], 0) if avg_water else 0,
            'avg_sleep': round(avg_sleep['avg'], 1) if avg_sleep else 0,
            'workout_count': workout_count['count'] if workout_count else 0,
            'avg_steps': round(avg_steps['avg'], 0) if avg_steps else 0,
        }
