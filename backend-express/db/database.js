/**
 * FoodSense - SQLite Database Layer
 * Lightweight embedded database for user authentication, meal history & corrections.
 * Supports persistent Railway volume mounts (RAILWAY_VOLUME_MOUNT_PATH).
 */

const path = require('path');
const fs = require('fs');
const Database = require('better-sqlite3');

// Persistent storage location: checks Railway volume mount first, falls back to local data directory
const DB_DIR = process.env.RAILWAY_VOLUME_MOUNT_PATH || process.env.DATA_DIR || path.join(__dirname, '..', 'data');
if (!fs.existsSync(DB_DIR)) {
  fs.mkdirSync(DB_DIR, { recursive: true });
}

const DB_PATH = path.join(DB_DIR, 'foodsense.db');
console.log(`[Database] Initializing SQLite at: ${DB_PATH}`);
const db = new Database(DB_PATH);

// Enable WAL mode for high performance and concurrency
db.pragma('journal_mode = WAL');

// Initialize schema
db.exec(`
  CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL COLLATE NOCASE,
    password TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );

  CREATE TABLE IF NOT EXISTS meal_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    meal_id TEXT NOT NULL,
    items TEXT NOT NULL,
    meal_summary TEXT NOT NULL,
    image_preview TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
  );

  CREATE INDEX IF NOT EXISTS idx_meal_user_date ON meal_history(user_id, created_at);

  CREATE TABLE IF NOT EXISTS corrections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    meal_id TEXT NOT NULL,
    original_label TEXT NOT NULL,
    corrected_label TEXT NOT NULL,
    correction_type TEXT DEFAULT 'misclassified',
    item_bbox TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
  );

  CREATE INDEX IF NOT EXISTS idx_corrections_meal ON corrections(meal_id);
  CREATE INDEX IF NOT EXISTS idx_corrections_class ON corrections(corrected_label);

  CREATE TABLE IF NOT EXISTS dishes (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL COLLATE NOCASE,
    category TEXT NOT NULL COLLATE NOCASE,
    region TEXT NOT NULL COLLATE NOCASE,
    calories REAL NOT NULL,
    protein REAL NOT NULL,
    carbs REAL NOT NULL,
    fat REAL NOT NULL,
    fiber REAL NOT NULL,
    gi INTEGER NOT NULL,
    standard_portion TEXT NOT NULL,
    dietary_type TEXT NOT NULL DEFAULT 'Vegetarian',
    source_type TEXT NOT NULL DEFAULT 'estimated',
    tags TEXT NOT NULL DEFAULT '[]',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );

  CREATE INDEX IF NOT EXISTS idx_dishes_name ON dishes(name);
  CREATE INDEX IF NOT EXISTS idx_dishes_category ON dishes(category);
  CREATE INDEX IF NOT EXISTS idx_dishes_region ON dishes(region);
`);

// Auto-seed dishes table from data/dishes.json if empty
try {
  const dishCount = db.prepare('SELECT COUNT(*) as count FROM dishes').get().count;
  if (dishCount < 100) {
    const dishesJsonPath = [
      path.join(__dirname, '..', '..', 'data', 'dishes.json'),
      path.join(__dirname, '..', 'data', 'dishes.json'),
      path.join(process.cwd(), 'data', 'dishes.json')
    ].find(p => fs.existsSync(p));

    if (dishesJsonPath) {
      const rawDishes = JSON.parse(fs.readFileSync(dishesJsonPath, 'utf-8'));
      const insertDishStmt = db.prepare(`
        INSERT OR REPLACE INTO dishes (
          id, name, category, region, calories, protein, carbs, fat, fiber, gi, standard_portion, dietary_type, source_type, tags
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `);

      const insertMany = db.transaction((dishesList) => {
        for (const d of dishesList) {
          insertDishStmt.run(
            d.id,
            d.name,
            d.category || 'General',
            d.region || 'Pan-Indian',
            Number(d.calories) || 0,
            Number(d.protein) || 0,
            Number(d.carbs) || 0,
            Number(d.fat) || 0,
            Number(d.fiber) || 0,
            Number(d.gi) || 50,
            d.standard_portion || '1 serving (150g)',
            d.dietary_type || 'Vegetarian',
            d.source_type || 'estimated',
            Array.isArray(d.tags) ? JSON.stringify(d.tags) : '[]'
          );
        }
      });

      insertMany(rawDishes);
      console.log(`[Database] Successfully seeded ${rawDishes.length} dishes into SQLite 'dishes' table.`);
    }
  }
} catch (seedErr) {
  console.warn('[Database] Dish auto-seeding warning:', seedErr.message);
}

// Graceful migration: ensure correction_type column exists
try {
  db.exec(`ALTER TABLE corrections ADD COLUMN correction_type TEXT DEFAULT 'misclassified'`);
} catch (e) {
  // Column already exists
}

/**
 * User Operations
 */
const createUser = ({ email, passwordHash, name }) => {
  const stmt = db.prepare(`
    INSERT INTO users (email, password, name)
    VALUES (?, ?, ?)
  `);
  const info = stmt.run(email.trim().toLowerCase(), passwordHash, name.trim());
  return { id: info.lastInsertRowid, email: email.trim().toLowerCase(), name: name.trim() };
};

const findUserByEmail = (email) => {
  const stmt = db.prepare(`
    SELECT * FROM users WHERE email = ? LIMIT 1
  `);
  return stmt.get(email.trim().toLowerCase());
};

const findUserById = (id) => {
  const stmt = db.prepare(`
    SELECT id, email, name, created_at FROM users WHERE id = ? LIMIT 1
  `);
  return stmt.get(id);
};

/**
 * Meal History Operations
 */
const saveMealHistory = ({ userId, mealId, items, mealSummary, imagePreview = null }) => {
  const stmt = db.prepare(`
    INSERT INTO meal_history (user_id, meal_id, items, meal_summary, image_preview)
    VALUES (?, ?, ?, ?, ?)
  `);
  const itemsJson = typeof items === 'string' ? items : JSON.stringify(items || []);
  const summaryJson = typeof mealSummary === 'string' ? mealSummary : JSON.stringify(mealSummary || {});
  
  const info = stmt.run(userId, mealId, itemsJson, summaryJson, imagePreview);
  return {
    id: info.lastInsertRowid,
    user_id: userId,
    meal_id: mealId,
    items: typeof items === 'string' ? JSON.parse(items) : items,
    meal_summary: typeof mealSummary === 'string' ? JSON.parse(mealSummary) : mealSummary,
    image_preview: imagePreview,
    created_at: new Date().toISOString()
  };
};

const getUserMealHistory = ({ userId, limit = 50, offset = 0 }) => {
  const stmt = db.prepare(`
    SELECT id, meal_id, items, meal_summary, image_preview, created_at
    FROM meal_history
    WHERE user_id = ?
    ORDER BY created_at DESC
    LIMIT ? OFFSET ?
  `);
  const rows = stmt.all(userId, limit, offset);
  return rows.map(r => ({
    id: r.id,
    meal_id: r.meal_id,
    items: JSON.parse(r.items),
    meal_summary: JSON.parse(r.meal_summary),
    image_preview: r.image_preview,
    created_at: r.created_at
  }));
};

const updateMealHistoryItemsAndSummary = ({ userId, mealId, updatedItems, updatedSummary }) => {
  const stmt = db.prepare(`
    UPDATE meal_history
    SET items = ?, meal_summary = ?
    WHERE user_id = ? AND meal_id = ?
  `);
  const itemsJson = JSON.stringify(updatedItems);
  const summaryJson = JSON.stringify(updatedSummary);
  const info = stmt.run(itemsJson, summaryJson, userId, mealId);
  return info.changes > 0;
};

const getDailyMealTotals = ({ userId, dateString }) => {
  const targetDate = dateString || new Date().toISOString().split('T')[0];
  
  const stmt = db.prepare(`
    SELECT id, meal_id, items, meal_summary, image_preview, created_at
    FROM meal_history
    WHERE user_id = ? AND date(created_at) = date(?)
    ORDER BY created_at ASC
  `);
  const rows = stmt.all(userId, targetDate);

  let totalCalories = 0;
  let totalProtein = 0;
  let totalCarbs = 0;
  let totalFat = 0;
  let totalFiber = 0;
  let totalGiSum = 0;
  let validGiCount = 0;

  const meals = rows.map(r => {
    const summary = JSON.parse(r.meal_summary);
    const items = JSON.parse(r.items);

    const cal = summary.total_calories || summary.calories || 0;
    const prot = summary.total_protein || summary.protein || 0;
    const carbs = summary.total_carbs || summary.carbs || 0;
    const fat = summary.total_fat || summary.fat || 0;
    const fiber = summary.total_fiber || summary.fiber || 0;
    const gi = summary.average_gi || 50;

    totalCalories += cal;
    totalProtein += prot;
    totalCarbs += carbs;
    totalFat += fat;
    totalFiber += fiber;
    if (gi > 0) {
      totalGiSum += gi;
      validGiCount++;
    }

    return {
      id: r.id,
      meal_id: r.meal_id,
      items: items,
      meal_summary: summary,
      image_preview: r.image_preview,
      created_at: r.created_at
    };
  });

  const avgGi = validGiCount > 0 ? Math.round(totalGiSum / validGiCount) : 0;

  return {
    date: targetDate,
    total_meals: meals.length,
    totals: {
      total_calories: Math.round(totalCalories),
      total_protein: Math.round(totalProtein * 10) / 10,
      total_carbs: Math.round(totalCarbs * 10) / 10,
      total_fat: Math.round(totalFat * 10) / 10,
      total_fiber: Math.round(totalFiber * 10) / 10,
      average_gi: avgGi
    },
    meals: meals
  };
};

const deleteMealHistory = ({ id, userId }) => {
  const stmt = db.prepare(`
    DELETE FROM meal_history WHERE id = ? AND user_id = ?
  `);
  const info = stmt.run(id, userId);
  return info.changes > 0;
};

/**
 * Corrections Operations
 */
const logCorrection = ({
  userId = null,
  mealId,
  originalLabel,
  correctedLabel,
  correctionType = 'misclassified',
  itemBbox = null
}) => {
  const stmt = db.prepare(`
    INSERT INTO corrections (user_id, meal_id, original_label, corrected_label, correction_type, item_bbox)
    VALUES (?, ?, ?, ?, ?, ?)
  `);
  const bboxJson = itemBbox ? (typeof itemBbox === 'string' ? itemBbox : JSON.stringify(itemBbox)) : null;
  const info = stmt.run(userId, mealId, originalLabel, correctedLabel, correctionType, bboxJson);

  return {
    id: info.lastInsertRowid,
    user_id: userId,
    meal_id: mealId,
    original_label: originalLabel,
    corrected_label: correctedLabel,
    correction_type: correctionType,
    item_bbox: itemBbox,
    created_at: new Date().toISOString()
  };
};

const getAllCorrections = ({ limit = 100, offset = 0 } = {}) => {
  const stmt = db.prepare(`
    SELECT c.id, c.user_id, u.email as user_email, c.meal_id, c.original_label, c.corrected_label, c.correction_type, c.item_bbox, c.created_at
    FROM corrections c
    LEFT JOIN users u ON c.user_id = u.id
    ORDER BY c.created_at DESC
    LIMIT ? OFFSET ?
  `);
  const rows = stmt.all(limit, offset);
  return rows.map(r => ({
    id: r.id,
    user_id: r.user_id,
    user_email: r.user_email || 'guest',
    meal_id: r.meal_id,
    original_label: r.original_label,
    corrected_label: r.corrected_label,
    correction_type: r.correction_type || 'misclassified',
    item_bbox: r.item_bbox ? JSON.parse(r.item_bbox) : null,
    created_at: r.created_at
  }));
};

const getCorrectionsCount = () => {
  const stmt = db.prepare(`SELECT COUNT(*) as count FROM corrections`);
  return stmt.get().count;
};

/**
 * 1500+ Indian Dishes Database Operations
 */
const searchDishes = ({ q = '', category = null, region = null, dietaryType = null, limit = 25, offset = 0 } = {}) => {
  let queryParts = ['1=1'];
  const params = [];

  const cleanQ = (q || '').trim();
  if (cleanQ) {
    queryParts.push(`(name LIKE ? OR tags LIKE ? OR category LIKE ? OR region LIKE ?)`);
    const likePattern = `%${cleanQ}%`;
    params.push(likePattern, likePattern, likePattern, likePattern);
  }

  if (category && category !== 'All') {
    queryParts.push(`category = ? COLLATE NOCASE`);
    params.push(category.trim());
  }

  if (region && region !== 'All') {
    queryParts.push(`region = ? COLLATE NOCASE`);
    params.push(region.trim());
  }

  if (dietaryType && dietaryType !== 'All') {
    queryParts.push(`dietary_type = ? COLLATE NOCASE`);
    params.push(dietaryType.trim());
  }

  const whereClause = queryParts.join(' AND ');

  // Fetch count
  const countStmt = db.prepare(`SELECT COUNT(*) as total FROM dishes WHERE ${whereClause}`);
  const totalCount = countStmt.get(...params).total;

  // Exact matches first, then prefix matches, then substring
  let orderBy = 'name ASC';
  if (cleanQ) {
    orderBy = `
      CASE
        WHEN name = '${cleanQ.replace(/'/g, "''")}' THEN 1
        WHEN name LIKE '${cleanQ.replace(/'/g, "''")}%' THEN 2
        ELSE 3
      END, name ASC
    `;
  }

  const stmt = db.prepare(`
    SELECT id, name, category, region, calories, protein, carbs, fat, fiber, gi, standard_portion, dietary_type, source_type, tags
    FROM dishes
    WHERE ${whereClause}
    ORDER BY ${orderBy}
    LIMIT ? OFFSET ?
  `);

  const rows = stmt.all(...params, Number(limit) || 25, Number(offset) || 0);

  return {
    total: totalCount,
    limit: Number(limit) || 25,
    offset: Number(offset) || 0,
    dishes: rows.map(r => ({
      ...r,
      tags: typeof r.tags === 'string' ? JSON.parse(r.tags || '[]') : r.tags
    }))
  };
};

const getDishById = (id) => {
  if (!id) return null;
  const stmt = db.prepare(`SELECT * FROM dishes WHERE id = ? OR name = ? COLLATE NOCASE LIMIT 1`);
  const row = stmt.get(id, id);
  if (!row) return null;
  return {
    ...row,
    tags: typeof row.tags === 'string' ? JSON.parse(row.tags || '[]') : row.tags
  };
};

const getDishCategoriesAndRegions = () => {
  const catRows = db.prepare(`SELECT DISTINCT category FROM dishes WHERE category IS NOT NULL AND category != '' ORDER BY category ASC`).all();
  const regRows = db.prepare(`SELECT DISTINCT region FROM dishes WHERE region IS NOT NULL AND region != '' ORDER BY region ASC`).all();
  return {
    categories: catRows.map(r => r.category),
    regions: regRows.map(r => r.region),
    total_dishes: db.prepare('SELECT COUNT(*) as c FROM dishes').get().c
  };
};

const insertCustomDish = (dish) => {
  const cleanName = (dish.name || 'Custom Dish').trim();
  const id = dish.id || cleanName.toLowerCase().replace(/[^a-z0-9_]/g, '_') + '_' + Date.now();
  const stmt = db.prepare(`
    INSERT OR REPLACE INTO dishes (
      id, name, category, region, calories, protein, carbs, fat, fiber, gi, standard_portion, dietary_type, source_type, tags
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);

  stmt.run(
    id,
    cleanName,
    dish.category || 'Custom',
    dish.region || 'User Created',
    Number(dish.calories) || 200,
    Number(dish.protein) || 5,
    Number(dish.carbs) || 25,
    Number(dish.fat) || 5,
    Number(dish.fiber) || 2,
    Number(dish.gi) || 50,
    dish.standard_portion || '1 serving (150g)',
    dish.dietary_type || 'Vegetarian',
    'user_custom',
    JSON.stringify(dish.tags || ['custom'])
  );

  return getDishById(id);
};

module.exports = {
  db,
  DB_PATH,
  createUser,
  findUserByEmail,
  findUserById,
  saveMealHistory,
  getUserMealHistory,
  updateMealHistoryItemsAndSummary,
  getDailyMealTotals,
  deleteMealHistory,
  logCorrection,
  getAllCorrections,
  getCorrectionsCount,
  searchDishes,
  getDishById,
  getDishCategoriesAndRegions,
  insertCustomDish
};
