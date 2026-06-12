"""
Route decorators for FitAI.

Provides:
    @login_required  – redirects unauthenticated users to the login page.
    @handle_errors   – catches unhandled exceptions and redirects gracefully.
"""

import functools
import traceback

from flask import flash, redirect, session, url_for, current_app


def login_required(view):
    """Decorator that ensures the user is logged in before accessing the view."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return view(**kwargs)

    return wrapped_view


def handle_errors(view):
    """Decorator that catches unhandled exceptions, logs them, and redirects to the dashboard."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        try:
            return view(**kwargs)
        except Exception:
            current_app.logger.error(traceback.format_exc())
            flash('An error occurred. Please try again.', 'danger')
            return redirect(url_for('dashboard.index'))

    return wrapped_view
