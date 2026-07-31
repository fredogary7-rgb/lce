"""Script de seed pour peupler la base de données avec les formations initiales."""
from app import create_app
from extensions import db
from models import Formation, AdminUser
from datetime import datetime

app = create_app()

formations_data = [
    {
        'nom': 'Chariot élévateur',
        'slug': 'chariot-elevateur',
        'description': 'Formation complète à la conduite de chariots élévateurs, conforme aux normes de sécurité. Maîtrisez la manutention de charges en entrepôt et sur chantier.',
        'image': 'char.JPG',
        'duree': '4 semaines',
        'categorie': 'Manutention',
        'actif': True,
        'ordre_affichage': 1,
    },
    {
        'nom': 'Reachstacker',
        'slug': 'reachstacker',
        'description': 'Spécialisation sur le reachstacker, engin de manutention portuaire et logistique lourde. Formation avancée pour la gestion des conteneurs.',
        'image': 'reash.JPG',
        'duree': '6 semaines',
        'categorie': 'Logistique',
        'actif': True,
        'ordre_affichage': 2,
    },
    {
        'nom': 'Grue PPM',
        'slug': 'grue-ppm',
        'description': 'Maîtrise de la grue PPM pour le levage de charges lourdes en toute sécurité. Formation aux techniques de levage et à la sécurité sur chantier.',
        'image': 'gru.JPG',
        'duree': '8 semaines',
        'categorie': 'BTP',
        'actif': True,
        'ordre_affichage': 3,
    },
    {
        'nom': 'Chargeuse',
        'slug': 'chargeuse',
        'description': 'Formation à la conduite de chargeuses pour les travaux de terrassement et carrières. Apprenez à manipuler les matériaux en vrac avec précision.',
        'image': 'cha.JPG',
        'duree': '5 semaines',
        'categorie': 'BTP',
        'actif': True,
        'ordre_affichage': 4,
    },
    {
        'nom': 'Pelle hydraulique',
        'slug': 'pelle-hydraulique',
        'description': 'Apprenez à manipuler la pelle hydraulique pour les chantiers de construction. Formation aux techniques d\'excavation, de tranchée et de terrassement.',
        'image': 'pelle.JPG',
        'duree': '6 semaines',
        'categorie': 'BTP',
        'actif': True,
        'ordre_affichage': 5,
    },
    {
        'nom': 'Manitou télescopique',
        'slug': 'manitou-telescopique',
        'description': 'Formation complète sur le manitou télescopique, idéal pour la manutention polyvalente sur chantier et en exploitation agricole.',
        'image': 'mani.JPG',
        'duree': '4 semaines',
        'categorie': 'Manutention',
        'actif': True,
        'ordre_affichage': 6,
    },
    {
        'nom': 'Niveleuse',
        'slug': 'niveleuse',
        'description': 'Spécialisation sur la niveleuse pour les travaux de nivellement et de voirie. Maîtrisez les techniques de réglage et de finition.',
        'image': 'niveu.JPG',
        'duree': '6 semaines',
        'categorie': 'BTP',
        'actif': True,
        'ordre_affichage': 7,
    },
    {
        'nom': 'Bulldozer',
        'slug': 'bulldozer',
        'description': 'Formation à la conduite de bulldozer pour les grands travaux de terrassement. Apprenez à déplacer d\'importants volumes de terre.',
        'image': 'buldo.JPG',
        'duree': '6 semaines',
        'categorie': 'BTP',
        'actif': True,
        'ordre_affichage': 8,
    },
    {
        'nom': 'Camion Benne',
        'slug': 'camion-benne',
        'description': 'Conduite de camion benne pour le transport de matériaux en vrac. Formation à la sécurité routière et à la gestion des chargements.',
        'image': 'benne.JPG',
        'duree': '4 semaines',
        'categorie': 'Transport',
        'actif': True,
        'ordre_affichage': 9,
    },
    {
        'nom': 'Bus',
        'slug': 'bus',
        'description': 'Formation à la conduite de bus pour le transport de passagers en toute sécurité. Maîtrisez la réglementation et les bonnes pratiques.',
        'image': 'bus.JPG',
        'duree': '4 semaines',
        'categorie': 'Transport',
        'actif': True,
        'ordre_affichage': 10,
    },
    {
        'nom': 'Camion Semi-remorque',
        'slug': 'camion-semi-remorque',
        'description': 'Formation avancée à la conduite de camions semi-remorques pour le transport longue distance. Maîtrisez la conduite en toute sécurité.',
        'image': 'semi.JPG',
        'duree': '6 semaines',
        'categorie': 'Transport',
        'actif': True,
        'ordre_affichage': 11,
    },
]


def seed():
    with app.app_context():
        # Drop and recreate the formations table to match new model
        from sqlalchemy import text
        print("Drop table formations si elle existe...")
        db.session.execute(text("DROP TABLE IF EXISTS formations CASCADE"))
        db.session.commit()

        print("Création des tables...")
        db.create_all()

        print("Insertion des formations...")
        for data in formations_data:
            formation = Formation(**data)
            db.session.add(formation)

        db.session.commit()
        print(f"✅ {len(formations_data)} formations insérées avec succès !")

        # Créer l'admin par défaut
        existing = AdminUser.query.filter_by(email='admin@lcetg.com').first()
        if not existing:
            admin = AdminUser(nom='Super Admin', email='admin@lcetg.com', role='super_admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin par défaut créé: admin@lcetg.com / admin123")
        else:
            print("ℹ️ Admin par défaut existe déjà.")


if __name__ == '__main__':
    seed()
