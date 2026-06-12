"""
AI Engine — Groq-powered fitness intelligence layer.

Provides workout plans, diet plans, motivational messages, progress
analysis, weekly reports, conversational chat, and multi-week programs
via the Groq LLM API (llama-3.3-70b-versatile).
"""

import os
import time
import logging
from groq import Groq

logger = logging.getLogger(__name__)


class AIEngine:
    """Central gateway for all AI-powered features in FitAI."""

    def __init__(self):
        api_key = os.environ.get('GROQ_API_KEY')
        self.client = Groq(api_key=api_key) if api_key else None
        self.model = 'llama-3.3-70b-versatile'

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _call_api(self, messages, temperature=0.7, max_tokens=2048):
        """Call Groq API with exponential-backoff retry logic."""
        if not self.client:
            return 'AI features require a valid GROQ_API_KEY in .env file.'

        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(
                    messages=messages,
                    model=self.model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response.choices[0].message.content
            except Exception as e:
                if 'rate_limit' in str(e).lower() or '429' in str(e):
                    time.sleep(2 ** attempt)
                    continue
                logger.error(f'Groq API error: {e}')
                return 'AI service temporarily unavailable. Please try again.'

        return 'AI service is busy. Please try again in a moment.'

    @staticmethod
    def _profile_summary(profile: dict) -> str:
        """Build a concise profile block for system prompts."""
        return (
            f"User Profile:\n"
            f"- Age: {profile.get('age', 'N/A')}\n"
            f"- Gender: {profile.get('gender', 'N/A')}\n"
            f"- Height: {profile.get('height', 'N/A')} cm\n"
            f"- Weight: {profile.get('weight', 'N/A')} kg\n"
            f"- Goal Weight: {profile.get('goal_weight', 'N/A')} kg\n"
            f"- Fitness Goal: {profile.get('fitness_goal', 'N/A')}\n"
            f"- Activity Level: {profile.get('activity_level', 'N/A')}\n"
            f"- Workout Preference: {profile.get('workout_preference', 'N/A')}\n"
            f"- Diet Preference: {profile.get('diet_preference', 'N/A')}\n"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_workout_plan(
        self,
        profile: dict,
        workout_type: str = 'general',
        duration: str = '45 min',
        equipment: str = 'full gym',
    ) -> str:
        """Generate a structured workout plan tailored to the user."""
        system_prompt = (
            "You are an expert certified personal trainer with 15+ years of "
            "experience. Create detailed, safe, and effective workout plans "
            "personalised to the client.\n\n"
            f"{self._profile_summary(profile)}"
        )
        user_prompt = (
            f"Create a detailed {workout_type} workout plan.\n"
            f"Duration: {duration}\n"
            f"Available Equipment: {equipment}\n\n"
            "Format the plan in structured markdown with these sections:\n"
            "## Warm-Up (5-10 minutes)\n"
            "- List each warm-up exercise with duration\n\n"
            "## Main Workout\n"
            "For each exercise include:\n"
            "- Exercise name\n"
            "- Sets × Reps (or duration)\n"
            "- Rest period between sets\n"
            "- Brief form cue\n\n"
            "## Cool-Down (5-10 minutes)\n"
            "- List each cool-down stretch with duration\n\n"
            "## Notes\n"
            "- Estimated calories burned\n"
            "- Difficulty level\n"
            "- Tips for progression"
        )
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ]
        return self._call_api(messages, temperature=0.7, max_tokens=2048)

    def generate_diet_plan(
        self,
        profile: dict,
        diet_type: str = 'balanced',
        target_calories: int = 2000,
    ) -> str:
        """Generate a full-day meal plan with macro breakdown."""
        system_prompt = (
            "You are a certified nutritionist and registered dietitian with "
            "expertise in sports nutrition and body composition. Create "
            "detailed, practical meal plans personalised to the client.\n\n"
            f"{self._profile_summary(profile)}"
        )
        user_prompt = (
            f"Create a detailed {diet_type} meal plan targeting "
            f"{target_calories} calories per day.\n\n"
            "Format the plan in structured markdown with these sections:\n\n"
            "## Daily Macro Targets\n"
            "- Protein, Carbs, Fat in grams and percentages\n\n"
            "## Breakfast (~X cal)\n"
            "- Food items with portions\n"
            "- Macros: P/C/F\n\n"
            "## Morning Snack (~X cal)\n"
            "- Food items with portions\n"
            "- Macros: P/C/F\n\n"
            "## Lunch (~X cal)\n"
            "- Food items with portions\n"
            "- Macros: P/C/F\n\n"
            "## Afternoon Snack (~X cal)\n"
            "- Food items with portions\n"
            "- Macros: P/C/F\n\n"
            "## Dinner (~X cal)\n"
            "- Food items with portions\n"
            "- Macros: P/C/F\n\n"
            "## Daily Totals\n"
            "- Total calories and macro summary\n"
            "- Hydration recommendation\n"
            "- Supplement suggestions if appropriate"
        )
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ]
        return self._call_api(messages, temperature=0.7, max_tokens=2048)

    def generate_motivation(self) -> str:
        """Return a short, powerful motivational fitness message."""
        system_prompt = (
            "You are an elite motivational fitness coach known for powerful, "
            "concise messages that ignite action. Your words have helped "
            "thousands transform their lives."
        )
        user_prompt = (
            "Generate a short, powerful motivational message for someone on "
            "their fitness journey. Keep it to 2-3 sentences. Make it "
            "personal, energetic, and actionable. No generic platitudes."
        )
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ]
        return self._call_api(messages, temperature=0.9, max_tokens=256)

    def analyze_progress(self, profile: dict, tracking_data: dict) -> str:
        """Analyze user tracking data and provide actionable insights."""
        system_prompt = (
            "You are a data-driven fitness analyst who provides clear, "
            "actionable insights based on tracking data. Be encouraging but "
            "honest. Back observations with the numbers provided.\n\n"
            f"{self._profile_summary(profile)}"
        )
        data_block = (
            "Tracking Data (last 30 days):\n"
            f"- Weight History: {tracking_data.get('weight_history', 'N/A')}\n"
            f"- Workout Count: {tracking_data.get('workout_count', 0)}\n"
            f"- Average Sleep: {tracking_data.get('avg_sleep', 'N/A')} hours\n"
            f"- Average Water: {tracking_data.get('avg_water', 'N/A')} ml\n"
            f"- Average Calories: {tracking_data.get('avg_calories', 'N/A')} kcal\n"
        )
        user_prompt = (
            f"{data_block}\n"
            "Provide a progress analysis with these sections:\n\n"
            "## Progress Summary\n"
            "Overall assessment of progress toward goals.\n\n"
            "## What's Going Well 💪\n"
            "Highlight positive trends and achievements.\n\n"
            "## Areas to Improve 🎯\n"
            "Identify areas that need attention with specific suggestions.\n\n"
            "## Actionable Recommendations\n"
            "3-5 specific, practical steps for the next week."
        )
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ]
        return self._call_api(messages, temperature=0.6, max_tokens=2048)

    def generate_weekly_report(self, profile: dict, weekly_data: dict) -> str:
        """Generate a comprehensive weekly health & fitness report."""
        system_prompt = (
            "You are a health analyst creating a professional weekly fitness "
            "report. Use data to provide comprehensive, structured analysis. "
            "Be precise with numbers and clear with recommendations.\n\n"
            f"{self._profile_summary(profile)}"
        )
        user_prompt = (
            f"Weekly Data:\n{weekly_data}\n\n"
            "Generate a comprehensive weekly report with:\n\n"
            "## 📊 Weekly Overview\n"
            "Summary of the week's activity and overall performance.\n\n"
            "## 🏆 Achievements\n"
            "Notable milestones, personal records, and consistency wins.\n\n"
            "## 📈 Areas for Improvement\n"
            "Where the user fell short and why it matters.\n\n"
            "## 💡 Recommendations\n"
            "Specific, actionable advice for next week.\n\n"
            "## 🎯 Next Week Goals\n"
            "3-5 measurable goals for the coming week."
        )
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ]
        return self._call_api(messages, temperature=0.6, max_tokens=2048)

    def chat_response(
        self,
        profile: dict,
        chat_history: list,
        user_message: str,
    ) -> str:
        """Conversational fitness assistant with context memory."""
        system_prompt = (
            "You are FitAI, a friendly and knowledgeable AI fitness "
            "assistant. You help users with workout advice, nutrition "
            "guidance, motivation, and general fitness questions. Keep "
            "responses helpful, concise, and encouraging. Use the user's "
            "profile to personalise your answers.\n\n"
            f"{self._profile_summary(profile)}"
        )

        messages = [{'role': 'system', 'content': system_prompt}]

        # Carry over prior conversation turns for context
        for entry in chat_history:
            messages.append({
                'role': entry.get('role', 'user'),
                'content': entry.get('content', ''),
            })

        # Append the new user message
        messages.append({'role': 'user', 'content': user_message})

        return self._call_api(messages, temperature=0.7, max_tokens=1024)

    def get_program(self, profile: dict, program_type: str) -> str:
        """Generate a complete multi-week training program."""
        program_descriptions = {
            'muscle_gain': (
                'a progressive muscle-building hypertrophy program. '
                'Focus on compound movements, progressive overload, '
                'and adequate volume per muscle group.'
            ),
            'weight_loss': (
                'a fat-loss program combining strength training and cardio. '
                'Include calorie-burn estimates and HIIT sessions.'
            ),
            'home_workout': (
                'a bodyweight / minimal-equipment home workout program. '
                'No gym required — use furniture, resistance bands, and '
                'bodyweight exercises.'
            ),
            'gym_workout': (
                'a comprehensive gym-based training program utilising full '
                'gym equipment including barbells, dumbbells, cables, and '
                'machines.'
            ),
        }
        description = program_descriptions.get(
            program_type,
            'a general fitness program tailored to the user.',
        )

        system_prompt = (
            "You are an elite strength & conditioning coach designing "
            "complete multi-week training programs. Programs must be "
            "progressive, periodised, and safe.\n\n"
            f"{self._profile_summary(profile)}"
        )
        user_prompt = (
            f"Design {description}\n\n"
            "Structure the program as:\n\n"
            "## Program Overview\n"
            "- Duration, frequency, difficulty, equipment needed\n\n"
            "## Week 1-2: Foundation Phase\n"
            "Day-by-day breakdown with exercises, sets, reps, rest\n\n"
            "## Week 3-4: Building Phase\n"
            "Increased intensity / volume\n\n"
            "## Week 5-6: Peak Phase\n"
            "Advanced progressions\n\n"
            "## Nutrition Guidelines\n"
            "Calorie and macro recommendations for this program\n\n"
            "## Recovery Protocol\n"
            "Rest days, stretching, sleep recommendations\n\n"
            "## Progress Markers\n"
            "How to know the program is working"
        )
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ]
        return self._call_api(messages, temperature=0.7, max_tokens=4096)
