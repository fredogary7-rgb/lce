import os
from flask import Flask
from config import config

def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Init extensions
    from extensions import db, migrate
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from routes import main_bp
    app.register_blueprint(main_bp)

    # SEO routes
    @app.route('/robots.txt')
    def robots():
        return app.send_static_file('robots.txt')

    @app.route('/sitemap.xml')
    def sitemap():
        return app.send_static_file('sitemap.xml')

    return app