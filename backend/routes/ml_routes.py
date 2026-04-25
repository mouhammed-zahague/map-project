from flask              import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from ml.classifier      import predict_full, predict_category, predict_priority, get_model_info

ml_bp = Blueprint('ml', __name__, url_prefix='/api/ml')


@ml_bp.route('/predict', methods=['POST'])
@jwt_required()
def predict():
    data  = request.get_json() or {}
    title = data.get('title', '')
    desc  = data.get('description', '')
    if not title and not desc:
        return jsonify({'error': 'title or description required'}), 400
    result = predict_full(title, desc)
    return jsonify({'prediction': result}), 200


@ml_bp.route('/predict/category', methods=['POST'])
def predict_cat():
    data = request.get_json() or {}
    text = data.get('text', '')
    if not text:
        return jsonify({'error': 'text required'}), 400
    return jsonify(predict_category(text)), 200


@ml_bp.route('/predict/priority', methods=['POST'])
def predict_pri():
    data = request.get_json() or {}
    text = data.get('text', '')
    if not text:
        return jsonify({'error': 'text required'}), 400
    return jsonify(predict_priority(text)), 200


@ml_bp.route('/info', methods=['GET'])
def model_info():
    return jsonify(get_model_info()), 200