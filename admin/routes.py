import os
import uuid
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from admin import admin_bp
from extensions import db
from models import (
    AdminUser, Formation, Message, Temoignage, Inscription,
    Galerie, Video, Equipe, ParametreSite, ContactMessage,
    PushSubscription
)


def admin_required(f):
    """Decorator to require admin role"""
    from functools import wraps
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.actif:
            logout_user()
            flash('Votre compte a été désactivé.', 'danger')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated


# --- AUTH ---
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = AdminUser.query.filter_by(email=email).first()
        if user and user.check_password(password):
            if not user.actif:
                flash('Votre compte a été désactivé.', 'danger')
                return render_template('admin/login.html')
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user, remember=request.form.get('remember'))
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin.dashboard'))
        flash('Email ou mot de passe incorrect.', 'danger')
    return render_template('admin/login.html')


@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('admin.login'))


# --- DASHBOARD ---
@admin_bp.route('/')
@admin_required
def dashboard():
    nb_formations = Formation.query.count()
    nb_messages = Message.query.filter_by(lu=False).count()
    nb_inscriptions = Inscription.query.count()
    nb_galerie = Galerie.query.count()
    nb_videos = Video.query.count()
    nb_temoignages = Temoignage.query.count()

    return render_template('admin/dashboard.html',
                           nb_formations=nb_formations,
                           nb_messages=nb_messages,
                           nb_inscriptions=nb_inscriptions,
                           nb_galerie=nb_galerie,
                           nb_videos=nb_videos,
                           nb_temoignages=nb_temoignages)


# --- FORMATIONS ---
@admin_bp.route('/formations')
@admin_required
def formations():
    formations = Formation.query.order_by(Formation.ordre_affichage.asc()).all()
    return render_template('admin/formations.html', formations=formations)


@admin_bp.route('/formation/add', methods=['GET', 'POST'])
@admin_required
def formation_add():
    if request.method == 'POST':
        from slugify import slugify
        nom = request.form.get('nom', '').strip()
        slug = slugify(nom) if nom else ''
        description = request.form.get('description', '').strip()
        duree = request.form.get('duree', '').strip()
        prix = request.form.get('prix', '').strip()
        categorie = request.form.get('categorie', '').strip()
        ordre = int(request.form.get('ordre', 0))
        actif = request.form.get('actif') == '1'

        image = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
                file.save(os.path.join(current_app.static_folder, 'uploads', 'formations', filename))
                image = filename

        f = Formation(
            nom=nom, slug=slug, description=description,
            image=image, duree=duree, prix=prix,
            categorie=categorie, ordre_affichage=ordre, actif=actif
        )
        db.session.add(f)
        db.session.commit()
        flash('Formation ajoutée avec succès !', 'success')
        return redirect(url_for('admin.formations'))

    return render_template('admin/formation_form.html', formation=None)


def slugify(text):
    """Simple slug function without external dependency"""
    import re
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return re.sub(r'^-+|-+$', '', text)


def allowed_file(filename):
    ALLOWED = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED


@admin_bp.route('/formation/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def formation_edit(id):
    formation = Formation.query.get_or_404(id)
    if request.method == 'POST':
        formation.nom = request.form.get('nom', '').strip()
        formation.slug = slugify(formation.nom)
        formation.description = request.form.get('description', '').strip()
        formation.duree = request.form.get('duree', '').strip()
        formation.prix = request.form.get('prix', '').strip()
        formation.categorie = request.form.get('categorie', '').strip()
        formation.ordre_affichage = int(request.form.get('ordre', 0))
        formation.actif = request.form.get('actif') == '1'

        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                # Delete old image
                if formation.image:
                    old_path = os.path.join(current_app.static_folder, 'uploads', 'formations', formation.image)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
                file.save(os.path.join(current_app.static_folder, 'uploads', 'formations', filename))
                formation.image = filename

        formation.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Formation modifiée avec succès !', 'success')
        return redirect(url_for('admin.formations'))

    return render_template('admin/formation_form.html', formation=formation)


@admin_bp.route('/formation/<int:id>/delete', methods=['POST'])
@admin_required
def formation_delete(id):
    formation = Formation.query.get_or_404(id)
    if formation.image:
        img_path = os.path.join(current_app.static_folder, 'uploads', 'formations', formation.image)
        if os.path.exists(img_path):
            os.remove(img_path)
    db.session.delete(formation)
    db.session.commit()
    flash('Formation supprimée.', 'success')
    return redirect(url_for('admin.formations'))


@admin_bp.route('/formation/<int:id>/toggle', methods=['POST'])
@admin_required
def formation_toggle(id):
    formation = Formation.query.get_or_404(id)
    formation.actif = not formation.actif
    db.session.commit()
    return jsonify({'status': 'ok', 'actif': formation.actif})


# --- GALERIE ---
@admin_bp.route('/galerie')
@admin_required
def galerie():
    images = Galerie.query.order_by(Galerie.ordre.asc()).all()
    return render_template('admin/galerie.html', images=images)


@admin_bp.route('/galerie/add', methods=['POST'])
@admin_required
def galerie_add():
    titre = request.form.get('titre', '').strip()
    description = request.form.get('description', '').strip()
    categorie = request.form.get('categorie', 'general')
    ordre = int(request.form.get('ordre', 0))
    actif = request.form.get('actif') == '1'

    image = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename and allowed_file(file.filename):
            filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
            file.save(os.path.join(current_app.static_folder, 'uploads', 'galerie', filename))
            image = filename

    if not image:
        flash('Veuillez sélectionner une image.', 'danger')
        return redirect(url_for('admin.galerie'))

    g = Galerie(titre=titre, image=image, categorie=categorie, description=description, ordre=ordre, actif=actif)
    db.session.add(g)
    db.session.commit()
    flash('Image ajoutée.', 'success')
    return redirect(url_for('admin.galerie'))


@admin_bp.route('/galerie/<int:id>/edit', methods=['POST'])
@admin_required
def galerie_edit(id):
    g = Galerie.query.get_or_404(id)
    g.titre = request.form.get('titre', '').strip()
    g.description = request.form.get('description', '').strip()
    g.categorie = request.form.get('categorie', 'general')
    g.ordre = int(request.form.get('ordre', 0))
    g.actif = request.form.get('actif') == '1'

    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename and allowed_file(file.filename):
            if g.image:
                old_path = os.path.join(current_app.static_folder, 'uploads', 'galerie', g.image)
                if os.path.exists(old_path):
                    os.remove(old_path)
            filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
            file.save(os.path.join(current_app.static_folder, 'uploads', 'galerie', filename))
            g.image = filename

    db.session.commit()
    flash('Image modifiée.', 'success')
    return redirect(url_for('admin.galerie'))


@admin_bp.route('/galerie/<int:id>/delete', methods=['POST'])
@admin_required
def galerie_delete(id):
    g = Galerie.query.get_or_404(id)
    if g.image:
        img_path = os.path.join(current_app.static_folder, 'uploads', 'galerie', g.image)
        if os.path.exists(img_path):
            os.remove(img_path)
    db.session.delete(g)
    db.session.commit()
    flash('Image supprimée.', 'success')
    return redirect(url_for('admin.galerie'))


# --- VIDEOS ---
@admin_bp.route('/videos')
@admin_required
def videos():
    videos = Video.query.order_by(Video.ordre.asc()).all()
    return render_template('admin/videos.html', videos=videos)


@admin_bp.route('/video/add', methods=['POST'])
@admin_required
def video_add():
    titre = request.form.get('titre', '').strip()
    url_video = request.form.get('url_video', '').strip()
    description = request.form.get('description', '').strip()
    ordre = int(request.form.get('ordre', 0))
    actif = request.form.get('actif') == '1'

    miniature = None
    if 'miniature' in request.files:
        file = request.files['miniature']
        if file and file.filename and allowed_file(file.filename):
            filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
            file.save(os.path.join(current_app.static_folder, 'uploads', 'videos', filename))
            miniature = filename

    v = Video(titre=titre, url_video=url_video, miniature=miniature, description=description, ordre=ordre, actif=actif)
    db.session.add(v)
    db.session.commit()
    flash('Vidéo ajoutée.', 'success')
    return redirect(url_for('admin.videos'))


@admin_bp.route('/video/<int:id>/edit', methods=['POST'])
@admin_required
def video_edit(id):
    v = Video.query.get_or_404(id)
    v.titre = request.form.get('titre', '').strip()
    v.url_video = request.form.get('url_video', '').strip()
    v.description = request.form.get('description', '').strip()
    v.ordre = int(request.form.get('ordre', 0))
    v.actif = request.form.get('actif') == '1'

    if 'miniature' in request.files:
        file = request.files['miniature']
        if file and file.filename and allowed_file(file.filename):
            if v.miniature:
                old_path = os.path.join(current_app.static_folder, 'uploads', 'videos', v.miniature)
                if os.path.exists(old_path):
                    os.remove(old_path)
            filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
            file.save(os.path.join(current_app.static_folder, 'uploads', 'videos', filename))
            v.miniature = filename

    db.session.commit()
    flash('Vidéo modifiée.', 'success')
    return redirect(url_for('admin.videos'))


@admin_bp.route('/video/<int:id>/delete', methods=['POST'])
@admin_required
def video_delete(id):
    v = Video.query.get_or_404(id)
    if v.miniature:
        img_path = os.path.join(current_app.static_folder, 'uploads', 'videos', v.miniature)
        if os.path.exists(img_path):
            os.remove(img_path)
    db.session.delete(v)
    db.session.commit()
    flash('Vidéo supprimée.', 'success')
    return redirect(url_for('admin.videos'))


# --- EQUIPE ---
@admin_bp.route('/equipe')
@admin_required
def equipe():
    membres = Equipe.query.order_by(Equipe.ordre.asc()).all()
    return render_template('admin/equipe.html', membres=membres)


@admin_bp.route('/equipe/add', methods=['POST'])
@admin_required
def equipe_add():
    nom = request.form.get('nom', '').strip()
    fonction = request.form.get('fonction', '').strip()
    description = request.form.get('description', '').strip()
    ordre = int(request.form.get('ordre', 0))
    actif = request.form.get('actif') == '1'

    photo = None
    if 'photo' in request.files:
        file = request.files['photo']
        if file and file.filename and allowed_file(file.filename):
            filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
            file.save(os.path.join(current_app.static_folder, 'uploads', 'equipe', filename))
            photo = filename

    e = Equipe(nom=nom, fonction=fonction, photo=photo, description=description, ordre=ordre, actif=actif)
    db.session.add(e)
    db.session.commit()
    flash('Membre ajouté.', 'success')
    return redirect(url_for('admin.equipe'))


@admin_bp.route('/equipe/<int:id>/edit', methods=['POST'])
@admin_required
def equipe_edit(id):
    e = Equipe.query.get_or_404(id)
    e.nom = request.form.get('nom', '').strip()
    e.fonction = request.form.get('fonction', '').strip()
    e.description = request.form.get('description', '').strip()
    e.ordre = int(request.form.get('ordre', 0))
    e.actif = request.form.get('actif') == '1'

    if 'photo' in request.files:
        file = request.files['photo']
        if file and file.filename and allowed_file(file.filename):
            if e.photo:
                old_path = os.path.join(current_app.static_folder, 'uploads', 'equipe', e.photo)
                if os.path.exists(old_path):
                    os.remove(old_path)
            filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
            file.save(os.path.join(current_app.static_folder, 'uploads', 'equipe', filename))
            e.photo = filename

    db.session.commit()
    flash('Membre modifié.', 'success')
    return redirect(url_for('admin.equipe'))


@admin_bp.route('/equipe/<int:id>/delete', methods=['POST'])
@admin_required
def equipe_delete(id):
    e = Equipe.query.get_or_404(id)
    if e.photo:
        img_path = os.path.join(current_app.static_folder, 'uploads', 'equipe', e.photo)
        if os.path.exists(img_path):
            os.remove(img_path)
    db.session.delete(e)
    db.session.commit()
    flash('Membre supprimé.', 'success')
    return redirect(url_for('admin.equipe'))


# --- TEMOIGNAGES ---
@admin_bp.route('/temoignages')
@admin_required
def temoignages():
    temoignages = Temoignage.query.order_by(Temoignage.created_at.desc()).all()
    return render_template('admin/temoignages.html', temoignages=temoignages)


@admin_bp.route('/temoignage/add', methods=['POST'])
@admin_required
def temoignage_add():
    nom = request.form.get('nom', '').strip()
    fonction = request.form.get('fonction', '').strip()
    contenu = request.form.get('contenu', '').strip()
    note = int(request.form.get('note', 5))
    actif = request.form.get('actif') == '1'

    photo = None
    if 'photo' in request.files:
        file = request.files['photo']
        if file and file.filename and allowed_file(file.filename):
            filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
            file.save(os.path.join(current_app.static_folder, 'uploads', 'temoignages', filename))
            photo = filename

    t = Temoignage(nom=nom, fonction=fonction, contenu=contenu, note=note, photo=photo, actif=actif)
    db.session.add(t)
    db.session.commit()
    flash('Témoignage ajouté.', 'success')
    return redirect(url_for('admin.temoignages'))


@admin_bp.route('/temoignage/<int:id>/edit', methods=['POST'])
@admin_required
def temoignage_edit(id):
    t = Temoignage.query.get_or_404(id)
    t.nom = request.form.get('nom', '').strip()
    t.fonction = request.form.get('fonction', '').strip()
    t.contenu = request.form.get('contenu', '').strip()
    t.note = int(request.form.get('note', 5))
    t.actif = request.form.get('actif') == '1'

    if 'photo' in request.files:
        file = request.files['photo']
        if file and file.filename and allowed_file(file.filename):
            if t.photo:
                old_path = os.path.join(current_app.static_folder, 'uploads', 'temoignages', t.photo)
                if os.path.exists(old_path):
                    os.remove(old_path)
            filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
            file.save(os.path.join(current_app.static_folder, 'uploads', 'temoignages', filename))
            t.photo = filename

    db.session.commit()
    flash('Témoignage modifié.', 'success')
    return redirect(url_for('admin.temoignages'))


@admin_bp.route('/temoignage/<int:id>/delete', methods=['POST'])
@admin_required
def temoignage_delete(id):
    t = Temoignage.query.get_or_404(id)
    if t.photo:
        img_path = os.path.join(current_app.static_folder, 'uploads', 'temoignages', t.photo)
        if os.path.exists(img_path):
            os.remove(img_path)
    db.session.delete(t)
    db.session.commit()
    flash('Témoignage supprimé.', 'success')
    return redirect(url_for('admin.temoignages'))


# --- MESSAGES ---
@admin_bp.route('/messages')
@admin_required
def messages():
    search = request.args.get('q', '').strip()
    if search:
        msgs = ContactMessage.query.filter(
            (ContactMessage.nom.ilike(f'%{search}%')) |
            (ContactMessage.email.ilike(f'%{search}%')) |
            (ContactMessage.message.ilike(f'%{search}%'))
        ).order_by(ContactMessage.created_at.desc()).all()
    else:
        msgs = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template('admin/messages.html', messages=msgs, search=search)


@admin_bp.route('/message/<int:id>/toggle-lu', methods=['POST'])
@admin_required
def message_toggle_lu(id):
    msg = ContactMessage.query.get_or_404(id)
    msg.lu = not msg.lu
    db.session.commit()
    return jsonify({'status': 'ok', 'lu': msg.lu})


@admin_bp.route('/message/<int:id>/delete', methods=['POST'])
@admin_required
def message_delete(id):
    msg = ContactMessage.query.get_or_404(id)
    db.session.delete(msg)
    db.session.commit()
    flash('Message supprimé.', 'success')
    return redirect(url_for('admin.messages'))


# --- INSCRIPTIONS ---
@admin_bp.route('/inscriptions')
@admin_required
def inscriptions():
    search = request.args.get('q', '').strip()
    statut_filter = request.args.get('statut', '').strip()
    query = Inscription.query
    if statut_filter:
        query = query.filter(Inscription.statut == statut_filter)
    if search:
        query = query.filter(
            (Inscription.nom.ilike(f'%{search}%')) |
            (Inscription.nom_complet.ilike(f'%{search}%')) |
            (Inscription.telephone.ilike(f'%{search}%')) |
            (Inscription.email.ilike(f'%{search}%')) |
            (Inscription.formation.ilike(f'%{search}%')) |
            (Inscription.numero_inscription.ilike(f'%{search}%'))
        )
    inscs = query.order_by(Inscription.created_at.desc()).all()
    return render_template('admin/inscriptions.html', inscriptions=inscs, search=search, statut_filter=statut_filter)


@admin_bp.route('/inscription/<int:id>/statut', methods=['POST'])
@admin_required
def inscription_statut(id):
    insc = Inscription.query.get_or_404(id)
    new_statut = request.form.get('statut', '').strip()
    if new_statut in ['en_attente', 'validee', 'contactee', 'refusee']:
        insc.statut = new_statut
        db.session.commit()
    return redirect(url_for('admin.inscriptions', **dict(request.args)))


@admin_bp.route('/inscription/<int:id>/delete', methods=['POST'])
@admin_required
def inscription_delete(id):
    insc = Inscription.query.get_or_404(id)
    db.session.delete(insc)
    db.session.commit()
    flash('Inscription supprimée.', 'success')
    return redirect(url_for('admin.inscriptions'))


# --- PARAMETRES ---
@admin_bp.route('/parametres', methods=['GET', 'POST'])
@admin_required
def parametres():
    if request.method == 'POST':
        for key, value in request.form.items():
            if key == 'csrf_token':
                continue
            param = ParametreSite.query.filter_by(cle=key).first()
            if param:
                param.valeur = value
            else:
                db.session.add(ParametreSite(cle=key, valeur=value))
        db.session.commit()
        flash('Paramètres enregistrés !', 'success')
        return redirect(url_for('admin.parametres'))

    params = ParametreSite.query.all()
    params_dict = {p.cle: p.valeur for p in params}
    return render_template('admin/parametres.html', params=params_dict)


# --- ADMINISTRATEURS ---
@admin_bp.route('/administrateurs')
@admin_required
def administrateurs():
    if not current_user.is_super_admin:
        flash('Accès réservé au super administrateur.', 'danger')
        return redirect(url_for('admin.dashboard'))
    admins = AdminUser.query.order_by(AdminUser.created_at.desc()).all()
    return render_template('admin/administrateurs.html', admins=admins)


@admin_bp.route('/administrateur/add', methods=['POST'])
@admin_required
def administrateur_add():
    if not current_user.is_super_admin:
        flash('Accès refusé.', 'danger')
        return redirect(url_for('admin.dashboard'))

    nom = request.form.get('nom', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    role = request.form.get('role', 'administrateur')

    if AdminUser.query.filter_by(email=email).first():
        flash('Cet email est déjà utilisé.', 'danger')
        return redirect(url_for('admin.administrateurs'))

    admin = AdminUser(nom=nom, email=email, role=role)
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    flash('Administrateur ajouté.', 'success')
    return redirect(url_for('admin.administrateurs'))


@admin_bp.route('/administrateur/<int:id>/edit', methods=['POST'])
@admin_required
def administrateur_edit(id):
    if not current_user.is_super_admin:
        flash('Accès refusé.', 'danger')
        return redirect(url_for('admin.dashboard'))

    admin = AdminUser.query.get_or_404(id)
    admin.nom = request.form.get('nom', '').strip()
    admin.role = request.form.get('role', 'administrateur')
    admin.actif = request.form.get('actif') == '1'

    new_password = request.form.get('password', '').strip()
    if new_password:
        admin.set_password(new_password)

    db.session.commit()
    flash('Administrateur modifié.', 'success')
    return redirect(url_for('admin.administrateurs'))


@admin_bp.route('/administrateur/<int:id>/delete', methods=['POST'])
@admin_required
def administrateur_delete(id):
    if not current_user.is_super_admin:
        flash('Accès refusé.', 'danger')
        return redirect(url_for('admin.dashboard'))

    if id == current_user.id:
        flash('Vous ne pouvez pas supprimer votre propre compte.', 'danger')
        return redirect(url_for('admin.administrateurs'))

    admin = AdminUser.query.get_or_404(id)
    db.session.delete(admin)
    db.session.commit()
    flash('Administrateur supprimé.', 'success')
    return redirect(url_for('admin.administrateurs'))


# ========== NOTIFICATIONS PUSH ==========

@admin_bp.route('/notifications-push')
@admin_required
def notifications_push():
    subs = PushSubscription.query.order_by(PushSubscription.created_at.desc()).all()
    count = len([s for s in subs if s.actif])
    return render_template('admin/notifications.html', subs=subs, count=count)


@admin_bp.route('/api/push/subscribe', methods=['POST'])
@login_required
def push_subscribe():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Données manquantes'}), 400

    endpoint = data.get('endpoint')
    keys = data.get('keys', {})
    p256dh = keys.get('p256dh')
    auth = keys.get('auth')
    navigateur = data.get('navigateur', '?')
    plateforme = data.get('plateforme', '?')

    if not endpoint or not p256dh or not auth:
        return jsonify({'error': 'Données de souscription incomplètes'}), 400

    existing = PushSubscription.query.filter_by(endpoint=endpoint).first()
    if existing:
        existing.p256dh = p256dh
        existing.auth = auth
        existing.navigateur = navigateur
        existing.plateforme = plateforme
        existing.actif = True
        existing.admin_id = current_user.id
        existing.updated_at = datetime.utcnow()
    else:
        sub = PushSubscription(
            admin_id=current_user.id,
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth,
            navigateur=navigateur,
            plateforme=plateforme,
            actif=True,
        )
        db.session.add(sub)

    db.session.commit()
    return jsonify({'status': 'ok', 'message': 'Souscription enregistrée'})


@admin_bp.route('/api/push/unsubscribe', methods=['POST'])
@login_required
def push_unsubscribe():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Données manquantes'}), 400
    endpoint = data.get('endpoint')
    if endpoint:
        sub = PushSubscription.query.filter_by(endpoint=endpoint).first()
        if sub:
            sub.actif = False
            db.session.commit()
    return jsonify({'status': 'ok'})


@admin_bp.route('/api/push/test', methods=['POST'])
@admin_required
def push_test():
    from push_notification import send_push_to_all_admins
    sent = send_push_to_all_admins(
        title='Notification test',
        body='Ceci est une notification test depuis le panneau d\'administration LCE.',
        url='/admin',
        tag='lce-test',
        require_interaction=False,
        vibrate=[200, 50, 100],
    )
    flash(f'Notification test envoyée à {sent} appareil(s).', 'success')
    return redirect(url_for('admin.notifications_push'))


@admin_bp.route('/api/push/delete/<int:id>', methods=['POST'])
@admin_required
def push_delete(id):
    sub = PushSubscription.query.get_or_404(id)
    db.session.delete(sub)
    db.session.commit()
    flash('Souscription supprimée.', 'success')
    return redirect(url_for('admin.notifications_push'))


@admin_bp.route('/api/push/vapid-public-key')
@login_required
def push_vapid_public_key():
    return jsonify({'publicKey': current_app.config.get('VAPID_PUBLIC_KEY', '')})


@admin_bp.route('/api/notifications/stats')
@login_required
def notifications_stats():
    nouvelles_inscriptions = Inscription.query.filter(
        Inscription.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    ).count()
    nouveaux_messages = ContactMessage.query.filter_by(lu=False).count()
    return jsonify({
        'inscriptions': nouvelles_inscriptions,
        'messages': nouveaux_messages,
    })
