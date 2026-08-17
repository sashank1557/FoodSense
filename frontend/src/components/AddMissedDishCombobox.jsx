import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Search, PlusCircle, X, Sparkles, MapPin, Tag, ChevronDown, Check, Flame, Activity } from 'lucide-react';
import { searchDishes, fetchDishCategories, saveCustomDish } from '../services/api';

export default function AddMissedDishCombobox({ onSelectDish, onClose }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [categories, setCategories] = useState([]);
  const [regions, setRegions] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [selectedRegion, setSelectedRegion] = useState('All');
  
  // Custom dish modal state
  const [isCustomModalOpen, setIsCustomModalOpen] = useState(false);
  const [customForm, setCustomForm] = useState({
    name: '',
    category: 'Curries & Gravies',
    region: 'North Indian',
    standard_portion: '1 bowl (200g)',
    calories: 220,
    protein: 8,
    carbs: 25,
    fat: 9,
    fiber: 3,
    gi: 50
  });
  const [isSavingCustom, setIsSavingCustom] = useState(false);

  const debounceTimerRef = useRef(null);
  const inputRef = useRef(null);
  const listRef = useRef(null);

  // Focus input on mount & load categories
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
    fetchDishCategories().then(data => {
      if (data?.categories) setCategories(data.categories);
      if (data?.regions) setRegions(data.regions);
    });
    // Trigger initial search
    performSearch('', 'All', 'All');
  }, []);

  // Debounced search
  const performSearch = useCallback(async (searchQuery, cat, reg) => {
    setIsLoading(true);
    try {
      const data = await searchDishes(searchQuery, {
        category: cat !== 'All' ? cat : null,
        region: reg !== 'All' ? reg : null,
        limit: 30
      });
      setResults(data?.dishes || []);
      setSelectedIndex(-1);
    } catch (err) {
      console.error('Error searching dishes:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleQueryChange = (e) => {
    const val = e.target.value;
    setQuery(val);
    if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    debounceTimerRef.current = setTimeout(() => {
      performSearch(val, selectedCategory, selectedRegion);
    }, 200);
  };

  const handleCategoryChange = (cat) => {
    setSelectedCategory(cat);
    performSearch(query, cat, selectedRegion);
  };

  const handleRegionChange = (reg) => {
    setSelectedRegion(reg);
    performSearch(query, selectedCategory, reg);
  };

  // Keyboard navigation
  const handleKeyDown = (e) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => (prev < results.length - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => (prev > 0 ? prev - 1 : results.length - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (selectedIndex >= 0 && selectedIndex < results.length) {
        handlePickDish(results[selectedIndex]);
      }
    } else if (e.key === 'Escape') {
      onClose();
    }
  };

  // Select dish and notify parent
  const handlePickDish = (dish) => {
    onSelectDish(dish);
  };

  // Handle custom dish form submit
  const handleSaveCustom = async (e) => {
    e.preventDefault();
    if (!customForm.name.trim()) return;
    setIsSavingCustom(true);
    try {
      const res = await saveCustomDish(customForm);
      if (res?.dish) {
        onSelectDish(res.dish);
      }
    } catch (err) {
      alert('Could not save custom dish: ' + err.message);
    } finally {
      setIsSavingCustom(false);
    }
  };

  return (
    <div style={{
      background: '#ffffff',
      border: '1px solid #bfdbfe',
      borderRadius: '16px',
      padding: '1.25rem',
      marginBottom: '1.5rem',
      boxShadow: '0 12px 30px rgba(37, 99, 235, 0.08)'
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.85rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{
            background: '#eff6ff',
            color: '#2563eb',
            padding: '0.4rem',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Search size={18} />
          </div>
          <div>
            <h4 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700, color: '#0f172a' }}>
              Add Missed Dish from 1,500+ Indian Catalog
            </h4>
            <span style={{ fontSize: '0.78rem', color: '#64748b' }}>
              Search across regional cuisines (North, South, Bengali, Gujarati, Mithai, etc.) or add a custom dish
            </span>
          </div>
        </div>

        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            color: '#94a3b8',
            cursor: 'pointer',
            padding: '4px',
            borderRadius: '6px'
          }}
        >
          <X size={18} />
        </button>
      </div>

      {/* Search Input Box */}
      <div style={{ position: 'relative', marginBottom: '0.75rem' }}>
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={handleQueryChange}
          onKeyDown={handleKeyDown}
          placeholder="Search by dish name (e.g. Rava Idli, Butter Chicken, Dal Tadka, Rasgulla)..."
          style={{
            width: '100%',
            padding: '0.65rem 2.5rem 0.65rem 1rem',
            borderRadius: '10px',
            border: '1.5px solid #93c5fd',
            fontSize: '0.9rem',
            fontWeight: 500,
            outline: 'none',
            boxShadow: '0 2px 6px rgba(0,0,0,0.02)',
            transition: 'border-color 0.15s'
          }}
        />
        {query && (
          <button
            onClick={() => { setQuery(''); performSearch('', selectedCategory, selectedRegion); }}
            style={{
              position: 'absolute',
              right: '12px',
              top: '50%',
              transform: 'translateY(-50%)',
              background: 'none',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer'
            }}
          >
            ✕
          </button>
        )}
      </div>

      {/* Filter Badges (Category & Region) */}
      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '0.85rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.75rem', color: '#64748b' }}>
          <Tag size={13} />
          <span>Category:</span>
          <select
            value={selectedCategory}
            onChange={(e) => handleCategoryChange(e.target.value)}
            style={{
              padding: '0.2rem 0.5rem',
              borderRadius: '6px',
              border: '1px solid #cbd5e1',
              fontSize: '0.75rem',
              background: '#f8fafc'
            }}
          >
            <option value="All">All Categories</option>
            {categories.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.75rem', color: '#64748b' }}>
          <MapPin size={13} />
          <span>Region:</span>
          <select
            value={selectedRegion}
            onChange={(e) => handleRegionChange(e.target.value)}
            style={{
              padding: '0.2rem 0.5rem',
              borderRadius: '6px',
              border: '1px solid #cbd5e1',
              fontSize: '0.75rem',
              background: '#f8fafc'
            }}
          >
            <option value="All">All Regions</option>
            {regions.map(r => <option key={r} value={r}>{r}</option>)}
          </select>
        </div>

        <button
          onClick={() => setIsCustomModalOpen(true)}
          style={{
            marginLeft: 'auto',
            background: 'none',
            border: '1px dashed #3b82f6',
            color: '#2563eb',
            padding: '0.2rem 0.6rem',
            borderRadius: '6px',
            fontSize: '0.75rem',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.3rem'
          }}
        >
          <PlusCircle size={13} />
          <span>Add Custom Dish</span>
        </button>
      </div>

      {/* Results Dropdown List */}
      <div
        ref={listRef}
        style={{
          maxHeight: '260px',
          overflowY: 'auto',
          borderRadius: '10px',
          border: '1px solid #e2e8f0',
          background: '#f8fafc'
        }}
      >
        {isLoading ? (
          <div style={{ padding: '1.5rem', textAlign: 'center', color: '#64748b', fontSize: '0.85rem' }}>
            Searching database...
          </div>
        ) : results.length === 0 ? (
          <div style={{ padding: '1.5rem', textAlign: 'center' }}>
            <p style={{ margin: '0 0 0.5rem', color: '#64748b', fontSize: '0.85rem' }}>
              No matching dishes found for "{query}".
            </p>
            <button
              onClick={() => {
                setCustomForm(prev => ({ ...prev, name: query }));
                setIsCustomModalOpen(true);
              }}
              className="btn btn-primary"
              style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem' }}
            >
              <PlusCircle size={13} />
              <span>Create "{query}" as Custom Dish</span>
            </button>
          </div>
        ) : (
          results.map((dish, idx) => {
            const isSelected = selectedIndex === idx;
            return (
              <div
                key={dish.id || idx}
                onClick={() => handlePickDish(dish)}
                onMouseEnter={() => setSelectedIndex(idx)}
                style={{
                  padding: '0.65rem 0.9rem',
                  borderBottom: idx < results.length - 1 ? '1px solid #f1f5f9' : 'none',
                  background: isSelected ? '#eff6ff' : '#ffffff',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  transition: 'background 0.1s'
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', marginBottom: '0.15rem' }}>
                    <span style={{ fontWeight: 600, fontSize: '0.88rem', color: '#0f172a' }}>
                      {dish.name}
                    </span>
                    <span style={{
                      fontSize: '0.68rem',
                      padding: '0.15rem 0.45rem',
                      borderRadius: '4px',
                      background: '#e0f2fe',
                      color: '#0369a1',
                      fontWeight: 600
                    }}>
                      {dish.region}
                    </span>
                    <span style={{
                      fontSize: '0.68rem',
                      padding: '0.15rem 0.45rem',
                      borderRadius: '4px',
                      background: '#f1f5f9',
                      color: '#475569',
                      fontWeight: 500
                    }}>
                      {dish.category}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.74rem', color: '#64748b' }}>
                    {dish.standard_portion} • Protein: {dish.protein}g • Carbs: {dish.carbs}g • Fat: {dish.fat}g • GI: {dish.gi}
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.25rem',
                    background: '#fef2f2',
                    color: '#dc2626',
                    padding: '0.25rem 0.5rem',
                    borderRadius: '6px',
                    fontSize: '0.78rem',
                    fontWeight: 700
                  }}>
                    <Flame size={12} />
                    <span>{Math.round(dish.calories)} kcal</span>
                  </div>

                  <button
                    className="btn btn-primary"
                    style={{ padding: '0.3rem 0.65rem', fontSize: '0.78rem' }}
                  >
                    Add
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Manual Custom Dish Entry Modal */}
      {isCustomModalOpen && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(15, 23, 42, 0.6)',
          backdropFilter: 'blur(4px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 999,
          padding: '1rem'
        }}>
          <div style={{
            background: '#ffffff',
            borderRadius: '16px',
            width: '100%',
            maxWidth: '520px',
            padding: '1.5rem',
            boxShadow: '0 20px 40px rgba(0,0,0,0.2)',
            maxHeight: '90vh',
            overflowY: 'auto'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <PlusCircle size={20} color="#2563eb" />
                <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, color: '#0f172a' }}>
                  Add Custom Indian Dish
                </h3>
              </div>
              <button
                onClick={() => setIsCustomModalOpen(false)}
                style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSaveCustom}>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#334155', marginBottom: '0.3rem' }}>
                  Dish Name *
                </label>
                <input
                  type="text"
                  required
                  value={customForm.name}
                  onChange={(e) => setCustomForm({ ...customForm, name: e.target.value })}
                  placeholder="e.g. Grandmother's Fenugreek Khichdi"
                  style={{
                    width: '100%',
                    padding: '0.55rem 0.75rem',
                    borderRadius: '8px',
                    border: '1px solid #cbd5e1',
                    fontSize: '0.88rem'
                  }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#334155', marginBottom: '0.3rem' }}>
                    Category
                  </label>
                  <select
                    value={customForm.category}
                    onChange={(e) => setCustomForm({ ...customForm, category: e.target.value })}
                    style={{ width: '100%', padding: '0.55rem', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '0.82rem' }}
                  >
                    {categories.length > 0 ? categories.map(c => <option key={c} value={c}>{c}</option>) : (
                      <>
                        <option value="Curries & Gravies">Curries & Gravies</option>
                        <option value="Breakfast">Breakfast</option>
                        <option value="Rice & Biryanis">Rice & Biryanis</option>
                        <option value="Breads & Rotis">Breads & Rotis</option>
                        <option value="Street Food & Chaats">Street Food & Chaats</option>
                        <option value="Sweets & Mithai">Sweets & Mithai</option>
                        <option value="Beverages">Beverages</option>
                      </>
                    )}
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#334155', marginBottom: '0.3rem' }}>
                    Region
                  </label>
                  <select
                    value={customForm.region}
                    onChange={(e) => setCustomForm({ ...customForm, region: e.target.value })}
                    style={{ width: '100%', padding: '0.55rem', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '0.82rem' }}
                  >
                    {regions.length > 0 ? regions.map(r => <option key={r} value={r}>{r}</option>) : (
                      <>
                        <option value="North Indian">North Indian</option>
                        <option value="South Indian">South Indian</option>
                        <option value="Punjabi">Punjabi</option>
                        <option value="Bengali">Bengali</option>
                        <option value="Gujarati">Gujarati</option>
                        <option value="Maharashtrian">Maharashtrian</option>
                        <option value="Pan-Indian">Pan-Indian</option>
                      </>
                    )}
                  </select>
                </div>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#334155', marginBottom: '0.3rem' }}>
                  Standard Portion Description
                </label>
                <input
                  type="text"
                  value={customForm.standard_portion}
                  onChange={(e) => setCustomForm({ ...customForm, standard_portion: e.target.value })}
                  placeholder="e.g. 1 bowl (200g), 2 pieces (90g)"
                  style={{ width: '100%', padding: '0.55rem 0.75rem', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '0.82rem' }}
                />
              </div>

              {/* Macros Matrix */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem', marginBottom: '1.25rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.72rem', fontWeight: 600, color: '#64748b', marginBottom: '0.2rem' }}>
                    Calories (kcal)
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={customForm.calories}
                    onChange={(e) => setCustomForm({ ...customForm, calories: parseFloat(e.target.value) || 0 })}
                    style={{ width: '100%', padding: '0.45rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.85rem' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.72rem', fontWeight: 600, color: '#64748b', marginBottom: '0.2rem' }}>
                    Protein (g)
                  </label>
                  <input
                    type="number"
                    min="0"
                    step="0.1"
                    value={customForm.protein}
                    onChange={(e) => setCustomForm({ ...customForm, protein: parseFloat(e.target.value) || 0 })}
                    style={{ width: '100%', padding: '0.45rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.85rem' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.72rem', fontWeight: 600, color: '#64748b', marginBottom: '0.2rem' }}>
                    Carbs (g)
                  </label>
                  <input
                    type="number"
                    min="0"
                    step="0.1"
                    value={customForm.carbs}
                    onChange={(e) => setCustomForm({ ...customForm, carbs: parseFloat(e.target.value) || 0 })}
                    style={{ width: '100%', padding: '0.45rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.85rem' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.72rem', fontWeight: 600, color: '#64748b', marginBottom: '0.2rem' }}>
                    Fat (g)
                  </label>
                  <input
                    type="number"
                    min="0"
                    step="0.1"
                    value={customForm.fat}
                    onChange={(e) => setCustomForm({ ...customForm, fat: parseFloat(e.target.value) || 0 })}
                    style={{ width: '100%', padding: '0.45rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.85rem' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.72rem', fontWeight: 600, color: '#64748b', marginBottom: '0.2rem' }}>
                    Fiber (g)
                  </label>
                  <input
                    type="number"
                    min="0"
                    step="0.1"
                    value={customForm.fiber}
                    onChange={(e) => setCustomForm({ ...customForm, fiber: parseFloat(e.target.value) || 0 })}
                    style={{ width: '100%', padding: '0.45rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.85rem' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.72rem', fontWeight: 600, color: '#64748b', marginBottom: '0.2rem' }}>
                    GI Index (0-100)
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={customForm.gi}
                    onChange={(e) => setCustomForm({ ...customForm, gi: parseInt(e.target.value, 10) || 50 })}
                    style={{ width: '100%', padding: '0.45rem', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '0.85rem' }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                <button
                  type="button"
                  onClick={() => setIsCustomModalOpen(false)}
                  className="btn btn-secondary"
                  style={{ fontSize: '0.85rem', padding: '0.5rem 1rem' }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSavingCustom}
                  className="btn btn-primary"
                  style={{ fontSize: '0.85rem', padding: '0.5rem 1.25rem' }}
                >
                  {isSavingCustom ? 'Saving...' : 'Save & Add to Meal'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
