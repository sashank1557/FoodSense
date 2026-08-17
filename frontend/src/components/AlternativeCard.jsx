import React from 'react';
import { ArrowRight, Sparkles, TrendingDown, Check, Zap, Flame, Dumbbell, Wheat, Droplets } from 'lucide-react';

export default function AlternativeCard({ alternative, baseItemName, onSwap, isSwapped }) {
  if (!alternative) return null;

  const macros = alternative.macros || {
    calories: alternative.calories || 0,
    protein: alternative.protein || 0,
    carbs: alternative.carbs || 0,
    fat: alternative.fat || 0,
    fiber: alternative.fiber || 0,
    gi: alternative.gi || alternative.glycemic_index || 50
  };

  return (
    <div style={{
      marginTop: '1rem',
      padding: '1rem 1.1rem',
      borderRadius: '12px',
      background: isSwapped ? '#ecfdf5' : '#f8fafc',
      border: `1.5px dashed ${isSwapped ? '#10b981' : '#cbd5e1'}`,
      transition: 'all 200ms ease'
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <Sparkles size={15} color="#10b981" />
          <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#047857', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            KNN Healthy Alternative
          </span>
        </div>
        {isSwapped && (
          <span style={{
            fontSize: '0.72rem',
            fontWeight: 700,
            background: '#10b981',
            color: 'white',
            padding: '0.15rem 0.5rem',
            borderRadius: '9999px',
            display: 'flex',
            alignItems: 'center',
            gap: '0.25rem'
          }}>
            <Check size={12} /> Swapped in Meal
          </span>
        )}
      </div>

      {/* Alternative Title */}
      <div style={{ fontSize: '1rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.35rem' }}>
        {alternative.name}
      </div>

      {/* Macro Pill Chips */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginBottom: '0.65rem' }}>
        <span style={{
          fontSize: '0.75rem',
          fontWeight: 700,
          background: '#dcfce7',
          color: '#15803d',
          padding: '0.2rem 0.5rem',
          borderRadius: '6px',
          display: 'flex',
          alignItems: 'center',
          gap: '0.25rem'
        }}>
          <Flame size={12} /> {macros.calories} kcal
        </span>

        <span style={{
          fontSize: '0.75rem',
          fontWeight: 700,
          background: '#e0e7ff',
          color: '#4338ca',
          padding: '0.2rem 0.5rem',
          borderRadius: '6px',
          display: 'flex',
          alignItems: 'center',
          gap: '0.25rem'
        }}>
          <Zap size={12} /> GI: {macros.gi}
        </span>

        <span style={{
          fontSize: '0.75rem',
          fontWeight: 600,
          background: '#f1f5f9',
          color: '#475569',
          padding: '0.2rem 0.5rem',
          borderRadius: '6px'
        }}>
          P: {macros.protein}g | C: {macros.carbs}g | F: {macros.fat}g | Fib: {macros.fiber}g
        </span>
      </div>

      {/* Dynamic server-generated Rationale text */}
      <p style={{ fontSize: '0.82rem', color: '#475569', lineHeight: 1.45, marginBottom: '0.75rem' }}>
        {alternative.reason}
      </p>

      {/* Swap Button */}
      {onSwap && (
        <button
          onClick={onSwap}
          className={isSwapped ? 'btn btn-secondary' : 'btn btn-primary'}
          style={{
            width: '100%',
            padding: '0.45rem 0.75rem',
            fontSize: '0.8rem',
            borderRadius: '8px'
          }}
        >
          {isSwapped ? (
            <span>Revert to original {baseItemName}</span>
          ) : (
            <>
              <span>Swap this dish in meal calculation</span>
              <ArrowRight size={14} />
            </>
          )}
        </button>
      )}
    </div>
  );
}
