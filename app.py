import os
from flask import Flask
from config import config

def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Init extensions
    from extensions import db, migrate, login_manager, mail
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)

    # Réparation automatique des tables au démarrage
    with app.app_context():
        from sqlalchemy import text, inspect
        inspector = inspect(db.engine)
        try:
            # Test: tenter un SELECT simple sur temoignages
            if 'temoignages' in inspector.get_table_names():
                db.session.execute(text("SELECT 1 FROM temoignages LIMIT 1"))
        except Exception:
            # La table existe mais a un schéma incompatible -> DROP
            db.session.execute(text("DROP TABLE IF EXISTS temoignages CASCADE"))
            db.session.commit()
        db.create_all()

    # Register blueprints
    from routes import main_bp
    app.register_blueprint(main_bp)

    from admin import admin_bp
    app.register_blueprint(admin_bp)

    # SEO routes
    @app.route('/robots.txt')
    def robots():
        return app.send_static_file('robots.txt')

    @app.route('/sitemap.xml')
    def sitemap():
        return app.send_static_file('sitemap.xml')

    return app