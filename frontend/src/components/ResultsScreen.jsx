import React, { useState, useEffect } from 'react';
import BoundingBoxCanvas from './BoundingBoxCanvas';
import NutritionSummary from './NutritionSummary';
import ItemDetailCard from './ItemDetailCard';
import { RotateCcw, Sparkles, Layers, Clock, CheckCircle2, PlusCircle, X, Info } from 'lucide-react';
import { submitMealCorrection } from '../services/api';

const ALL_CLASSES = [
  { id: 'burger', name: 'Burger' },
  { id: 'butter_naan', name: 'Butter Naan' },
  { id: 'chai', name: 'Masala Chai' },
  { id: 'chapati', name: 'Chapati (Roti)' },
  { id: 'chole_bhature', name: 'Chole Bhature' },
  { id: 'dal_makhani', name: 'Dal Makhani' },
  { id: 'dhokla', name: 'Khaman Dhokla' },
  { id: 'fried_rice', name: 'Fried Rice' },
  { id: 'idli', name: 'Steamed Idli' },
  { id: 'jalebi', name: 'Jalebi' },
  { id: 'kaathi_rolls', name: 'Kaathi Roll' },
  { id: 'kadai_paneer', name: 'Kadai Paneer' },
  { id: 'kulfi', name: 'Kesar Kulfi' },
  { id: 'masala_dosa', name: 'Masala Dosa' },
  { id: 'momos', name: 'Steamed Veg Momos' },
  { id: 'paani_puri', name: 'Paani Puri' },
  { id: 'pakode', name: 'Pakode (Pakora)' },
  { id: 'pav_bhaji', name: 'Pav Bhaji' },
  { id: 'pizza', name: 'Veg Pizza' },
  { id: 'samosa', name: 'Potato Samosa' }
];

export default function ResultsScreen({
  analysisData,
  previewUrl,
  onReset
}) {
  const [selectedItemId, setSelectedItemId] = useState(null);
  const [hoveredItemId, setHoveredItemId] = useState(null);
  const [swappedItems, setSwappedItems] = useState({});
  const [portionMultipliers, setPortionMultipliers] = useState({});
  const [currentItems, setCurrentItems] = useState([]);
  const [currentSummary, setCurrentSummary] = useState({});
  const [toastMessage, setToastMessage] = useState(null);
  const [isAddingMissedItem, setIsAddingMissedItem] = useState(false);
  const [missedItemClass, setMissedItemClass] = useState('masala_dosa');
  const [isSubmittingMissed, setIsSubmittingMissed] = useState(false);

  // Initialize and normalize items when analysisData loads
  useEffect(() => {
    const rawItems = analysisData?.items || analysisData?.detections || [];
    const baseSummary = analysisData?.meal_summary || analysisData?.meal_totals || {};

    const normalized = rawItems.map((item, idx) => ({
      ...item,
      item_id: item.item_id || item.label || `item_${idx}`,
      display_name: item.display_name || item.label?.replace(/_/g, ' ').toUpperCase(),
      macros: item.macros || item.nutrition || { calories: 0, protein: 0, carbs: 0, fat: 0, fiber: 0, gi: 50 },
      needs_confirmation: Boolean(item.needs_confirmation)
    }));

    setCurrentItems(normalized);
    setCurrentSummary(baseSummary);
  }, [analysisData]);

  const processingTimeMs = analysisData?.processing_time_ms || 180;

  // Handle portion adjustments
  const handlePortionChange = (itemId, multiplier) => {
    setPortionMultipliers(prev => ({
      ...prev,
      [itemId]: multiplier
    }));
  };

  // 1-Click confirm candidate items
  const handleConfirmSuggested = (item) => {
    setCurrentItems(prev => prev.map(it => {
      if (it.item_id === item.item_id) {
        return { ...it, needs_confirmation: false };
      }
      return it;
    }));
    setToastMessage(`Confirmed ${item.display_name}`);
    setTimeout(() => setToastMessage(null), 3000);
  };

  // Handle manual dish correction
  const handleClassCorrection = async (item, newClassId) => {
    try {
      const res = await submitMealCorrection({
        meal_id: analysisData.meal_id || 'meal_active',
        original_label: item.label,
        corrected_label: newClassId,
        correction_type: 'misclassified',
        bbox: item.bbox,
        all_items: currentItems
      });

      if (res.status === 'success' && res.corrected_item) {
        const updatedItem = {
          ...res.corrected_item,
          item_id: item.item_id,
          is_corrected: true,
          needs_confirmation: false
        };

        setCurrentItems(prev => prev.map(it => it.item_id === item.item_id ? updatedItem : it));
        if (res.meal_summary) {
          setCurrentSummary(res.meal_summary);
        }

        setToastMessage(`Corrected dish to ${updatedItem.display_name}`);
        setTimeout(() => setToastMessage(null), 3500);
      }
    } catch (err) {
      console.error('Correction failed:', err);
      throw err;
    }
  };

  // Handle adding a missed item
  const handleAddMissedItem = async () => {
    setIsSubmittingMissed(true);
    try {
      const res = await submitMealCorrection({
        meal_id: analysisData.meal_id || 'meal_active',
        original_label: 'unrecognized',
        corrected_label: missedItemClass,
        correction_type: 'missed_item',
        bbox: [40, 40, 600, 600],
        all_items: currentItems
      });

      if (res.status === 'success' && res.corrected_item) {
        const newItem = {
          ...res.corrected_item,
          item_id: `item_manual_${Date.now()}`,
          is_manual_addition: true,
          needs_confirmation: false
        };

        setCurrentItems(prev => [...prev, newItem]);
        if (res.meal_summary) {
          setCurrentSummary(res.meal_summary);
        }

        setIsAddingMissedItem(false);
        setToastMessage(`Added ${newItem.display_name} to meal analysis!`);
        setTimeout(() => setToastMessage(null), 3500);
      }
    } catch (err) {
      alert('Could not add missed item: ' + err.message);
    } finally {
      setIsSubmittingMissed(false);
    }
  };

  // Handle healthy swap toggles
  const handleSwapAlternative = (itemId, alternative) => {
    setSwappedItems(prev => {
      const copy = { ...prev };
      if (copy[itemId]) {
        delete copy[itemId];
      } else {
        copy[itemId] = alternative;
      }
      return copy;
    });
  };

  // Compute active aggregate totals based on portion multipliers and swaps
  let activeCalories = 0;
  let activeProtein = 0;
  let activeCarbs = 0;
  let activeFat = 0;
  let activeFiber = 0;
  let activeGiSum = 0;

  currentItems.forEach(item => {
    const id = item.item_id;
    const mult = portionMultipliers[id] || 1.0;
    const isSwapped = Boolean(swappedItems[id]);
    const activeMacros = isSwapped
      ? (swappedItems[id].macros || item.healthy_alternative?.macros || item.macros)
      : item.macros;

    activeCalories += (activeMacros.calories || 0) * mult;
    activeProtein += (activeMacros.protein || 0) * mult;
    activeCarbs += (activeMacros.carbs || 0) * mult;
    activeFat += (activeMacros.fat || 0) * mult;
    activeFiber += (activeMacros.fiber || 0) * mult;
    activeGiSum += (activeMacros.gi || activeMacros.glycemic_index || 50);
  });

  const activeAvgGi = currentItems.length > 0 ? Math.round(activeGiSum / currentItems.length) : (currentSummary.average_gi || 50);

  const dynamicSummary = {
    total_items: currentItems.length,
    total_calories: Math.round(activeCalories),
    total_protein: Math.round(activeProtein * 10) / 10,
    total_carbs: Math.round(activeCarbs * 10) / 10,
    total_fat: Math.round(activeFat * 10) / 10,
    total_fiber: Math.round(activeFiber * 10) / 10,
    average_gi: activeAvgGi,
    dietary_note: currentSummary.dietary_note
  };

  const isAnySwapped = Object.keys(swappedItems).length > 0;
  const originalCalories = currentSummary.total_calories || currentSummary.calories || 0;

  return (
    <div style={{ maxWidth: '1120px', margin: '0 auto', paddingBottom: '3rem' }}>
      
      {/* Toast Notification */}
      {toastMessage && (
        <div style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          background: '#0f172a',
          color: '#ffffff',
          padding: '0.75rem 1.25rem',
          borderRadius: '12px',
          boxShadow: '0 10px 25px rgba(0,0,0,0.2)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          fontSize: '0.85rem',
          fontWeight: 600,
          zIndex: 100,
          border: '1px solid #334155'
        }}>
          <CheckCircle2 size={16} color="#10b981" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Top Banner Action Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '1.25rem',
        flexWrap: 'wrap',
        gap: '0.75rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <div style={{
            background: '#ecfdf5',
            color: '#059669',
            padding: '0.4rem 0.75rem',
            borderRadius: '9999px',
            fontSize: '0.82rem',
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem'
          }}>
            <Sparkles size={14} />
            <span>Analysis Complete</span>
          </div>
          <span style={{ fontSize: '0.82rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <Clock size={13} /> {processingTimeMs}ms inference
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <button
            onClick={() => setIsAddingMissedItem(true)}
            className="btn btn-secondary"
            style={{
              fontSize: '0.85rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              borderColor: '#cbd5e1',
              color: '#0f172a'
            }}
          >
            <PlusCircle size={15} color="#2563eb" />
            <span>Add Missed Dish</span>
          </button>

          <button
            onClick={onReset}
            className="btn btn-secondary"
            style={{ fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
          >
            <RotateCcw size={15} />
            <span>Analyze Another</span>
          </button>
        </div>
      </div>

      {/* Manual Missed Item Insertion Dialog */}
      {isAddingMissedItem && (
        <div style={{
          background: '#eff6ff',
          border: '1px solid #bfdbfe',
          borderRadius: '12px',
          padding: '1rem 1.25rem',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '0.75rem'
        }}>
          <div>
            <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#1e40af', marginBottom: '0.2rem' }}>
              Add an item missed by detection
            </div>
            <div style={{ fontSize: '0.78rem', color: '#3b82f6' }}>
              Select a dish from our 20 supported Indian food classes to include in your meal analysis:
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <select
              value={missedItemClass}
              onChange={(e) => setMissedItemClass(e.target.value)}
              style={{
                padding: '0.45rem 0.75rem',
                borderRadius: '8px',
                border: '1px solid #93c5fd',
                fontSize: '0.85rem',
                fontWeight: 600,
                background: '#ffffff'
              }}
            >
              {ALL_CLASSES.map(cls => (
                <option key={cls.id} value={cls.id}>
                  {cls.name}
                </option>
              ))}
            </select>

            <button
              onClick={handleAddMissedItem}
              disabled={isSubmittingMissed}
              className="btn btn-primary"
              style={{ padding: '0.45rem 0.85rem', fontSize: '0.85rem' }}
            >
              {isSubmittingMissed ? 'Adding...' : 'Add Item'}
            </button>

            <button
              onClick={() => setIsAddingMissedItem(false)}
              style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', padding: '4px' }}
            >
              <X size={18} />
            </button>
          </div>
        </div>
      )}

      {/* Main Grid: Visuals & Item Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))',
        gap: '1.5rem',
        marginBottom: '2rem'
      }}>
        {/* Left Column: Bounding Box Image Canvas */}
        <div>
          <BoundingBoxCanvas
            imageUrl={previewUrl}
            imageMeta={analysisData?.image_meta}
            items={currentItems}
            selectedItemId={selectedItemId}
            hoveredItemId={hoveredItemId}
            onSelectItem={(id) => setSelectedItemId(prev => prev === id ? null : id)}
          />

          <div style={{
            marginTop: '0.75rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '0.78rem',
            color: '#64748b',
            padding: '0 0.5rem'
          }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
              <Layers size={13} /> {currentItems.length} food items localized
            </span>
            <span>Click any box to inspect & correct</span>
          </div>

          {/* Condiments Note */}
          <div style={{
            marginTop: '0.85rem',
            padding: '0.65rem 0.85rem',
            background: '#f8fafc',
            borderRadius: '10px',
            border: '1px solid #e2e8f0',
            fontSize: '0.75rem',
            color: '#64748b',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '0.45rem'
          }}>
            <Info size={14} color="#64748b" style={{ flexShrink: 0, marginTop: '2px' }} />
            <span>
              <strong>Note on Condiments:</strong> Sambar, chutneys, and pickles are tracked as complementary side accompaniments. If you wish to calculate primary macros for a specific side dish, use <strong>"Add Missed Dish"</strong> above.
            </span>
          </div>
        </div>

        {/* Right Column: Detected Food Item Cards */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h4 style={{ fontSize: '1.1rem', color: '#0f172a', margin: 0, fontWeight: 700 }}>
              Detected Food Items ({currentItems.length})
            </h4>
            {isAnySwapped && (
              <span style={{ fontSize: '0.78rem', color: '#059669', fontWeight: 600 }}>
                ✓ {Object.keys(swappedItems).length} swap active
              </span>
            )}
          </div>

          {currentItems.map((item) => (
            <ItemDetailCard
              key={item.item_id}
              item={item}
              isSelected={selectedItemId === item.item_id}
              onSelect={setSelectedItemId}
              onHover={setHoveredItemId}
              onPortionChange={handlePortionChange}
              onClassCorrection={handleClassCorrection}
              onConfirmSuggested={handleConfirmSuggested}
              onSwapAlternative={handleSwapAlternative}
              isSwapped={Boolean(swappedItems[item.item_id])}
            />
          ))}
        </div>
      </div>

      {/* Full-Meal Macro & Glycemic Summary */}
      <NutritionSummary
        summary={dynamicSummary}
        originalCalories={originalCalories}
        isAnySwapped={isAnySwapped}
      />

    </div>
  );
}
