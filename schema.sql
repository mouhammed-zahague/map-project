-- ═══════════════════════════════════════════════════════════════════════════
-- GREEN CAMPUS ALERT MAP — Schéma de Base de Données
-- ENSSRESD Batna, Algérie
-- SGBD: SQLite (ou MySQL/PostgreSQL compatible avec ajustements mineurs)
-- ═══════════════════════════════════════════════════════════════════════════

PRAGMA foreign_keys = ON;

-- ─── TABLE: users ─────────────────────────────────────────────────────────────
-- Gestion des utilisateurs et rôles
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    full_name       TEXT NOT NULL,
    email           TEXT UNIQUE,
    role            TEXT NOT NULL DEFAULT 'student'
                    CHECK(role IN ('admin','staff','student')),
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ─── TABLE: categories ────────────────────────────────────────────────────────
-- Catégories des problèmes environnementaux
CREATE TABLE IF NOT EXISTS categories (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    slug    TEXT NOT NULL UNIQUE,
    name    TEXT NOT NULL,
    name_ar TEXT,                     -- Traduction arabe
    icon    TEXT NOT NULL,
    color   TEXT NOT NULL DEFAULT '#2db362'
);

-- ─── TABLE: zones ─────────────────────────────────────────────────────────────
-- Zones et bâtiments du campus ENSSRESD
CREATE TABLE IF NOT EXISTS zones (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    slug        TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    description TEXT,
    latitude    REAL,
    longitude   REAL,
    area_type   TEXT CHECK(area_type IN ('building','outdoor','parking','green','other'))
);

-- ─── TABLE: alerts ────────────────────────────────────────────────────────────
-- Alertes environnementales (table centrale)
CREATE TABLE IF NOT EXISTS alerts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT NOT NULL,
    description     TEXT NOT NULL,
    category_id     INTEGER NOT NULL REFERENCES categories(id),
    zone_id         INTEGER NOT NULL REFERENCES zones(id),
    latitude        REAL,
    longitude       REAL,
    priority        TEXT NOT NULL DEFAULT 'medium'
                    CHECK(priority IN ('high','medium','low')),
    status          TEXT NOT NULL DEFAULT 'reported'
                    CHECK(status IN ('reported','validated','in_progress','resolved')),
    user_id         INTEGER NOT NULL REFERENCES users(id),
    image_path      TEXT,               -- Chemin vers la photo uploadée
    ai_priority     TEXT,               -- Priorité suggérée par l'IA
    ai_confidence   REAL,               -- Confiance de l'IA (0-100)
    views           INTEGER DEFAULT 0,
    resolved_at     TEXT,               -- Horodatage de résolution
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ─── TABLE: comments ──────────────────────────────────────────────────────────
-- Commentaires et mises à jour sur les alertes
CREATE TABLE IF NOT EXISTS comments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id    INTEGER NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    content     TEXT NOT NULL,
    is_official INTEGER DEFAULT 0,   -- 1 si commentaire officiel admin/staff
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ─── TABLE: alert_history ─────────────────────────────────────────────────────
-- Historique des changements de statut (audit trail)
CREATE TABLE IF NOT EXISTS alert_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id    INTEGER NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    old_status  TEXT,
    new_status  TEXT,
    old_priority TEXT,
    new_priority TEXT,
    note        TEXT,
    changed_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ─── TABLE: ai_classifications ────────────────────────────────────────────────
-- Résultats de classification IA (historique ML)
CREATE TABLE IF NOT EXISTS ai_classifications (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id        INTEGER REFERENCES alerts(id) ON DELETE CASCADE,
    input_text      TEXT NOT NULL,
    predicted_cat   TEXT NOT NULL,
    predicted_prio  TEXT NOT NULL,
    confidence      REAL,
    model_version   TEXT DEFAULT 'claude-sonnet-v1',
    processing_ms   INTEGER,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ─── TABLE: notifications ─────────────────────────────────────────────────────
-- Système de notifications utilisateurs
CREATE TABLE IF NOT EXISTS notifications (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    alert_id    INTEGER REFERENCES alerts(id) ON DELETE SET NULL,
    message     TEXT NOT NULL,
    type        TEXT DEFAULT 'info' CHECK(type IN ('info','warning','success','error')),
    is_read     INTEGER DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════════════════════════════════════════════
-- INDEX pour performances
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_category ON alerts(category_id);
CREATE INDEX IF NOT EXISTS idx_alerts_zone ON alerts(zone_id);
CREATE INDEX IF NOT EXISTS idx_alerts_user ON alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_priority ON alerts(priority);
CREATE INDEX IF NOT EXISTS idx_comments_alert ON comments(alert_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, is_read);

-- ═══════════════════════════════════════════════════════════════════════════════
-- DONNÉES INITIALES (seed data)
-- ═══════════════════════════════════════════════════════════════════════════════

-- Catégories
INSERT OR IGNORE INTO categories (slug, name, name_ar, icon, color) VALUES
    ('water',     'Eau',           'الماء',           '💧', '#1565c0'),
    ('energy',    'Énergie',       'الطاقة',          '⚡', '#e67e00'),
    ('waste',     'Déchets',       'النفايات',        '🗑️', '#7b1fa2'),
    ('green',     'Espaces verts', 'المساحات الخضراء','🌳', '#2e7d32'),
    ('pollution', 'Pollution',     'التلوث',          '☁️', '#795548');

-- Zones campus ENSSRESD Batna (coordonnées approximatives)
INSERT OR IGNORE INTO zones (slug, name, description, latitude, longitude, area_type) VALUES
    ('batiment_a',    'Bâtiment A – Administration', 'Direction, bureau du personnel, salle des réunions', 35.5551, 6.1747, 'building'),
    ('batiment_b',    'Bâtiment B – Laboratoires',   'Laboratoires de recherche, salles TP',               35.5561, 6.1754, 'building'),
    ('batiment_c',    'Bâtiment C – Pédagogique',    'Amphithéâtres, salles de cours',                     35.5548, 6.1734, 'building'),
    ('bibliotheque',  'Bibliothèque',                 'Centre de documentation et d''apprentissage',        35.5554, 6.1739, 'building'),
    ('cafeteria',     'Cafétéria',                    'Restaurant universitaire',                           35.5545, 6.1732, 'building'),
    ('parking',       'Parking',                      'Zone de stationnement véhicules',                   35.5541, 6.1760, 'parking'),
    ('espaces_verts', 'Espaces verts',                'Jardins, pelouses, zone de détente',                35.5568, 6.1737, 'green'),
    ('terrain_sport', 'Terrain de sport',             'Terrains de basketball, football, jogging',         35.5571, 6.1762, 'outdoor'),
    ('entree',        'Entrée principale',            'Accueil, gardiennage, portail',                     35.5533, 6.1742, 'other');

-- Utilisateurs par défaut (mots de passe hashés avec bcrypt)
-- admin123 / pass123 — CHANGER EN PRODUCTION !
INSERT OR IGNORE INTO users (username, password_hash, full_name, email, role) VALUES
    ('admin',     '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy', 'Dr. Amina Bensalem',      'admin@enssresd.dz',     'admin'),
    ('etudiant1', '$2a$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'Mohamed Amine Bouali',   'm.bouali@enssresd.dz',  'student'),
    ('etudiant2', '$2a$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'Sara Khettab',           's.khettab@enssresd.dz', 'student'),
    ('staff1',    '$2a$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'Karim Hadj Ali',         'k.hadjali@enssresd.dz', 'staff'),
    ('staff2',    '$2a$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'Fatima Zahra Touati',    'f.touati@enssresd.dz',  'staff');

-- ═══════════════════════════════════════════════════════════════════════════════
-- VUES UTILES (pour rapports et statistiques)
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE VIEW IF NOT EXISTS v_alerts_full AS
SELECT
    a.id, a.title, a.description, a.priority, a.status,
    a.latitude, a.longitude, a.image_path,
    a.ai_priority, a.ai_confidence,
    a.created_at, a.updated_at, a.resolved_at,
    c.slug AS category_slug, c.name AS category_name, c.icon AS category_icon,
    z.slug AS zone_slug, z.name AS zone_name,
    u.username, u.full_name AS reporter_name, u.role AS reporter_role,
    (SELECT COUNT(*) FROM comments WHERE alert_id = a.id) AS comment_count
FROM alerts a
JOIN categories c ON a.category_id = c.id
JOIN zones z ON a.zone_id = z.id
JOIN users u ON a.user_id = u.id;

CREATE VIEW IF NOT EXISTS v_stats_summary AS
SELECT
    (SELECT COUNT(*) FROM alerts) AS total_alerts,
    (SELECT COUNT(*) FROM alerts WHERE status = 'reported') AS pending,
    (SELECT COUNT(*) FROM alerts WHERE status = 'in_progress') AS in_progress,
    (SELECT COUNT(*) FROM alerts WHERE status = 'resolved') AS resolved,
    (SELECT COUNT(*) FROM alerts WHERE priority = 'high' AND status != 'resolved') AS high_priority_open,
    (SELECT COUNT(*) FROM users) AS total_users,
    (SELECT ROUND(AVG(julianday(resolved_at) - julianday(created_at)), 1)
     FROM alerts WHERE status = 'resolved') AS avg_resolution_days;
