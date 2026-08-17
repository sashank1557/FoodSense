/**
 * FoodSense - Express Health & Relay Status Route
 * Provides unified health status of Express relay + upstream Flask inference engine.
 */

const express = require('express');
const axios = require('axios');
const router = express.Router();

const FLASK_URL = process.env.FLASK_BACKEND_URL || 'http://127.0.0.1:5000';

router.get('/', async (req, res) => {
  const startTime = Date.now();
  let flaskStatus = { status: 'unreachable', latency_ms: null, models_ready: false };

  try {
    const flaskRes = await axios.get(`${FLASK_URL}/health`, { timeout: 5000 });
    flaskStatus = {
      status: flaskRes.data.status || 'healthy',
      latency_ms: Date.now() - startTime,
      models_ready: flaskRes.data.models_ready || true,
      supported_classes: flaskRes.data.supported_classes || 20,
      uptime_seconds: flaskRes.data.uptime_seconds
    };
  } catch (err) {
    flaskStatus = {
      status: 'cold_starting_or_unreachable',
      latency_ms: Date.now() - startTime,
      models_ready: false,
      message: err.message
    };
  }

  const isHealthy = flaskStatus.status === 'healthy';

  res.status(isHealthy ? 200 : 503).json({
    status: isHealthy ? 'healthy' : 'degraded',
    service: 'FoodSense-Express-Relay',
    timestamp: new Date().toISOString(),
    upstream_flask: flaskStatus
  });
});

module.exports = router;
