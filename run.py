from app import create_app
from extensions import db
from models import Formation, Message, Temoignage, Inscription, Galerie, ParametreSite

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
