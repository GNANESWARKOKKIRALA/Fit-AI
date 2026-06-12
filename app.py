"""
FitAI - AI-Powered Fitness Coach & Health Analytics Platform
Flask Application Factory and Entry Point
"""
import os
import logging
from flask import Flask, redirect, url_for, session, render_template_string
from config import Config
from database.db import init_db, init_app as init_db_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = app.config['SECRET_KEY']
    app.permanent_session_lifetime = app.config['SESSION_LIFETIME']

    # Initialize database
    init_db_app(app)

    # Register blueprints
    from auth.routes import bp as auth_bp
    from routes.dashboard import bp as dashboard_bp
    from routes.profile import bp as profile_bp
    from routes.tracking import bp as tracking_bp
    from routes.ai_coach import bp as ai_bp
    from routes.analytics import bp as analytics_bp
    from routes.export import bp as export_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(tracking_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(export_bp)

    # Root redirect
    @app.route('/')
    def index():
        if 'user_id' in session:
            return redirect(url_for('dashboard.dashboard'))
        return redirect(url_for('auth.login'))

    # Error handlers
    ERROR_TEMPLATE = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ title }} | FitAI</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Inter', sans-serif; background: #0a0a1a; color: #f1f5f9;
                   display: flex; align-items: center; justify-content: center; min-height: 100vh; }
            .error-card { text-align: center; padding: 48px; background: rgba(255,255,255,0.05);
                          backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.1);
                          border-radius: 16px; max-width: 480px; }
            .error-code { font-size: 80px; font-weight: 700;
                          background: linear-gradient(135deg, #7C3AED, #06B6D4);
                          -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            .error-title { font-size: 24px; margin: 16px 0 8px; }
            .error-msg { color: #94a3b8; margin-bottom: 24px; }
            .error-btn { display: inline-block; padding: 12px 24px; background: linear-gradient(135deg, #7C3AED, #06B6D4);
                         color: white; text-decoration: none; border-radius: 12px; font-weight: 600; }
            .error-btn:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(124,58,237,0.4); }
        </style>
    </head>
    <body>
        <div class="error-card">
            <div class="error-code">{{ code }}</div>
            <h1 class="error-title">{{ title }}</h1>
            <p class="error-msg">{{ message }}</p>
            <a href="/" class="error-btn">Go Home</a>
        </div>
    </body>
    </html>
    '''

    @app.errorhandler(404)
    def not_found(e):
        return render_template_string(ERROR_TEMPLATE,
                                      code=404, title='Page Not Found',
                                      message="The page you're looking for doesn't exist."), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template_string(ERROR_TEMPLATE,
                                      code=500, title='Server Error',
                                      message='Something went wrong. Please try again later.'), 500

    # Initialize DB tables on startup
    with app.app_context():
        init_db()
        logger.info('FitAI application initialized successfully.')
        logger.info(f"GROQ_API_KEY loaded on startup: {Config.GROQ_API_KEY[:8] if Config.GROQ_API_KEY else 'None'}")

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
