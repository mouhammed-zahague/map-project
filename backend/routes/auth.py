from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from datetime import datetime
import logging
from models import db, User, Role, Notification
from supabase_storage import get_storage_manager

log = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    required = ['username', 'email', 'password', 'full_name']
    missing  = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'error': f'Missing fields: {", ".join(missing)}'}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already taken'}), 409
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409

    student_role = Role.query.filter_by(name='student').first()
    user = User(
        username   = data['username'],
        email      = data['email'],
        full_name  = data['full_name'],
        role_id    = student_role.id if student_role else 3,
        student_id = data.get('student_id'),
        department = data.get('department'),
        phone      = data.get('phone'),
    )
    user.set_password(data['password'])

    db.session.add(user)
    db.session.commit()

    # Welcome notification
    notif = Notification(
        user_id  = user.id,
        type     = 'welcome',
        message  = f'Welcome to Green Campus Alert Map, {user.full_name}!'
    )
    db.session.add(notif)
    db.session.commit()

    tokens = _generate_tokens(user)
    return jsonify({
        'message': 'Registration successful',
        'user':    user.to_dict(),
        **tokens
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    identifier = data.get('username') or data.get('email')
    password   = data.get('password')

    if not identifier or not password:
        return jsonify({'error': 'Username/email and password required'}), 400

    user = (User.query.filter_by(username=identifier).first() or
            User.query.filter_by(email=identifier).first())

    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid credentials'}), 401
    if not user.is_active:
        return jsonify({'error': 'Account deactivated. Contact admin.'}), 403

    user.last_login = datetime.utcnow()
    db.session.commit()

    tokens = _generate_tokens(user)
    return jsonify({
        'message': 'Login successful',
        'user':    user.to_dict(),
        **tokens
    }), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    user    = User.query.get(user_id)
    if not user or not user.is_active:
        return jsonify({'error': 'User not found'}), 404
    token = create_access_token(identity=user_id,
                                additional_claims={'role': user.role.name})
    return jsonify({'access_token': token}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    user_id = get_jwt_identity()
    user    = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'user': user.to_dict(include_sensitive=True)}), 200


@auth_bp.route('/change-password', methods=['PUT'])
@jwt_required()
def change_password():
    user_id  = get_jwt_identity()
    user     = User.query.get(user_id)
    data     = request.get_json() or {}
    old_pass = data.get('old_password')
    new_pass = data.get('new_password')

    if not old_pass or not new_pass:
        return jsonify({'error': 'old_password and new_password required'}), 400
    if not user.check_password(old_pass):
        return jsonify({'error': 'Current password is incorrect'}), 403
    if len(new_pass) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    user.set_password(new_pass)
    db.session.commit()
    return jsonify({'message': 'Password changed successfully'}), 200


# ─────────────────────────────────────────────────────────────
# POST /api/auth/avatar  – upload user avatar
# ─────────────────────────────────────────────────────────────
@auth_bp.route('/avatar', methods=['POST'])
@jwt_required()
def upload_avatar():
    """Upload or update user avatar."""
    user_id = get_jwt_identity()
    user    = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if 'avatar' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['avatar']

    try:
        # Delete old avatar if it exists
        if user.avatar_url:
            try:
                storage = get_storage_manager()
                storage.delete_file(user.avatar_url)
            except Exception as e:
                log.warning(f"Could not delete old avatar: {str(e)}")

        # Upload new avatar
        storage = get_storage_manager()
        result = storage.upload_file(
            file=file,
            user_id=user_id,
            feature_name='profile'
        )

        user.avatar_url = result['path']
        db.session.commit()

        log.info(f"Avatar uploaded for user {user_id}")
        return jsonify({
            'message': 'Avatar uploaded successfully',
            'avatar_url': user.avatar_url
        }), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        log.error(f"Error uploading avatar: {str(e)}")
        return jsonify({'error': 'Failed to upload avatar'}), 500


# ─────────────────────────────────────────────────────────────
# DELETE /api/auth/avatar  – delete user avatar
# ─────────────────────────────────────────────────────────────
@auth_bp.route('/avatar', methods=['DELETE'])
@jwt_required()
def delete_avatar():
    """Delete user avatar."""
    user_id = get_jwt_identity()
    user    = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if not user.avatar_url:
        return jsonify({'error': 'No avatar to delete'}), 404

    try:
        storage = get_storage_manager()
        storage.delete_file(user.avatar_url)

        user.avatar_url = None
        db.session.commit()

        log.info(f"Avatar deleted for user {user_id}")
        return jsonify({'message': 'Avatar deleted successfully'}), 200

    except Exception as e:
        log.error(f"Error deleting avatar: {str(e)}")
        return jsonify({'error': 'Failed to delete avatar'}), 500


# ─────────────────────────────────────────────────────────────
# POST /api/auth/signed-url  – get signed URL for a file
# ─────────────────────────────────────────────────────────────
@auth_bp.route('/signed-url', methods=['POST'])
@jwt_required()
def get_signed_url():
    """Generate a signed URL for accessing a private file."""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    file_path = data.get('file_path')

    if not file_path:
        return jsonify({'error': 'file_path required'}), 400

    # Verify user owns the file (path starts with user_id)
    if not file_path.startswith(f"{user_id}/"):
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        storage = get_storage_manager()
        result = storage.get_signed_url(
            file_path=file_path,
            expires_in=3600  # 1 hour
        )
        return jsonify(result), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        log.error(f"Error creating signed URL: {str(e)}")
        return jsonify({'error': 'Failed to create signed URL'}), 500


# ─────────────────────────────────────────────────────────────
# POST /api/auth/delete-file  – delete a file from storage
# ─────────────────────────────────────────────────────────────
@auth_bp.route('/delete-file', methods=['POST'])
@jwt_required()
def delete_file():
    """Delete a file from Supabase Storage."""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    file_path = data.get('file_path')

    if not file_path:
        return jsonify({'error': 'file_path required'}), 400

    # Verify user owns the file (path starts with user_id)
    if not file_path.startswith(f"{user_id}/"):
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        storage = get_storage_manager()
        success = storage.delete_file(file_path)

        if success:
            return jsonify({'message': 'File deleted successfully'}), 200
        else:
            return jsonify({'error': 'File not found or already deleted'}), 404

    except Exception as e:
        log.error(f"Error deleting file: {str(e)}")
        return jsonify({'error': 'Failed to delete file'}), 500


# ── Helper ────────────────────────────────────────────────────
def _generate_tokens(user: User) -> dict:
    claims = {'role': user.role.name, 'username': user.username}
    return {
        'access_token':  create_access_token(identity=user.id,
                                             additional_claims=claims),
        'refresh_token': create_refresh_token(identity=user.id),
    }