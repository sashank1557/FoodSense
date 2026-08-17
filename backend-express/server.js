/**
 * FoodSense - Express API Server (Thin Relay, History & Corrections Layer)
 * Bridges React Frontend with Flask ML Inference Engine.
 * Features JWT Auth, SQLite Persistence, Manual Corrections, and Cold-Start Resilience.
 */

const express = require('express');
const cors = require('cors');
require('dotenv').config();

const healthRouter = require('./routes/health');
const analyzeRouter = require('./routes/analyze');
const authRouter = require('./routes/auth');
const historyRouter = require('./routes/history');
const correctRouter = require('./routes/correct');
const errorHandler = require('./middleware/errorHandler');
const { generalLimiter } = require('./middleware/rateLimiter');

// Initialize database
require('./db/database');

const app = express();
const PORT = process.env.PORT || 3001;
const FLASK_URL = process.env.FLASK_BACKEND_URL || 'http://127.0.0.1:5000';
const CORS_ORIGIN = process.env.CORS_ORIGIN || '*';

// Middlewares
app.use(cors({
  origin: CORS_ORIGIN,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

app.use(express.json({ limit: '20mb' }));
app.use(express.urlencoded({ extended: true, limit: '20mb' }));
app.use(generalLimiter);

// Request Logger
app.use((req, res, next) => {
  const timeStr = new Date().toISOString().split('T')[1].slice(0, 8);
  console.log(`[Express] ${timeStr} ${req.method} ${req.originalUrl}`);
  next();
});

// Primary Routes
app.use('/api/health', healthRouter);
app.use('/health', healthRouter);

app.use('/api/analyze', analyzeRouter);
app.use('/api/v1/analyze', analyzeRouter);

app.use('/api/auth', authRouter);
app.use('/api/history', historyRouter);

app.use('/api/correct', correctRouter);
app.use('/api/corrections', correctRouter);

// Root informative endpoint
app.get('/', (req, res) => {
  res.json({
    name: 'FoodSense Relay API',
    status: 'online',
    version: '1.2.0',
    endpoints: [
      'GET  /api/health',
      'POST /api/analyze',
      'GET  /api/analyze/classes',
      'POST /api/auth/signup',
      'POST /api/auth/login',
      'GET  /api/auth/me',
      'GET  /api/history',
      'GET  /api/history/daily-totals',
      'POST /api/correct',
      'GET  /api/corrections/export'
    ],
    upstream_inference_backend: FLASK_URL
  });
});

// Centralized error handler
app.use(errorHandler);

app.listen(PORT, () => {
  console.log(`=============================================================`);
  console.log(`FoodSense Express Relay Layer running on port ${PORT}`);
  console.log(`Forwarding inference requests to Flask backend at: ${FLASK_URL}`);
  console.log(`SQLite database initialized for auth, history & corrections.`);
  console.log(`=============================================================`);
});

module.exports = app;
