-- ============================================================
-- Green Campus Alert Map - Database Schema
-- École Nationale Supérieure des Énergies Renouvelables,
-- Environnement et Développement Durable (ENREDD) - Batna
-- ============================================================

CREATE DATABASE IF NOT EXISTS green_campus_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE green_campus_db;

-- ------------------------------------------------------------
-- TABLE: zones (Campus zones/areas)
-- ------------------------------------------------------------
CREATE TABLE zones (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    color_code  VARCHAR(7) DEFAULT '#28a745',
    lat_center  DECIMAL(10, 8),
    lng_center  DECIMAL(11, 8),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- TABLE: roles
-- ------------------------------------------------------------
CREATE TABLE roles (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- TABLE: users
-- ------------------------------------------------------------
CREATE TABLE users (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(80)  NOT NULL UNIQUE,
    email           VARCHAR(120) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    full_name       VARCHAR(150),
    role_id         INT NOT NULL DEFAULT 2,
    student_id      VARCHAR(20),
    
    avatar_url      VARCHAR(255),
    is_active       BOOLEAN DEFAULT TRUE,
    last_login      TIMESTAMP NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

-- ------------------------------------------------------------
-- TABLE: categories
-- ------------------------------------------------------------
CREATE TABLE categories (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,
    name_ar     VARCHAR(100),
    name_fr     VARCHAR(100),
    description TEXT,
    icon        VARCHAR(50),
    color       VARCHAR(7) DEFAULT '#28a745',
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- TABLE: alerts
-- ------------------------------------------------------------
CREATE TABLE alerts (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    title           VARCHAR(200) NOT NULL,
    description     TEXT NOT NULL,
    category_id     INT NOT NULL,
    zone_id         INT,
    user_id         INT NOT NULL,
    latitude        DECIMAL(10, 8) NOT NULL,
    longitude       DECIMAL(11, 8) NOT NULL,
    location_name   VARCHAR(200),
    image_url       VARCHAR(255),
    status          ENUM('reported','validated','in_progress','resolved','rejected')
                    DEFAULT 'reported',
    priority        ENUM('low','medium','high','critical') DEFAULT 'medium',
    ml_category     VARCHAR(100),
    ml_priority     VARCHAR(20),
    ml_confidence   DECIMAL(5, 4),
    severity_score  INT DEFAULT 5,
    views_count     INT DEFAULT 0,
    upvotes         INT DEFAULT 0,
    is_anonymous    BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    validated_at    TIMESTAMP NULL,
    resolved_at     TIMESTAMP NULL,
    FOREIGN KEY (category_id) REFERENCES categories(id),
    FOREIGN KEY (zone_id) REFERENCES zones(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ------------------------------------------------------------
-- TABLE: alert_status_history
-- ------------------------------------------------------------
CREATE TABLE alert_status_history (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    alert_id    INT NOT NULL,
    old_status  VARCHAR(20),
    new_status  VARCHAR(20) NOT NULL,
    changed_by  INT NOT NULL,
    note        TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (alert_id) REFERENCES alerts(id) ON DELETE CASCADE,
    FOREIGN KEY (changed_by) REFERENCES users(id)
);

-- ------------------------------------------------------------
-- TABLE: comments
-- ------------------------------------------------------------
CREATE TABLE comments (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    alert_id    INT NOT NULL,
    user_id     INT NOT NULL,
    content     TEXT NOT NULL,
    is_official BOOLEAN DEFAULT FALSE,
    parent_id   INT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (alert_id) REFERENCES alerts(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (parent_id) REFERENCES comments(id)
);

-- ------------------------------------------------------------
-- TABLE: alert_images (Multiple images per alert)
-- ------------------------------------------------------------
CREATE TABLE alert_images (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    alert_id    INT NOT NULL,
    image_url   VARCHAR(255) NOT NULL,
    caption     VARCHAR(200),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (alert_id) REFERENCES alerts(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- TABLE: votes
-- ------------------------------------------------------------
CREATE TABLE votes (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    alert_id    INT NOT NULL,
    user_id     INT NOT NULL,
    vote_type   ENUM('up', 'down') DEFAULT 'up',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_vote (alert_id, user_id),
    FOREIGN KEY (alert_id) REFERENCES alerts(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ------------------------------------------------------------
-- TABLE: notifications
-- ------------------------------------------------------------
CREATE TABLE notifications (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL,
    alert_id    INT,
    type        VARCHAR(50) NOT NULL,
    message     TEXT NOT NULL,
    is_read     BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (alert_id) REFERENCES alerts(id)
);

-- ------------------------------------------------------------
-- TABLE: activity_logs
-- ------------------------------------------------------------
CREATE TABLE activity_logs (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT,
    action      VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id   INT,
    ip_address  VARCHAR(45),
    user_agent  TEXT,
    details     JSON,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ------------------------------------------------------------
-- INDEXES for performance
-- ------------------------------------------------------------
CREATE INDEX idx_alerts_status     ON alerts(status);
CREATE INDEX idx_alerts_category   ON alerts(category_id);
CREATE INDEX idx_alerts_zone       ON alerts(zone_id);
CREATE INDEX idx_alerts_user       ON alerts(user_id);
CREATE INDEX idx_alerts_priority   ON alerts(priority);
CREATE INDEX idx_alerts_created    ON alerts(created_at);
CREATE INDEX idx_alerts_location   ON alerts(latitude, longitude);
CREATE INDEX idx_comments_alert    ON comments(alert_id);
CREATE INDEX idx_notifications_user ON notifications(user_id, is_read);

-- ------------------------------------------------------------
-- VIEWS
-- ------------------------------------------------------------
CREATE VIEW v_alerts_full AS
SELECT
    a.id,
    a.title,
    a.description,
    a.status,
    a.priority,
    a.latitude,
    a.longitude,
    a.location_name,
    a.image_url,
    a.ml_category,
    a.ml_priority,
    a.ml_confidence,
    a.severity_score,
    a.upvotes,
    a.views_count,
    a.is_anonymous,
    a.created_at,
    a.updated_at,
    a.resolved_at,
    c.name        AS category_name,
    c.icon        AS category_icon,
    c.color       AS category_color,
    z.name        AS zone_name,
    u.username    AS reporter_username,
    u.full_name   AS reporter_name,
    u.email       AS reporter_email,
    r.name        AS reporter_role,
    (SELECT COUNT(*) FROM comments cm WHERE cm.alert_id = a.id) AS comments_count
FROM alerts a
JOIN categories c ON a.category_id = c.id
LEFT JOIN zones z ON a.zone_id = z.id
JOIN users u ON a.user_id = u.id
JOIN roles r ON u.role_id = r.id;

CREATE VIEW v_dashboard_stats AS
SELECT
    COUNT(*)                                            AS total_alerts,
    SUM(status = 'reported')                            AS reported_count,
    SUM(status = 'validated')                           AS validated_count,
    SUM(status = 'in_progress')                         AS in_progress_count,
    SUM(status = 'resolved')                            AS resolved_count,
    SUM(status = 'rejected')                            AS rejected_count,
    SUM(priority = 'critical')                          AS critical_count,
    SUM(priority = 'high')                              AS high_count,
    ROUND(AVG(severity_score), 2)                       AS avg_severity,
    ROUND(
        SUM(status = 'resolved') * 100.0 / COUNT(*), 2
    )                                                   AS resolution_rate,
    ROUND(
        AVG(TIMESTAMPDIFF(HOUR, created_at, resolved_at)), 2
    )                                                   AS avg_resolution_hours
FROM alerts;

show TABLES ;