from flask              import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy         import func, text
from datetime           import datetime, timedelta

from models import db, Alert, User, Category, Zone

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


@dashboard_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    total     = Alert.query.count()
    reported  = Alert.query.filter_by(status='reported').count()
    validated = Alert.query.filter_by(status='validated').count()
    in_prog   = Alert.query.filter_by(status='in_progress').count()
    resolved  = Alert.query.filter_by(status='resolved').count()
    rejected  = Alert.query.filter_by(status='rejected').count()
    critical  = Alert.query.filter_by(priority='critical').count()
    high      = Alert.query.filter_by(priority='high').count()

    resolution_rate = round(resolved / total * 100, 1) if total else 0

    # Avg resolution time (hours)
    avg_res = db.session.query(
        func.avg(func.timestampdiff(
            text('HOUR'), Alert.created_at, Alert.resolved_at
        ))
    ).filter(Alert.resolved_at.isnot(None)).scalar()

    # Per category
    cats = db.session.query(
        Category.name, Category.color, Category.icon,
        func.count(Alert.id).label('count')
    ).join(Alert).group_by(Category.id).all()

    # Per zone
    zones = db.session.query(
        Zone.name, func.count(Alert.id).label('count')
    ).join(Alert).group_by(Zone.id).order_by(func.count(Alert.id).desc()).all()

    # Last 7 days daily count
    seven_days = []
    for i in range(6, -1, -1):
        d     = datetime.utcnow() - timedelta(days=i)
        start = d.replace(hour=0, minute=0, second=0, microsecond=0)
        end   = start + timedelta(days=1)
        count = Alert.query.filter(Alert.created_at >= start,
                                   Alert.created_at < end).count()
        seven_days.append({'date': start.strftime('%Y-%m-%d'), 'count': count})

    # Recent alerts
    recent = Alert.query.order_by(Alert.created_at.desc()).limit(5).all()

    return jsonify({
        'overview': {
            'total': total, 'reported': reported, 'validated': validated,
            'in_progress': in_prog, 'resolved': resolved, 'rejected': rejected,
            'critical': critical, 'high': high,
            'resolution_rate': resolution_rate,
            'avg_resolution_hours': round(float(avg_res), 1) if avg_res else 0,
        },
        'by_category': [
            {'name': c.name, 'color': c.color, 'icon': c.icon, 'count': c.count}
            for c in cats
        ],
        'by_zone': [
            {'zone': z.name, 'count': z.count} for z in zones
        ],
        'daily_trend':  seven_days,
        'recent_alerts': [a.to_dict() for a in recent],
        'total_users':  User.query.count(),
    }), 200


@dashboard_bp.route('/heatmap', methods=['GET'])
def get_heatmap():
    """Returns lat/lng weight data for heatmap overlay."""
    alerts = Alert.query.filter(Alert.status != 'rejected').all()
    weight_map = {'low': 0.3, 'medium': 0.6, 'high': 0.8, 'critical': 1.0}
    data = [
        [float(a.latitude), float(a.longitude),
         weight_map.get(a.priority, 0.5)]
        for a in alerts
    ]
    return jsonify({'heatmap_data': data}), 200