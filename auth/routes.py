"""
FitAI - Authentication Routes
Handles user registration, login, logout, and password changes.
"""
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_bcrypt import Bcrypt
from database.db import get_db
from utils.validators import validate_registration, validate_login

logger = logging.getLogger(__name__)
bcrypt = Bcrypt()

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validate inputs
        is_valid, error_msg = validate_registration(username, email, password, confirm_password)
        if not is_valid:
            flash(error_msg, 'error')
            return render_template('auth/register.html')

        db = get_db()

        # Check if username or email already exists
        existing = db.execute(
            'SELECT id FROM users WHERE username = ? OR email = ?',
            (username, email)
        ).fetchone()

        if existing:
            flash('Username or email already exists.', 'error')
            return render_template('auth/register.html')

        # Hash password and create user
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        try:
            db.execute(
                'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                (username, email, password_hash)
            )
            db.commit()

            # Auto-login after registration
            user = db.execute(
                'SELECT id, username FROM users WHERE username = ?',
                (username,)
            ).fetchone()

            session.permanent = True
            session['user_id'] = user['id']
            session['username'] = user['username']

            logger.info(f'New user registered: {username}')
            flash('Welcome to FitAI! Please complete your profile.', 'success')
            return redirect(url_for('profile.profile'))
        except Exception as e:
            logger.error(f'Registration error: {e}')
            flash('An error occurred during registration. Please try again.', 'error')

    return render_template('auth/register.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        is_valid, error_msg = validate_login(username, password)
        if not is_valid:
            flash(error_msg, 'error')
            return render_template('auth/login.html')

        db = get_db()
        user = db.execute(
            'SELECT id, username, password_hash FROM users WHERE username = ? OR email = ?',
            (username, username.lower())
        ).fetchone()

        if user and bcrypt.check_password_hash(user['password_hash'], password):
            session.permanent = True
            session['user_id'] = user['id']
            session['username'] = user['username']

            # Update last login
            db.execute(
                'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
                (user['id'],)
            )
            db.commit()

            logger.info(f'User logged in: {username}')
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('auth/login.html')


@bp.route('/logout')
def logout():
    """Handle user logout."""
    username = session.get('username', 'Unknown')
    session.clear()
    logger.info(f'User logged out: {username}')
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


@bp.route('/change-password', methods=['POST'])
def change_password():
    """Handle password change."""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    old_password = request.form.get('old_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not old_password or not new_password:
        flash('All password fields are required.', 'error')
        return redirect(url_for('profile.profile'))

    if new_password != confirm_password:
        flash('New passwords do not match.', 'error')
        return redirect(url_for('profile.profile'))

    if len(new_password) < 6:
        flash('New password must be at least 6 characters.', 'error')
        return redirect(url_for('profile.profile'))

    db = get_db()
    user = db.execute(
        'SELECT password_hash FROM users WHERE id = ?',
        (session['user_id'],)
    ).fetchone()

    if not bcrypt.check_password_hash(user['password_hash'], old_password):
        flash('Current password is incorrect.', 'error')
        return redirect(url_for('profile.profile'))

    new_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
    db.execute(
        'UPDATE users SET password_hash = ? WHERE id = ?',
        (new_hash, session['user_id'])
    )
    db.commit()

    logger.info(f'Password changed for user ID: {session["user_id"]}')
    flash('Password changed successfully!', 'success')
    return redirect(url_for('profile.profile'))
