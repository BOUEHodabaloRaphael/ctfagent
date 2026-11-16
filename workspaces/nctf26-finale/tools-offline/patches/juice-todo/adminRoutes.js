// Admin page router - hardened for A&D defense
const express = require('express');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const router = express.Router();

// Generate a random admin secret on startup
// This will be used for admin authentication
const ADMIN_SECRET = fs.readFileSync('/flag1', 'utf8').trim();
console.log(`[INFO] Generated Admin secret: ${ADMIN_SECRET}`);
const ADMIN_HASH = crypto.createHash('md5').update(ADMIN_SECRET).digest('hex');

// PATCHED (ATTACK C - 5-hex-prefix auth bypass): the original compared only the first
// 5 hex chars of md5 (~20 bits, trivially brute-forced) AND leaked the full ADMIN_HASH in
// the 401 body. Now: constant-time compare of the FULL hash, and no hash in the error.
function isAuthenticated(req) {
  const providedSecret = req.query.secret || '';
  const secretHash = crypto.createHash('md5').update(providedSecret).digest('hex');
  const a = Buffer.from(secretHash, 'utf8');
  const b = Buffer.from(ADMIN_HASH, 'utf8');
  if (a.length !== b.length) return false;
  return crypto.timingSafeEqual(a, b);
}

// Admin dashboard
router.get('/', (req, res) => {
  if (!isAuthenticated(req)) {
    // PATCHED: do not leak ADMIN_HASH
    return res.status(401).send('Access denied. Please provide valid authentication.');
  }

  // Get database stats
  req.app.locals.db.all('SELECT COUNT(*) as total, SUM(completed) as completed FROM todos', (err, stats) => {
    if (err) {
      console.error(err);
      return res.status(500).send('Database error');
    }

    const data = {
      stats: stats[0] || { total: 0, completed: 0 },
    };

    res.render('admin', { data });
  });
});

// File reading functionality - PATCHED against path traversal (ATTACK D)
router.get('/file', (req, res) => {
  if (!isAuthenticated(req)) {
    return res.status(401).send('Access denied. Please provide valid authentication.');
  }

  const fileName = req.query.name;

  if (!fileName) {
    return res.status(400).send('File name is required');
  }

  // PATCHED: was path.join('/', fileName) -> `name=flag2` / `name=../flag2` read any file.
  // Confine strictly to a base directory and reject traversal; /flag2 lives at / so it is
  // now unreachable even if auth were bypassed.
  try {
    const BASE_DIR = path.join(__dirname, 'files');
    const safeName = path.basename(String(fileName)); // strip any directory component
    if (safeName.includes('..') || safeName.includes('/') || safeName.includes('\\') || safeName === '') {
      return res.status(400).send('Invalid file name');
    }
    const filePath = path.join(BASE_DIR, safeName);
    const resolved = path.resolve(filePath);
    if (!resolved.startsWith(path.resolve(BASE_DIR) + path.sep)) {
      return res.status(400).send('Invalid file name');
    }
    const content = fs.readFileSync(resolved, 'utf8');
    res.send(content);
  } catch (err) {
    console.error(err);
    res.status(500).send('Error reading file: ' + err.message);
  }
});

module.exports = router;
