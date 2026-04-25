"""
Green Campus Alert Map - Flask Application Entry Point
ENREDD Batna, Algeria
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from flask            import Flask, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors        import CORS
from flask_migrate     import Migrate

from config  import config_map
from models  import db

jwt     = JWTManager()
migrate = Migrate()


def create_app(env: str = None) -> Flask:
    env = env or os.getenv('FLASK_ENV', 'development')
    app = Flask(__name__, static_folder='../frontend')
    app.config.from_object(config_map.get(env, config_map['default']))

    # ── Extensions ────────────────────────────────────────────
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    CORS(app, resources={r"/api/*": {"origins": "*"}},
         supports_credentials=True)

    # ── Logging ───────────────────────────────────────────────
    _setup_logging(app)

    # ── Blueprints ────────────────────────────────────────────
    from routes.auth       import auth_bp
    from routes.alerts     import alerts_bp
    from routes.dashboard  import dashboard_bp
    from routes.ml_routes  import ml_bp
    from routes.categories import categories_bp

    for bp in [auth_bp, alerts_bp, dashboard_bp, ml_bp, categories_bp]:
        app.register_blueprint(bp)

    # ── Static / Uploads ──────────────────────────────────────
    @app.route('/uploads/<path:filename>')
    def serve_upload(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        if path and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, 'index.html')

    # ── Error handlers ────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Resource not found'}), 404

    @app.errorhandler(422)
    def unprocessable(e):
        return jsonify({'error': 'Unprocessable entity'}), 422

    @app.errorhandler(500)
    def server_error(e):
        app.logger.error("Server Error: %s", e)
        return jsonify({'error': 'Internal server error'}), 500

    @jwt.expired_token_loader
    def expired_token_cb(jwt_header, jwt_payload):
        return jsonify({'error': 'Token has expired', 'code': 'token_expired'}), 401

    @jwt.unauthorized_loader
    def missing_token_cb(reason):
        return jsonify({'error': 'Authorization required', 'reason': reason}), 401

    # ── Health check ──────────────────────────────────────────
    @app.route('/api/health')
    def health():
        return jsonify({
            'status':  'ok',
            'campus':  app.config['CAMPUS_NAME'],
            'version': '1.0.0',
        }), 200

    app.logger.info("Green Campus Alert Map started - ENREDD Batna")
    return app


def _setup_logging(app: Flask):
    log_dir = app.config['LOG_FOLDER']
    os.makedirs(log_dir, exist_ok=True)
    handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=10 * 1024 * 1024, backupCount=5
    )
    handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    ))
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)


if __name__ == '__main__':
    application = create_app()
    with application.app_context():
        db.create_all()
    application.run(host='0.0.0.0', port=5000, debug=True)