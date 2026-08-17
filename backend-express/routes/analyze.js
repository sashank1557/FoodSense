/**
 * FoodSense - Analyze Route (Express Thin Relay Layer)
 * Validates multipart image upload, proxies to Flask inference engine,
 * and auto-saves to user history if authenticated.
 * Guest requests are 100% supported without friction.
 */

const express = require('express');
const multer = require('multer');
const axios = require('axios');
const FormData = require('form-data');
const { analyzeLimiter } = require('../middleware/rateLimiter');
const { authOptional } = require('../middleware/auth');
const { saveMealHistory } = require('../db/database');

const router = express.Router();
const FLASK_URL = process.env.FLASK_BACKEND_URL || 'http://127.0.0.1:5000';
const TIMEOUT_MS = parseInt(process.env.REQUEST_TIMEOUT_MS || '45000', 10);
const MAX_FILE_SIZE = parseInt(process.env.MAX_FILE_SIZE_MB || '15', 10) * 1024 * 1024;

// Multer in-memory storage supporting both 'image' and 'file' field names
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: MAX_FILE_SIZE },
  fileFilter: (req, file, cb) => {
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    if (file.mimetype.startsWith('image/') || allowedTypes.includes(file.mimetype.toLowerCase())) {
      cb(null, true);
    } else {
      const err = new Error('Invalid file type. Only image files (JPEG, PNG, WEBP) are supported.');
      err.statusCode = 400;
      cb(err, false);
    }
  }
});

// Middleware accepting either 'image' or 'file' field
const uploadImageMiddleware = (req, res, next) => {
  upload.fields([
    { name: 'image', maxCount: 1 },
    { name: 'file', maxCount: 1 }
  ])(req, res, (err) => {
    if (err) {
      if (err.code === 'LIMIT_FILE_SIZE') {
        return res.status(413).json({
          status: 'error',
          error: 'FILE_TOO_LARGE',
          message: `Image exceeds maximum allowed size of ${MAX_FILE_SIZE / (1024 * 1024)}MB.`
        });
      }
      return res.status(err.statusCode || 400).json({
        status: 'error',
        error: 'INVALID_UPLOAD',
        message: err.message
      });
    }

    // Normalize uploaded file into req.uploadedFile
    if (req.files) {
      if (req.files.image && req.files.image.length > 0) {
        req.uploadedFile = req.files.image[0];
      } else if (req.files.file && req.files.file.length > 0) {
        req.uploadedFile = req.files.file[0];
      }
    }

    next();
  });
};

router.post('/', analyzeLimiter, authOptional, uploadImageMiddleware, async (req, res, next) => {
  try {
    if (!req.uploadedFile) {
      return res.status(400).json({
        status: 'error',
        error: 'MISSING_IMAGE',
        message: 'No meal photo found in request. Please upload an image under form field "image" or "file".'
      });
    }

    const file = req.uploadedFile;
    console.log(`[Express Relay] Forwarding ${file.originalname} (${(file.size / 1024).toFixed(1)} KB) to Flask: ${FLASK_URL}/analyze`);

    // Construct multipart form payload for Flask
    const form = new FormData();
    form.append('file', file.buffer, {
      filename: file.originalname || 'meal_photo.jpg',
      contentType: file.mimetype || 'image/jpeg'
    });

    const startRelay = Date.now();

    // Forward to Flask with generous timeout for cold starts
    const flaskResponse = await axios.post(`${FLASK_URL}/analyze`, form, {
      headers: {
        ...form.getHeaders()
      },
      timeout: TIMEOUT_MS,
      maxContentLength: 20 * 1024 * 1024,
      maxBodyLength: 20 * 1024 * 1024
    });

    const relayDuration = Date.now() - startRelay;
    console.log(`[Express Relay] Received response from Flask in ${relayDuration}ms (HTTP ${flaskResponse.status})`);

    const resultData = flaskResponse.data;

    // If request is from an authenticated user, auto-save to meal history!
    if (req.user && resultData.status === 'success') {
      try {
        const savedMeal = saveMealHistory({
          userId: req.user.id,
          mealId: resultData.meal_id || `meal_${Date.now()}`,
          items: resultData.items,
          mealSummary: resultData.meal_summary,
          imagePreview: null // Can optionally store thumbnail or skip to save space
        });
        resultData.saved_to_history = true;
        resultData.history_id = savedMeal.id;
        console.log(`[Express Relay] Auto-saved meal ${resultData.meal_id} for user ${req.user.email} (Entry #${savedMeal.id})`);
      } catch (saveErr) {
        console.error('[Express Relay] Warning: Failed to auto-save meal history:', saveErr.message);
      }
    }

    // Relay standardized JSON response directly to client
    return res.status(flaskResponse.status).json(resultData);

  } catch (error) {
    if (error.code === 'ECONNREFUSED' || error.code === 'ETIMEDOUT' || error.code === 'ECONNABORTED') {
      console.warn(`[Express Relay] Flask backend unavailable (${error.code}). Probable cold start.`);
      return res.status(503).json({
        status: 'error',
        error: 'INFERENCE_BACKEND_COLD_START',
        message: 'AI inference backend is currently waking up from sleep. Please wait 10-15 seconds and try again.',
        code: error.code,
        upstream_target: FLASK_URL
      });
    }

    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }

    next(error);
  }
});

// Proxy route for supported classes metadata
router.get('/classes', async (req, res, next) => {
  try {
    const response = await axios.get(`${FLASK_URL}/classes`, { timeout: 10000 });
    res.status(200).json(response.data);
  } catch (error) {
    if (error.code === 'ECONNREFUSED' || error.code === 'ETIMEDOUT') {
      return res.status(503).json({
        status: 'error',
        error: 'INFERENCE_BACKEND_COLD_START',
        message: 'Inference backend is starting up.'
      });
    }
    next(error);
  }
});

module.exports = router;
