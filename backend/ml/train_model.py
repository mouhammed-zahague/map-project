"""
ML Training Script - Green Campus Alert Map
Trains two models:
  1. Category Classifier  (text → category)
  2. Priority Predictor   (text + features → priority)
"""

import os
import sys
import pandas as pd
import numpy as np
import joblib
import json
import logging

from sklearn.model_selection    import train_test_split, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline           import Pipeline
from sklearn.linear_model       import LogisticRegression
from sklearn.ensemble           import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm                import SVC
from sklearn.naive_bayes        import MultinomialNB
from sklearn.preprocessing      import LabelEncoder
from sklearn.metrics            import (classification_report,
                                        confusion_matrix,
                                        accuracy_score)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
log = logging.getLogger(__name__)

DATASET_PATH = os.path.join(os.path.dirname(__file__), 'dataset.csv')
MODEL_DIR    = os.path.join(os.path.dirname(__file__), 'models')

KEYWORDS = {
    'Water Leak':        ['water','leak','pipe','flood','drip','wet','moisture'],
    'Energy Waste':      ['light','energy','electric','power','ac','heating','cooling'],
    'Waste Management':  ['waste','garbage','trash','bin','litter','dump','recycl'],
    'Chemical Hazard':   ['chemical','toxic','hazard','spill','fume','acid','lab'],
    'Green Space Damage':['tree','plant','garden','grass','soil','green','flower'],
    'Water Pollution':   ['sewage','contamin','algae','dirty water','oil','pollut'],
    'Air Pollution':     ['smoke','air','dust','exhaust','odor','smell','fume'],
    'Noise Pollution':   ['noise','loud','sound','disturb'],
    'Infrastructure':    ['broken','damage','crack','infrastructure','solar panel'],
    'Other':             ['general','unknown','other'],
}


def extract_features(text: str) -> dict:
    """Hand-crafted features to augment TF-IDF."""
    text_lower = text.lower()
    feats = {}
    for cat, kws in KEYWORDS.items():
        feats[f'kw_{cat.replace(" ","_")}'] = sum(k in text_lower for k in kws)
    feats['text_length']   = len(text.split())
    feats['has_urgent']    = int(any(w in text_lower for w in
                                ['urgent','critical','danger','immediately','emergency']))
    feats['has_large']     = int(any(w in text_lower for w in
                                ['large','significant','major','severe','serious']))
    return feats


def load_and_enrich(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.dropna(subset=['text', 'category', 'priority'], inplace=True)
    df['text'] = df['text'].str.strip().str.lower()
    # Augment each row with keyword-feature columns
    feat_dicts = df['text'].apply(extract_features)
    feat_df    = pd.DataFrame(feat_dicts.tolist())
    df = pd.concat([df.reset_index(drop=True), feat_df], axis=1)
    log.info("Dataset loaded: %d samples", len(df))
    log.info("Category distribution:\n%s", df['category'].value_counts())
    log.info("Priority distribution:\n%s",  df['priority'].value_counts())
    return df


def build_category_pipeline() -> Pipeline:
    return Pipeline([
        ('tfidf', TfidfVectorizer(
            ngram_range=(1, 3),
            max_features=5000,
            sublinear_tf=True,
            strip_accents='unicode',
            analyzer='word',
        )),
        ('clf', LogisticRegression(
            C=5.0,
            max_iter=1000,
            class_weight='balanced',
            solver='lbfgs',
           
        )),
    ])


def build_priority_pipeline() -> Pipeline:
    return Pipeline([
        ('tfidf', TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=3000,
            sublinear_tf=True,
        )),
        ('clf', GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=4,
            random_state=42,
        )),
    ])


def evaluate(pipeline, X_test, y_test, label: str):
    y_pred = pipeline.predict(X_test)
    acc    = accuracy_score(y_test, y_pred)
    log.info("── %s ──", label)
    log.info("Accuracy : %.4f", acc)
    log.info("Report:\n%s", classification_report(y_test, y_pred))
    return acc


def train_and_save():
    os.makedirs(MODEL_DIR, exist_ok=True)

    df  = load_and_enrich(DATASET_PATH)
    texts = df['text'].tolist()

    # ── Category model ─────────────────────────────────────
    log.info("Training CATEGORY classifier …")
    le_cat  = LabelEncoder()
    y_cat   = le_cat.fit_transform(df['category'])
    X_tr, X_te, y_tr, y_te = train_test_split(
        texts, y_cat, test_size=0.2, random_state=42, stratify=y_cat)

    cat_pipe = build_category_pipeline()
    cat_pipe.fit(X_tr, y_tr)

    cat_acc = evaluate(cat_pipe,
                       X_te, y_te,
                       "Category Classifier")

    cv_scores = cross_val_score(cat_pipe, texts, y_cat, cv=5, scoring='accuracy')
    log.info("CV scores: %s  mean=%.4f", cv_scores, cv_scores.mean())

    joblib.dump(cat_pipe, os.path.join(MODEL_DIR, 'category_classifier.pkl'))
    joblib.dump(le_cat,   os.path.join(MODEL_DIR, 'category_encoder.pkl'))

    # ── Priority model ─────────────────────────────────────
    log.info("Training PRIORITY predictor …")
    le_pri  = LabelEncoder()
    y_pri   = le_pri.fit_transform(df['priority'])
    X_tr2, X_te2, y_tr2, y_te2 = train_test_split(
        texts, y_pri, test_size=0.2, random_state=42, stratify=y_pri)

    pri_pipe = build_priority_pipeline()
    pri_pipe.fit(X_tr2, y_tr2)

    pri_acc = evaluate(pri_pipe,
                       X_te2, y_te2,
                       "Priority Predictor")

    joblib.dump(pri_pipe, os.path.join(MODEL_DIR, 'priority_predictor.pkl'))
    joblib.dump(le_pri,   os.path.join(MODEL_DIR, 'priority_encoder.pkl'))

    # ── Save metadata ──────────────────────────────────────
    meta = {
        'categories':       list(le_cat.classes_),
        'priorities':       list(le_pri.classes_),
        'category_accuracy': round(cat_acc, 4),
        'priority_accuracy': round(pri_acc, 4),
        'cv_mean':           round(float(cv_scores.mean()), 4),
        'training_samples':  len(df),
    }
    with open(os.path.join(MODEL_DIR, 'model_metadata.json'), 'w') as f:
        json.dump(meta, f, indent=2)

    log.info("All models saved to %s", MODEL_DIR)
    log.info("Category accuracy : %.4f", cat_acc)
    log.info("Priority  accuracy : %.4f", pri_acc)
    return meta


if __name__ == '__main__':
    train_and_save()