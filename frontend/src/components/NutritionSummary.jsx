import React from 'react';
import { Flame, Dumbbell, Wheat, Droplets, Heart, Sparkles, AlertCircle, Info, Zap } from 'lucide-react';

export default function NutritionSummary({ summary, originalCalories, isAnySwapped }) {
  if (!summary) return null;

  const totalItems = summary.total_items || 1;
  const calories = Math.round(summary.total_calories || summary.calories || 0);
  const protein = Math.round((summary.total_protein || summary.protein || 0) * 10) / 10;
  const carbs = Math.round((summary.total_carbs || summary.carbs || 0) * 10) / 10;
  const fat = Math.round((summary.total_fat || summary.fat || 0) * 10) / 10;
  const fiber = Math.round((summary.total_fiber || summary.fiber || 0) * 10) / 10;
  const avgGi = summary.average_gi || 50;
  const dietaryNote = summary.dietary_note || "Balanced meal with diverse macro sources.";

  // Calculate percentage of total calories
  const proteinCal = protein * 4;
  const carbsCal = carbs * 4;
  const fatCal = fat * 9;
  const totalMacroCal = proteinCal + carbsCal + fatCal;

  const proteinPct = totalMacroCal > 0 ? Math.round((proteinCal / totalMacroCal) * 100) : 15;
  const carbsPct = totalMacroCal > 0 ? Math.round((carbsCal / totalMacroCal) * 100) : 55;
  const fatPct = totalMacroCal > 0 ? Math.round((fatCal / totalMacroCal) * 100) : 30;

  // Daily reference values (2000 kcal standard target)
  const calDailyPct = Math.min(100, Math.round((calories / 2000) * 100));
  const proteinDailyPct = Math.min(100, Math.round((protein / 60) * 100));
  const fiberDailyPct = Math.min(100, Math.round((fiber / 30) * 100));

  // Health Score (0 to 100)
  let healthScore = 70;
  if (fiber >= 8) healthScore += 12;
  else if (fiber >= 4) healthScore += 6;
  if (protein >= 25) healthScore += 10;
  if (fatPct > 38) healthScore -= 12;
  if (avgGi <= 55) healthScore += 8;
  else if (avgGi >= 70) healthScore -= 10;
  if (isAnySwapped) healthScore += 10;
  healthScore = Math.min(98, Math.max(45, healthScore));

  const calSavings = originalCalories ? Math.round(originalCalories - calories) : 0;

  return (
    <div className="glass-card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
      {/* Title & Health Score */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
        <div>
          <h3 style={{ fontSize: '1.25rem', color: '#0f172a', margin: 0, fontWeight: 700 }}>
            Meal Nutrition Summary
          </h3>
          <p style={{ fontSize: '0.8rem', color: '#64748b', margin: 0 }}>
            Aggregate nutritional totals across {totalItems} detected food items
          </p>
        </div>

        {/* Health Score Pill */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.4rem',
          padding: '0.35rem 0.75rem',
          borderRadius: '9999px',
          background: healthScore >= 80 ? '#ecfdf5' : '#fffbeb',
          border: `1px solid ${healthScore >= 80 ? '#a7f3d0' : '#fde68a'}`,
          fontSize: '0.82rem',
          fontWeight: 700,
          color: healthScore >= 80 ? '#047857' : '#b45309'
        }}>
          <Heart size={15} />
          <span>Health Score: {healthScore}/100</span>
        </div>
      </div>

      {/* Main Calories & Macros Split */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: '1rem',
        marginBottom: '1.25rem'
      }}>
        {/* Total Calories Box */}
        <div style={{
          background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
          color: 'white',
          padding: '1.25rem',
          borderRadius: '14px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          boxShadow: '0 8px 20px -4px rgba(15, 23, 42, 0.3)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.85rem', color: '#94a3b8', fontWeight: 600 }}>Total Energy</span>
            <Flame size={18} color="#f87171" />
          </div>
          <div>
            <div style={{ fontSize: '2.4rem', fontWeight: 800, lineHeight: 1.1, color: '#ffffff' }}>
              {calories} <span style={{ fontSize: '1rem', fontWeight: 500, color: '#94a3b8' }}>kcal</span>
            </div>
            <div style={{ fontSize: '0.78rem', color: '#38bdf8', marginTop: '0.35rem' }}>
              {calDailyPct}% of daily 2,000 kcal guideline
            </div>
          </div>
          {calSavings > 0 && (
            <div style={{
              marginTop: '0.5rem',
              fontSize: '0.75rem',
              color: '#34d399',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              gap: '0.25rem'
            }}>
              <Sparkles size={13} /> Saved {calSavings} kcal with healthier swaps!
            </div>
          )}
        </div>

        {/* Protein Card */}
        <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', padding: '1rem', borderRadius: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#059669', fontSize: '0.8rem', fontWeight: 700, marginBottom: '0.25rem' }}>
            <Dumbbell size={15} /> PROTEIN
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#065f46' }}>
            {protein}g
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
            {proteinPct}% of calories ({proteinDailyPct}% daily target)
          </div>
          <div style={{ height: '6px', background: '#e2e8f0', borderRadius: '3px', marginTop: '0.5rem', overflow: 'hidden' }}>
            <div style={{ width: `${proteinDailyPct}%`, height: '100%', background: '#10b981', borderRadius: '3px' }} />
          </div>
        </div>

        {/* Carbs Card */}
        <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', padding: '1rem', borderRadius: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#2563eb', fontSize: '0.8rem', fontWeight: 700, marginBottom: '0.25rem' }}>
            <Wheat size={15} /> CARBS
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#1e40af' }}>
            {carbs}g
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
            {carbsPct}% of calories (Fiber: {fiber}g)
          </div>
          <div style={{ height: '6px', background: '#e2e8f0', borderRadius: '3px', marginTop: '0.5rem', overflow: 'hidden' }}>
            <div style={{ width: `${fiberDailyPct}%`, height: '100%', background: '#3b82f6', borderRadius: '3px' }} />
          </div>
        </div>

        {/* Fats Card */}
        <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', padding: '1rem', borderRadius: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#d97706', fontSize: '0.8rem', fontWeight: 700, marginBottom: '0.25rem' }}>
            <Droplets size={15} /> FATS
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#92400e' }}>
            {fat}g
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
            {fatPct}% of calories
          </div>
          <div style={{ height: '6px', background: '#e2e8f0', borderRadius: '3px', marginTop: '0.5rem', overflow: 'hidden' }}>
            <div style={{ width: `${Math.min(100, Math.round((fat / 65) * 100))}%`, height: '100%', background: '#f59e0b', borderRadius: '3px' }} />
          </div>
        </div>

        {/* Glycemic Index Card */}
        <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', padding: '1rem', borderRadius: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#7c3aed', fontSize: '0.8rem', fontWeight: 700, marginBottom: '0.25rem' }}>
            <Zap size={15} /> AVG GLYCEMIC INDEX
          </div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#5b21b6' }}>
            {avgGi}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
            {avgGi >= 70 ? 'High Glycemic Load' : avgGi >= 55 ? 'Moderate Glycemic Load' : 'Low Glycemic (Optimal)'}
          </div>
          <div style={{ height: '6px', background: '#e2e8f0', borderRadius: '3px', marginTop: '0.5rem', overflow: 'hidden' }}>
            <div style={{ width: `${Math.min(100, (avgGi / 100) * 100)}%`, height: '100%', background: avgGi >= 70 ? '#ef4444' : avgGi >= 55 ? '#f59e0b' : '#10b981', borderRadius: '3px' }} />
          </div>
        </div>
      </div>

      {/* Server-Computed Dietary Recommendation Banner */}
      {dietaryNote && (
        <div style={{
          background: '#f0fdf4',
          border: '1px solid #bbf7d0',
          borderRadius: '10px',
          padding: '0.85rem 1rem',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '0.65rem'
        }}>
          <Info size={18} color="#16a34a" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div style={{ fontSize: '0.85rem', color: '#166534', lineHeight: 1.45 }}>
            <strong>Dietary Insight:</strong> {dietaryNote}
          </div>
        </div>
      )}
    </div>
  );
}
