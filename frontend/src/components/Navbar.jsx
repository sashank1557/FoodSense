import React from 'react';
import { UtensilsCrossed, History, PlusCircle, User, LogOut, LogIn } from 'lucide-react';

export default function Navbar({
  serverStatus,
  onOpenHistory,
  onReset,
  hasResults,
  user,
  onOpenAuth,
  onLogout
}) {
  return (
    <header style={{
      background: 'rgba(255, 255, 255, 0.95)',
      backdropFilter: 'blur(12px)',
      borderBottom: '1px solid #e2e8f0',
      position: 'sticky',
      top: 0,
      zIndex: 40,
      padding: '0.85rem 1.5rem',
      boxShadow: '0 1px 3px rgba(0,0,0,0.04)'
    }}>
      <div style={{
        maxWidth: '1280px',
        margin: '0 auto',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        {/* Brand */}
        <div 
          onClick={onReset}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            cursor: 'pointer',
            userSelect: 'none'
          }}
        >
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            boxShadow: '0 4px 10px rgba(16, 185, 129, 0.3)'
          }}>
            <UtensilsCrossed size={22} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <span style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0f172a', letterSpacing: '-0.02em' }}>
                Food<span style={{ color: '#10b981' }}>Sense</span>
              </span>
              <span style={{
                fontSize: '0.65rem',
                fontWeight: 700,
                background: '#ecfdf5',
                color: '#059669',
                padding: '0.15rem 0.45rem',
                borderRadius: '9999px',
                border: '1px solid #a7f3d0'
              }}>
                AI 20-CLASS
              </span>
            </div>
            <p style={{ fontSize: '0.72rem', color: '#64748b', margin: 0 }}>Indian Meal & Nutrition Intelligence</p>
          </div>
        </div>

        {/* Right actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {/* Server Status Pill */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.45rem',
            padding: '0.35rem 0.75rem',
            borderRadius: '9999px',
            background: serverStatus === 'healthy' ? '#ecfdf5' : serverStatus === 'waking' ? '#fef3c7' : '#fee2e2',
            border: `1px solid ${serverStatus === 'healthy' ? '#a7f3d0' : serverStatus === 'waking' ? '#fde68a' : '#fecaca'}`,
            fontSize: '0.75rem',
            fontWeight: 600,
            color: serverStatus === 'healthy' ? '#065f46' : serverStatus === 'waking' ? '#92400e' : '#991b1b'
          }}>
            <span style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: serverStatus === 'healthy' ? '#10b981' : serverStatus === 'waking' ? '#f59e0b' : '#ef4444',
              display: 'inline-block'
            }} />
            <span>
              {serverStatus === 'healthy' ? 'ML Engine Online' : serverStatus === 'waking' ? 'Waking Up...' : 'Engine Offline'}
            </span>
          </div>

          {/* History & Daily Dashboard Button */}
          <button
            onClick={onOpenHistory}
            className="btn btn-secondary"
            style={{ padding: '0.5rem 0.9rem', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}
            title="View Meal History & Daily Dashboard"
          >
            <History size={16} />
            <span>Daily & History</span>
          </button>

          {/* User Account / Sign In Button */}
          {user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem',
                background: '#f1f5f9',
                padding: '0.4rem 0.75rem',
                borderRadius: '8px',
                fontSize: '0.82rem',
                fontWeight: 600,
                color: '#334155'
              }}>
                <User size={14} color="#059669" />
                <span>{user.name}</span>
              </div>
              <button
                onClick={onLogout}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#94a3b8',
                  cursor: 'pointer',
                  padding: '4px',
                  display: 'flex',
                  alignItems: 'center'
                }}
                title="Log Out"
              >
                <LogOut size={16} />
              </button>
            </div>
          ) : (
            <button
              onClick={onOpenAuth}
              className="btn btn-primary"
              style={{ padding: '0.5rem 0.9rem', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.35rem' }}
            >
              <LogIn size={15} />
              <span>Sign In</span>
            </button>
          )}

          {/* New Scan Button if in results */}
          {hasResults && (
            <button
              onClick={onReset}
              className="btn btn-secondary"
              style={{ padding: '0.5rem 0.9rem', fontSize: '0.85rem' }}
            >
              <PlusCircle size={16} />
              <span>New Scan</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
