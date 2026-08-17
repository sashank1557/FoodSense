/**
 * FoodSense - JWT Auth Middleware
 * Supports both required auth (history endpoints) and optional auth (analyze relay).
 */

const jwt = require('jsonwebtoken');
const { findUserById } = require('../db/database');

const JWT_SECRET = process.env.JWT_SECRET || 'foodsense_super_secret_jwt_key_2026';

/**
 * Strict authentication: Blocks unauthorized requests (401)
 */
const authRequired = (req, res, next) => {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({
      status: 'error',
      error: 'UNAUTHORIZED',
      message: 'Authentication required. Please log in.'
    });
  }

  const token = authHeader.split(' ')[1];
  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    const user = findUserById(decoded.userId);
    if (!user) {
      return res.status(401).json({
        status: 'error',
        error: 'USER_NOT_FOUND',
        message: 'Invalid session. User no longer exists.'
      });
    }

    req.user = user;
    next();
  } catch (err) {
    return res.status(401).json({
      status: 'error',
      error: 'INVALID_TOKEN',
      message: 'Session expired or invalid token. Please log in again.'
    });
  }
};

/**
 * Optional authentication: Attaches user if valid JWT present, otherwise proceeds as guest
 */
const authOptional = (req, res, next) => {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    req.user = null;
    return next();
  }

  const token = authHeader.split(' ')[1];
  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    const user = findUserById(decoded.userId);
    req.user = user || null;
  } catch (err) {
    req.user = null;
  }

  next();
};

const generateToken = (user) => {
  return jwt.sign(
    { userId: user.id, email: user.email },
    JWT_SECRET,
    { expiresIn: '30d' }
  );
};

module.exports = {
  authRequired,
  authOptional,
  generateToken,
  JWT_SECRET
};
