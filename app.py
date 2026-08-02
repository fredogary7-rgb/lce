import os
from flask import Flask
from config import config
from sqlalchemy import String, Text, Integer, Boolean, DateTime, Float, ForeignKey


def _column_type_to_sql(col):
    """Convertit un type de colonne SQLAlchemy en type SQL PostgreSQL."""
    type_map = {
        String: 'VARCHAR',
        Text: 'TEXT',
        Integer: 'INTEGER',
        Boolean: 'BOOLEAN',
        DateTime: 'TIMESTAMP',
        Float: 'FLOAT',
    }
    col_type = type(col.type)
    sql_type = type_map.get(col_type, 'TEXT')

    if isinstance(col.type, String) and col.type.length:
        sql_type = f'VARCHAR({col.type.length})'

    nullable = '' if col.nullable else ' NOT NULL'
    default = ''
    if col.default and col.default.arg is not None:
        if isinstance(col.default.arg, bool):
            default = f" DEFAULT {'TRUE' if col.default.arg else 'FALSE'}"
        elif isinstance(col.default.arg, (int, float)):
            default = f" DEFAULT {col.default.arg}"
        elif isinstance(col.default.arg, str):
            default = f" DEFAULT '{col.default.arg}'"

    return f'{sql_type}{default}{nullable}'


def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Init extensions
    from extensions import db, migrate, login_manager
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Réparation automatique des tables au démarrage
    from models import Temoignage, Inscription  # noqa: imports nécessaires pour metadata
    with app.app_context():
        from sqlalchemy import text, inspect
        inspector = inspect(db.engine)
        tables_inspectees = inspector.get_table_names()

        # --- Réparer temoignages (DROP car peu de données) ---
        if 'temoignages' in tables_inspectees:
            colonnes_reelles = sorted(c['name'] for c in inspector.get_columns('temoignages'))
            colonnes_attendues = sorted(c.name for c in Temoignage.__table__.columns)
            if colonnes_reelles != colonnes_attendues:
                print(f"[AUTO-FIX] Schéma temoignages obsolète. Re-création...")
                print(f"  Base: {colonnes_reelles}")
                print(f"  Modèle: {colonnes_attendues}")
                db.session.execute(text("DROP TABLE IF EXISTS temoignages CASCADE"))
                db.session.commit()

        # --- Réparer inscriptions (ALTER pour préserver les données) ---
        if 'inscriptions' in tables_inspectees:
            colonnes_reelles = {c['name'] for c in inspector.get_columns('inscriptions')}
            colonnes_attendues = {c.name for c in Inscription.__table__.columns}
            manquantes = colonnes_attendues - colonnes_reelles
            if manquantes:
                print(f"[AUTO-FIX] Ajout colonnes manquantes à inscriptions: {manquantes}")
                for col_name in manquantes:
                    col = Inscription.__table__.columns[col_name]
                    col_type_sql = _column_type_to_sql(col)
                    db.session.execute(text(f"""
                        DO $$
                        BEGIN
                            ALTER TABLE inscriptions ADD COLUMN {col_name} {col_type_sql};
                        EXCEPTION WHEN duplicate_column THEN
                            -- ignore
                        END $$;
                    """))
                db.session.commit()

        db.create_all()

        # Créer l'admin par défaut si absent
        from models import AdminUser
        existing = AdminUser.query.filter_by(email='admin@lcetg.com').first()
        if not existing:
            admin = AdminUser(nom='Super Admin', email='admin@lcetg.com', role='super_admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("[AUTO-FIX] Admin par défaut créé: admin@lcetg.com / admin123")

    # Register blueprints
    from routes import main_bp
    app.register_blueprint(main_bp)

    from admin import admin_bp
    app.register_blueprint(admin_bp)

    # CSRF protection context processor
    from flask import session
    import secrets

    @app.context_processor
    def inject_csrf():
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(32)
        return {'csrf_token': session['csrf_token']}

    # SEO routes
    @app.route('/robots.txt')
    def robots():
        return app.send_static_file('robots.txt')

    @app.route('/sitemap.xml')
    def sitemap():
        return app.send_static_file('sitemap.xml')

    @app.route('/offline')
    def offline():
        from flask import render_template
        return render_template('offline.html')

    @app.route('/sw.js')
    def service_worker():
        from flask import make_response, Response
        sw = app.send_static_file('service-worker.js')
        return sw

    @app.route('/sw-admin.js')
    def service_worker_admin():
        """Service Worker dédié admin pour éviter conflit de scope."""
        from flask import make_response
        content = """self.addEventListener('push', function(e) {
    var data = e.data ? e.data.json() : {};
    var title = data.title || 'LCE Admin';
    var options = {
        body: data.body || '',
        icon: data.icon || '/static/images/lc.JPG',
        badge: data.badge || '/static/images/lc.JPG',
        vibrate: data.vibrate || [200, 100, 200],
        tag: data.tag || 'lce-admin',
        requireInteraction: data.requireInteraction !== false,
        data: { url: data.url || '/admin/inscriptions' },
        actions: data.actions || [
            { action: 'view', title: "Voir" },
            { action: 'close', title: 'Fermer' }
        ]
    };
    e.waitUntil(self.registration.showNotification(title, options));
});
self.addEventListener('notificationclick', function(e) {
    e.notification.close();
    var url = (e.notification.data && e.notification.data.url) || '/admin/inscriptions';
    if (e.action === 'close') return;
    e.waitUntil(clients.openWindow(url));
});
"""
        from flask import Response
        return Response(content, mimetype='application/javascript')

    return app
