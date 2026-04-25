from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# ─────────────────────────────────────────────────────────────
# Role
# ─────────────────────────────────────────────────────────────
class Role(db.Model):
    __tablename__ = 'roles'
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    users       = db.relationship('User', backref='role', lazy='dynamic')

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'description': self.description}


# ─────────────────────────────────────────────────────────────
# Zone
# ─────────────────────────────────────────────────────────────
class Zone(db.Model):
    __tablename__ = 'zones'
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    color_code  = db.Column(db.String(7), default='#28a745')
    lat_center  = db.Column(db.Numeric(10, 8))
    lng_center  = db.Column(db.Numeric(11, 8))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    alerts      = db.relationship('Alert', backref='zone', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name,
            'description': self.description,
            'color_code': self.color_code,
            'lat_center': float(self.lat_center) if self.lat_center else None,
            'lng_center': float(self.lng_center) if self.lng_center else None,
        }


# ─────────────────────────────────────────────────────────────
# User
# ─────────────────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80),  nullable=False, unique=True)
    email         = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name     = db.Column(db.String(150))
    role_id       = db.Column(db.Integer, db.ForeignKey('roles.id'), default=3)
    student_id    = db.Column(db.String(20))
    department    = db.Column(db.String(100))
    phone         = db.Column(db.String(20))
    avatar_url    = db.Column(db.String(255))
    is_active     = db.Column(db.Boolean, default=True)
    last_login    = db.Column(db.DateTime)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at    = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    alerts        = db.relationship('Alert',   backref='reporter', lazy='dynamic')
    comments      = db.relationship('Comment', backref='author',   lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_sensitive=False):
        data = {
            'id': self.id, 'username': self.username,
            'full_name': self.full_name, 'email': self.email,
            'role': self.role.name if self.role else None,
            'department': self.department, 'student_id': self.student_id,
            'avatar_url': self.avatar_url, 'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if include_sensitive:
            data['phone'] = self.phone
        return data


# ─────────────────────────────────────────────────────────────
# Category
# ─────────────────────────────────────────────────────────────
class Category(db.Model):
    __tablename__ = 'categories'
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False, unique=True)
    name_ar     = db.Column(db.String(100))
    name_fr     = db.Column(db.String(100))
    description = db.Column(db.Text)
    icon        = db.Column(db.String(50))
    color       = db.Column(db.String(7), default='#28a745')
    is_active   = db.Column(db.Boolean, default=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    alerts      = db.relationship('Alert', backref='category', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name,
            'name_ar': self.name_ar, 'name_fr': self.name_fr,
            'description': self.description,
            'icon': self.icon, 'color': self.color,
            'is_active': self.is_active,
        }


# ─────────────────────────────────────────────────────────────
# Alert
# ─────────────────────────────────────────────────────────────
class Alert(db.Model):
    __tablename__ = 'alerts'
    id              = db.Column(db.Integer, primary_key=True)
    title           = db.Column(db.String(200), nullable=False)
    description     = db.Column(db.Text,        nullable=False)
    category_id     = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    zone_id         = db.Column(db.Integer, db.ForeignKey('zones.id'))
    user_id         = db.Column(db.Integer, db.ForeignKey('users.id'),      nullable=False)
    latitude        = db.Column(db.Numeric(10, 8), nullable=False)
    longitude       = db.Column(db.Numeric(11, 8), nullable=False)
    location_name   = db.Column(db.String(200))
    image_url       = db.Column(db.String(255))
    status          = db.Column(db.Enum('reported','validated','in_progress','resolved','rejected'),
                                default='reported')
    priority        = db.Column(db.Enum('low','medium','high','critical'), default='medium')
    ml_category     = db.Column(db.String(100))
    ml_priority     = db.Column(db.String(20))
    ml_confidence   = db.Column(db.Numeric(5, 4))
    severity_score  = db.Column(db.Integer, default=5)
    views_count     = db.Column(db.Integer, default=0)
    upvotes         = db.Column(db.Integer, default=0)
    is_anonymous    = db.Column(db.Boolean, default=False)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    validated_at    = db.Column(db.DateTime)
    resolved_at     = db.Column(db.DateTime)

    comments        = db.relationship('Comment',           backref='alert',  lazy='dynamic', cascade='all,delete-orphan')
    status_history  = db.relationship('AlertStatusHistory', backref='alert', lazy='dynamic', cascade='all,delete-orphan')
    images          = db.relationship('AlertImage',         backref='alert', lazy='dynamic', cascade='all,delete-orphan')

    def to_dict(self, full=False):
        data = {
            'id': self.id, 'title': self.title,
            'description': self.description,
            'status': self.status, 'priority': self.priority,
            'latitude': float(self.latitude),
            'longitude': float(self.longitude),
            'location_name': self.location_name,
            'image_url': self.image_url,
            'severity_score': self.severity_score,
            'upvotes': self.upvotes,
            'views_count': self.views_count,
            'is_anonymous': self.is_anonymous,
            'ml_category': self.ml_category,
            'ml_priority': self.ml_priority,
            'ml_confidence': float(self.ml_confidence) if self.ml_confidence else None,
            'category': self.category.to_dict() if self.category else None,
            'zone': self.zone.to_dict() if self.zone else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'comments_count': self.comments.count(),
        }
        if not self.is_anonymous:
            data['reporter'] = self.reporter.to_dict() if self.reporter else None
        if full:
            data['comments'] = [c.to_dict() for c in self.comments.order_by(
                Comment.created_at.asc()).all()]
            data['status_history'] = [h.to_dict() for h in
                self.status_history.order_by(AlertStatusHistory.created_at.asc()).all()]
        return data


# ─────────────────────────────────────────────────────────────
# AlertStatusHistory
# ─────────────────────────────────────────────────────────────
class AlertStatusHistory(db.Model):
    __tablename__ = 'alert_status_history'
    id          = db.Column(db.Integer, primary_key=True)
    alert_id    = db.Column(db.Integer, db.ForeignKey('alerts.id', ondelete='CASCADE'))
    old_status  = db.Column(db.String(20))
    new_status  = db.Column(db.String(20), nullable=False)
    changed_by  = db.Column(db.Integer, db.ForeignKey('users.id'))
    note        = db.Column(db.Text)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    changer     = db.relationship('User')

    def to_dict(self):
        return {
            'id': self.id, 'old_status': self.old_status,
            'new_status': self.new_status,
            'changed_by': self.changer.username if self.changer else None,
            'note': self.note,
            'created_at': self.created_at.isoformat(),
        }


# ─────────────────────────────────────────────────────────────
# Comment
# ─────────────────────────────────────────────────────────────
class Comment(db.Model):
    __tablename__ = 'comments'
    id          = db.Column(db.Integer, primary_key=True)
    alert_id    = db.Column(db.Integer, db.ForeignKey('alerts.id', ondelete='CASCADE'))
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'))
    content     = db.Column(db.Text, nullable=False)
    is_official = db.Column(db.Boolean, default=False)
    parent_id   = db.Column(db.Integer, db.ForeignKey('comments.id'))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'content': self.content,
            'is_official': self.is_official,
            'parent_id': self.parent_id,
            'author': self.author.to_dict() if self.author else None,
            'created_at': self.created_at.isoformat(),
        }


# ─────────────────────────────────────────────────────────────
# AlertImage
# ─────────────────────────────────────────────────────────────
class AlertImage(db.Model):
    __tablename__ = 'alert_images'
    id          = db.Column(db.Integer, primary_key=True)
    alert_id    = db.Column(db.Integer, db.ForeignKey('alerts.id', ondelete='CASCADE'))
    image_url   = db.Column(db.String(255), nullable=False)
    caption     = db.Column(db.String(200))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {'id': self.id, 'image_url': self.image_url,
                'caption': self.caption, 'uploaded_at': self.uploaded_at.isoformat()}


# ─────────────────────────────────────────────────────────────
# Notification
# ─────────────────────────────────────────────────────────────
class Notification(db.Model):
    __tablename__ = 'notifications'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'))
    alert_id    = db.Column(db.Integer, db.ForeignKey('alerts.id'))
    type        = db.Column(db.String(50), nullable=False)
    message     = db.Column(db.Text, nullable=False)
    is_read     = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    user        = db.relationship('User')
    alert_ref   = db.relationship('Alert')

    def to_dict(self):
        return {
            'id': self.id, 'type': self.type,
            'message': self.message, 'is_read': self.is_read,
            'alert_id': self.alert_id,
            'created_at': self.created_at.isoformat(),
        }