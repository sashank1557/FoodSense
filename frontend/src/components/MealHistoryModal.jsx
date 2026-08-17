import React, { useState, useEffect } from 'react';
import {
  X,
  Calendar,
  Clock,
  Flame,
  Dumbbell,
  Wheat,
  Droplets,
  Zap,
  Trash2,
  ChevronRight,
  Sparkles,
  PieChart,
  ListFilter,
  Lock,
  UserCheck
} from 'lucide-react';
import { fetchMealHistory, fetchDailyTotals, deleteMealHistoryEntry } from '../services/api';

export default function MealHistoryModal({
  isOpen,
  onClose,
  user,
  onOpenAuth,
  onSelectMeal
}) {
  const [activeTab, setActiveTab] = useState('daily'); // 'daily' | 'all'
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [dailyData, setDailyData] = useState(null);
  const [allHistory, setAllHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && user) {
      loadData();
    }
  }, [isOpen, user, selectedDate, activeTab]);

  const loadData = async () => {
    if (!user) return;
    setLoading(true);
    try {
      if (activeTab === 'daily') {
        const res = await fetchDailyTotals(selectedDate);
        setDailyData(res);
      } else {
        const res = await fetchMealHistory({ limit: 50 });
        setAllHistory(res.history || []);
      }
    } catch (err) {
      console.error('Failed to load history data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm('Delete this meal entry from your history?')) return;

    try {
      await deleteMealHistoryEntry(id);
      loadData();
    } catch (err) {
      alert('Failed to delete meal: ' + err.message);
    }
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(15, 23, 42, 0.65)',
      backdropFilter: 'blur(6px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '1rem'
    }}>
      <div className="glass-card" style={{
        width: '100%',
        maxWidth: '720px',
        maxHeight: '90vh',
        background: '#ffffff',
        borderRadius: '20px',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 25px 50px -12px rgba(0,0,0,0.25)',
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* Modal Top Header */}
        <div style={{
          padding: '1.25rem 1.5rem',
          borderBottom: '1px solid #e2e8f0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: '#f8fafc'
        }}>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0f172a', margin: '0 0 0.2rem 0' }}>
              Meal History & Daily Totals
            </h2>
            <p style={{ fontSize: '0.8rem', color: '#64748b', margin: 0 }}>
              {user ? `Logged in as ${user.name} (${user.email})` : 'Guest Mode (Local Analysis)'}
            </p>
          </div>

          <button
            onClick={onClose}
            style={{
              background: '#f1f5f9',
              border: 'none',
              borderRadius: '50%',
              width: '32px',
              height: '32px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              color: '#64748b'
            }}
          >
            <X size={16} />
          </button>
        </div>

        {/* Guest Lockout Banner if not logged in */}
        {!user ? (
          <div style={{ padding: '2.5rem 2rem', textAlign: 'center' }}>
            <div style={{
              width: '64px',
              height: '64px',
              borderRadius: '50%',
              background: '#f1f5f9',
              color: '#64748b',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 1.25rem auto'
            }}>
              <Lock size={30} />
            </div>
            <h3 style={{ fontSize: '1.2rem', color: '#0f172a', marginBottom: '0.5rem' }}>
              Account Required for Meal Persistence
            </h3>
            <p style={{ fontSize: '0.88rem', color: '#64748b', maxWidth: '440px', margin: '0 auto 1.75rem auto', lineHeight: 1.5 }}>
              Sign in or create a free FoodSense account to automatically save your meal scans, calculate daily calorie & macro totals, and monitor glycemic trends over time!
            </p>
            <button
              onClick={() => { onClose(); onOpenAuth(); }}
              className="btn btn-primary"
              style={{ padding: '0.75rem 1.75rem', fontSize: '0.95rem' }}
            >
              <UserCheck size={18} />
              <span>Sign In / Create Account</span>
            </button>
          </div>
        ) : (
          <>
            {/* Navigation Tabs */}
            <div style={{
              display: 'flex',
              padding: '0.75rem 1.5rem',
              background: '#f8fafc',
              borderBottom: '1px solid #e2e8f0',
              gap: '0.75rem'
            }}>
              <button
                onClick={() => setActiveTab('daily')}
                style={{
                  padding: '0.45rem 0.9rem',
                  borderRadius: '8px',
                  border: 'none',
                  fontSize: '0.85rem',
                  fontWeight: 700,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                  cursor: 'pointer',
                  background: activeTab === 'daily' ? '#0f172a' : '#e2e8f0',
                  color: activeTab === 'daily' ? '#ffffff' : '#475569'
                }}
              >
                <PieChart size={15} />
                <span>Daily Dashboard</span>
              </button>

              <button
                onClick={() => setActiveTab('all')}
                style={{
                  padding: '0.45rem 0.9rem',
                  borderRadius: '8px',
                  border: 'none',
                  fontSize: '0.85rem',
                  fontWeight: 700,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                  cursor: 'pointer',
                  background: activeTab === 'all' ? '#0f172a' : '#e2e8f0',
                  color: activeTab === 'all' ? '#ffffff' : '#475569'
                }}
              >
                <ListFilter size={15} />
                <span>All Meals Log</span>
              </button>
            </div>

            {/* Modal Body Container */}
            <div style={{ padding: '1.5rem', overflowY: 'auto', flex: 1 }}>

              {/* TAB 1: DAILY DASHBOARD */}
              {activeTab === 'daily' && (
                <div>
                  {/* Date Selector Header */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: '1.25rem',
                    flexWrap: 'wrap',
                    gap: '0.5rem'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <Calendar size={18} color="#059669" />
                      <span style={{ fontSize: '0.9rem', fontWeight: 700, color: '#0f172a' }}>
                        Selected Date:
                      </span>
                      <input
                        type="date"
                        value={selectedDate}
                        onChange={(e) => setSelectedDate(e.target.value)}
                        style={{
                          padding: '0.35rem 0.6rem',
                          borderRadius: '8px',
                          border: '1px solid #cbd5e1',
                          fontSize: '0.85rem',
                          fontWeight: 600
                        }}
                      />
                    </div>

                    <span style={{ fontSize: '0.8rem', color: '#64748b' }}>
                      {dailyData?.total_meals || 0} meals logged
                    </span>
                  </div>

                  {/* Daily Macro Aggregation Card */}
                  {dailyData?.totals && (
                    <div style={{
                      background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
                      color: 'white',
                      borderRadius: '16px',
                      padding: '1.25rem',
                      marginBottom: '1.5rem',
                      boxShadow: '0 8px 20px -4px rgba(15, 23, 42, 0.3)'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                        <span style={{ fontSize: '0.82rem', color: '#94a3b8', fontWeight: 600 }}>Daily Intake</span>
                        <span style={{
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          background: 'rgba(16, 185, 129, 0.2)',
                          color: '#34d399',
                          padding: '0.2rem 0.55rem',
                          borderRadius: '9999px',
                          border: '1px solid rgba(52, 211, 153, 0.3)'
                        }}>
                          Average GI: {dailyData.totals.average_gi || 0}
                        </span>
                      </div>

                      <div style={{ fontSize: '2.2rem', fontWeight: 800, color: '#ffffff', marginBottom: '1rem' }}>
                        {dailyData.totals.total_calories}{' '}
                        <span style={{ fontSize: '1rem', fontWeight: 500, color: '#94a3b8' }}>
                          / 2000 kcal ({Math.round((dailyData.totals.total_calories / 2000) * 100)}%)
                        </span>
                      </div>

                      {/* Daily Macro 4-Grid */}
                      <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(4, 1fr)',
                        gap: '0.5rem',
                        textAlign: 'center'
                      }}>
                        <div style={{ background: 'rgba(255,255,255,0.08)', padding: '0.5rem', borderRadius: '8px' }}>
                          <div style={{ fontSize: '0.7rem', color: '#34d399', fontWeight: 700 }}>PROTEIN</div>
                          <div style={{ fontSize: '1.1rem', fontWeight: 800 }}>{dailyData.totals.total_protein}g</div>
                        </div>
                        <div style={{ background: 'rgba(255,255,255,0.08)', padding: '0.5rem', borderRadius: '8px' }}>
                          <div style={{ fontSize: '0.7rem', color: '#60a5fa', fontWeight: 700 }}>CARBS</div>
                          <div style={{ fontSize: '1.1rem', fontWeight: 800 }}>{dailyData.totals.total_carbs}g</div>
                        </div>
                        <div style={{ background: 'rgba(255,255,255,0.08)', padding: '0.5rem', borderRadius: '8px' }}>
                          <div style={{ fontSize: '0.7rem', color: '#fbbf24', fontWeight: 700 }}>FATS</div>
                          <div style={{ fontSize: '1.1rem', fontWeight: 800 }}>{dailyData.totals.total_fat}g</div>
                        </div>
                        <div style={{ background: 'rgba(255,255,255,0.08)', padding: '0.5rem', borderRadius: '8px' }}>
                          <div style={{ fontSize: '0.7rem', color: '#c084fc', fontWeight: 700 }}>FIBER</div>
                          <div style={{ fontSize: '1.1rem', fontWeight: 800 }}>{dailyData.totals.total_fiber}g</div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Meals Logged on this day */}
                  <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.75rem' }}>
                    Meals Logged ({dailyData?.meals?.length || 0})
                  </h4>

                  {dailyData?.meals?.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: '2rem 1rem', color: '#94a3b8', fontSize: '0.85rem' }}>
                      No meals logged on this date. Scan a meal to add it here!
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                      {dailyData?.meals?.map((meal) => (
                        <div
                          key={meal.id}
                          onClick={() => {
                            onClose();
                            onSelectMeal({
                              items: meal.items,
                              meal_summary: meal.meal_summary,
                              meal_id: meal.meal_id
                            });
                          }}
                          style={{
                            padding: '1rem',
                            borderRadius: '12px',
                            background: '#f8fafc',
                            border: '1px solid #e2e8f0',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            cursor: 'pointer',
                            transition: 'all 150ms ease'
                          }}
                        >
                          <div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
                              <Clock size={13} color="#64748b" />
                              <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>
                                {new Date(meal.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                              </span>
                              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#059669', background: '#ecfdf5', padding: '0.1rem 0.4rem', borderRadius: '4px' }}>
                                {meal.meal_summary?.total_calories || 0} kcal
                              </span>
                            </div>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                              {meal.items?.map((it, i) => (
                                <span key={i} style={{ fontSize: '0.75rem', background: '#e2e8f0', color: '#334155', padding: '0.15rem 0.45rem', borderRadius: '6px' }}>
                                  {it.display_name || it.label}
                                </span>
                              ))}
                            </div>
                          </div>

                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <button
                              onClick={(e) => handleDelete(meal.id, e)}
                              style={{ background: 'none', border: 'none', color: '#ef4444', padding: '4px', cursor: 'pointer' }}
                              title="Delete meal"
                            >
                              <Trash2 size={15} />
                            </button>
                            <ChevronRight size={18} color="#94a3b8" />
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* TAB 2: ALL MEALS LOG */}
              {activeTab === 'all' && (
                <div>
                  {allHistory.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: '3rem 1rem', color: '#94a3b8', fontSize: '0.9rem' }}>
                      No saved meals found. Scan your first meal photo to start tracking!
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                      {allHistory.map((meal) => (
                        <div
                          key={meal.id}
                          onClick={() => {
                            onClose();
                            onSelectMeal({
                              items: meal.items,
                              meal_summary: meal.meal_summary,
                              meal_id: meal.meal_id
                            });
                          }}
                          style={{
                            padding: '1rem',
                            borderRadius: '12px',
                            background: '#f8fafc',
                            border: '1px solid #e2e8f0',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            cursor: 'pointer',
                            transition: 'all 150ms ease'
                          }}
                        >
                          <div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
                              <Calendar size={13} color="#64748b" />
                              <span style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 600 }}>
                                {new Date(meal.created_at).toLocaleDateString()} at {new Date(meal.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                              </span>
                              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#059669', background: '#ecfdf5', padding: '0.1rem 0.4rem', borderRadius: '4px' }}>
                                {meal.meal_summary?.total_calories || 0} kcal
                              </span>
                            </div>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                              {meal.items?.map((it, i) => (
                                <span key={i} style={{ fontSize: '0.75rem', background: '#e2e8f0', color: '#334155', padding: '0.15rem 0.45rem', borderRadius: '6px' }}>
                                  {it.display_name || it.label}
                                </span>
                              ))}
                            </div>
                          </div>

                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <button
                              onClick={(e) => handleDelete(meal.id, e)}
                              style={{ background: 'none', border: 'none', color: '#ef4444', padding: '4px', cursor: 'pointer' }}
                              title="Delete meal"
                            >
                              <Trash2 size={15} />
                            </button>
                            <ChevronRight size={18} color="#94a3b8" />
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

            </div>
          </>
        )}

      </div>
    </div>
  );
}
