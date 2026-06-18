"""
FitAI - Analytics Service
Fitness score calculation, predictions, habit analysis, and achievement tracking.
"""
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service class for fitness analytics and insights."""

    @staticmethod
    def calculate_fitness_score(db, user_id):
        """
        Calculate fitness score (0-100) based on:
        - Consistency (40%): How regularly the user logs data
        - Progress (30%): Movement toward goals
        - Habits (30%): Quality of habits (sleep, water, workout frequency)
        """
        try:
            cutoff = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            total_days = 30

            # Consistency score (40%) - days with at least one log entry
            tracking_days = set()
            for table in ['weight_logs', 'water_logs', 'calorie_logs', 'sleep_logs', 'workout_logs', 'step_logs']:
                rows = db.execute(
                    f'SELECT DISTINCT DATE(logged_at) as d FROM {table} WHERE user_id = ? AND DATE(logged_at) >= ?',
                    (user_id, cutoff)
                ).fetchall()
                for row in rows:
                    tracking_days.add(row['d'])

            consistency = min((len(tracking_days) / total_days) * 100, 100)

            # Progress score (30%) - weight progress toward goal
            profile = db.execute(
                'SELECT weight, goal_weight FROM profiles WHERE user_id = ?',
                (user_id,)
            ).fetchone()

            progress = 50  # Default
            if profile and profile['goal_weight']:
                weights = db.execute(
                    'SELECT weight FROM weight_logs WHERE user_id = ? ORDER BY logged_at ASC',
                    (user_id,)
                ).fetchall()
                if len(weights) >= 2:
                    start_weight = weights[0]['weight']
                    current_weight = weights[-1]['weight']
                    goal_weight = profile['goal_weight']
                    total_needed = abs(start_weight - goal_weight)
                    if total_needed > 0:
                        achieved = abs(start_weight - current_weight)
                        # Check direction
                        if (goal_weight < start_weight and current_weight < start_weight) or \
                           (goal_weight > start_weight and current_weight > start_weight):
                            progress = min((achieved / total_needed) * 100, 100)
                        else:
                            progress = max(0, 50 - (achieved / total_needed) * 50)

            # Habits score (30%)
            habits = AnalyticsService.analyze_habits(db, user_id)
            habits_score = habits.get('overall', 0)

            # Weighted total
            fitness_score = int(
                (consistency * 0.4) +
                (progress * 0.3) +
                (habits_score * 0.3)
            )

            return max(0, min(100, fitness_score))
        except Exception as e:
            logger.error(f'Error calculating fitness score: {e}')
            return 0

    @staticmethod
    def calculate_bmi_history(db, user_id):
        """Calculate BMI history from weight logs and profile height."""
        profile = db.execute(
            'SELECT height FROM profiles WHERE user_id = ?',
            (user_id,)
        ).fetchone()

        if not profile or not profile['height']:
            return []

        height_m = profile['height'] / 100
        weights = db.execute(
            'SELECT weight, DATE(logged_at) as date FROM weight_logs WHERE user_id = ? ORDER BY logged_at ASC',
            (user_id,)
        ).fetchall()

        bmi_history = []
        for w in weights:
            bmi = round(w['weight'] / (height_m ** 2), 1)
            bmi_history.append({'date': w['date'], 'bmi': bmi})

        return bmi_history

    @staticmethod
    def predict_goal_achievement(db, user_id):
        """
        Predict when the user will reach their goal weight
        using linear regression on weight history.
        """
        try:
            import numpy as np

            profile = db.execute(
                'SELECT goal_weight FROM profiles WHERE user_id = ?',
                (user_id,)
            ).fetchone()

            if not profile or not profile['goal_weight']:
                return {'predicted_date': None, 'on_track': False, 'days_remaining': None}

            weights = db.execute(
                'SELECT weight, julianday(logged_at) as day FROM weight_logs WHERE user_id = ? ORDER BY logged_at ASC',
                (user_id,)
            ).fetchall()

            if len(weights) < 3:
                return {'predicted_date': None, 'on_track': False, 'days_remaining': None}

            goal_weight = profile['goal_weight']
            days = np.array([w['day'] for w in weights])
            weight_vals = np.array([w['weight'] for w in weights])

            # Avoid SVD convergence error if all entries logged on same day
            if days[-1] - days[0] < 0.01:
                return {'predicted_date': None, 'on_track': False, 'days_remaining': None}

            first_weight = weight_vals[0]
            current_weight = weight_vals[-1]

            # 1. Check if goal is already achieved
            is_weight_loss = first_weight > goal_weight
            if is_weight_loss:
                achieved = current_weight <= goal_weight
            else:
                achieved = current_weight >= goal_weight

            if achieved:
                return {'predicted_date': 'Achieved!', 'on_track': True, 'days_remaining': 0}

            # Normalize days to start from 0
            days_normalized = days - days[0]

            # Linear regression
            coeffs = np.polyfit(days_normalized, weight_vals, 1)
            slope = coeffs[0]
            intercept = coeffs[1]

            # 2. Check if moving toward goal
            on_track = (goal_weight < current_weight and slope < 0) or \
                       (goal_weight > current_weight and slope > 0)

            if not on_track or abs(slope) < 0.001:
                return {'predicted_date': 'Not on track', 'on_track': False, 'days_remaining': None}

            # 3. Calculate days to goal
            days_to_goal = (goal_weight - intercept) / slope - days_normalized[-1]

            if days_to_goal <= 0:
                return {'predicted_date': 'Achieved!', 'on_track': True, 'days_remaining': 0}

            predicted_date = (datetime.now() + timedelta(days=int(days_to_goal))).strftime('%B %d, %Y')

            return {
                'predicted_date': predicted_date,
                'on_track': True,
                'days_remaining': int(days_to_goal)
            }
        except Exception as e:
            logger.error(f'Error predicting goal: {e}')
            return {'predicted_date': None, 'on_track': False, 'days_remaining': None}

    @staticmethod
    def analyze_habits(db, user_id):
        """
        Calculate consistency scores for each tracking metric over the last 30 days.
        """
        cutoff = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        total_days = 30

        def count_unique_days(table):
            result = db.execute(
                f'SELECT COUNT(DISTINCT DATE(logged_at)) as cnt FROM {table} WHERE user_id = ? AND DATE(logged_at) >= ?',
                (user_id, cutoff)
            ).fetchone()
            return result['cnt'] if result else 0

        water_days = count_unique_days('water_logs')
        sleep_days = count_unique_days('sleep_logs')
        workout_days = count_unique_days('workout_logs')
        calorie_days = count_unique_days('calorie_logs')

        water_consistency = round(min((water_days / total_days) * 100, 100))
        sleep_consistency = round(min((sleep_days / total_days) * 100, 100))
        workout_consistency = round(min((workout_days / total_days) * 100, 100))
        calorie_consistency = round(min((calorie_days / total_days) * 100, 100))

        overall = round((water_consistency + sleep_consistency + workout_consistency + calorie_consistency) / 4)

        return {
            'water_consistency': water_consistency,
            'sleep_consistency': sleep_consistency,
            'workout_consistency': workout_consistency,
            'calorie_consistency': calorie_consistency,
            'overall': overall,
        }

    @staticmethod
    def get_streak(db, user_id):
        """Count consecutive days with at least one tracking entry, starting from today."""
        today = datetime.now().date()
        streak = 0

        for i in range(365):  # Max check 1 year
            check_date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
            has_entry = False

            for table in ['weight_logs', 'water_logs', 'calorie_logs', 'sleep_logs', 'workout_logs', 'step_logs']:
                result = db.execute(
                    f'SELECT 1 FROM {table} WHERE user_id = ? AND DATE(logged_at) = ? LIMIT 1',
                    (user_id, check_date)
                ).fetchone()
                if result:
                    has_entry = True
                    break

            if has_entry:
                streak += 1
            else:
                # Allow skipping today if no entries yet
                if i == 0:
                    continue
                break

        return streak

    @staticmethod
    def get_achievements(db, user_id):
        """Check various milestones and return achievement badges."""
        achievements = []

        # Count total entries across all tables
        total_entries = 0
        for table in ['weight_logs', 'water_logs', 'calorie_logs', 'sleep_logs', 'workout_logs', 'step_logs']:
            result = db.execute(
                f'SELECT COUNT(*) as cnt FROM {table} WHERE user_id = ?',
                (user_id,)
            ).fetchone()
            total_entries += result['cnt'] if result else 0

        # Weight logs count
        weight_count = db.execute(
            'SELECT COUNT(*) as cnt FROM weight_logs WHERE user_id = ?', (user_id,)
        ).fetchone()['cnt']

        # Workout count
        workout_count = db.execute(
            'SELECT COUNT(*) as cnt FROM workout_logs WHERE user_id = ?', (user_id,)
        ).fetchone()['cnt']

        # Water logging days
        water_days = db.execute(
            'SELECT COUNT(DISTINCT DATE(logged_at)) as cnt FROM water_logs WHERE user_id = ?', (user_id,)
        ).fetchone()['cnt']

        # Sleep logging days
        sleep_days = db.execute(
            'SELECT COUNT(DISTINCT DATE(logged_at)) as cnt FROM sleep_logs WHERE user_id = ?', (user_id,)
        ).fetchone()['cnt']

        # Completed goals
        completed_goals = db.execute(
            "SELECT COUNT(*) as cnt FROM fitness_goals WHERE user_id = ? AND status = 'completed'", (user_id,)
        ).fetchone()['cnt']

        streak = AnalyticsService.get_streak(db, user_id)

        achievements.append({
            'name': 'First Step',
            'icon': '🎯',
            'description': 'Log your first entry',
            'earned': total_entries >= 1
        })
        achievements.append({
            'name': '7-Day Streak',
            'icon': '🔥',
            'description': '7 consecutive days of tracking',
            'earned': streak >= 7
        })
        achievements.append({
            'name': '30-Day Streak',
            'icon': '⚡',
            'description': '30 consecutive days of tracking',
            'earned': streak >= 30
        })
        achievements.append({
            'name': 'Hydration Hero',
            'icon': '💧',
            'description': 'Log water for 7 days',
            'earned': water_days >= 7
        })
        achievements.append({
            'name': 'Early Bird',
            'icon': '🌅',
            'description': 'Log sleep for 7 days',
            'earned': sleep_days >= 7
        })
        achievements.append({
            'name': 'Weight Warrior',
            'icon': '⚖️',
            'description': 'Log weight 10 times',
            'earned': weight_count >= 10
        })
        achievements.append({
            'name': 'Century Club',
            'icon': '💪',
            'description': 'Complete 100 workouts',
            'earned': workout_count >= 100
        })
        achievements.append({
            'name': 'Goal Crusher',
            'icon': '🏆',
            'description': 'Complete a fitness goal',
            'earned': completed_goals >= 1
        })

        return achievements
