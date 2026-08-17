/**
 * FoodSense - Auth Routes
 * Signup, Login, and Session Verification with bcrypt and JWT.
 */

const express = require('express');
const bcrypt = require('bcryptjs');
const { createUser, findUserByEmail, findUserById } = require('../db/database');
const { generateToken, authRequired } = require('../middleware/auth');

const router = express.Router();

// POST /api/auth/signup
router.post('/signup', async (req, res, next) => {
  try {
    const { email, password, name } = req.body;

    if (!email || !password || !name) {
      return res.status(400).json({
        status: 'error',
        error: 'MISSING_FIELDS',
        message: 'Name, email, and password are required.'
      });
    }

    if (password.length < 6) {
      return res.status(400).json({
        status: 'error',
        error: 'WEAK_PASSWORD',
        message: 'Password must be at least 6 characters.'
      });
    }

    const existingUser = findUserByEmail(email);
    if (existingUser) {
      return res.status(409).json({
        status: 'error',
        error: 'EMAIL_ALREADY_EXISTS',
        message: 'An account with this email already exists. Please log in.'
      });
    }

    const salt = await bcrypt.genSalt(10);
    const passwordHash = await bcrypt.hash(password, salt);

    const user = createUser({ email, passwordHash, name });
    const token = generateToken(user);

    return res.status(201).json({
      status: 'success',
      message: 'Account created successfully.',
      user: {
        id: user.id,
        email: user.email,
        name: user.name
      },
      token: token
    });

  } catch (err) {
    next(err);
  }
});

// POST /api/auth/login
router.post('/login', async (req, res, next) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({
        status: 'error',
        error: 'MISSING_CREDENTIALS',
        message: 'Email and password are required.'
      });
    }

    const user = findUserByEmail(email);
    if (!user) {
      return res.status(401).json({
        status: 'error',
        error: 'INVALID_CREDENTIALS',
        message: 'Invalid email or password.'
      });
    }

    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) {
      return res.status(401).json({
        status: 'error',
        error: 'INVALID_CREDENTIALS',
        message: 'Invalid email or password.'
      });
    }

    const token = generateToken(user);

    return res.status(200).json({
      status: 'success',
      message: 'Logged in successfully.',
      user: {
        id: user.id,
        email: user.email,
        name: user.name
      },
      token: token
    });

  } catch (err) {
    next(err);
  }
});

// GET /api/auth/me
router.get('/me', authRequired, (req, res) => {
  return res.status(200).json({
    status: 'success',
    user: req.user
  });
});

module.exports = router;
