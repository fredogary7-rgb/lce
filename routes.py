from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import Formation, Message, Temoignage, Inscription, Galerie, ParametreSite, ContactMessage, Video, Equipe, Statistique
from extensions import db
from datetime import datetime

main_bp = Blueprint('main', __name__)


# --- FORMATIONS (données initiales) ---
FORMATIONS_DATA = [
    {'nom': 'Chariot élévateur', 'slug': 'chariot-elevateur', 'image': 'char.JPG',
     'description': 'Formation complète à la conduite de chariots élévateurs, conforme aux normes de sécurité.'},
    {'nom': 'Reachstacker', 'slug': 'reachstacker', 'image': 'reash.JPG',
     'description': 'Spécialisation sur le reachstacker, engin de manutention portuaire et logistique lourde.'},
    {'nom': 'Grue PPM', 'slug': 'grue-ppm', 'image': 'gru.JPG',
     'description': 'Maîtrise de la grue PPM pour le levage de charges lourdes en toute sécurité.'},
    {'nom': 'Chargeuse', 'slug': 'chargeuse', 'image': 'cha.JPG',
     'description': 'Formation à la conduite de chargeuses pour les travaux de terrassement et carrières.'},
    {'nom': 'Pelle hydraulique', 'slug': 'pelle-hydraulique', 'image': 'pelle.JPG',
     'description': 'Apprenez à manipuler la pelle hydraulique pour les chantiers de construction.'},
    {'nom': 'Manitou télescopique', 'slug': 'manitou-telescopique', 'image': 'mani.JPG',
     'description': 'Formation complète sur le manitou télescopique, idéal pour la manutention polyvalente.'},
    {'nom': 'Niveleuse', 'slug': 'niveleuse', 'image': 'niveu.JPG',
     'description': 'Spécialisation sur la niveleuse pour les travaux de nivellement et de voirie.'},
    {'nom': 'Bulldozer', 'slug': 'bulldozer', 'image': 'buldo.JPG',
     'description': 'Formation à la conduite de bulldozer pour les grands travaux de terrassement.'},
    {'nom': 'Camion Benne', 'slug': 'camion-benne', 'image': 'benne.JPG',
     'description': 'Conduite de camion benne pour le transport de matériaux en vrac.'},
    {'nom': 'Bus', 'slug': 'bus', 'image': 'bus.JPG',
     'description': 'Formation à la conduite de bus pour le transport de passagers en toute sécurité.'},
    {'nom': 'Camion Semi-remorque', 'slug': 'camion-semi-remorque', 'image': 'semi.JPG',
     'description': 'Formation avancée à la conduite de camions semi-remorques pour le transport longue distance.'},
]


@main_bp.route('/')
def index():
    formations = FORMATIONS_DATA
    temoignages = Temoignage.query.filter_by(actif=True).order_by(Temoignage.created_at.desc()).all()
    return render_template('index.html', formations=formations, temoignages=temoignages)


@main_bp.route('/formations')
def formations_page():
    formations = Formation.query.filter_by(actif=True).order_by(Formation.ordre_affichage.asc()).all()
    return render_template('formations.html', formations=formations)


@main_bp.route('/galerie')
def galerie_page():
    images = Galerie.query.filter_by(actif=True).order_by(Galerie.ordre.asc()).all()
    videos = Video.query.filter_by(actif=True).order_by(Video.ordre.asc()).all()
    categories = ['Toutes', 'Apprenants', 'Engins', 'Formations', 'Événements']
    return render_template('galerie.html', images=images, videos=videos, categories=categories)


@main_bp.route('/contact', methods=['POST'])
def contact():
    nom = request.form.get('nom', '').strip()
    telephone = request.form.get('telephone', '').strip()
    email = request.form.get('email', '').strip()
    message_text = request.form.get('message', '').strip()

    if not nom or not telephone or not email or not message_text:
        flash('Veuillez remplir tous les champs obligatoires.', 'danger')
        return redirect(url_for('main.index', _anchor='contact'))

    try:
        msg = Message(nom=nom, telephone=telephone, email=email, message=message_text)
        db.session.add(msg)
        db.session.commit()
        flash('Votre message a été envoyé avec succès !', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Une erreur est survenue. Veuillez réessayer.', 'danger')

    return redirect(url_for('main.index', _anchor='contact'))


@main_bp.route('/contact-page')
def contact_page():
    contacts = {
        'telephone1': ParametreSite.query.filter_by(cle='contact_telephone1').first(),
        'telephone2': ParametreSite.query.filter_by(cle='contact_telephone2').first(),
        'email': ParametreSite.query.filter_by(cle='contact_email').first(),
        'adresse': ParametreSite.query.filter_by(cle='contact_adresse').first(),
        'maps_url': ParametreSite.query.filter_by(cle='contact_maps_url').first(),
        'tiktok': ParametreSite.query.filter_by(cle='social_tiktok').first(),
        'facebook': ParametreSite.query.filter_by(cle='social_facebook').first(),
        'instagram': ParametreSite.query.filter_by(cle='social_instagram').first(),
        'linkedin': ParametreSite.query.filter_by(cle='social_linkedin').first(),
    }
    return render_template('contact.html', contacts=contacts)


@main_bp.route('/api/contact-message', methods=['POST'])
def contact_message():
    nom = request.form.get('nom', '').strip()
    telephone = request.form.get('telephone', '').strip()
    email = request.form.get('email', '').strip()
    sujet = request.form.get('sujet', '').strip()
    message_text = request.form.get('message', '').strip()

    if not nom or not telephone or not email or not message_text:
        flash('Veuillez remplir tous les champs obligatoires.', 'danger')
        return redirect(url_for('main.contact_page', _anchor='contact-form'))

    try:
        msg = ContactMessage(
            nom=nom, telephone=telephone, email=email,
            sujet=sujet, message=message_text
        )
        db.session.add(msg)
        db.session.commit()
        flash('Votre message a été envoyé avec succès ! Nous vous répondrons dans les plus brefs délais.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Une erreur est survenue. Veuillez réessayer.', 'danger')

    return redirect(url_for('main.contact_page', _anchor='contact-form'))


@main_bp.route('/a-propos')
def a_propos_page():
    equipiers = Equipe.query.filter_by(actif=True).order_by(Equipe.ordre.asc()).all()
    temoignages = Temoignage.query.filter_by(actif=True).order_by(Temoignage.created_at.desc()).all()
    stats = Statistique.query.order_by(Statistique.ordre.asc()).all()
    formations = Formation.query.filter_by(actif=True).order_by(Formation.ordre_affichage.asc()).all()
    return render_template('a-propos.html', equipiers=equipiers, temoignages=temoignages, stats=stats, formations=formations)


@main_bp.route('/inscription', methods=['POST'])
def inscription():
    nom = request.form.get('nom', '').strip()
    prenom = request.form.get('prenom', '').strip()
    telephone = request.form.get('telephone', '').strip()
    email = request.form.get('email', '').strip()
    formation_nom = request.form.get('formation', '').strip()

    if not nom or not telephone:
        flash('Le nom et le téléphone sont obligatoires.', 'danger')
        return redirect(url_for('main.index', _anchor='inscription'))

    try:
        insc = Inscription(
            nom=nom, prenom=prenom, telephone=telephone,
            email=email, formation=formation_nom
        )
        db.session.add(insc)
        db.session.commit()
        flash('Votre inscription a été enregistrée avec succès !', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Une erreur est survenue. Veuillez réessayer.', 'danger')

    return redirect(url_for('main.index', _anchor='inscription'))