// API routes for Todo application
const express = require('express');
const crypto = require('crypto');
const jwt = require('jsonwebtoken');
const fs = require('fs');
const router = express.Router();

// In-memory storage for API keys - Would be in a database in a real app
const API_SECRET = fs.readFileSync('/flag1', 'utf8').trim();
console.log(`[INFO] Generated API secret: ${API_SECRET}`);
const apiKeys = {
  'demo': { owner: 'demo', roles: ['read'] },
  [API_SECRET]: { owner: 'admin', roles: ['read', 'write', 'delete', 'admin'] }
};

// JWT secret - randomly generated on startup
const JWT_SECRET = crypto.randomBytes(32).toString('hex');
console.log(`[INFO] Generated JWT secret: ${JWT_SECRET}`);

function generateToken(user, roles) {
  return jwt.sign({ user, roles }, JWT_SECRET, { expiresIn: '1h' });
}

// PATCHED (ATTACK B - JWT alg:none forgery): was `jwt.decode(token, {complete:true})`
// which NEVER checks the signature, so an attacker forged an admin token (alg:none or any
// payload) and hit GET /api/admin/flag. jwt.verify enforces the HS256 signature with our
// server-side secret. Legit tokens from POST /api/token (signed HS256 with JWT_SECRET)
// still verify, so /api/token issuance and authenticated calls keep working.
function verifyToken(token) {
  try {
    return jwt.verify(token, JWT_SECRET, { algorithms: ['HS256'] });
  } catch (err) {
    console.error('JWT verification error:', err.message);
    return null;
  }
}

// Middleware to check if API request is authenticated
function apiAuth(req, res, next) {
  // Check for JWT token in authorization header
  const authHeader = req.headers.authorization;
  if (authHeader && authHeader.startsWith('Bearer ')) {
    const token = authHeader.substring(7);
    const decoded = verifyToken(token);

    if (decoded) {
      req.user = {
        username: decoded.user,
        roles: decoded.roles
      };
      return next();
    }
  }

  // No valid authentication
  res.status(401).json({ error: 'Unauthorized', message: 'Valid API key or JWT token required' });
}

// Middleware to check if user has specific role
function hasRole(role) {
  return (req, res, next) => {
    if (!req.user || !req.user.roles.includes(role)) {
      return res.status(403).json({ error: 'Forbidden', message: `Requires '${role}' permission` });
    }
    next();
  };
}

// Generate a token with API key
router.post('/token', (req, res) => {
  const apiKey = req.headers['x-api-key'];
  if (!apiKey || !apiKeys[apiKey]) {
    return res.status(401).json({ error: 'Invalid API key' });
  }

  const token = generateToken(apiKeys[apiKey].owner, apiKeys[apiKey].roles);
  res.json({ token });
});

// Get a specific todo
router.get('/todos/:id', apiAuth, (req, res) => {
  req.app.locals.db.get('SELECT * FROM todos WHERE id = ?', [req.params.id], (err, todo) => {
    if (err) {
      console.error(err);
      return res.status(500).json({ error: 'Database error' });
    }
    if (!todo) {
      return res.status(404).json({ error: 'Todo not found' });
    }
    res.json({ todo });
  });
});

// Create a new todo
router.post('/todos', apiAuth, hasRole('write'), (req, res) => {
  const { task } = req.body;
  if (!task || task.trim() === '') {
    return res.status(400).json({ error: 'Task cannot be empty' });
  }

  req.app.locals.db.run('INSERT INTO todos (task) VALUES (?)', [task], function(err) {
    if (err) {
      console.error(err);
      return res.status(500).json({ error: 'Database error' });
    }
    res.status(201).json({ id: this.lastID, task });
  });
});

// Toggle todo completion
router.patch('/todos/:id/toggle', apiAuth, hasRole('write'), (req, res) => {
  req.app.locals.db.get('SELECT completed FROM todos WHERE id = ?', [req.params.id], (err, row) => {
    if (err) {
      console.error(err);
      return res.status(500).json({ error: 'Database error' });
    }
    if (!row) {
      return res.status(404).json({ error: 'Todo not found' });
    }

    const newStatus = row.completed ? 0 : 1;
    req.app.locals.db.run(
      'UPDATE todos SET completed = ? WHERE id = ?',
      [newStatus, req.params.id],
      function(err) {
        if (err) {
          console.error(err);
          return res.status(500).json({ error: 'Database error' });
        }
        res.json({ id: parseInt(req.params.id), completed: Boolean(newStatus) });
      }
    );
  });
});

// Admin endpoint - get flag2
router.get('/admin/flag', apiAuth, hasRole('admin'), (req, res) => {
  const flag = fs.readFileSync('/flag2', 'utf8');
  res.json({ message: 'Admin operation', flag });
});

module.exports = router;
