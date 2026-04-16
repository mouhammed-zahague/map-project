/**
 * Green Campus Alert Map — Backend Server
 * ENSSRESD Batna, Algérie
 * Technologies: Node.js · Express · SQLite · Multer · JWT
 */

const express = require('express');
const cors = require('cors');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const Database = require('better-sqlite3');

const app = express();
const PORT = process.env.PORT || 3000;
const JWT_SECRET = process.env.JWT_SECRET || 'enssresd_green_campus_secret_2025';
const DB_PATH = './database/campus_alerts.db';
const UPLOADS_DIR = './uploads';

// ─── Middleware ───────────────────────────────────────────────────────────────
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use('/uploads', express.static(UPLOADS_DIR));
app.use(express.static('public'));

// ─── Database Setup ───────────────────────────────────────────────────────────
if (!fs.existsSync('./database')) fs.mkdirSync('./database', { recursive: true });
if (!fs.existsSync(UPLOADS_DIR)) fs.mkdirSync(UPLOADS_DIR, { recursive: true });

const db = new Database(DB_PATH);
db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');

// Run schema
const schema = fs.readFileSync('./database/schema.sql', 'utf8');
db.exec(schema);

// ─── File Upload (Multer) ─────────────────────────────────────────────────────
const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, UPLOADS_DIR),
  filename: (req, file, cb) => {
    const unique = Date.now() + '-' + Math.round(Math.random() * 1e9);
    cb(null, unique + path.extname(file.originalname));
  }
});
const upload = multer({
  storage,
  limits: { fileSize: 5 * 1024 * 1024 }, // 5MB
  fileFilter: (req, file, cb) => {
    const allowed = /jpeg|jpg|png|webp/;
    cb(null, allowed.test(file.mimetype));
  }
});

// ─── Auth Middleware ──────────────────────────────────────────────────────────
function authenticate(req, res, next) {
  const header = req.headers.authorization;
  if (!header) return res.status(401).json({ error: 'Token manquant' });
  try {
    const token = header.split(' ')[1];
    req.user = jwt.verify(token, JWT_SECRET);
    next();
  } catch {
    res.status(401).json({ error: 'Token invalide ou expiré' });
  }
}

function requireAdmin(req, res, next) {
  if (req.user?.role !== 'admin') return res.status(403).json({ error: 'Accès refusé' });
  next();
}

// ═══════════════════════════════════════════════════════════════════════════════
// AUTH ROUTES
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * POST /api/auth/login
 * Body: { username, password }
 */
app.post('/api/auth/login', (req, res) => {
  const { username, password } = req.body;
  if (!username || !password) return res.status(400).json({ error: 'Champs requis' });
  const user = db.prepare('SELECT * FROM users WHERE username = ?').get(username);
  if (!user || !bcrypt.compareSync(password, user.password_hash)) {
    return res.status(401).json({ error: 'Identifiants incorrects' });
  }
  const token = jwt.sign({ id: user.id, username: user.username, role: user.role }, JWT_SECRET, { expiresIn: '24h' });
  res.json({
    token,
    user: { id: user.id, name: user.full_name, username: user.username, role: user.role }
  });
});

/**
 * GET /api/auth/me — Get current user profile
 */
app.get('/api/auth/me', authenticate, (req, res) => {
  const user = db.prepare('SELECT id, username, full_name, role, created_at FROM users WHERE id = ?').get(req.user.id);
  res.json(user);
});

// ═══════════════════════════════════════════════════════════════════════════════
// ALERTS ROUTES
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * GET /api/alerts — List alerts with optional filtering
 * Query: ?category=water&status=reported&priority=high&zone=batiment_a&search=fuite
 */
app.get('/api/alerts', authenticate, (req, res) => {
  const { category, status, priority, zone, search } = req.query;
  let query = `
    SELECT a.*, u.full_name as reporter_name, u.username as reporter_username,
           c.name as category_name, c.icon as category_icon, c.color as category_color,
           z.name as zone_name
    FROM alerts a
    JOIN users u ON a.user_id = u.id
    JOIN categories c ON a.category_id = c.id
    JOIN zones z ON a.zone_id = z.id
    WHERE 1=1
  `;
  const params = [];
  if (category) { query += ' AND c.slug = ?'; params.push(category); }
  if (status) { query += ' AND a.status = ?'; params.push(status); }
  if (priority) { query += ' AND a.priority = ?'; params.push(priority); }
  if (zone) { query += ' AND z.slug = ?'; params.push(zone); }
  if (search) { query += ' AND (a.title LIKE ? OR a.description LIKE ?)'; params.push(`%${search}%`, `%${search}%`); }
  query += ' ORDER BY a.created_at DESC';
  const alerts = db.prepare(query).all(...params);
  res.json({ alerts, total: alerts.length });
});

/**
 * GET /api/alerts/:id — Get single alert with comments
 */
app.get('/api/alerts/:id', authenticate, (req, res) => {
  const alert = db.prepare(`
    SELECT a.*, u.full_name as reporter_name,
           c.name as category_name, c.icon as category_icon,
           z.name as zone_name
    FROM alerts a
    JOIN users u ON a.user_id = u.id
    JOIN categories c ON a.category_id = c.id
    JOIN zones z ON a.zone_id = z.id
    WHERE a.id = ?
  `).get(req.params.id);
  if (!alert) return res.status(404).json({ error: 'Alerte introuvable' });
  const comments = db.prepare(`
    SELECT co.*, u.full_name as author_name, u.role as author_role
    FROM comments co JOIN users u ON co.user_id = u.id
    WHERE co.alert_id = ? ORDER BY co.created_at ASC
  `).all(alert.id);
  res.json({ ...alert, comments });
});

/**
 * POST /api/alerts — Create new alert (with optional image)
 */
app.post('/api/alerts', authenticate, upload.single('image'), (req, res) => {
  const { title, description, category, zone, latitude, longitude, ai_priority, ai_confidence } = req.body;
  if (!title || !description || !category || !zone) {
    return res.status(400).json({ error: 'Champs obligatoires manquants' });
  }
  const cat = db.prepare('SELECT id FROM categories WHERE slug = ?').get(category);
  const zon = db.prepare('SELECT id FROM zones WHERE slug = ?').get(zone);
  if (!cat || !zon) return res.status(400).json({ error: 'Catégorie ou zone invalide' });

  const result = db.prepare(`
    INSERT INTO alerts (title, description, category_id, zone_id, latitude, longitude,
      priority, status, user_id, image_path, ai_priority, ai_confidence)
    VALUES (?, ?, ?, ?, ?, ?, ?, 'reported', ?, ?, ?, ?)
  `).run(
    title, description, cat.id, zon.id,
    parseFloat(latitude) || null, parseFloat(longitude) || null,
    ai_priority || 'medium',
    req.user.id,
    req.file ? req.file.filename : null,
    ai_priority || null,
    parseFloat(ai_confidence) || null
  );

  // Log OS activity
  logActivity('alert_created', req.user.id, result.lastInsertRowid);
  res.status(201).json({ message: 'Alerte créée', id: result.lastInsertRowid });
});

/**
 * PATCH /api/alerts/:id — Update alert status (admin/staff only)
 */
app.patch('/api/alerts/:id', authenticate, (req, res) => {
  if (!['admin', 'staff'].includes(req.user.role)) return res.status(403).json({ error: 'Accès refusé' });
  const { status, priority } = req.body;
  const allowed_status = ['reported', 'validated', 'in_progress', 'resolved'];
  if (status && !allowed_status.includes(status)) return res.status(400).json({ error: 'Statut invalide' });
  const updates = [];
  const params = [];
  if (status) { updates.push('status = ?'); params.push(status); }
  if (priority) { updates.push('priority = ?'); params.push(priority); }
  if (status === 'resolved') { updates.push('resolved_at = datetime("now")'); }
  params.push(req.params.id);
  db.prepare(`UPDATE alerts SET ${updates.join(', ')}, updated_at = datetime('now') WHERE id = ?`).run(...params);
  logActivity('alert_updated', req.user.id, req.params.id);
  res.json({ message: 'Alerte mise à jour' });
});

/**
 * DELETE /api/alerts/:id — Delete alert (admin only)
 */
app.delete('/api/alerts/:id', authenticate, requireAdmin, (req, res) => {
  const alert = db.prepare('SELECT image_path FROM alerts WHERE id = ?').get(req.params.id);
  if (!alert) return res.status(404).json({ error: 'Alerte introuvable' });
  if (alert.image_path) {
    const imgPath = path.join(UPLOADS_DIR, alert.image_path);
    if (fs.existsSync(imgPath)) fs.unlinkSync(imgPath);
  }
  db.prepare('DELETE FROM alerts WHERE id = ?').run(req.params.id);
  logActivity('alert_deleted', req.user.id, req.params.id);
  res.json({ message: 'Alerte supprimée' });
});

// ═══════════════════════════════════════════════════════════════════════════════
// COMMENTS ROUTES
// ═══════════════════════════════════════════════════════════════════════════════

app.post('/api/alerts/:id/comments', authenticate, (req, res) => {
  const { content } = req.body;
  if (!content) return res.status(400).json({ error: 'Contenu requis' });
  const alert = db.prepare('SELECT id FROM alerts WHERE id = ?').get(req.params.id);
  if (!alert) return res.status(404).json({ error: 'Alerte introuvable' });
  const result = db.prepare('INSERT INTO comments (alert_id, user_id, content) VALUES (?, ?, ?)').run(alert.id, req.user.id, content);
  res.status(201).json({ message: 'Commentaire ajouté', id: result.lastInsertRowid });
});

// ═══════════════════════════════════════════════════════════════════════════════
// STATISTICS ROUTES
// ═══════════════════════════════════════════════════════════════════════════════

app.get('/api/stats', authenticate, (req, res) => {
  const total = db.prepare('SELECT COUNT(*) as n FROM alerts').get().n;
  const byStatus = db.prepare("SELECT status, COUNT(*) as count FROM alerts GROUP BY status").all();
  const byCategory = db.prepare(`
    SELECT c.slug, c.name, c.icon, COUNT(a.id) as count
    FROM categories c LEFT JOIN alerts a ON a.category_id = c.id
    GROUP BY c.id`).all();
  const byZone = db.prepare(`
    SELECT z.slug, z.name, COUNT(a.id) as count
    FROM zones z LEFT JOIN alerts a ON a.zone_id = z.id
    GROUP BY z.id ORDER BY count DESC`).all();
  const byMonth = db.prepare(`
    SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count
    FROM alerts GROUP BY month ORDER BY month`).all();
  const avgResolution = db.prepare(`
    SELECT AVG(julianday(resolved_at) - julianday(created_at)) as avg_days
    FROM alerts WHERE status = 'resolved' AND resolved_at IS NOT NULL`).get();
  res.json({ total, byStatus, byCategory, byZone, byMonth, avgResolutionDays: avgResolution?.avg_days?.toFixed(1) || null });
});

// ═══════════════════════════════════════════════════════════════════════════════
// AI CLASSIFICATION ROUTE (proxy to Claude API)
// ═══════════════════════════════════════════════════════════════════════════════

app.post('/api/ai/classify', authenticate, async (req, res) => {
  const { title, description } = req.body;
  try {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': process.env.ANTHROPIC_API_KEY,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-20250514',
        max_tokens: 500,
        system: `Classifie l'alerte environnementale en JSON avec:
{"category":"water|energy|waste|green|pollution","priority":"high|medium|low","confidence":0-100,"reason":"fr","urgency_keywords":["..."]}`,
        messages: [{ role: 'user', content: `Titre: ${title}\nDescription: ${description}` }]
      })
    });
    const data = await response.json();
    const text = data.content[0].text.replace(/```json|```/g, '').trim();
    res.json(JSON.parse(text));
  } catch (err) {
    res.status(500).json({ error: 'Erreur de classification IA', details: err.message });
  }
});

// ═══════════════════════════════════════════════════════════════════════════════
// CATEGORIES & ZONES
// ═══════════════════════════════════════════════════════════════════════════════

app.get('/api/categories', authenticate, (req, res) => {
  res.json(db.prepare('SELECT * FROM categories').all());
});
app.get('/api/zones', authenticate, (req, res) => {
  res.json(db.prepare('SELECT * FROM zones').all());
});

// ═══════════════════════════════════════════════════════════════════════════════
// USERS (admin only)
// ═══════════════════════════════════════════════════════════════════════════════

app.get('/api/users', authenticate, requireAdmin, (req, res) => {
  const users = db.prepare(`
    SELECT u.id, u.username, u.full_name, u.role, u.created_at,
           COUNT(a.id) as alert_count
    FROM users u LEFT JOIN alerts a ON a.user_id = u.id
    GROUP BY u.id ORDER BY u.created_at`).all();
  res.json(users);
});

// ═══════════════════════════════════════════════════════════════════════════════
// OS: LOGS & SYSTEM
// ═══════════════════════════════════════════════════════════════════════════════

function logActivity(action, userId, resourceId) {
  const logLine = `[${new Date().toISOString()}] action=${action} user=${userId} resource=${resourceId}\n`;
  fs.appendFileSync('./logs/activity.log', logLine);
}

app.get('/api/system/logs', authenticate, requireAdmin, (req, res) => {
  try {
    const logPath = './logs/activity.log';
    const content = fs.existsSync(logPath) ? fs.readFileSync(logPath, 'utf8') : '';
    const lines = content.trim().split('\n').filter(Boolean).slice(-100).reverse();
    res.json({ logs: lines });
  } catch (err) {
    res.status(500).json({ error: 'Impossible de lire les logs' });
  }
});

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', server: 'Green Campus API', campus: 'ENSSRESD Batna', timestamp: new Date().toISOString() });
});

// ─── Start Server ─────────────────────────────────────────────────────────────
if (!fs.existsSync('./logs')) fs.mkdirSync('./logs');
app.listen(PORT, () => {
  console.log(`\n🌿 Green Campus Alert Map — Backend Server`);
  console.log(`📍 ENSSRESD Batna, Algérie`);
  console.log(`🚀 Serveur démarré sur http://localhost:${PORT}`);
  console.log(`📊 Base de données: ${DB_PATH}`);
  console.log(`📁 Uploads: ${UPLOADS_DIR}\n`);
});

module.exports = app;
