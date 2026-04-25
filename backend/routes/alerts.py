import os
import uuid
import logging
from datetime import datetime

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from werkzeug.utils import secure_filename

from models import db, Alert, Category, Zone, AlertStatusHistory, Comment, Notification
from ml.classifier import predict_full
from supabase_storage import get_storage_manager

log       = logging.getLogger(__name__)
alerts_bp = Blueprint('alerts', __name__, url_prefix='/api/alerts')

VALID_STATUSES   = ('reported', 'validated', 'in_progress', 'resolved', 'rejected')
MANAGER_ROLES    = {'admin', 'manager', 'staff'}


def allowed_file(filename: str) -> bool:
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return ext in current_app.config['ALLOWED_EXTENSIONS']


def upload_file_to_storage(file, user_id: int, feature_name: str, item_id=None) -> str | None:
    """Upload file to Supabase Storage and return the path."""
    if not file or file.filename == '':
        return None
    
    try:
        storage = get_storage_manager()
        result = storage.upload_file(
            file=file,
            user_id=user_id,
            feature_name=feature_name,
            item_id=item_id
        )
        return result['path']
    except ValueError as e:
        log.error(f"File upload error: {str(e)}")
        return None



# ─────────────────────────────────────────────────────────────
# GET /api/alerts  – list with filters
# ─────────────────────────────────────────────────────────────
@alerts_bp.route('', methods=['GET'])
def get_alerts():
    q = Alert.query

    status      = request.args.get('status')
    category_id = request.args.get('category_id', type=int)
    zone_id     = request.args.get('zone_id',     type=int)
    priority    = request.args.get('priority')
    search      = request.args.get('search')
    page        = request.args.get('page',  1,   type=int)
    per_page    = request.args.get('limit', 20,  type=int)
    sort_by     = request.args.get('sort',  'created_at')

    if status      and status      in VALID_STATUSES:   q = q.filter(Alert.status == status)
    if category_id:                                      q = q.filter(Alert.category_id == category_id)
    if zone_id:                                          q = q.filter(Alert.zone_id == zone_id)
    if priority:                                         q = q.filter(Alert.priority == priority)
    if search:
        like = f"%{search}%"
        q = q.filter(Alert.title.ilike(like) | Alert.description.ilike(like))

    sort_map = {
        'created_at': Alert.created_at.desc(),
        'priority':   Alert.severity_score.desc(),
        'upvotes':    Alert.upvotes.desc(),
        'updated_at': Alert.updated_at.desc(),
    }
    q = q.order_by(sort_map.get(sort_by, Alert.created_at.desc()))

    paginated = q.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'alerts':     [a.to_dict() for a in paginated.items],
        'total':      paginated.total,
        'page':       paginated.page,
        'pages':      paginated.pages,
        'per_page':   paginated.per_page,
        'has_next':   paginated.has_next,
        'has_prev':   paginated.has_prev,
    }), 200


# ─────────────────────────────────────────────────────────────
# GET /api/alerts/map  – all alerts lightweight (for map pins)
# ─────────────────────────────────────────────────────────────
@alerts_bp.route('/map', methods=['GET'])
def get_map_alerts():
    alerts = Alert.query.filter(Alert.status != 'rejected').all()
    return jsonify([{
        'id':           a.id,
        'title':        a.title,
        'status':       a.status,
        'priority':     a.priority,
        'latitude':     float(a.latitude),
        'longitude':    float(a.longitude),
        'location_name':a.location_name,
        'category':     a.category.to_dict() if a.category else None,
        'created_at':   a.created_at.isoformat(),
    } for a in alerts]), 200


# ─────────────────────────────────────────────────────────────
# POST /api/alerts  – create new alert
# ─────────────────────────────────────────────────────────────
@alerts_bp.route('', methods=['POST'])
@jwt_required()
def create_alert():
    user_id = get_jwt_identity()

    # Support both JSON and form-data (for file upload)
    if request.content_type and 'multipart' in request.content_type:
        data = request.form.to_dict()
        file = request.files.get('image')
    else:
        data = request.get_json() or {}
        file = None

    required = ['title', 'description', 'category_id', 'latitude', 'longitude']
    missing  = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'error': f'Missing: {", ".join(missing)}'}), 400

    try:
        lat = float(data['latitude'])
        lng = float(data['longitude'])
    except ValueError:
        return jsonify({'error': 'Invalid coordinates'}), 400

    # ML prediction
    ml = predict_full(data['title'], data['description'])

    # Create alert first without image
    alert = Alert(
        title         = data['title'].strip(),
        description   = data['description'].strip(),
        category_id   = int(data['category_id']),
        zone_id       = int(data['zone_id']) if data.get('zone_id') else None,
        user_id       = user_id,
        latitude      = lat,
        longitude     = lng,
        location_name = data.get('location_name', ''),
        image_url     = None,  # Will be set after flush
        is_anonymous  = str(data.get('is_anonymous', 'false')).lower() == 'true',
        ml_category   = ml['ml_category'],
        ml_priority   = ml['ml_priority'],
        ml_confidence = ml['ml_confidence'],
        priority      = ml['ml_priority'],   # default to ML suggestion
    )
    db.session.add(alert)
    db.session.flush()   # get alert.id

    # Upload file if provided (now we have alert.id)
    if file:
        try:
            file_path = upload_file_to_storage(
                file=file,
                user_id=user_id,
                feature_name='alerts',
                item_id=alert.id
            )
            if file_path:
                alert.image_url = file_path
        except Exception as e:
            log.error(f"Error uploading file for alert {alert.id}: {str(e)}")
            # Continue without image rather than failing the whole request

    # Initial status log
    history = AlertStatusHistory(
        alert_id   = alert.id,
        old_status = None,
        new_status = 'reported',
        changed_by = user_id,
        note       = 'Alert created',
    )
    db.session.add(history)
    db.session.commit()

    log.info("New alert #%d created by user #%d", alert.id, user_id)
    return jsonify({
        'message': 'Alert submitted successfully',
        'alert':   alert.to_dict(),
        'ml':      ml,
    }), 201


# ─────────────────────────────────────────────────────────────
# GET /api/alerts/<id>
# ─────────────────────────────────────────────────────────────
@alerts_bp.route('/<int:alert_id>', methods=['GET'])
def get_alert(alert_id):
    alert = Alert.query.get_or_404(alert_id)
    alert.views_count += 1
    db.session.commit()
    return jsonify({'alert': alert.to_dict(full=True)}), 200


# ─────────────────────────────────────────────────────────────
# POST /api/alerts/<id>/image-url  – get signed URL for alert image
# ─────────────────────────────────────────────────────────────
@alerts_bp.route('/<int:alert_id>/image-url', methods=['POST'])
def get_alert_image_url(alert_id):
    """Get signed URL for alert image (public access for viewing)."""
    alert = Alert.query.get_or_404(alert_id)

    if not alert.image_url:
        return jsonify({'error': 'Alert has no image'}), 404

    try:
        storage = get_storage_manager()
        result = storage.get_signed_url(
            file_path=alert.image_url,
            expires_in=3600  # 1 hour
        )
        return jsonify(result), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        log.error(f"Error creating signed URL: {str(e)}")
        return jsonify({'error': 'Failed to create signed URL'}), 500


# ─────────────────────────────────────────────────────────────
# POST /api/alerts/<id>/upload-image  – upload/update alert image
# ─────────────────────────────────────────────────────────────
@alerts_bp.route('/<int:alert_id>/upload-image', methods=['POST'])
@jwt_required()
def upload_alert_image(alert_id):
    """Upload or update image for an existing alert."""
    user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get('role', 'student')
    alert = Alert.query.get_or_404(alert_id)

    # Check authorization
    if alert.user_id != user_id and role not in MANAGER_ROLES:
        return jsonify({'error': 'Unauthorized'}), 403

    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']

    try:
        # Delete old image if it exists
        if alert.image_url:
            try:
                storage = get_storage_manager()
                storage.delete_file(alert.image_url)
            except Exception as e:
                log.warning(f"Could not delete old image: {str(e)}")

        # Upload new image
        file_path = upload_file_to_storage(
            file=file,
            user_id=user_id,
            feature_name='alerts',
            item_id=alert_id
        )

        if not file_path:
            return jsonify({'error': 'Failed to upload image'}), 500

        alert.image_url = file_path
        db.session.commit()

        log.info(f"Image uploaded for alert {alert_id}")
        return jsonify({
            'message': 'Image uploaded successfully',
            'image_url': alert.image_url,
            'alert': alert.to_dict()
        }), 200

    except Exception as e:
        log.error(f"Error uploading alert image: {str(e)}")
        return jsonify({'error': 'Failed to upload image'}), 500


# ─────────────────────────────────────────────────────────────
# PUT /api/alerts/<id>  – update alert (owner or admin)
# ─────────────────────────────────────────────────────────────
@alerts_bp.route('/<int:alert_id>', methods=['PUT'])
@jwt_required()
def update_alert(alert_id):
    user_id = get_jwt_identity()
    claims  = get_jwt()
    role    = claims.get('role', 'student')
    alert   = Alert.query.get_or_404(alert_id)

    if alert.user_id != user_id and role not in MANAGER_ROLES:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json() or {}
    for field in ['title', 'description', 'location_name']:
        if field in data:
            setattr(alert, field, data[field])
    if 'category_id' in data:
        alert.category_id = int(data['category_id'])
    if 'zone_id' in data:
        alert.zone_id = int(data['zone_id']) if data['zone_id'] else None

    db.session.commit()
    return jsonify({'message': 'Alert updated', 'alert': alert.to_dict()}), 200


# ─────────────────────────────────────────────────────────────
# PATCH /api/alerts/<id>/status  – change status (manager only)
# ─────────────────────────────────────────────────────────────
@alerts_bp.route('/<int:alert_id>/status', methods=['PATCH'])
@jwt_required()
def update_status(alert_id):
    user_id = get_jwt_identity()
    claims  = get_jwt()
    role    = claims.get('role', 'student')

    if role not in MANAGER_ROLES:
        return jsonify({'error': 'Insufficient permissions'}), 403

    alert  = Alert.query.get_or_404(alert_id)
    data   = request.get_json() or {}
    new_st = data.get('status')

    if new_st not in VALID_STATUSES:
        return jsonify({'error': f'Invalid status. Must be one of: {VALID_STATUSES}'}), 400

    old_st = alert.status
    alert.status = new_st

    if new_st == 'validated':
        alert.validated_at = datetime.utcnow()
    elif new_st == 'resolved':
        alert.resolved_at = datetime.utcnow()

    history = AlertStatusHistory(
        alert_id   = alert.id,
        old_status = old_st,
        new_status = new_st,
        changed_by = user_id,
        note       = data.get('note', ''),
    )
    db.session.add(history)

    # Notify reporter
    notif = Notification(
        user_id  = alert.user_id,
        alert_id = alert.id,
        type     = 'status_change',
        message  = (f'Your alert "{alert.title}" status changed '
                    f'from {old_st} to {new_st}.'),
    )
    db.session.add(notif)
    db.session.commit()

    return jsonify({'message': 'Status updated', 'alert': alert.to_dict()}), 200


# ─────────────────────────────────────────────────────────────
# POST /api/alerts/<id>/comments
# ─────────────────────────────────────────────────────────────
@alerts_bp.route('/<int:alert_id>/comments', methods=['POST'])
@jwt_required()
def add_comment(alert_id):
    user_id = get_jwt_identity()
    claims  = get_jwt()
    role    = claims.get('role', 'student')
    alert   = Alert.query.get_or_404(alert_id)
    data    = request.get_json() or {}

    if not data.get('content'):
        return jsonify({'error': 'Comment content required'}), 400

    comment = Comment(
        alert_id    = alert.id,
        user_id     = user_id,
        content     = data['content'].strip(),
        is_official = role in MANAGER_ROLES,
        parent_id   = data.get('parent_id'),
    )
    db.session.add(comment)

    # Notify alert owner
    if alert.user_id != user_id:
        notif = Notification(
            user_id  = alert.user_id,
            alert_id = alert.id,
            type     = 'new_comment',
            message  = f'New comment on your alert: "{alert.title}"',
        )
        db.session.add(notif)

    db.session.commit()
    return jsonify({'message': 'Comment added', 'comment': comment.to_dict()}), 201


# ─────────────────────────────────────────────────────────────
# POST /api/alerts/<id>/vote
# ─────────────────────────────────────────────────────────────
@alerts_bp.route('/<int:alert_id>/vote', methods=['POST'])
@jwt_required()
def vote_alert(alert_id):
    alert = Alert.query.get_or_404(alert_id)
    alert.upvotes = (alert.upvotes or 0) + 1
    db.session.commit()
    return jsonify({'upvotes': alert.upvotes}), 200


# ─────────────────────────────────────────────────────────────
# DELETE /api/alerts/<id>
# ─────────────────────────────────────────────────────────────
@alerts_bp.route('/<int:alert_id>', methods=['DELETE'])
@jwt_required()
def delete_alert(alert_id):
    user_id = get_jwt_identity()
    claims  = get_jwt()
    role    = claims.get('role', 'student')
    alert   = Alert.query.get_or_404(alert_id)

    if alert.user_id != user_id and role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    # Delete associated image from Supabase Storage
    if alert.image_url:
        try:
            storage = get_storage_manager()
            storage.delete_file(alert.image_url)
        except Exception as e:
            log.error(f"Error deleting file {alert.image_url}: {str(e)}")
            # Continue with alert deletion even if file delete fails

    db.session.delete(alert)
    db.session.commit()
    return jsonify({'message': 'Alert deleted'}), 200