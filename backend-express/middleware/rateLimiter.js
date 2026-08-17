/**
 * FoodSense - Rate Limiter Middleware
 * Protects inference endpoint against overload while allowing smooth interactive use.
 */

const rateLimit = require('express-rate-limit');

// Limiter for meal analysis (allows 30 analyses per 15 minutes per IP)
const analyzeLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 30,
  standardHeaders: true,
  legacyHeaders: false,
  message: {
    error: 'Too Many Requests',
    message: 'Meal analysis limit reached. Please wait a few moments before scanning another meal.'
  }
});

// General API limiter for health / metadata routes
const generalLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 120,
  standardHeaders: true,
  legacyHeaders: false
});

module.exports = {
  analyzeLimiter,
  generalLimiter
};
