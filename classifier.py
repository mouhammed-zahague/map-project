"""
Green Campus Alert Map — Module de Classification ML
ENSSRESD Batna, Algérie

Objectif: Classifier automatiquement les alertes environnementales
selon la catégorie (eau, énergie, déchets, espaces verts, pollution)
et prédire leur niveau de priorité (haute, moyenne, faible).

Modèle: Régression logistique + TF-IDF (scikit-learn)
Dataset: Alertes synthétiques en français/arabe/darija
"""

import json
import pickle
import os
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multioutput import MultiOutputClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder


# ═══════════════════════════════════════════════════════════════════════════════
# DATASET — Alertes d'entraînement (campus ENSSRESD Batna)
# ═══════════════════════════════════════════════════════════════════════════════

TRAINING_DATA = [
    # ── EAU (water) ──
    {"text": "fuite d'eau importante tuyau labo laboratoire robinet coule", "category": "water", "priority": "high"},
    {"text": "robinet ouvert gaspillage eau cafétéria sanitaires", "category": "water", "priority": "medium"},
    {"text": "tuyauterie cassée inondation salle cours eau partout", "category": "water", "priority": "high"},
    {"text": "eau stagnante flaque humidité moisissure couloir", "category": "water", "priority": "medium"},
    {"text": "fuite toiture pluie infiltration bâtiment", "category": "water", "priority": "medium"},
    {"text": "robinet cassé coulant nuit gaspillage eau potable", "category": "water", "priority": "high"},
    {"text": "chauffe eau défectueux fuite vapeur danger", "category": "water", "priority": "high"},
    {"text": "fontaine eau cassée inutilisable étudiants soif", "category": "water", "priority": "low"},
    {"text": "tuyau percé jardin irrigation eau gaspillée", "category": "water", "priority": "medium"},
    {"text": "سرب ماء مكسور تدفق مستمر هدر", "category": "water", "priority": "high"},
    {"text": "toilettes inondées overflow débordement sanitaires", "category": "water", "priority": "high"},
    {"text": "vanne ouverte nuit personne gaspillage eau piscine", "category": "water", "priority": "medium"},

    # ── ÉNERGIE (energy) ──
    {"text": "lumières allumées nuit salle vide gaspillage énergie électricité", "category": "energy", "priority": "medium"},
    {"text": "climatiseur chauffage simultané énergie gâchée bureau", "category": "energy", "priority": "low"},
    {"text": "panneau solaire cassé fissuré production réduite", "category": "energy", "priority": "high"},
    {"text": "prise défectueuse court circuit danger électrique", "category": "energy", "priority": "high"},
    {"text": "ampoules grillées remplacement nécessaire couloir sombre", "category": "energy", "priority": "low"},
    {"text": "ordinateurs laissés allumés week-end gaspillage électricité", "category": "energy", "priority": "low"},
    {"text": "câble électrique nu dangereux sol risque électrocution", "category": "energy", "priority": "high"},
    {"text": "compteur électrique défaillant surchauffe risque incendie", "category": "energy", "priority": "high"},
    {"text": "éclairage extérieur allumé jour capteur panne gaspillage", "category": "energy", "priority": "medium"},
    {"text": "générateur fume bruit anormal problème mécanique énergie", "category": "energy", "priority": "high"},
    {"text": "الإضاءة مفتوحة طوال الليل هدر كهرباء", "category": "energy", "priority": "medium"},
    {"text": "tableau électrique surchauffe odeur brûlé danger", "category": "energy", "priority": "high"},

    # ── DÉCHETS (waste) ──
    {"text": "déchets sauvages poubelles débordantes ordures traîner", "category": "waste", "priority": "high"},
    {"text": "bac recyclage plein non vidé cartons papiers", "category": "waste", "priority": "medium"},
    {"text": "poubelles non triées déchets mélangés recyclable ordures", "category": "waste", "priority": "medium"},
    {"text": "déchets chimiques laboratoire mal stockés danger", "category": "waste", "priority": "high"},
    {"text": "papiers jetés sol propreté campus nettoyage", "category": "waste", "priority": "low"},
    {"text": "conteneur déchets renversé vent détritus éparpillés", "category": "waste", "priority": "medium"},
    {"text": "odeur forte poubelles décomposition chaleur insectes", "category": "waste", "priority": "high"},
    {"text": "déchets électroniques abandonnés vieux ordinateurs écrans", "category": "waste", "priority": "medium"},
    {"text": "النفايات متناثرة في الفناء قمامة", "category": "waste", "priority": "medium"},
    {"text": "déchets plastiques brûlés fumée noire toxique", "category": "waste", "priority": "high"},
    {"text": "bennes non collectées depuis semaine odeur nauséabonde", "category": "waste", "priority": "high"},
    {"text": "restes nourriture cafétéria animaux rongeurs hygiène", "category": "waste", "priority": "high"},

    # ── ESPACES VERTS (green) ──
    {"text": "arbres non entretenus branches tombent danger étudiants", "category": "green", "priority": "high"},
    {"text": "pelouse sèche arrosage insuffisant espace vert mort", "category": "green", "priority": "low"},
    {"text": "fleurs arrachées vandales jardins dégradés espaces verts", "category": "green", "priority": "medium"},
    {"text": "plantes envahissantes herbes mauvaises envahissent allées", "category": "green", "priority": "low"},
    {"text": "arbre malade champignons risque chute dangereux", "category": "green", "priority": "high"},
    {"text": "bancs cassés espaces verts mobilier urbain dégradé", "category": "green", "priority": "medium"},
    {"text": "plantation morte manque eau entretien espaces verts", "category": "green", "priority": "low"},
    {"text": "allée verte bloquée branches taille nécessaire passage", "category": "green", "priority": "medium"},
    {"text": "الأشجار لم تقلم منذ فترة طويلة خطر السقوط", "category": "green", "priority": "medium"},
    {"text": "espace vert squatté voitures garées herbe abîmée", "category": "green", "priority": "medium"},
    {"text": "insectes nuisibles plantes malades traitement nécessaire", "category": "green", "priority": "medium"},

    # ── POLLUTION ──
    {"text": "huile moteur déversée parking contamination sol dangereux", "category": "pollution", "priority": "high"},
    {"text": "fumée noire voiture parking mauvaises odeurs air", "category": "pollution", "priority": "medium"},
    {"text": "bruit excessif travaux construction nuisance sonore cours", "category": "pollution", "priority": "medium"},
    {"text": "produits chimiques laboratoire odeur forte irritante", "category": "pollution", "priority": "high"},
    {"text": "air conditionné fuit fluide frigorigène pollution atmosphérique", "category": "pollution", "priority": "high"},
    {"text": "peinture murs émanations toxiques ventilation insuffisante", "category": "pollution", "priority": "medium"},
    {"text": "poussière chantier voisin air pollué masques nécessaires", "category": "pollution", "priority": "medium"},
    {"text": "égout débordant odeur fétide contamination eau sol", "category": "pollution", "priority": "high"},
    {"text": "التلوث الصوتي بسبب الأشغال ضوضاء", "category": "pollution", "priority": "medium"},
    {"text": "lumière parasite éclairage nocturne pollue obscurité", "category": "pollution", "priority": "low"},
    {"text": "détergents chimiques évacuation directe sol pollution eau", "category": "pollution", "priority": "high"},
    {"text": "fumée cigarette interdite espaces non fumeurs intérieur", "category": "pollution", "priority": "low"},
]


# ═══════════════════════════════════════════════════════════════════════════════
# MODÈLE ML
# ═══════════════════════════════════════════════════════════════════════════════

class GreenCampusClassifier:
    """
    Classificateur d'alertes environnementales pour campus universitaire.
    
    Pipeline: TF-IDF → Régression Logistique Multisorties
    - Sortie 1: Catégorie (water, energy, waste, green, pollution)
    - Sortie 2: Priorité (high, medium, low)
    """

    CATEGORIES = ['water', 'energy', 'waste', 'green', 'pollution']
    PRIORITIES = ['high', 'medium', 'low']
    MODEL_PATH = './ml/model.pkl'

    def __init__(self):
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                analyzer='word',
                ngram_range=(1, 2),
                max_features=3000,
                min_df=1,
                strip_accents='unicode',
                lowercase=True
            )),
            ('clf', MultiOutputClassifier(
                LogisticRegression(
                    C=2.0,
                    max_iter=500,
                    solver='lbfgs',
                    class_weight='balanced',
                    random_state=42
                )
            ))
        ])
        self.le_cat = LabelEncoder()
        self.le_prio = LabelEncoder()
        self.is_trained = False

    def train(self, data=None):
        """Entraîner le modèle sur le dataset fourni ou les données par défaut."""
        if data is None:
            data = TRAINING_DATA

        df = pd.DataFrame(data)
        X = df['text']
        y_cat = self.le_cat.fit_transform(df['category'])
        y_prio = self.le_prio.fit_transform(df['priority'])
        Y = np.column_stack([y_cat, y_prio])

        X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42, stratify=y_cat)

        self.pipeline.fit(X_train, Y_train)
        Y_pred = self.pipeline.predict(X_test)
        self.is_trained = True

        # Métriques
        acc_cat = accuracy_score(Y_test[:, 0], Y_pred[:, 0])
        acc_prio = accuracy_score(Y_test[:, 1], Y_pred[:, 1])

        print(f"\n✅ Modèle entraîné avec succès")
        print(f"📊 Précision catégorie: {acc_cat:.1%}")
        print(f"📊 Précision priorité:  {acc_prio:.1%}")
        print(f"📈 Données: {len(X_train)} entraînement / {len(X_test)} test\n")
        print("─── Rapport Catégories ───")
        print(classification_report(
            Y_test[:, 0], Y_pred[:, 0],
            target_names=self.le_cat.classes_
        ))
        return {'accuracy_category': acc_cat, 'accuracy_priority': acc_prio}

    def predict(self, text: str) -> dict:
        """
        Classer un texte d'alerte.
        
        Returns:
            {
                "category": "water",
                "priority": "high",
                "confidence": 87.5,
                "probabilities": {...}
            }
        """
        if not self.is_trained:
            raise RuntimeError("Modèle non entraîné. Appelez train() d'abord.")

        proba = self.pipeline.predict_proba([text])
        cat_proba = proba[0][0]
        prio_proba = proba[1][0]

        cat_idx = cat_proba.argmax()
        prio_idx = prio_proba.argmax()

        category = self.le_cat.inverse_transform([cat_idx])[0]
        priority = self.le_prio.inverse_transform([prio_idx])[0]
        confidence = round(float(cat_proba[cat_idx]) * 100, 1)

        return {
            "category": category,
            "priority": priority,
            "confidence": confidence,
            "category_probabilities": {
                cls: round(float(p) * 100, 1)
                for cls, p in zip(self.le_cat.classes_, cat_proba)
            },
            "priority_probabilities": {
                cls: round(float(p) * 100, 1)
                for cls, p in zip(self.le_prio.classes_, prio_proba)
            }
        }

    def save(self, path=None):
        """Sauvegarder le modèle entraîné."""
        path = path or self.MODEL_PATH
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump(self, f)
        print(f"💾 Modèle sauvegardé: {path}")

    @classmethod
    def load(cls, path=None):
        """Charger un modèle sauvegardé."""
        path = path or cls.MODEL_PATH
        if not os.path.exists(path):
            raise FileNotFoundError(f"Modèle introuvable: {path}")
        with open(path, 'rb') as f:
            return pickle.load(f)


# ─── API Flask (optionnel) ────────────────────────────────────────────────────
def create_api():
    """Serveur Flask pour exposer le classifieur ML en API REST."""
    try:
        from flask import Flask, request, jsonify
    except ImportError:
        print("Flask non installé. pip install flask")
        return

    api = Flask(__name__)
    classifier = None

    @api.route('/health')
    def health():
        return jsonify({"status": "ok", "model_ready": classifier is not None and classifier.is_trained})

    @api.route('/classify', methods=['POST'])
    def classify():
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "Champ 'text' requis"}), 400
        try:
            result = classifier.predict(data['text'])
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @api.route('/retrain', methods=['POST'])
    def retrain():
        data = request.get_json() or {}
        new_samples = data.get('samples', [])
        all_data = TRAINING_DATA + new_samples
        metrics = classifier.train(all_data)
        classifier.save()
        return jsonify({"message": "Modèle ré-entraîné", "metrics": metrics})

    return api, classifier


# ─── Script principal ─────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("🌿 Green Campus ML Classifier")
    print("📍 ENSSRESD Batna — Module d'apprentissage automatique\n")

    # 1. Créer et entraîner le modèle
    clf = GreenCampusClassifier()
    metrics = clf.train()

    # 2. Tester avec des exemples
    test_cases = [
        "Le robinet de la salle de bain du labo 3 fuit abondamment depuis hier soir",
        "Les lampes du couloir restent allumées 24h/24 personne ne les éteint",
        "Des déchets ont été jetés illégalement derrière la cafétéria ça sent mauvais",
        "L'arbre à l'entrée principale menace de tomber sur les étudiants",
        "Déversement d'huile dans le parking contamination grave du sol",
    ]

    print("\n─── Tests de classification ───")
    for text in test_cases:
        result = clf.predict(text)
        icon = {'water':'💧','energy':'⚡','waste':'🗑️','green':'🌳','pollution':'☁️'}.get(result['category'],'❓')
        prio_icon = {'high':'🔴','medium':'🟡','low':'🟢'}.get(result['priority'],'⚪')
        print(f"{icon} [{result['category']:10}] {prio_icon} [{result['priority']:6}] ({result['confidence']:5.1f}%) → {text[:60]}...")

    # 3. Sauvegarder
    clf.save()
    print(f"\n✅ Modèle prêt à l'emploi.")
    print(f"📌 Utilisation: clf = GreenCampusClassifier.load(); clf.predict('votre texte')")
