/**
 * FoodSense — 1500+ Indian Dishes Catalog & Search API
 * Exposes live debounced autocomplete search, filtering by category/region/diet, and custom dish persistence.
 */

const express = require('express');
const router = express.Router();
const {
  searchDishes,
  getDishById,
  getDishCategoriesAndRegions,
  insertCustomDish
} = require('../db/database');

/**
 * GET /api/dishes/search
 * Query parameters:
 *   q: string (Search query, partial or exact match)
 *   category: string (Category filter, e.g. "Breakfast", "Curries & Gravies")
 *   region: string (Regional filter, e.g. "South Indian", "Punjabi")
 *   dietary_type: string ("Vegetarian", "Non-Vegetarian", "Vegan")
 *   limit: number (default 25)
 *   offset: number (default 0)
 */
router.get('/search', (req, res) => {
  try {
    const { q, category, region, dietary_type, limit, offset } = req.query;

    const results = searchDishes({
      q: q || '',
      category: category || null,
      region: region || null,
      dietaryType: dietary_type || null,
      limit: parseInt(limit, 10) || 25,
      offset: parseInt(offset, 10) || 0
    });

    res.json({
      status: 'success',
      ...results
    });
  } catch (err) {
    console.error('[Dishes API] Search error:', err);
    res.status(500).json({
      status: 'error',
      error: 'SEARCH_FAILED',
      message: 'Failed to execute dish search: ' + err.message
    });
  }
});

/**
 * GET /api/dishes/categories
 * Returns distinct categories and regional groups for frontend filtering tags.
 */
router.get('/categories', (req, res) => {
  try {
    const metadata = getDishCategoriesAndRegions();
    res.json({
      status: 'success',
      ...metadata
    });
  } catch (err) {
    console.error('[Dishes API] Categories error:', err);
    res.status(500).json({
      status: 'error',
      error: 'FETCH_CATEGORIES_FAILED',
      message: 'Failed to retrieve categories: ' + err.message
    });
  }
});

/**
 * GET /api/dishes/:id
 * Retrieve full nutritional breakdown of a single dish.
 */
router.get('/:id', (req, res) => {
  try {
    const { id } = req.params;
    const dish = getDishById(id);

    if (!dish) {
      return res.status(404).json({
        status: 'error',
        error: 'DISH_NOT_FOUND',
        message: `Dish with ID '${id}' was not found in catalog.`
      });
    }

    res.json({
      status: 'success',
      dish
    });
  } catch (err) {
    console.error('[Dishes API] Get dish error:', err);
    res.status(500).json({
      status: 'error',
      error: 'FETCH_DISH_FAILED',
      message: 'Failed to retrieve dish: ' + err.message
    });
  }
});

/**
 * POST /api/dishes/custom
 * Allow users to add and persist a custom dish.
 */
router.post('/custom', (req, res) => {
  try {
    const { name, category, region, calories, protein, carbs, fat, fiber, gi, standard_portion, dietary_type, tags } = req.body;

    if (!name || typeof name !== 'string' || !name.trim()) {
      return res.status(400).json({
        status: 'error',
        error: 'INVALID_NAME',
        message: 'Dish name is required.'
      });
    }

    const createdDish = insertCustomDish({
      name: name.trim(),
      category: category || 'Custom',
      region: region || 'User Added',
      calories: Number(calories) || 200,
      protein: Number(protein) || 5,
      carbs: Number(carbs) || 25,
      fat: Number(fat) || 5,
      fiber: Number(fiber) || 2,
      gi: Number(gi) || 50,
      standard_portion: standard_portion || '1 serving (150g)',
      dietary_type: dietary_type || 'Vegetarian',
      tags: Array.isArray(tags) ? tags : ['custom']
    });

    res.status(201).json({
      status: 'success',
      message: `Custom dish '${createdDish.name}' saved successfully.`,
      dish: createdDish
    });
  } catch (err) {
    console.error('[Dishes API] Custom dish error:', err);
    res.status(500).json({
      status: 'error',
      error: 'CUSTOM_DISH_FAILED',
      message: 'Failed to create custom dish: ' + err.message
    });
  }
});

module.exports = router;
