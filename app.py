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
    from models import Temoignage  # noqa: import nécessaire pour metadata
    with app.app_context():
        from sqlalchemy import text, inspect
        inspector = inspect(db.engine)
        tables_inspectees = inspector.get_table_names()
        if 'temoignages' in tables_inspectees:
            # Comparer les colonnes réelles en base vs modèle Python
            colonnes_reelles = sorted(c['name'] for c in inspector.get_columns('temoignages'))
            colonnes_attendues = sorted(c.name for c in Temoignage.__table__.columns)
            if colonnes_reelles != colonnes_attendues:
                print(f"[AUTO-FIX] Schéma temoignages obsolète. Re-création...")
                print(f"  Base: {colonnes_reelles}")
                print(f"  Modèle: {colonnes_attendues}")
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