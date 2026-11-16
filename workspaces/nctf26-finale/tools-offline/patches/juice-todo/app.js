const express = require('express');
const bodyParser = require('body-parser');
const cookieParser = require('cookie-parser');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
const sqlite3 = require('sqlite3').verbose();
const adminRoutes = require('./adminRoutes');
const apiRoutes = require('./apiRoutes');

// Initialize express app
const app = express();
const PORT = process.env.PORT || 8080;

// Set up view engine
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Middleware
app.use(bodyParser.urlencoded({ extended: false }));
app.use(bodyParser.json());
app.use(cookieParser());
app.use(express.static(path.join(__dirname, 'public')));

// Initialize database
const dbFile = path.join(__dirname, 'todo.db');
const db = new sqlite3.Database(dbFile);

// Make db available to routes
app.locals.db = db;

// Create todo table if it doesn't exist
const flag1 = fs.readFileSync('/flag1', 'utf8');
db.serialize(() => {
  db.run(`CREATE TABLE IF NOT EXISTS todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task TEXT NOT NULL,
    completed BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );`);
  db.run(`CREATE TABLE IF NOT EXISTS flags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flag TEXT NOT NULL
  );`);
  // PATCHED: parameterize the flag seed too (defense in depth; flag1 can contain quotes)
  db.run('INSERT INTO flags (flag) VALUES (?)', [flag1]);
});

// Routes
app.get('/', (req, res) => {
  // Check if user is logged in
  const sessionId = req.cookies?.sessionId;

  db.all('SELECT * FROM todos ORDER BY created_at DESC', (err, todos) => {
    if (err) {
      console.error(err);
      return res.status(500).send('Database error');
    }
    res.render('index', { todos });
  });
});

// Add a new todo
app.post('/todos', (req, res) => {
  const { task } = req.body;
  if (!task || task.trim() === '') {
    return res.status(400).send('Task cannot be empty');
  }

  // PATCHED (ATTACK A - SQLi): was `INSERT INTO todos (task) VALUES ('${task}')`
  // Parameterized query kills the UNION/concat SQLi that leaked flag1 from the flags table.
  db.run('INSERT INTO todos (task) VALUES (?)', [task], function(err) {
    if (err) {
      console.error(err);
      return res.status(500).send('Database error');
    }
    res.redirect('/');
  });
});

// Toggle todo completion status
app.post('/todos/:id/toggle', (req, res) => {
  const id = req.params.id;
  db.get('SELECT completed FROM todos WHERE id = ?', [id], (err, row) => {
    if (err || !row) {
      console.error(err);
      return res.status(404).send('Todo not found');
    }

    const newStatus = row.completed ? 0 : 1;
    db.run('UPDATE todos SET completed = ? WHERE id = ?', [newStatus, id], (err) => {
      if (err) {
        console.error(err);
        return res.status(500).send('Database error');
      }
      res.redirect('/');
    });
  });
});

// Mount API routes
app.use('/api', apiRoutes);

// Mount admin routes
app.use('/admin', adminRoutes);

// Start the server
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
