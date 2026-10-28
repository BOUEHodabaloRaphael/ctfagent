const crypto = require('crypto');
const express = require('express');
const fetch = require('node-fetch');
const { signToken, verifyToken } = require('./utils/auth');

const app = express();
const PORT = process.env.PORT || 3000;
const LEDGER_SERVICE_URL = process.env.LEDGER_SERVICE_URL || 'http://ledger:4000';

app.use(express.json());


const { publicKey, privateKey } = crypto.generateKeyPairSync('rsa', {
  modulusLength: 2048,
  publicKeyEncoding: { type: 'spki', format: 'pem' },
  privateKeyEncoding: { type: 'pkcs8', format: 'pem' }
});


const merchants = {
  acme: { password: 'acme12345', role: 'merchant' },
  wonka: { password: 'ch0c0lat3', role: 'merchant' }
};

function auth(req, res, next) {
  const header = req.headers.authorization || '';
  const token = header.startsWith('Bearer ') ? header.slice(7) : null;
  if (!token) return res.status(401).json({ error: 'Missing token' });
  try {
    req.user = verifyToken(token, publicKey);
    next();
  } catch (e) {
    res.status(401).json({ error: 'Invalid or expired token' });
  }
}

function requireOps(req, res, next) {
  if (!req.user || req.user.role !== 'ops') {
    return res.status(403).json({ error: 'Ops staff only' });
  }
  next();
}

app.get('/pubkey', (req, res) => {
  res.type('text/plain').send(publicKey);
});

app.post('/login', (req, res) => {
  const { username, password } = req.body || {};
  const merchant = merchants[username];
  if (!merchant || merchant.password !== password) {
    return res.status(401).json({ error: 'Invalid credentials' });
  }
  const token = signToken({ username, role: merchant.role }, privateKey);
  res.json({ token });
});

app.get('/ops/dashboard', auth, requireOps, (req, res) => {
  res.json({
    message: `Welcome, ${req.user.username}`,
    ledgerService: LEDGER_SERVICE_URL,
    note: 'Use /ops/webhooks/test to verify a merchant payment-notification endpoint before enabling it.'
  });
});


const BLOCKED_HOSTS = ['ledger', 'localhost', '127.0.0.1'];
const PRIVATE_IP_RE = /^(10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)/;

function isBlockedHost(hostname) {
  return BLOCKED_HOSTS.includes(hostname) || PRIVATE_IP_RE.test(hostname);
}

app.post('/ops/webhooks/test', auth, requireOps, async (req, res) => {
  const { url, method, body } = req.body || {};
  if (!url) return res.status(400).json({ error: 'url is required' });
  let parsed;
  try {
    parsed = new URL(url);
  } catch (e) {
    return res.status(400).json({ error: 'Invalid URL' });
  }
  if (isBlockedHost(parsed.hostname)) {
    return res.status(403).json({ error: 'Target host is not allowed' });
  }
  try {
    const upstream = await fetch(url, {
      method: method || 'GET',
      headers: { 'Content-Type': 'application/json' },
      body: body !== undefined ? JSON.stringify(body) : undefined
    });
    const text = await upstream.text();
    res.json({ status: upstream.status, body: text });
  } catch (e) {
    res.status(502).json({ error: e.message });
  }
});

app.listen(PORT, () => console.log(`paygate gateway listening on port ${PORT}`));
