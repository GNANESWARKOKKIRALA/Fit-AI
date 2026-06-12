"""
FitAI - Profile Service
Profile CRUD and goal management operations.
"""


class ProfileService:
    """Service class for user profile and goal management."""

    @staticmethod
    def get_profile(db, user_id):
        """Get user profile."""
        row = db.execute(
            'SELECT * FROM profiles WHERE user_id = ?',
            (user_id,)
        ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def create_or_update_profile(db, user_id, data):
        """Create or update user profile (UPSERT)."""
        existing = db.execute(
            'SELECT id FROM profiles WHERE user_id = ?',
            (user_id,)
        ).fetchone()

        if existing:
            db.execute(
                '''UPDATE profiles SET
                    age = ?, gender = ?, height = ?, weight = ?, goal_weight = ?,
                    activity_level = ?, fitness_goal = ?, workout_preference = ?,
                    diet_preference = ?, medical_notes = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE user_id = ?''',
                (
                    data.get('age'), data.get('gender'),
                    data.get('height'), data.get('weight'), data.get('goal_weight'),
                    data.get('activity_level'), data.get('fitness_goal'),
                    data.get('workout_preference'), data.get('diet_preference'),
                    data.get('medical_notes'), user_id
                )
            )
        else:
            db.execute(
                '''INSERT INTO profiles (user_id, age, gender, height, weight, goal_weight,
                    activity_level, fitness_goal, workout_preference, diet_preference, medical_notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    user_id, data.get('age'), data.get('gender'),
                    data.get('height'), data.get('weight'), data.get('goal_weight'),
                    data.get('activity_level'), data.get('fitness_goal'),
                    data.get('workout_preference'), data.get('diet_preference'),
                    data.get('medical_notes')
                )
            )
        db.commit()

    @staticmethod
    def get_goals(db, user_id):
        """Get all fitness goals for a user."""
        rows = db.execute(
            'SELECT * FROM fitness_goals WHERE user_id = ? ORDER BY created_at DESC',
            (user_id,)
        ).fetchall()
        goals = []
        for row in rows:
            goal = dict(row)
            if goal['target_value'] and goal['target_value'] > 0:
                current = goal.get('current_value') or 0
                goal['progress'] = min(round((current / goal['target_value']) * 100, 1), 100)
            else:
                goal['progress'] = 0
            goals.append(goal)
        return goals

    @staticmethod
    def create_goal(db, user_id, goal_type, target_value, target_date=None):
        """Create a new fitness goal."""
        db.execute(
            '''INSERT INTO fitness_goals (user_id, goal_type, target_value, current_value, start_date, target_date)
               VALUES (?, ?, ?, 0, DATE('now'), ?)''',
            (user_id, goal_type, float(target_value), target_date)
        )
        db.commit()

    @staticmethod
    def update_goal_progress(db, goal_id, current_value):
        """Update goal progress."""
        db.execute(
            'UPDATE fitness_goals SET current_value = ? WHERE id = ?',
            (float(current_value), goal_id)
        )
        db.commit()

    @staticmethod
    def complete_goal(db, goal_id):
        """Mark a goal as completed."""
        db.execute(
            "UPDATE fitness_goals SET status = 'completed' WHERE id = ?",
            (goal_id,)
        )
        db.commit()

    @staticmethod
    def delete_goal(db, goal_id):
        """Delete a fitness goal."""
        db.execute('DELETE FROM fitness_goals WHERE id = ?', (goal_id,))
        db.commit()
