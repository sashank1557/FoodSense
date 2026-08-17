/**
 * FoodSense - Food Item Correction & Retraining Dataset Route
 * Lets users (guest or authenticated) correct misclassifications or manually add missed items.
 * Queries Flask /lookup_item for authentic nutrition & KNN alternatives,
 * logs the correction event for future model retraining,
 * and updates user meal_history in SQLite if authenticated.
 */

const express = require('express');
const axios = require('axios');
const { authOptional } = require('../middleware/auth');
const { analyzeLimiter } = require('../middleware/rateLimiter');
const {
  logCorrection,
  getAllCorrections,
  getCorrectionsCount,
  updateMealHistoryItemsAndSummary,
  getDishById,
  insertCustomDish
} = require('../db/database');

const router = express.Router();
const FLASK_URL = process.env.FLASK_BACKEND_URL || 'http://127.0.0.1:5000';

// 20 Core ML-Trained Indian Food Classes
const VALID_CLASSES = [
  'burger', 'butter_naan', 'chai', 'chapati', 'chole_bhature',
  'dal_makhani', 'dhokla', 'fried_rice', 'idli', 'jalebi',
  'kaathi_rolls', 'kadai_paneer', 'kulfi', 'masala_dosa', 'momos',
  'paani_puri', 'pakode', 'pav_bhaji', 'pizza', 'samosa'
];

/**
 * POST /api/correct
 * Submit a manual classification correction or add a missed food item
 */
router.post('/', analyzeLimiter, authOptional, async (req, res, next) => {
  try {
    const {
      meal_id,
      original_label = 'unrecognized',
      corrected_label,
      correction_type = 'misclassified', // 'misclassified' or 'missed_item'
      item_bbox,
      bbox,
      all_items,
      custom_item
    } = req.body;

    if (!meal_id || (!corrected_label && !custom_item)) {
      return res.status(400).json({
        status: 'error',
        error: 'MISSING_FIELDS',
        message: 'meal_id and corrected_label (or custom_item) are required.'
      });
    }

    const effectiveBbox = item_bbox || bbox || [40, 40, 600, 600];
    let itemInfo = null;
    let finalLabel = corrected_label ? corrected_label.trim().toLowerCase().replace(/ /g, '_') : 'custom_dish';

    // Strategy 1: Core 20-class lookup from Flask Inference Engine
    if (corrected_label && VALID_CLASSES.includes(finalLabel)) {
      try {
        const flaskRes = await axios.post(`${FLASK_URL}/lookup_item`, {
          label: finalLabel
        }, { timeout: 5000 });
        itemInfo = flaskRes.data?.item;
      } catch (flaskErr) {
        console.warn('[Express Correct] Flask lookup error:', flaskErr.message);
      }
    }

    // Strategy 2: Expanded 1500+ Indian dishes database lookup
    if (!itemInfo && corrected_label) {
      const dbDish = getDishById(corrected_label) || getDishById(finalLabel);
      if (dbDish) {
        finalLabel = dbDish.id || finalLabel;
        itemInfo = {
          label: dbDish.id,
          display_name: dbDish.name,
          confidence: 1.0,
          portion: dbDish.standard_portion,
          category: dbDish.category,
          region: dbDish.region,
          macros: {
            calories: Number(dbDish.calories),
            protein: Number(dbDish.protein),
            carbs: Number(dbDish.carbs),
            fat: Number(dbDish.fat),
            fiber: Number(dbDish.fiber),
            gi: Number(dbDish.gi)
          },
          healthy_alternative: null
        };
      }
    }

    // Strategy 3: User Custom Dish manual insertion
    if (!itemInfo && custom_item) {
      const saved = insertCustomDish(custom_item);
      finalLabel = saved.id;
      itemInfo = {
        label: saved.id,
        display_name: saved.name,
        confidence: 1.0,
        portion: saved.standard_portion,
        category: saved.category,
        region: saved.region,
        macros: {
          calories: Number(saved.calories),
          protein: Number(saved.protein),
          carbs: Number(saved.carbs),
          fat: Number(saved.fat),
          fiber: Number(saved.fiber),
          gi: Number(saved.gi)
        },
        healthy_alternative: null
      };
    }

    if (!itemInfo) {
      return res.status(400).json({
        status: 'error',
        error: 'INVALID_CLASS',
        message: `Class '${corrected_label}' was not found in the 1500+ Indian dishes database.`
      });
    }

    // Preserve bounding box
    const correctedItem = {
      ...itemInfo,
      bbox: effectiveBbox,
      is_manual_addition: correction_type === 'missed_item'
    };

    // 2. Log correction to database
    const logged = logCorrection({
      userId: req.user ? req.user.id : null,
      mealId: meal_id,
      originalLabel: original_label,
      correctedLabel: finalLabel,
      correctionType: correction_type,
      itemBbox: effectiveBbox
    });

    console.log(`[Express Correct] Logged ${correction_type} #${logged.id}: '${original_label}' -> '${finalLabel}' (User: ${req.user ? req.user.email : 'guest'})`);

    // 3. If all_items provided, recalculate whole meal summary & update meal_history
    let updatedSummary = null;
    let updatedItems = [];

    if (Array.isArray(all_items)) {
      if (correction_type === 'missed_item') {
        // Append newly added item
        updatedItems = [...all_items, correctedItem];
      } else {
        // Replace existing item matching bbox or original_label
        updatedItems = all_items.map(it => {
          const isTarget = effectiveBbox && it.bbox
            ? JSON.stringify(it.bbox) === JSON.stringify(effectiveBbox)
            : it.label === original_label;

          return isTarget ? correctedItem : it;
        });
      }

      // Recalculate whole-meal aggregate summary
      let totCal = 0;
      let totProt = 0;
      let totCarb = 0;
      let totFat = 0;
      let totFib = 0;
      let giSum = 0;

      updatedItems.forEach(it => {
        const m = it.macros || {};
        totCal += m.calories || 0;
        totProt += m.protein || 0;
        totCarb += m.carbs || 0;
        totFat += m.fat || 0;
        totFib += m.fiber || 0;
        giSum += m.gi || 50;
      });

      const avgGi = updatedItems.length > 0 ? Math.round(giSum / updatedItems.length) : 50;

      updatedSummary = {
        total_items: updatedItems.length,
        total_calories: Math.round(totCal * 10) / 10,
        total_protein: Math.round(totProt * 10) / 10,
        total_carbs: Math.round(totCarb * 10) / 10,
        total_fat: Math.round(totFat * 10) / 10,
        total_fiber: Math.round(totFib * 10) / 10,
        average_gi: avgGi,
        dietary_note: totCal > 800
          ? 'High-calorie meal. Consider replacing high-fat gravies with steamed or grilled items.'
          : 'Well-balanced macronutrient meal.'
      };

      if (req.user) {
        try {
          updateMealHistoryItemsAndSummary({
            userId: req.user.id,
            mealId: meal_id,
            updatedItems,
            updatedSummary
          });
          console.log(`[Express Correct] Updated stored meal_history record for meal ${meal_id}`);
        } catch (dbErr) {
          console.warn('[Express Correct] Warning: Could not update history record:', dbErr.message);
        }
      }
    }

    return res.status(200).json({
      status: 'success',
      message: correction_type === 'missed_item'
        ? `Added '${finalLabel}' to meal analysis.`
        : `Item successfully corrected from '${original_label}' to '${finalLabel}'.`,
      corrected_item: correctedItem,
      items: updatedItems.length > 0 ? updatedItems : undefined,
      meal_summary: updatedSummary,
      logged_correction: logged
    });

  } catch (err) {
    next(err);
  }
});

/**
 * GET /api/corrections/export & GET /api/corrections
 * Export all logged corrections for future dataset training/retraining
 */
router.get('/export', (req, res, next) => {
  try {
    const limit = Math.min(1000, parseInt(req.query.limit || '500', 10));
    const offset = parseInt(req.query.offset || '0', 10);

    const corrections = getAllCorrections({ limit, offset });
    const totalCount = getCorrectionsCount();

    return res.status(200).json({
      status: 'success',
      export_timestamp: new Date().toISOString(),
      total_count: totalCount,
      count: corrections.length,
      corrections: corrections
    });
  } catch (err) {
    next(err);
  }
});

router.get('/', (req, res, next) => {
  res.redirect('/api/corrections/export');
});

module.exports = router;
