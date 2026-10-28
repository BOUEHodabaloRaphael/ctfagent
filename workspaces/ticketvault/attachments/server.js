const crypto = require('crypto');
const path = require('path');
const express = require('express');
const session = require('express-session');
const { connect, getDb } = require('./db');
const { resolveLoginCredentials } = require('./utils/sanitize');
const { buildScopedFilter } = require('./utils/ticketFilter');

const app = express();
const PORT = process.env.PORT || 3000;

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.use(session({
  secret: crypto.randomBytes(32).toString('hex'),
  resave: false,
  saveUninitialized: false,
  cookie: { httpOnly: true }
}));

function requireAuth(req, res, next) {
  if (!req.session.username) return res.redirect('/login');
  next();
}

app.get('/', (req, res) => {
  res.redirect(req.session.username ? '/tickets' : '/login');
});

app.get('/register', (req, res) => {
  res.render('register', { error: null });
});

app.post('/register', async (req, res) => {
  const { username, password } = req.body;
  if (!username || !password) {
    return res.render('register', { error: 'Username and password required.' });
  }
  const db = getDb();
  const existing = await db.collection('users').findOne({ username });
  if (existing) {
    return res.render('register', { error: 'Username already taken.' });
  }
  await db.collection('users').insertOne({ username, password });
  req.session.username = username;
  res.redirect('/tickets');
});

app.get('/login', (req, res) => {
  res.render('login', { error: null });
});

app.post('/login', async (req, res) => {
  const { username, password } = resolveLoginCredentials(req);
  const db = getDb();
  const user = await db.collection('users').findOne({ username, password });
  if (!user) return res.render('login', { error: 'Invalid credentials.' });
  req.session.username = user.username;
  res.redirect('/tickets');
});

app.get('/logout', (req, res) => {
  req.session.destroy(() => res.redirect('/login'));
});

app.get('/tickets', requireAuth, async (req, res) => {
  const db = getDb();
  const tickets = await db.collection('tickets').find({ owner: req.session.username }).toArray();
  res.render('tickets', { tickets, username: req.session.username, q: '' });
});

app.post('/tickets', requireAuth, async (req, res) => {
  const { subject, content } = req.body;
  if (subject && content) {
    const db = getDb();
    await db.collection('tickets').insertOne({
      owner: req.session.username,
      subject: String(subject).slice(0, 200),
      content: String(content).slice(0, 2000)
    });
  }
  res.redirect('/tickets');
});

app.get('/tickets/search', requireAuth, async (req, res) => {
  const db = getDb();
  const filter = buildScopedFilter(req);
  const tickets = await db.collection('tickets').find(filter).toArray();
  res.render('tickets', { tickets, username: req.session.username, q: req.query.q || '' });
});

connect()
  .then(() => {
    app.listen(PORT, () => console.log(`ticketvault listening on port ${PORT}`));
  })
  .catch((err) => {
    console.error('Failed to connect to MongoDB', err);
    process.exit(1);
  });
