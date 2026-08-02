from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file, jsonify
from models import Formation, Message, Temoignage, Inscription, Galerie, ParametreSite, ContactMessage, Video, Equipe, Statistique, PushSubscription, CommentairePublic, DemandeVoyage
from extensions import db
from datetime import datetime
import os
import uuid
import base64
import io
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph, Frame, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white, grey
from PIL import Image, ImageDraw, ImageFont
import requests
import json

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
    total_inscriptions = Inscription.query.count()
    commentaires = CommentairePublic.query.filter_by(actif=True).order_by(CommentairePublic.created_at.desc()).limit(20).all()
    return render_template('index.html', formations=formations, temoignages=temoignages, total_inscriptions=total_inscriptions, commentaires=commentaires)


@main_bp.route('/api/commentaire', methods=['POST'])
def ajouter_commentaire():
    """Ajoute un commentaire public depuis la page index."""
    nom = request.form.get('nom', '').strip()
    email = request.form.get('email', '').strip()
    commentaire = request.form.get('commentaire', '').strip()

    if not nom or not commentaire:
        flash('Veuillez remplir votre nom et votre commentaire.', 'danger')
        return redirect(url_for('main.index', _anchor='commentaires'))

    if len(commentaire) < 5:
        flash('Votre commentaire est trop court.', 'danger')
        return redirect(url_for('main.index', _anchor='commentaires'))

    try:
        c = CommentairePublic(nom=nom, email=email, commentaire=commentaire)
        db.session.add(c)
        db.session.commit()
        flash('Merci pour votre commentaire ! Il sera visible après validation.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Une erreur est survenue. Veuillez réessayer.', 'danger')

    return redirect(url_for('main.index', _anchor='commentaires'))


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
    website = request.form.get('website', '').strip()  # honeypot

    # --- ANTI-SPAM ---
    # Honeypot : si le champ invisible "website" est rempli → bot
    if website:
        current_app.logger.warning(f"SPAM honeypot triggered from {request.remote_addr}")
        # Renvoyer un faux success pour ne pas informer le bot
        flash('Votre message a été envoyé avec succès !', 'success')
        return redirect(url_for('main.contact_page', _anchor='contact-form'))

    # Téléphone trop court (>20 chiffres = faux)
    digits_only = ''.join(c for c in telephone if c.isdigit())
    if len(digits_only) < 6 or len(digits_only) > 20:
        flash('Veuillez entrer un numéro de téléphone valide.', 'danger')
        return redirect(url_for('main.contact_page', _anchor='contact-form'))

    # Message trop court (< 10 chars) ou contient des URLs suspectes
    if len(message_text) < 10:
        flash('Votre message est trop court. Veuillez donner plus de détails.', 'danger')
        return redirect(url_for('main.contact_page', _anchor='contact-form'))

    spam_patterns = ['graph.org', 'http://', 'https://', 'www.', '.com/', '.org/', '.net/',
                     'BALANCE', 'DOLLARS', 'TRANSACTION', '$$$', '<<<', '>>>']
    message_upper = message_text.upper()
    for pattern in spam_patterns:
        if pattern in message_text.lower() or pattern.upper() in message_upper:
            current_app.logger.warning(f"SPAM link detected from {request.remote_addr}: {pattern}")
            flash('Votre message a été envoyé avec succès !', 'success')
            return redirect(url_for('main.contact_page', _anchor='contact-form'))

    # Nom trop court ou contient des patterns bizarres
    if len(nom) < 3:
        flash('Veuillez entrer votre nom complet.', 'danger')
        return redirect(url_for('main.contact_page', _anchor='contact-form'))

    # Email suspect (trop de chiffres random, domaines bizarres)
    if email:
        email_lower = email.lower()
        suspicious_domains = ['web-library.net', 'temp-mail', 'guerrillamail', '10minutemail',
                              'yopmail', 'mailinator', 'trashmail']
        for sd in suspicious_domains:
            if sd in email_lower:
                flash('Votre message a été envoyé avec succès !', 'success')
                return redirect(url_for('main.contact_page', _anchor='contact-form'))

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
        # Notification push aux admins (background)
        try:
            from push_notification import send_push_to_all_admins
            sent = send_push_to_all_admins(
                title='📩 Nouveau message',
                body=f'{nom} vous a envoyé un message.\nSujet: {sujet or "Sans sujet"}',
                url='/admin/messages',
                tag='lce-contact',
                require_interaction=True,
            )
            current_app.logger.info(f'[PUSH CONTACT] Notification envoyée à {sent} appareil(s)')
        except Exception as e:
            current_app.logger.warning(f'[PUSH CONTACT] Échec envoi push: {e}')
    except Exception as e:
        db.session.rollback()
        flash('Une erreur est survenue. Veuillez réessayer.', 'danger')

    return redirect(url_for('main.contact_page', _anchor='contact-form'))


@main_bp.route('/voyages')
def voyages_page():
    destinations = [
        {'nom': 'Dubaï', 'drapeau': '��', 'slug': 'dubai',
         'image': 'https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=800&q=80',
         'description': 'Hub économique mondial offrant des opportunités exceptionnelles dans le commerce, le tourisme de luxe, la construction et les nouvelles technologies.',
         'opportunites': 'Commerce, Tourisme, Finance, Tech',
         'avantages': ['Exonération fiscale', 'Salaire attractif', 'Qualité de vie', 'Cosmopolite']},
        {'nom': 'Canada', 'drapeau': '��', 'slug': 'canada',
         'image': 'https://images.unsplash.com/photo-1501594907352-04cda38ebc29?w=800&q=80',
         'description': 'Réputé pour sa qualité de vie exceptionnelle, son système de santé et ses nombreuses voies d\'immigration pour les travailleurs qualifiés.',
         'opportunites': 'Immigration, Emploi, Études',
         'avantages': ['Résidence permanente', 'Santé gratuite', 'Multiculturel', 'Sécurité']},
        {'nom': 'Allemagne', 'drapeau': '��', 'slug': 'allemagne',
         'image': 'https://images.unsplash.com/photo-1467269204594-9661b134dd2b?w=800&q=80',
         'description': 'Première puissance économique européenne avec une forte demande de main-d\'œuvre qualifiée dans l\'industrie, l\'ingénierie et la santé.',
         'opportunites': 'Emploi, Formation, Études',
         'avantages': ['Salaire élevé', 'Protection sociale', 'Formation duale', 'Stabilité']},
        {'nom': 'Belgique', 'drapeau': '🇧🇪', 'slug': 'belgique',
         'image': 'https://images.unsplash.com/photo-1491557345352-5929e343eb89?w=800&q=80',
         'description': 'Au cœur de l\'Europe, siège des institutions européennes, avec un cadre de vie agréable et des opportunités dans les secteurs publics et privés.',
         'opportunites': 'Emploi, Stages, Études',
         'avantages': ['Cœur de l\'Europe', 'Multilingue', 'Sécurité sociale', 'Culture riche']},
        {'nom': 'Brésil', 'drapeau': '��', 'slug': 'bresil',
         'image': 'https://images.unsplash.com/photo-1483729558449-99ef09a8c325?w=800&q=80',
         'description': 'Géant économique sud-américain avec un marché dynamique dans l\'industrie, l\'agroalimentaire, les mines et les services.',
         'opportunites': 'Emploi, Commerce, Industrie',
         'avantages': ['Marché émergent', 'Climat agréable', 'Culture accueillante', 'Coût de vie abordable']},
    ]
    services = [
        {'icon': 'bi-compass', 'label': 'Orientation pays'},
        {'icon': 'bi-file-earmark-check', 'label': 'Constitution du dossier'},
        {'icon': 'bi-building-check', 'label': 'Recherche d\'emploi'},
        {'icon': 'bi-airplane', 'label': 'Préparation au départ'},
        {'icon': 'bi-headset', 'label': 'Suivi personnalisé'},
        {'icon': 'bi-shield-check', 'label': 'Assistance administrative'},
    ]
    etapes = [
        {'num': '01', 'titre': 'Consultation initiale', 'desc': 'Nous analysons votre profil, vos compétences et vos aspirations pour identifier les meilleures opportunités.'},
        {'num': '02', 'titre': 'Stratégie sur mesure', 'desc': 'Nous élaborons un plan d\'action personnalisé adapté à votre projet et au pays ciblé.'},
        {'num': '03', 'titre': 'Préparation du dossier', 'desc': 'Nous vous accompagnons dans la collecte et la préparation de tous les documents requis.'},
        {'num': '04', 'titre': 'Mise en relation', 'desc': 'Nous facilitons les contacts avec les employeurs, écoles ou partenaires locaux selon votre projet.'},
        {'num': '05', 'titre': 'Finalisation', 'desc': 'Nous assurons le suivi jusqu\'à la validation de votre dossier par les autorités compétentes.'},
    ]
    faq = [
        ('Quels sont les pays disponibles ?', 'Nous accompagnons vers Dubaï, le Canada, l\'Allemagne, la Belgique et le Brésil. Chaque destination offre des avantages spécifiques selon votre profil.'),
        ('Quels types de projets accompagnez-vous ?', 'Projets d\'emploi, études supérieures, stages professionnels, formations qualifiantes et mobilité professionnelle.'),
        ('Comment se déroule l\'accompagnement ?', 'En 5 étapes : consultation, stratégie, préparation, mise en relation et finalisation. Un conseiller dédié vous suit tout au long du processus.'),
        ('Quels sont vos tarifs ?', 'Les tarifs varient selon la destination et le type de projet. Contactez-nous pour un devis personnalisé sans engagement.'),
        ('Combien de temps prend une procédure ?', 'Les délais varient de 2 à 8 mois selon le pays et le type de demande. Nous vous donnons une estimation précise lors de la consultation.'),
    ]
    return render_template('voyages.html', destinations=destinations, services=services, etapes=etapes, faq=faq)


@main_bp.route('/api/demande-voyage', methods=['POST'])
def demande_voyage():
    nom = request.form.get('nom', '').strip()
    telephone = request.form.get('telephone', '').strip()
    whatsapp = request.form.get('whatsapp', '').strip()
    email = request.form.get('email', '').strip()
    pays = request.form.get('pays', '').strip()
    type_projet = request.form.get('type_projet', '').strip()
    message = request.form.get('message', '').strip()

    if not nom or not telephone:
        flash('Veuillez remplir votre nom et votre téléphone.', 'danger')
        return redirect(url_for('main.voyages_page', _anchor='demande'))

    try:
        dv = DemandeVoyage(
            nom=nom, telephone=telephone, whatsapp=whatsapp,
            email=email, pays=pays, type_projet=type_projet,
            message=message, statut='en_attente'
        )
        db.session.add(dv)
        db.session.commit()
        flash('Votre demande de voyage a été envoyée avec succès ! Notre équipe vous contactera dans les plus brefs délais.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Une erreur est survenue. Veuillez réessayer.', 'danger')

    return redirect(url_for('main.voyages_page', _anchor='demande'))


@main_bp.route('/a-propos')
def a_propos_page():
    equipiers = Equipe.query.filter_by(actif=True).order_by(Equipe.ordre.asc()).all()
    temoignages = Temoignage.query.filter_by(actif=True).order_by(Temoignage.created_at.desc()).all()
    stats = Statistique.query.order_by(Statistique.ordre.asc()).all()
    formations = Formation.query.filter_by(actif=True).order_by(Formation.ordre_affichage.asc()).all()
    return render_template('a-propos.html', equipiers=equipiers, temoignages=temoignages, stats=stats, formations=formations)


ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def secure_filename_custom(filename):
    import unicodedata, re
    filename = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').decode('ascii')
    filename = re.sub(r'[^\w\s.-]', '', filename).strip()
    filename = re.sub(r'[-\s]+', '-', filename)
    return filename

def generate_numero_inscription():
    from datetime import datetime
    annee = datetime.utcnow().strftime('%Y')
    prefix = f'LCE-{annee}-'
    last = Inscription.query.filter(Inscription.numero_inscription.like(f'{prefix}%')).order_by(Inscription.id.desc()).first()
    if last and last.numero_inscription:
        try:
            num = int(last.numero_inscription.split('-')[-1]) + 1
        except:
            num = 1
    else:
        num = 1
    return f'{prefix}{num:06d}'

def generate_qr_code(data):
    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

def generate_pdf_recu(inscription):
    buf = io.BytesIO()
    w, h = A4  # 210 x 297 mm
    c = canvas.Canvas(buf, pagesize=A4)
    c.setTitle(f'Recu_Inscription_{inscription.numero_inscription}')

    PRIMARY = HexColor('#0D47C7')
    DARK_BLUE = HexColor('#0A2E8B')
    LIGHT_BG = HexColor('#F4F6F9')
    TEXT_COLOR = HexColor('#1E293B')
    GREY_TEXT = HexColor('#64748B')

    # Fond blanc
    c.setFillColor(white)
    c.rect(0, 0, w, h, fill=1, stroke=0)

    # Bandeau bleu
    c.setFillColor(PRIMARY)
    c.rect(0, h - 45*mm, w, 45*mm, fill=1, stroke=0)

    # Logo LCE
    c.setFillColor(white)
    c.setFont('Helvetica-Bold', 22)
    c.drawString(20*mm, h - 22*mm, 'LCE')
    c.setFont('Helvetica', 9)
    c.drawString(20*mm, h - 28*mm, 'Leader Chiffre Entreprise')
    c.setFont('Helvetica', 7)
    c.drawString(20*mm, h - 33*mm, 'Centre Professionnel de Formation')
    c.setFont('Helvetica', 7)
    c.drawString(20*mm, h - 38*mm, 'Conduite d\'engins | Manutention | Logistique | Transport')

    # Titre reçu
    c.setFillColor(white)
    c.setFont('Helvetica-Bold', 18)
    c.drawRightString(w - 20*mm, h - 18*mm, "REÇU D'INSCRIPTION")
    c.setFont('Helvetica', 8)
    c.drawRightString(w - 20*mm, h - 23*mm, f"Date: {inscription.created_at.strftime('%d/%m/%Y') if inscription.created_at else datetime.utcnow().strftime('%d/%m/%Y')}")
    c.drawRightString(w - 20*mm, h - 27*mm, f"N°: {inscription.numero_inscription}")

    # Section Info Candidat
    y = h - 55*mm
    c.setFillColor(DARK_BLUE)
    c.setFont('Helvetica-Bold', 11)
    c.drawString(20*mm, y, 'INFORMATIONS DU CANDIDAT')
    c.setStrokeColor(PRIMARY)
    c.setLineWidth(1)
    c.line(20*mm, y - 3*mm, w - 20*mm, y - 3*mm)

    y -= 12*mm
    c.setFillColor(TEXT_COLOR)
    c.setFont('Helvetica', 9)
    info_lines = [
        ('Nom complet:', inscription.nom_complet or inscription.nom or '—'),
        ('Date de naissance:', inscription.date_naissance or '—'),
        ('Sexe:', inscription.sexe or '—'),
        ('Nationalité:', inscription.nationalite or '—'),
        ('Téléphone:', inscription.telephone or '—'),
        ('WhatsApp:', inscription.whatsapp or '—'),
        ('Email:', inscription.email or '—'),
        ('Adresse:', (inscription.adresse or '') + (' ' + (inscription.ville or '')).strip() or '—'),
        ('Niveau d\'étude:', inscription.niveau_etude or '—'),
        ('Situation:', inscription.situation_professionnelle or '—'),
    ]
    left_col_x = 20*mm
    right_col_x = w/2 + 5*mm
    for i, (label, val) in enumerate(info_lines):
        col_x = left_col_x if i < len(info_lines)/2 else right_col_x
        row_y = y - (i % (len(info_lines)//2 + 1)) * 7*mm
        c.setFont('Helvetica-Bold', 8)
        c.setFillColor(GREY_TEXT)
        c.drawString(col_x, row_y, label)
        c.setFont('Helvetica', 9)
        c.setFillColor(TEXT_COLOR)
        c.drawString(col_x + 35*mm, row_y, str(val)[:35])

    # Formation
    y_form = y - 6 * 7*mm - 5*mm
    c.setFillColor(DARK_BLUE)
    c.setFont('Helvetica-Bold', 11)
    c.drawString(20*mm, y_form, 'FORMATION')
    c.setStrokeColor(PRIMARY)
    c.line(20*mm, y_form - 3*mm, w - 20*mm, y_form - 3*mm)

    y_form -= 12*mm
    formation_name = inscription.formation or (inscription.formation_ref.nom if inscription.formation_ref else '—')
    c.setFont('Helvetica-Bold', 12)
    c.setFillColor(PRIMARY)
    c.drawString(20*mm, y_form, formation_name)

    # Statut
    y_form -= 10*mm
    c.setFont('Helvetica-Bold', 10)
    statut_map = {'en_attente': 'EN ATTENTE', 'validee': 'VALIDÉE', 'contactee': 'CONTACTÉE', 'refusee': 'REFUSÉE'}
    statut_display = statut_map.get(inscription.statut, inscription.statut.upper())
    statut_colors = {'en_attente': HexColor('#F59E0B'), 'validee': HexColor('#10B981'), 'contactee': HexColor('#3B82F6'), 'refusee': HexColor('#EF4444')}
    c.setFillColor(statut_colors.get(inscription.statut, black))
    c.setStrokeColor(statut_colors.get(inscription.statut, black))
    c.setLineWidth(0.5)
    c.roundRect(20*mm, y_form - 5*mm, 40*mm, 10*mm, 3*mm, fill=0, stroke=1)
    c.drawCentredString(20*mm + 20*mm, y_form - 1*mm, statut_display)

    # Avis important
    y_avis = y_form - 22*mm
    c.setFillColor(HexColor('#FFF7ED'))
    c.setStrokeColor(HexColor('#F59E0B'))
    c.setLineWidth(1.5)
    c.roundRect(20*mm, y_avis - 18*mm, w - 40*mm, 22*mm, 4*mm, fill=1, stroke=1)
    c.setFillColor(HexColor('#92400E'))
    c.setFont('Helvetica-Bold', 9)
    c.drawString(27*mm, y_avis - 3*mm, '⚠ IMPORTANT')
    c.setFont('Helvetica', 8)
    c.drawString(27*mm, y_avis - 9*mm, 'Le montant de la formation sera communiqué lors de votre passage au centre de formation.')
    c.drawString(27*mm, y_avis - 14*mm, 'Les frais d\'inscription sont à régler UNIQUEMENT au bureau de Leader Chiffre Entreprise')
    c.drawString(27*mm, y_avis - 19*mm, 'ou directement sur le lieu de la formation. Aucun paiement en ligne n\'est demandé.')

    # QR Code
    qr_data = f"LCE|{inscription.numero_inscription}|{inscription.nom_complet or inscription.nom}|{formation_name}"
    qr_buf = generate_qr_code(qr_data)
    qr_img = ImageReader(qr_buf)
    c.drawImage(qr_img, w - 20*mm - 30*mm, y_avis - 18*mm - 5*mm, width=28*mm, height=28*mm)
    c.setFont('Helvetica', 6)
    c.setFillColor(GREY_TEXT)
    c.drawCentredString(w - 20*mm - 16*mm, y_avis - 21*mm - 5*mm, inscription.numero_inscription or '')

    # Footer
    y_footer = 20*mm
    c.setStrokeColor(PRIMARY)
    c.setLineWidth(1)
    c.line(20*mm, y_footer + 10*mm, w - 20*mm, y_footer + 10*mm)
    c.setFillColor(GREY_TEXT)
    c.setFont('Helvetica', 7)
    c.drawString(20*mm, y_footer + 5*mm, 'Leader Chiffre Entreprise — leaderchiffreentreprise.com')
    c.drawString(20*mm, y_footer, 'contact@lcetg.com | Tél: +228 70 01 96 23')
    c.drawRightString(w - 20*mm, y_footer + 5*mm, 'Reçu généré automatiquement')
    c.drawRightString(w - 20*mm, y_footer, 'Cachet & Signature')

    c.save()
    buf.seek(0)
    return buf


@main_bp.route('/s-inscrire')
def s_inscrire_page():
    formations = Formation.query.filter_by(actif=True).order_by(Formation.ordre_affichage.asc()).all()
    return render_template('s-inscrire.html', formations=formations)


@main_bp.route('/inscription', methods=['POST'])
def inscription():
    nom_complet = request.form.get('nom_complet', '').strip()
    telephone = request.form.get('telephone', '').strip()

    if not nom_complet or not telephone:
        flash('Le nom complet et le téléphone sont obligatoires.', 'danger')
        return redirect(url_for('main.s_inscrire_page'))

    # Récupérer tous les champs
    date_naissance = request.form.get('date_naissance', '').strip()
    sexe = request.form.get('sexe', '').strip()
    nationalite = request.form.get('nationalite', '').strip()
    adresse = request.form.get('adresse', '').strip()
    ville = request.form.get('ville', '').strip()
    whatsapp = request.form.get('whatsapp', '').strip()
    email = request.form.get('email', '').strip()
    formation_id = request.form.get('formation_id', '').strip()
    niveau_etude = request.form.get('niveau_etude', '').strip()
    situation_professionnelle = request.form.get('situation_professionnelle', '').strip()
    commentaire = request.form.get('commentaire', '').strip()
    consentement = request.form.get('consentement', '').strip()

    if consentement != 'on':
        flash('Vous devez accepter les conditions d\'inscription.', 'danger')
        return redirect(url_for('main.s_inscrire_page'))

    # Gestion des uploads
    upload_folder = current_app.config.get('UPLOAD_FOLDER', os.path.join(os.path.dirname(__file__), 'static', 'uploads'))
    os.makedirs(upload_folder, exist_ok=True)

    def save_upload(field_name):
        if field_name not in request.files:
            return None
        file = request.files[field_name]
        if file and file.filename and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            new_name = f"{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(upload_folder, new_name)
            file.save(filepath)
            return f'uploads/{new_name}'
        return None

    photo_path = save_upload('photo')
    piece_path = save_upload('piece_identite')
    cv_path = save_upload('cv')

    # Récupérer le nom de la formation
    formation_nom = ''
    if formation_id:
        try:
            f = Formation.query.get(int(formation_id))
            if f:
                formation_nom = f.nom
        except:
            pass

    try:
        insc = Inscription(
            nom=nom_complet,
            prenom='',
            nom_complet=nom_complet,
            date_naissance=date_naissance,
            sexe=sexe,
            nationalite=nationalite,
            adresse=adresse,
            ville=ville,
            telephone=telephone,
            whatsapp=whatsapp,
            email=email,
            formation=formation_nom,
            formation_id=int(formation_id) if formation_id else None,
            niveau_etude=niveau_etude,
            situation_professionnelle=situation_professionnelle,
            photo=photo_path,
            piece_identite=piece_path,
            cv=cv_path,
            commentaire=commentaire,
            statut='en_attente',
            created_at=datetime.utcnow()
        )
        db.session.add(insc)
        db.session.flush()  # Pour avoir l'ID

        # Générer numéro d'inscription
        numero = generate_numero_inscription()
        insc.numero_inscription = numero

        # Générer QR code
        qr_data = f"LCE|{numero}|{nom_complet}|{formation_nom}"
        qr_buf = generate_qr_code(qr_data)
        qr_folder = os.path.join(upload_folder, 'qrcodes')
        os.makedirs(qr_folder, exist_ok=True)
        qr_filename = f'qr_{uuid.uuid4().hex}.png'
        with open(os.path.join(qr_folder, qr_filename), 'wb') as f:
            f.write(qr_buf.getvalue())
        insc.qr_code = f'uploads/qrcodes/{qr_filename}'

        # Générer PDF reçu
        pdf_buf = generate_pdf_recu(insc)
        pdf_folder = os.path.join(upload_folder, 'recus')
        os.makedirs(pdf_folder, exist_ok=True)
        pdf_filename = f'recu_{numero}.pdf'
        pdf_path = os.path.join(pdf_folder, pdf_filename)
        with open(pdf_path, 'wb') as f:
            f.write(pdf_buf.getvalue())
        insc.pdf_recu = f'uploads/recus/{pdf_filename}'

        db.session.commit()

        # Envoyer email au candidat
        try:
            send_confirmation_email(insc, pdf_path)
            insc.confirmation_envoyee = True
            insc.date_confirmation = datetime.utcnow()
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Email candidat échoué: {e}")

        # Envoyer notification à l'admin
        try:
            send_admin_notification(insc)
        except Exception as e:
            current_app.logger.error(f"Email admin échoué: {e}")

        # Notification push aux admins (background, ne bloque jamais)
        try:
            from push_notification import send_push_to_all_admins
            heure = datetime.utcnow().strftime('%d/%m/%Y à %H:%M')
            send_push_to_all_admins(
                title='🔔 Nouvelle inscription',
                body=f'Une nouvelle demande d\'inscription vient d\'être reçue.\n'
                     f'Nom: {nom_complet}\n'
                     f'Formation: {formation_nom or "Non précisée"}\n'
                     f'Heure: {heure}',
                url='/admin/inscriptions',
                tag='lce-inscription',
                require_interaction=True,
            )
        except Exception:
            pass

        flash('Votre demande d\'inscription a été enregistrée avec succès ! Un email de confirmation vous a été envoyé.', 'success')
        return render_template('s-inscrire.html', inscriptions=[insc], formations=Formation.query.filter_by(actif=True).order_by(Formation.ordre_affichage.asc()).all(), success=True, numero=numero)

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erreur inscription: {e}")
        flash('Une erreur est survenue. Veuillez réessayer.', 'danger')
        return redirect(url_for('main.s_inscrire_page'))


def _send_resend_email(to_email, subject, html_body, attachment_path=None, attachment_name=None):
    """Envoie un email via l'API Resend."""
    api_key = current_app.config.get('RESEND_API_KEY')
    from_email = current_app.config.get('RESEND_FROM', 'LCE <contact@lcetg.com>')

    if not api_key:
        current_app.logger.error("RESEND_API_KEY non configurée")
        raise Exception("RESEND_API_KEY non configurée")

    url = 'https://api.resend.com/emails'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }

    payload = {
        'from': from_email,
        'to': [to_email],
        'subject': subject,
        'html': html_body,
    }

    # Pièce jointe
    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, 'rb') as f:
            file_content = f.read()
        payload['attachments'] = [{
            'filename': attachment_name or os.path.basename(attachment_path),
            'content': base64.b64encode(file_content).decode('utf-8'),
        }]

    response = requests.post(url, headers=headers, json=payload, timeout=15)
    if response.status_code >= 400:
        current_app.logger.error(f"Resend API error: {response.status_code} - {response.text}")
        raise Exception(f"Resend API error: {response.text}")
    return response.json()


def send_confirmation_email(inscription, pdf_path):
    nom = inscription.nom_complet or inscription.nom
    html_body = f'''
    <!DOCTYPE html><html><head><meta charset="utf-8"></head>
    <body style="font-family:Arial,sans-serif;background:#f4f6f9;margin:0;padding:20px">
    <div style="max-width:600px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.1)">
        <div style="background:#0D47C7;padding:30px;text-align:center">
            <h1 style="color:#fff;margin:0;font-size:24px">LCE</h1>
            <p style="color:#cbd5e1;margin:5px 0 0">Leader Chiffre Entreprise</p>
        </div>
        <div style="padding:30px">
            <h2 style="color:#0D47C7;margin-top:0">Confirmation de votre demande d'inscription</h2>
            <p>Bonjour <strong>{nom}</strong>,</p>
            <p>Nous avons bien reçu votre demande d'inscription.</p>
            <div style="background:#e8f0fe;border-radius:8px;padding:20px;text-align:center;margin:20px 0">
                <p style="color:#64748b;margin:0;font-size:14px">Votre numéro d'inscription</p>
                <p style="color:#0D47C7;font-size:28px;font-weight:700;margin:5px 0;letter-spacing:2px">{inscription.numero_inscription}</p>
            </div>
            <p>Veuillez trouver en <strong>pièce jointe</strong> votre reçu d'inscription officiel.</p>
            <div style="background:#FFF7ED;border-left:4px solid #F59E0B;padding:15px;margin:20px 0;border-radius:4px">
                <p style="margin:0;color:#92400E"><strong>⚠ Important :</strong></p>
                <p style="margin:5px 0 0;color:#92400E">Votre inscription n'est pas encore définitive. Afin de finaliser votre dossier, vous devez vous présenter au bureau de Leader Chiffre Entreprise ou directement sur le lieu de la formation.</p>
                <p style="margin:5px 0 0;color:#92400E">Les frais d'inscription seront réglés <strong>uniquement sur place</strong>. Le montant de la formation vous sera communiqué lors de votre passage.</p>
                <p style="margin:5px 0 0;color:#92400E">Merci de présenter votre reçu (imprimé ou sur votre téléphone) à votre arrivée.</p>
            </div>
            <p>Nous vous remercions de votre confiance.</p>
            <p style="color:#64748b"><strong>Leader Chiffre Entreprise</strong><br>Centre Professionnel de Formation</p>
        </div>
        <div style="background:#f1f5f9;padding:15px;text-align:center">
            <p style="color:#64748b;font-size:12px;margin:0">contact@lcetg.com | Tél: +228 70 01 96 23</p>
        </div>
    </div></body></html>'''

    _send_resend_email(
        to_email=inscription.email,
        subject='Confirmation de votre demande d\'inscription - Leader Chiffre Entreprise',
        html_body=html_body,
        attachment_path=pdf_path if pdf_path and os.path.exists(pdf_path) else None,
        attachment_name=f'Recu_{inscription.numero_inscription}.pdf'
    )


def send_admin_notification(inscription):
    nom = inscription.nom_complet or inscription.nom
    formation_nom = inscription.formation or (inscription.formation_ref.nom if inscription.formation_ref else '—')

    html_body = f'''
    <!DOCTYPE html><html><head><meta charset="utf-8"></head>
    <body style="font-family:Arial,sans-serif;background:#f4f6f9;margin:0;padding:20px">
    <div style="max-width:500px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.1)">
        <div style="background:#0A2E8B;padding:20px;text-align:center">
            <h2 style="color:#fff;margin:0">🔔 Nouvelle Inscription</h2>
        </div>
        <div style="padding:20px">
            <table style="width:100%;border-collapse:collapse">
                <tr><td style="padding:8px;border-bottom:1px solid #e2e8f0;color:#64748b">N° Inscription</td><td style="padding:8px;border-bottom:1px solid #e2e8f0;font-weight:700;color:#0D47C7">{inscription.numero_inscription}</td></tr>
                <tr><td style="padding:8px;border-bottom:1px solid #e2e8f0;color:#64748b">Nom</td><td style="padding:8px;border-bottom:1px solid #e2e8f0;font-weight:600">{nom}</td></tr>
                <tr><td style="padding:8px;border-bottom:1px solid #e2e8f0;color:#64748b">Téléphone</td><td style="padding:8px;border-bottom:1px solid #e2e8f0">{inscription.telephone}</td></tr>
                <tr><td style="padding:8px;border-bottom:1px solid #e2e8f0;color:#64748b">Email</td><td style="padding:8px;border-bottom:1px solid #e2e8f0">{inscription.email or '—'}</td></tr>
                <tr><td style="padding:8px;border-bottom:1px solid #e2e8f0;color:#64748b">Formation</td><td style="padding:8px;border-bottom:1px solid #e2e8f0">{formation_nom}</td></tr>
                <tr><td style="padding:8px;border-bottom:1px solid #e2e8f0;color:#64748b">Date</td><td style="padding:8px;border-bottom:1px solid #e2e8f0">{datetime.utcnow().strftime('%d/%m/%Y à %H:%M')}</td></tr>
            </table>
            <div style="text-align:center;margin-top:20px">
                <a href="https://leaderchiffreentreprise.com/admin" style="background:#0D47C7;color:#fff;padding:10px 24px;border-radius:8px;text-decoration:none;display:inline-block">Voir dans l'admin</a>
            </div>
        </div>
    </div></body></html>'''

    _send_resend_email(
        to_email='contact@lcetg.com',
        subject=f'Nouvelle inscription - {nom}',
        html_body=html_body,
    )


# --- API NOTIFICATIONS PUSH (visiteurs/public) ---
@main_bp.route('/api/push/vapid-public-key')
def api_push_vapid_public_key_public():
    """Renvoie la clé publique VAPID pour les visiteurs du site."""
    key = current_app.config.get('VAPID_PUBLIC_KEY', '')
    current_app.logger.info(f"[PUSH PUBLIC] VAPID public key demandée (longueur={len(key)})")
    return jsonify({'publicKey': key})


@main_bp.route('/api/push/subscribe', methods=['POST'])
def api_push_subscribe_public():
    """Enregistre une souscription push visiteur — DIAGNOSTIC COMPLET."""
    import traceback as tb
    import json as _json

    current_app.logger.critical("=" * 60)
    current_app.logger.critical("=== /api/push/subscribe APPELÉE (public) ===")
    current_app.logger.critical(f"Méthode: {request.method}")
    current_app.logger.critical(f"Content-Type: {request.content_type}")

    raw_data = request.get_data(as_text=True)[:500]
    current_app.logger.critical(f"Requête brute: {raw_data}")

    try:
        data = request.get_json(force=True)
    except Exception:
        current_app.logger.critical(f"JSON invalide: {tb.format_exc()}")
        return jsonify({'success': False, 'error': 'JSON parsing échoué'}), 400

    if not data:
        current_app.logger.critical("Aucune donnée JSON")
        return jsonify({'success': False, 'error': 'Aucune donnée'}), 400

    endpoint = data.get('endpoint', '')
    keys = data.get('keys', {})
    p256dh = keys.get('p256dh', '')
    auth = keys.get('auth', '')

    current_app.logger.critical(f"endpoint={endpoint[:100]}...")
    current_app.logger.critical(f"p256dh={'OK' if p256dh else 'MANQUANT'} (longueur={len(p256dh)})")
    current_app.logger.critical(f"auth={'OK' if auth else 'MANQUANT'} (longueur={len(auth)})")

    if not endpoint or not p256dh or not auth:
        current_app.logger.critical("DONNÉES INCOMPLÈTES → 400")
        return jsonify({'success': False, 'error': 'Données incomplètes'}), 400

    try:
        count_before = PushSubscription.query.count()
        current_app.logger.critical(f"DB: souscriptions AVANT insert = {count_before}")

        existing = PushSubscription.query.filter_by(endpoint=endpoint).first()
        if existing:
            current_app.logger.critical(f"DB: souscription EXISTANTE id={existing.id} — mise à jour")
            existing.p256dh = p256dh
            existing.auth = auth
            existing.actif = True
            existing.navigateur = data.get('navigateur', '')
            existing.plateforme = data.get('plateforme', '')
            existing.updated_at = datetime.utcnow()
        else:
            current_app.logger.critical("DB: création nouvelle souscription...")
            sub = PushSubscription(
                endpoint=endpoint,
                p256dh=p256dh,
                auth=auth,
                navigateur=data.get('navigateur', ''),
                plateforme=data.get('plateforme', ''),
                admin_id=None,
                actif=True,
            )
            db.session.add(sub)
            current_app.logger.critical("DB: db.session.add() OK")

        db.session.commit()
        current_app.logger.critical("DB: db.session.commit() RÉUSSI !")

        count_after = PushSubscription.query.count()
        current_app.logger.critical(f"DB: souscriptions APRÈS insert = {count_after}")
        current_app.logger.critical("=== /api/push/subscribe SUCCÈS ===")
        current_app.logger.critical("=" * 60)

        return jsonify({'success': True, 'count': count_after})
    except Exception:
        db.session.rollback()
        current_app.logger.critical(f"ERREUR DB: {tb.format_exc()}")
        return jsonify({'success': False, 'error': 'Erreur base de données'}), 500


@main_bp.route('/api/push/unsubscribe', methods=['POST'])
def api_push_unsubscribe_public():
    """Désactive une souscription push visiteur."""
    data = request.get_json(force=True)
    if not data or not data.get('endpoint'):
        return jsonify({'success': False, 'error': 'Données invalides'}), 400

    sub = PushSubscription.query.filter_by(endpoint=data['endpoint']).first()
    if sub:
        sub.actif = False
        db.session.commit()
    return jsonify({'success': True})


@main_bp.route('/telecharger-recu/<int:inscription_id>')
def telecharger_recu(inscription_id):
    insc = Inscription.query.get_or_404(inscription_id)
    if insc.pdf_recu:
        pdf_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', os.path.join(os.path.dirname(__file__), 'static', 'uploads')), insc.pdf_recu.replace('uploads/', ''))
        # Fallback: regenerate if file missing
        if not os.path.exists(pdf_path):
            pdf_buf = generate_pdf_recu(insc)
            os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
            with open(pdf_path, 'wb') as f:
                f.write(pdf_buf.getvalue())
        return send_file(pdf_path, as_attachment=True, download_name=f'Recu_{insc.numero_inscription}.pdf', mimetype='application/pdf')
    # Regenerate on the fly
    pdf_buf = generate_pdf_recu(insc)
    return send_file(pdf_buf, as_attachment=True, download_name=f'Recu_{insc.numero_inscription}.pdf', mimetype='application/pdf')
