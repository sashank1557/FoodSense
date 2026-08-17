/**
 * FoodSense - Meal History & Daily Totals Routes
 * Provides meal persistence, historical pagination, and daily aggregate dashboards.
 */

const express = require('express');
const { authRequired } = require('../middleware/auth');
const {
  getUserMealHistory,
  getDailyMealTotals,
  saveMealHistory,
  deleteMealHistory
} = require('../db/database');

const router = express.Router();

// Protect all history endpoints with JWT authentication
router.use(authRequired);

// GET /api/history — Retrieve paginated meal history for logged-in user
router.get('/', (req, res, next) => {
  try {
    const limit = Math.min(100, parseInt(req.query.limit || '50', 10));
    const offset = parseInt(req.query.offset || '0', 10);

    const history = getUserMealHistory({
      userId: req.user.id,
      limit,
      offset
    });

    return res.status(200).json({
      status: 'success',
      count: history.length,
      history: history
    });
  } catch (err) {
    next(err);
  }
});

// GET /api/history/daily-totals?date=YYYY-MM-DD — Get aggregated totals for a given day
router.get('/daily-totals', (req, res, next) => {
  try {
    const dateParam = req.query.date; // e.g. '2026-08-15'
    const dailyData = getDailyMealTotals({
      userId: req.user.id,
      dateString: dateParam
    });

    return res.status(200).json({
      status: 'success',
      ...dailyData
    });
  } catch (err) {
    next(err);
  }
});

// POST /api/history — Explicitly save a meal analysis
router.post('/', (req, res, next) => {
  try {
    const { meal_id, items, meal_summary, image_preview } = req.body;

    if (!items || !meal_summary) {
      return res.status(400).json({
        status: 'error',
        error: 'INVALID_MEAL_DATA',
        message: 'items and meal_summary are required.'
      });
    }

    const saved = saveMealHistory({
      userId: req.user.id,
      mealId: meal_id || `meal_${Date.now()}`,
      items,
      mealSummary: meal_summary,
      imagePreview: image_preview || null
    });

    return res.status(201).json({
      status: 'success',
      meal: saved
    });
  } catch (err) {
    next(err);
  }
});

// DELETE /api/history/:id — Delete a meal entry
router.delete('/:id', (req, res, next) => {
  try {
    const mealEntryId = parseInt(req.params.id, 10);
    const success = deleteMealHistory({
      id: mealEntryId,
      userId: req.user.id
    });

    if (!success) {
      return res.status(404).json({
        status: 'error',
        error: 'NOT_FOUND',
        message: 'Meal not found or not owned by user.'
      });
    }

    return res.status(200).json({
      status: 'success',
      message: 'Meal removed from history.'
    });
  } catch (err) {
    next(err);
  }
});

module.exports = router;
