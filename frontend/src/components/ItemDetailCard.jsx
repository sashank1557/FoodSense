import React, { useState } from 'react';
import { getCategoryTheme } from '../utils/bboxScaler';
import AlternativeCard from './AlternativeCard';
import { Flame, Dumbbell, Wheat, Droplets, Zap, Edit3, Check, X, CheckCircle2, HelpCircle, AlertCircle } from 'lucide-react';

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

export default function ItemDetailCard({
  item,
  isSelected,
  onSelect,
  onHover,
  onPortionChange,
  onClassCorrection,
  onConfirmSuggested,
  onSwapAlternative,
  isSwapped
}) {
  const [portionMultiplier, setPortionMultiplier] = useState(item.portion_multiplier || 1.0);
  const [isEditing, setIsEditing] = useState(false);
  const [selectedCorrection, setSelectedCorrection] = useState(item.label || 'idli');
  const [isSavingCorrection, setIsSavingCorrection] = useState(false);

  const isSuggested = Boolean(item.needs_confirmation);
  const theme = isSuggested
    ? { stroke: '#f59e0b', bg: '#d97706' }
    : getCategoryTheme(item.category || 'Default');

  const macros = item.macros || item.nutrition || {
    calories: 0,
    protein: 0,
    carbs: 0,
    fat: 0,
    fiber: 0,
    gi: 50
  };

  const confidencePct = Math.round((item.confidence || 0.90) * 100);
  const displayName = item.display_name || item.label?.replace(/_/g, ' ').toUpperCase() || 'Food Item';
  const portionLabel = item.portion || item.serving_size || '1 serving';

  // Apply active portion scaling
  const currentCalories = Math.round((macros.calories || 0) * portionMultiplier);
  const currentProtein = Math.round((macros.protein || 0) * portionMultiplier * 10) / 10;
  const currentCarbs = Math.round((macros.carbs || 0) * portionMultiplier * 10) / 10;
  const currentFat = Math.round((macros.fat || 0) * portionMultiplier * 10) / 10;
  const currentFiber = Math.round((macros.fiber || 0) * portionMultiplier * 10) / 10;
  const currentGi = macros.gi || macros.glycemic_index || 50;

  const handleSliderChange = (e) => {
    const val = parseFloat(e.target.value);
    setPortionMultiplier(val);
    if (onPortionChange) {
      onPortionChange(item.item_id || item.label, val);
    }
  };

  const handleSaveCorrection = async () => {
    setIsSavingCorrection(true);
    try {
      if (onClassCorrection) {
        await onClassCorrection(item, selectedCorrection);
      }
      setIsEditing(false);
    } catch (err) {
      alert('Correction failed: ' + err.message);
    } finally {
      setIsSavingCorrection(false);
    }
  };

  return (
    <div
      onClick={() => onSelect && onSelect(item.item_id || item.label)}
      onMouseEnter={() => onHover && onHover(item.item_id || item.label)}
      onMouseLeave={() => onHover && onHover(null)}
      className="glass-card"
      style={{
        padding: '1.25rem',
        borderRadius: '14px',
        border: isSelected
          ? `2px solid ${theme.stroke}`
          : (isSuggested ? '2px dashed #f59e0b' : '1px solid #e2e8f0'),
        background: isSuggested ? 'rgba(254, 243, 199, 0.25)' : '#ffffff',
        boxShadow: isSelected ? `0 6px 20px rgba(0,0,0,0.08), 0 0 0 1px ${theme.stroke}` : 'var(--shadow-sm)',
        transition: 'all 200ms ease',
        cursor: 'pointer'
      }}
    >
      {/* Low Confidence / Confirmation Alert Banner */}
      {isSuggested && (
        <div style={{
          background: '#fffbeb',
          border: '1px solid #fde68a',
          padding: '0.5rem 0.75rem',
          borderRadius: '8px',
          marginBottom: '0.85rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '0.5rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.78rem', color: '#92400e', fontWeight: 600 }}>
            <AlertCircle size={14} color="#d97706" />
            <span>Low confidence detection. Is this {displayName}?</span>
          </div>

          <div style={{ display: 'flex', gap: '0.35rem' }}>
            <button
              onClick={(e) => {
                e.stopPropagation();
                if (onConfirmSuggested) onConfirmSuggested(item);
              }}
              style={{
                background: '#059669',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                padding: '3px 8px',
                fontSize: '0.72rem',
                fontWeight: 700,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '2px'
              }}
            >
              <Check size={12} /> Confirm
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setSelectedCorrection(item.label);
                setIsEditing(true);
              }}
              style={{
                background: '#d97706',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                padding: '3px 8px',
                fontSize: '0.72rem',
                fontWeight: 700,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '2px'
              }}
            >
              <Edit3 size={12} /> Change
            </button>
          </div>
        </div>
      )}

      {/* Header Row */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
            <span
              style={{
                display: 'inline-block',
                width: '10px',
                height: '10px',
                borderRadius: '50%',
                backgroundColor: theme.stroke
              }}
            />
            <span style={{
              fontSize: '0.75rem',
              fontWeight: 700,
              color: theme.bg,
              textTransform: 'uppercase',
              letterSpacing: '0.04em'
            }}>
              {isSuggested ? 'Candidate Item' : (item.category || 'Detected Item')}
            </span>
            {item.is_corrected && (
              <span style={{
                fontSize: '0.7rem',
                fontWeight: 700,
                color: '#059669',
                background: '#ecfdf5',
                padding: '0.1rem 0.4rem',
                borderRadius: '4px',
                display: 'flex',
                alignItems: 'center',
                gap: '2px'
              }}>
                <CheckCircle2 size={11} /> Corrected
              </span>
            )}
            {item.is_manual_addition && (
              <span style={{
                fontSize: '0.7rem',
                fontWeight: 700,
                color: '#2563eb',
                background: '#eff6ff',
                padding: '0.1rem 0.4rem',
                borderRadius: '4px',
                display: 'flex',
                alignItems: 'center',
                gap: '2px'
              }}>
                + Manually Added
              </span>
            )}
          </div>

          {!isEditing ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <h3 style={{ fontSize: '1.15rem', color: '#0f172a', margin: 0, fontWeight: 700 }}>
                {displayName}
              </h3>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedCorrection(item.label);
                  setIsEditing(true);
                }}
                style={{
                  background: '#f1f5f9',
                  border: 'none',
                  borderRadius: '6px',
                  padding: '3px 6px',
                  fontSize: '0.72rem',
                  color: '#64748b',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '3px'
                }}
                title="Correct classification if wrong"
              >
                <Edit3 size={11} />
                <span>Not right?</span>
              </button>
            </div>
          ) : (
            <div onClick={(e) => e.stopPropagation()} style={{ marginTop: '0.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
                <select
                  value={selectedCorrection}
                  onChange={(e) => setSelectedCorrection(e.target.value)}
                  style={{
                    padding: '0.35rem 0.6rem',
                    borderRadius: '8px',
                    border: '1px solid #cbd5e1',
                    fontSize: '0.85rem',
                    fontWeight: 600
                  }}
                >
                  {ALL_CLASSES.map(cls => (
                    <option key={cls.id} value={cls.id}>
                      {cls.name}
                    </option>
                  ))}
                </select>

                <button
                  onClick={handleSaveCorrection}
                  disabled={isSavingCorrection}
                  className="btn btn-primary"
                  style={{ padding: '0.35rem 0.65rem', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '3px' }}
                >
                  <Check size={13} />
                  <span>Save</span>
                </button>

                <button
                  onClick={() => setIsEditing(false)}
                  style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '2px' }}
                >
                  <X size={16} />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Confidence Badge */}
        <div style={{ textAlign: 'right' }}>
          <span style={{
            fontSize: '0.75rem',
            fontWeight: 700,
            padding: '0.2rem 0.55rem',
            borderRadius: '9999px',
            background: isSuggested ? '#fef3c7' : (confidencePct >= 75 ? '#dcfce7' : '#fef3c7'),
            color: isSuggested ? '#92400e' : (confidencePct >= 75 ? '#166534' : '#92400e')
          }}>
            {isSuggested ? `${confidencePct}% (Candidate)` : `${confidencePct}% Conf`}
          </span>
          <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: '0.2rem' }}>
            {portionLabel}
          </div>
        </div>
      </div>

      {/* Portion Slider */}
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: '#f8fafc',
          padding: '0.65rem 0.85rem',
          borderRadius: '10px',
          marginBottom: '0.85rem',
          border: '1px solid #f1f5f9'
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', color: '#475569', marginBottom: '0.35rem' }}>
          <span>Adjust Portion:</span>
          <strong>{portionMultiplier}x serving ({Math.round(portionMultiplier * 100)}%)</strong>
        </div>
        <input
          type="range"
          min="0.5"
          max="3.0"
          step="0.25"
          value={portionMultiplier}
          onChange={handleSliderChange}
          style={{ width: '100%', accentColor: theme.stroke, cursor: 'pointer' }}
        />
      </div>

      {/* Primary Nutrition Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(5, 1fr)',
        gap: '0.4rem',
        textAlign: 'center'
      }}>
        {/* Calories */}
        <div style={{ background: '#fef2f2', padding: '0.5rem 0.25rem', borderRadius: '8px' }}>
          <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#ef4444', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '2px' }}>
            <Flame size={12} /> CAL
          </div>
          <div style={{ fontSize: '1rem', fontWeight: 800, color: '#991b1b' }}>
            {currentCalories}
          </div>
        </div>

        {/* Protein */}
        <div style={{ background: '#ecfdf5', padding: '0.5rem 0.25rem', borderRadius: '8px' }}>
          <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#10b981', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '2px' }}>
            <Dumbbell size={12} /> PROT
          </div>
          <div style={{ fontSize: '1rem', fontWeight: 800, color: '#065f46' }}>
            {currentProtein}g
          </div>
        </div>

        {/* Carbs */}
        <div style={{ background: '#eff6ff', padding: '0.5rem 0.25rem', borderRadius: '8px' }}>
          <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#3b82f6', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '2px' }}>
            <Wheat size={12} /> CARB
          </div>
          <div style={{ fontSize: '1rem', fontWeight: 800, color: '#1e40af' }}>
            {currentCarbs}g
          </div>
        </div>

        {/* Fats */}
        <div style={{ background: '#fffbeb', padding: '0.5rem 0.25rem', borderRadius: '8px' }}>
          <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#f59e0b', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '2px' }}>
            <Droplets size={12} /> FAT
          </div>
          <div style={{ fontSize: '1rem', fontWeight: 800, color: '#92400e' }}>
            {currentFat}g
          </div>
        </div>

        {/* Glycemic Index */}
        <div style={{ background: '#f5f3ff', padding: '0.5rem 0.25rem', borderRadius: '8px' }}>
          <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#8b5cf6', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '2px' }}>
            <Zap size={12} /> GI
          </div>
          <div style={{ fontSize: '1rem', fontWeight: 800, color: '#5b21b6' }}>
            {currentGi}
          </div>
        </div>
      </div>

      {/* Healthy Alternative Card */}
      {item.healthy_alternative && (
        <div onClick={(e) => e.stopPropagation()}>
          <AlternativeCard
            alternative={item.healthy_alternative}
            baseItemName={displayName}
            onSwap={onSwapAlternative ? () => onSwapAlternative(item.item_id || item.label, item.healthy_alternative) : null}
            isSwapped={isSwapped}
          />
        </div>
      )}
    </div>
  );
}
