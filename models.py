from extensions import db, login_manager
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class Formation(db.Model):
    __tablename__ = 'formations'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(300), nullable=True)
    prix = db.Column(db.String(100), nullable=True)
    duree = db.Column(db.String(100), nullable=True)
    categorie = db.Column(db.String(100), nullable=True)
    actif = db.Column(db.Boolean, default=True)
    ordre_affichage = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Formation {self.nom}>'


class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(200), nullable=False)
    telephone = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    lu = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Message {self.nom}>'


class Temoignage(db.Model):
    __tablename__ = 'temoignages'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(200), nullable=False)
    fonction = db.Column(db.String(200), nullable=True)
    photo = db.Column(db.String(300), nullable=True)
    contenu = db.Column(db.Text, nullable=False)
    note = db.Column(db.Integer, default=5)
    actif = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Temoignage {self.nom}>'


class Inscription(db.Model):
    __tablename__ = 'inscriptions'
    id = db.Column(db.Integer, primary_key=True)
    # Anciens champs
    nom = db.Column(db.String(200), nullable=False)
    prenom = db.Column(db.String(200), nullable=True)
    telephone = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(200), nullable=True)
    formation = db.Column(db.String(200), nullable=True)
    statut = db.Column(db.String(50), default='en_attente')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Nouveaux champs - formulaire complet
    nom_complet = db.Column(db.String(300), nullable=True)
    date_naissance = db.Column(db.String(20), nullable=True)
    sexe = db.Column(db.String(20), nullable=True)
    nationalite = db.Column(db.String(100), nullable=True)
    adresse = db.Column(db.Text, nullable=True)
    ville = db.Column(db.String(200), nullable=True)
    whatsapp = db.Column(db.String(50), nullable=True)
    formation_id = db.Column(db.Integer, db.ForeignKey('formations.id'), nullable=True)
    niveau_etude = db.Column(db.String(50), nullable=True)
    situation_professionnelle = db.Column(db.String(50), nullable=True)
    photo = db.Column(db.String(300), nullable=True)
    piece_identite = db.Column(db.String(300), nullable=True)
    cv = db.Column(db.String(300), nullable=True)
    commentaire = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Nouveaux champs - système d'inscription
    numero_inscription = db.Column(db.String(50), unique=True, nullable=True)
    qr_code = db.Column(db.String(300), nullable=True)
    pdf_recu = db.Column(db.String(300), nullable=True)
    confirmation_envoyee = db.Column(db.Boolean, default=False)
    date_confirmation = db.Column(db.DateTime, nullable=True)
    # Relation
    formation_ref = db.relationship('Formation', foreign_keys=[formation_id])

    def __repr__(self):
        return f'<Inscription {self.nom or self.nom_complet}>'


class Galerie(db.Model):
    __tablename__ = 'galerie'
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=True)
    image = db.Column(db.String(300), nullable=False)
    categorie = db.Column(db.String(100), default='general')
    description = db.Column(db.Text, nullable=True)
    actif = db.Column(db.Boolean, default=True)
    ordre = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Galerie {self.titre or self.image}>'


class Equipe(db.Model):
    __tablename__ = 'equipe'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(200), nullable=False)
    fonction = db.Column(db.String(200), nullable=False)
    photo = db.Column(db.String(300), nullable=True)
    description = db.Column(db.Text, nullable=True)
    ordre = db.Column(db.Integer, default=0)
    actif = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Equipe {self.nom}>'


class Video(db.Model):
    __tablename__ = 'videos'
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    miniature = db.Column(db.String(300), nullable=True)
    url_video = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=True)
    actif = db.Column(db.Boolean, default=True)
    ordre = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Video {self.titre}>'


class ParametreSite(db.Model):
    __tablename__ = 'parametres_site'
    id = db.Column(db.Integer, primary_key=True)
    cle = db.Column(db.String(100), unique=True, nullable=False)
    valeur = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Parametre {self.cle}>'


class Statistique(db.Model):
    __tablename__ = 'statistiques'
    id = db.Column(db.Integer, primary_key=True)
    cle = db.Column(db.String(100), unique=True, nullable=False)
    valeur = db.Column(db.String(200), nullable=False)
    icone = db.Column(db.String(200), nullable=True)
    ordre = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<Statistique {self.cle}>'


class AdminUser(UserMixin, db.Model):
    __tablename__ = 'admin_users'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(300), nullable=False)
    role = db.Column(db.String(50), default='administrateur')
    actif = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_super_admin(self):
        return self.role == 'super_admin'

    def __repr__(self):
        return f'<AdminUser {self.email}>'


@login_manager.user_loader
def load_user(user_id):
    return AdminUser.query.get(int(user_id))


class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(200), nullable=False)
    telephone = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    sujet = db.Column(db.String(300), nullable=True)
    message = db.Column(db.Text, nullable=False)
    lu = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ContactMessage {self.nom}>'


class PushSubscription(db.Model):
    __tablename__ = 'push_subscriptions'
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=True)
    endpoint = db.Column(db.Text, nullable=False)
    p256dh = db.Column(db.Text, nullable=False)
    auth = db.Column(db.Text, nullable=False)
    navigateur = db.Column(db.String(200), nullable=True)
    plateforme = db.Column(db.String(200), nullable=True)
    actif = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    admin = db.relationship('AdminUser', backref=db.backref('push_subscriptions', lazy=True))

    def __repr__(self):
        return f'<PushSubscription {self.plateforme} - {self.navigateur}>'
