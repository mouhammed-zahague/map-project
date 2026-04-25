"""
ML Inference Module - loads models and exposes predict() helpers
"""

import os
import json
import logging
import joblib
import numpy as np

log = logging.getLogger(__name__)

MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')

_cat_pipeline  = None
_cat_encoder   = None
_pri_pipeline  = None
_pri_encoder   = None
_meta          = {}


def _load_models():
    global _cat_pipeline, _cat_encoder, _pri_pipeline, _pri_encoder, _meta
    try:
        _cat_pipeline = joblib.load(os.path.join(MODEL_DIR, 'category_classifier.pkl'))
        _cat_encoder  = joblib.load(os.path.join(MODEL_DIR, 'category_encoder.pkl'))
        _pri_pipeline = joblib.load(os.path.join(MODEL_DIR, 'priority_predictor.pkl'))
        _pri_encoder  = joblib.load(os.path.join(MODEL_DIR, 'priority_encoder.pkl'))
        meta_path = os.path.join(MODEL_DIR, 'model_metadata.json')
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                _meta = json.load(f)
        log.info("ML models loaded successfully.")
    except FileNotFoundError:
        log.warning("ML models not found. Run train_model.py first.")


_load_models()


def predict_category(text: str) -> dict:
    """
    Returns {category, confidence, all_probabilities}
    Falls back to 'Other' if models not loaded.
    """
    if _cat_pipeline is None or _cat_encoder is None:
        return {'category': 'Other', 'confidence': 0.0, 'all_probabilities': {}}

    text_clean = str(text).strip().lower()
    proba      = _cat_pipeline.predict_proba([text_clean])[0]
    idx        = int(np.argmax(proba))
    category   = _cat_encoder.inverse_transform([idx])[0]
    confidence = float(proba[idx])

    all_probs = {
        _cat_encoder.inverse_transform([i])[0]: round(float(p), 4)
        for i, p in enumerate(proba)
    }

    return {
        'category':          category,
        'confidence':        round(confidence, 4),
        'all_probabilities': all_probs,
    }


def predict_priority(text: str) -> dict:
    """
    Returns {priority, confidence}
    """
    if _pri_pipeline is None or _pri_encoder is None:
        return {'priority': 'medium', 'confidence': 0.0}

    text_clean = str(text).strip().lower()
    proba      = _pri_pipeline.predict_proba([text_clean])[0]
    idx        = int(np.argmax(proba))
    priority   = _pri_encoder.inverse_transform([idx])[0]
    confidence = float(proba[idx])

    all_probs = {
        _pri_encoder.inverse_transform([i])[0]: round(float(p), 4)
        for i, p in enumerate(proba)
    }

    return {
        'priority':          priority,
        'confidence':        round(confidence, 4),
        'all_probabilities': all_probs,
    }


def predict_full(title: str, description: str) -> dict:
    """Combined prediction from title + description."""
    combined = f"{title} {description}"
    cat_result = predict_category(combined)
    pri_result = predict_priority(combined)
    return {
        'ml_category':    cat_result['category'],
        'ml_priority':    pri_result['priority'],
        'ml_confidence':  cat_result['confidence'],
        'cat_probs':      cat_result['all_probabilities'],
        'pri_probs':      pri_result['all_probabilities'],
        'model_accuracy': _meta.get('category_accuracy', 0),
    }


def get_model_info() -> dict:
    return {
        'models_loaded':       _cat_pipeline is not None,
        'categories':          _meta.get('categories', []),
        'priorities':          _meta.get('priorities', []),
        'category_accuracy':   _meta.get('category_accuracy', 0),
        'priority_accuracy':   _meta.get('priority_accuracy', 0),
        'cv_mean':             _meta.get('cv_mean', 0),
        'training_samples':    _meta.get('training_samples', 0),
    }