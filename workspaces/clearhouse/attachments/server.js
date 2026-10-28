const crypto = require('crypto');
const fs = require('fs');
const net = require('net');
const path = require('path');
const express = require('express');
const { graphql } = require('graphql');

const db = require('./utils/db');
const { createSession, getMerchantIdForToken } = require('./utils/auth');
const schema = require('./utils/schema');

const app = express();
const PORT = process.env.PORT || 3000;
const REPORT_CORE_HOST = process.env.REPORT_CORE_HOST || 'report-core';
const REPORT_CORE_PORT = parseInt(process.env.REPORT_CORE_PORT || '4100', 10);

function renderViaReportCore(rawText) {
  return new Promise((resolve, reject) => {
    const payload = Buffer.from(rawText, 'utf8');
    const header = Buffer.alloc(4);
    header.writeUInt32BE(payload.length, 0);

    const socket = net.createConnection({ host: REPORT_CORE_HOST, port: REPORT_CORE_PORT });
    const chunks = [];
    socket.setTimeout(10000);
    socket.on('connect', () => socket.end(Buffer.concat([header, payload])));
    socket.on('data', (c) => chunks.push(c));
    socket.on('end', () => {
      const full = Buffer.concat(chunks).toString('utf8');
      const idx = full.indexOf('\n');
      if (idx === -1) return reject(new Error('malformed report-core response'));
      const status = parseInt(full.slice(0, idx), 10) || 502;
      resolve({ status, body: full.slice(idx + 1) });
    });
    socket.on('timeout', () => {
      socket.destroy();
      reject(new Error('report-core timeout'));
    });
    socket.on('error', reject);
  });
}

const REPORT_CORE_TOKEN = crypto.randomBytes(24).toString('hex');

const CONFIG_DIR = path.join(__dirname, 'config');
const TEMPLATE_DIR = path.join(__dirname, 'assets', 'templates', 'receipts');

fs.mkdirSync(CONFIG_DIR, { recursive: true });
fs.writeFileSync(
  path.join(CONFIG_DIR, 'internal-secrets.json'),
  JSON.stringify({ reportCoreToken: REPORT_CORE_TOKEN }, null, 2)
);

function log(event, detail = {}) {
  const ts = new Date().toISOString();
  console.log(`[gateway] ${ts} event=${event} ${JSON.stringify(detail)}`);
}

app.use(express.json());

app.get('/health', (req, res) => res.json({ ok: true, service: 'gateway' }));

function auth(req, res, next) {
  const header = req.headers.authorization || '';
  const token = header.startsWith('Bearer ') ? header.slice(7) : null;
  const merchantId = token ? getMerchantIdForToken(token) : null;
  if (!merchantId) {
    log('auth_failed', { ip: req.ip });
    return res.status(401).json({ error: 'missing or invalid session' });
  }
  req.merchantId = merchantId;
  next();
}

function requireOpsApiKey(req, res, next) {
  const key = req.headers['x-api-key'];
  const merchant = key ? db.findMerchantByApiKey(key) : null;
  if (!merchant || merchant.role !== 'ops') {
    log('ops_denied', { ip: req.ip, path: req.path });
    return res.status(403).json({ error: 'ops access required' });
  }
  req.opsMerchant = merchant;
  next();
}

app.post('/register', (req, res) => {
  const { name, password } = req.body || {};
  if (!name || !password || typeof name !== 'string' || typeof password !== 'string') {
    return res.status(400).json({ error: 'name and password are required' });
  }
  const merchant = db.createMerchant(name, password);
  if (!merchant) {
    log('register_conflict', { ip: req.ip, name });
    return res.status(409).json({ error: 'name already taken' });
  }
  const token = createSession(merchant.id);
  log('register_ok', { ip: req.ip, merchantId: merchant.id });
  res.json({ token });
});

app.post('/login', (req, res) => {
  const { name, password } = req.body || {};
  const merchant = db.findMerchantByCredentials(name, password);
  if (!merchant) {
    log('login_failed', { ip: req.ip, name });
    return res.status(401).json({ error: 'invalid credentials' });
  }
  const token = createSession(merchant.id);
  log('login_ok', { ip: req.ip, merchantId: merchant.id });
  res.json({ token });
});

app.post('/graphql', auth, async (req, res) => {
  const { query, variables } = req.body || {};
  if (!query) return res.status(400).json({ error: 'query is required' });
  const ctx = { merchantId: req.merchantId };
  const result = await graphql({ schema, source: query, variableValues: variables, contextValue: ctx });
  log('graphql', { ip: req.ip, merchantId: req.merchantId, hasErrors: !!(result.errors && result.errors.length) });
  res.json(result);
});

app.get('/ops/templates/download', requireOpsApiKey, (req, res) => {
  const name = String(req.query.name || '');

  const safe = name.replace('../', '');
  const target = path.join(TEMPLATE_DIR, safe);
  fs.readFile(target, 'utf8', (err, data) => {
    if (err) {
      log('template_download_failed', { ip: req.ip, name });
      return res.status(404).json({ error: 'template not found' });
    }
    log('template_download_ok', { ip: req.ip, name, resolved: target });
    res.type('text/plain').send(data);
  });
});

const MAX_RENDER_ATTEMPTS = 5;
const RENDER_WINDOW_MS = 10 * 60 * 1000;
const renderAttempts = new Map();

function renderRateLimited(ip) {
  const now = Date.now();
  const timestamps = (renderAttempts.get(ip) || []).filter((t) => now - t < RENDER_WINDOW_MS);
  if (timestamps.length >= MAX_RENDER_ATTEMPTS) {
    renderAttempts.set(ip, timestamps);
    return true;
  }
  timestamps.push(now);
  renderAttempts.set(ip, timestamps);
  return false;
}

app.post('/ops/render-report', requireOpsApiKey, express.text({ type: '*/*' }), async (req, res) => {
  if (renderRateLimited(req.ip)) {
    log('render_rate_limited', { ip: req.ip });
    return res.status(429).json({ error: 'rate limited, try again later' });
  }
  const token = req.headers['x-report-core-token'];
  if (token !== REPORT_CORE_TOKEN) {
    log('render_bad_token', { ip: req.ip });
    return res.status(403).json({ error: 'invalid report-core token' });
  }
  try {
    const { status, body } = await renderViaReportCore(req.body);
    log('render_relayed', { ip: req.ip, backendStatus: status, flagGiven: body.includes('CTF{') });
    res.status(status).type('text/plain').send(body);
  } catch (e) {
    log('render_error', { ip: req.ip, message: e.message });
    res.status(502).json({ error: 'report-core unreachable' });
  }
});

app.listen(PORT, () => console.log(`clearhouse gateway listening on port ${PORT}`));
