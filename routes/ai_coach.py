"""
AI Coach route blueprint for FitAI application.

Provides endpoints for AI-powered workout plans, diet plans,
motivational messages, training programs, and an interactive chat.
"""

import json
import logging
from datetime import datetime

from flask import Blueprint, jsonify, render_template, request, session

from database.db import get_db
from services.profile_service import ProfileService
from services.ai_engine import AIEngine
from utils.decorators import login_required

logger = logging.getLogger(__name__)

bp = Blueprint('ai_coach', __name__, url_prefix='/ai')


# ---------------------------------------------------------------------------
# Coach landing page
# ---------------------------------------------------------------------------

@bp.route('/coach')
@login_required
def coach():
    """Render the AI coach interface with user profile context."""
    db = get_db()
    user_id = session['user_id']
    profile = ProfileService.get_profile(db, user_id)
    return render_template('ai/coach.html', profile=profile)


# ---------------------------------------------------------------------------
# AI generation endpoints (POST, return JSON)
# ---------------------------------------------------------------------------

@bp.route('/workout', methods=['POST'])
@login_required
def generate_workout():
    """Generate a personalised workout plan via AI."""
    db = get_db()
    user_id = session['user_id']

    workout_type = request.form.get('workout_type', '').strip()
    duration = request.form.get('duration', type=int, default=30)
    equipment = request.form.get('equipment', '').strip()

    try:
        profile = ProfileService.get_profile(db, user_id) or {}
        ai = AIEngine()
        content = ai.generate_workout_plan(profile, workout_type, f"{duration} min", equipment)
        return jsonify({'success': True, 'content': content})
    except Exception:
        logger.exception("Error generating workout plan for user %s", user_id)
        return jsonify({'success': False, 'message': 'Failed to generate workout plan.'}), 500


@bp.route('/diet', methods=['POST'])
@login_required
def generate_diet():
    """Generate a personalised diet plan via AI."""
    db = get_db()
    user_id = session['user_id']

    diet_type = request.form.get('diet_type', '').strip()
    target_calories = request.form.get('target_calories', type=int, default=2000)

    try:
        profile = ProfileService.get_profile(db, user_id) or {}
        ai = AIEngine()
        content = ai.generate_diet_plan(profile, diet_type, target_calories)
        return jsonify({'success': True, 'content': content})
    except Exception:
        logger.exception("Error generating diet plan for user %s", user_id)
        return jsonify({'success': False, 'message': 'Failed to generate diet plan.'}), 500


@bp.route('/motivation', methods=['POST'])
@login_required
def generate_motivation():
    """Generate an AI motivational message."""
    db = get_db()
    user_id = session['user_id']

    try:
        ai = AIEngine()
        content = ai.generate_motivation()
        return jsonify({'success': True, 'content': content})
    except Exception:
        logger.exception("Error generating motivation for user %s", user_id)
        return jsonify({'success': False, 'message': 'Failed to generate motivation.'}), 500


@bp.route('/program', methods=['POST'])
@login_required
def get_program():
    """Retrieve a structured training program from AI."""
    db = get_db()
    user_id = session['user_id']

    program_type = request.form.get('program_type', '').strip()
    if not program_type:
        return jsonify({'success': False, 'message': 'Program type is required.'}), 400

    try:
        profile = ProfileService.get_profile(db, user_id) or {}
        ai = AIEngine()
        content = ai.get_program(profile, program_type)
        return jsonify({'success': True, 'content': content})
    except Exception:
        logger.exception("Error generating program for user %s", user_id)
        return jsonify({'success': False, 'message': 'Failed to generate program.'}), 500


# ---------------------------------------------------------------------------
# Interactive chat
# ---------------------------------------------------------------------------

@bp.route('/chat', methods=['GET'])
@login_required
def chat():
    """Render the chat interface with previous conversation history."""
    db = get_db()
    user_id = session['user_id']

    rows = db.execute(
        "SELECT role, message AS content, created_at FROM chat_history "
        "WHERE user_id = ? ORDER BY created_at ASC",
        (user_id,),
    ).fetchall()

    chat_history = [dict(row) for row in rows]

    return render_template('ai/chat.html', chat_history=chat_history)


@bp.route('/chat', methods=['POST'])
@login_required
def chat_send():
    """Process a chat message and return the AI response."""
    db = get_db()
    user_id = session['user_id']

    data = request.get_json(silent=True)
    if not data or not data.get('message', '').strip():
        return jsonify({'success': False, 'message': 'Message cannot be empty.'}), 400

    user_message = data['message'].strip()

    # Load recent conversation history for context
    rows = db.execute(
        "SELECT role, message AS content FROM chat_history "
        "WHERE user_id = ? ORDER BY created_at DESC LIMIT 20",
        (user_id,),
    ).fetchall()

    # Reverse so oldest messages come first (chronological order)
    history = [dict(row) for row in reversed(rows)]

    try:
        profile = ProfileService.get_profile(db, user_id) or {}
        ai = AIEngine()
        ai_response = ai.chat_response(profile, history, user_message)
    except Exception:
        logger.exception("Error generating chat response for user %s", user_id)
        return jsonify({'success': False, 'message': 'Failed to get AI response.'}), 500

    # Persist both messages
    now = datetime.utcnow()
    db.execute(
        "INSERT INTO chat_history (user_id, role, message, created_at) VALUES (?, ?, ?, ?)",
        (user_id, 'user', user_message, now),
    )
    db.execute(
        "INSERT INTO chat_history (user_id, role, message, created_at) VALUES (?, ?, ?, ?)",
        (user_id, 'assistant', ai_response, now),
    )
    db.commit()

    return jsonify({'success': True, 'response': ai_response})


@bp.route('/chat/clear', methods=['POST'])
@login_required
def chat_clear():
    """Clear chat history for the user."""
    db = get_db()
    user_id = session['user_id']
    db.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
    db.commit()
    return jsonify({'success': True, 'message': 'Chat history cleared.'})
