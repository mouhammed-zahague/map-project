from flask              import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from models             import db, Category, Zone

categories_bp = Blueprint('categories', __name__, url_prefix='/api')


@categories_bp.route('/categories', methods=['GET'])
def get_categories():
    cats = Category.query.filter_by(is_active=True).all()
    return jsonify([c.to_dict() for c in cats]), 200


@categories_bp.route('/zones', methods=['GET'])
def get_zones():
    zones = Zone.query.all()
    return jsonify([z.to_dict() for z in zones]), 200