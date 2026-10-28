const crypto = require('crypto');
const path = require('path');
const express = require('express');
const session = require('express-session');
const merge = require('./utils/merge');

const app = express();
const PORT = process.env.PORT || 3000;

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));
app.set('view cache', false);

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.use(session({
  secret: crypto.randomBytes(32).toString('hex'),
  resave: false,
  saveUninitialized: false,
  cookie: { httpOnly: true }
}));

// In-memory "database" - good enough for a single-instance note app.
const users = {};

function requireAuth(req, res, next) {
  if (!req.session.username || !users[req.session.username]) {
    return res.redirect('/login');
  }
  next();
}

app.get('/', (req, res) => {
  res.redirect(req.session.username ? '/notes' : '/login');
});

app.get('/register', (req, res) => {
  res.render('register', { error: null });
});

app.post('/register', (req, res) => {
  const { username, password } = req.body;
  if (!username || !password || users[username]) {
    return res.render('register', { error: 'Invalid or already taken username.' });
  }
  users[username] = {
    password,
    notes: [],
    settings: { theme: 'light', notifications: true }
  };
  req.session.username = username;
  res.redirect('/notes');
});

app.get('/login', (req, res) => {
  res.render('login', { error: null });
});

app.post('/login', (req, res) => {
  const { username, password } = req.body;
  const user = users[username];
  if (!user || user.password !== password) {
    return res.render('login', { error: 'Invalid credentials.' });
  }
  req.session.username = username;
  res.redirect('/notes');
});

app.get('/logout', (req, res) => {
  req.session.destroy(() => res.redirect('/login'));
});

app.get('/notes', requireAuth, (req, res) => {
  const user = users[req.session.username];
  res.render('notes', { notes: user.notes, username: req.session.username });
});

app.post('/notes', requireAuth, (req, res) => {
  const user = users[req.session.username];
  const { content } = req.body;
  if (content) {
    user.notes.push(String(content).slice(0, 500));
  }
  res.redirect('/notes');
});

app.get('/settings', requireAuth, (req, res) => {
  const user = users[req.session.username];
  res.render('settings', { settings: user.settings, username: req.session.username });
});

// Lets the frontend push a partial settings update (e.g. { theme: 'dark' })
// without having to resend the whole settings object.
app.post('/api/settings', requireAuth, (req, res) => {
  const user = users[req.session.username];
  merge(user.settings, req.body || {});
  res.json({ ok: true, settings: user.settings });
});

app.listen(PORT, () => {
  console.log(`swiftnotes listening on port ${PORT}`);
});
