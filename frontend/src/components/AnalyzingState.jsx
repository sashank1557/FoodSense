import React, { useState, useEffect } from 'react';
import { Sparkles, Cpu, Clock, XCircle, CheckCircle2, Server, Flame } from 'lucide-react';

export default function AnalyzingState({ previewUrl, onCancel }) {
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [activeStep, setActiveStep] = useState(0);

  const steps = [
    { label: 'Uploading image to Express relay layer...', delay: 0 },
    { label: 'YOLO Item Localization (identifying bowls & dishes)...', delay: 1 },
    { label: 'MobileNetV2 CNN 19-Class Dish Classification...', delay: 2 },
    { label: 'Nutrition Database & GI Metric Lookup...', delay: 3 },
    { label: 'KNN Healthy Alternatives Clustering...', delay: 4 }
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setElapsedSeconds(prev => prev + 1);
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const stepIdx = Math.min(Math.floor(elapsedSeconds / 1.5), steps.length - 1);
    setActiveStep(stepIdx);
  }, [elapsedSeconds]);

  const isColdStarting = elapsedSeconds >= 3;

  return (
    <div style={{ maxWidth: '640px', margin: '2rem auto', textAlign: 'center' }}>
      <div className="glass-card" style={{ padding: '2.5rem 2rem', position: 'relative', overflow: 'hidden' }}>
        
        {/* Animated Scanning Box */}
        <div style={{
          position: 'relative',
          width: '280px',
          height: '280px',
          margin: '0 auto 2rem auto',
          borderRadius: '20px',
          overflow: 'hidden',
          boxShadow: '0 10px 30px rgba(16, 185, 129, 0.2)',
          border: '2px solid #a7f3d0',
          background: '#0f172a'
        }}>
          {previewUrl && (
            <img
              src={previewUrl}
              alt="Scanning Meal"
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                opacity: 0.8
              }}
            />
          )}

          {/* Scanner Line */}
          <div className="scanner-beam" />

          {/* Center pulsating AI badge */}
          <div style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            pointerEvents: 'none'
          }}>
            <div style={{
              width: '60px',
              height: '60px',
              borderRadius: '50%',
              background: 'rgba(16, 185, 129, 0.25)',
              backdropFilter: 'blur(8px)',
              border: '2px solid #10b981',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#10b981',
              boxShadow: '0 0 20px rgba(16, 185, 129, 0.5)'
            }}>
              <Sparkles size={28} className="animate-pulse-ring" />
            </div>
          </div>

          {/* Elapsed Timer Tag */}
          <div style={{
            position: 'absolute',
            top: '12px',
            right: '12px',
            background: 'rgba(15, 23, 42, 0.85)',
            backdropFilter: 'blur(6px)',
            color: '#34d399',
            padding: '0.25rem 0.6rem',
            borderRadius: '9999px',
            fontSize: '0.75rem',
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            gap: '0.3rem'
          }}>
            <Clock size={12} />
            <span>{elapsedSeconds}s</span>
          </div>
        </div>

        <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem', color: '#0f172a' }}>
          Analyzing Food Components
        </h2>
        <p style={{ fontSize: '0.92rem', color: '#64748b', marginBottom: '1.75rem' }}>
          Running multi-model inference pipeline (YOLO &rarr; CNN &rarr; KNN)
        </p>

        {/* Multi-step progress list */}
        <div style={{
          maxWidth: '420px',
          margin: '0 auto 1.5rem auto',
          textAlign: 'left',
          background: '#f8fafc',
          padding: '1rem 1.25rem',
          borderRadius: '12px',
          border: '1px solid #e2e8f0'
        }}>
          {steps.map((step, idx) => {
            const isDone = idx < activeStep;
            const isCurrent = idx === activeStep;
            return (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.65rem',
                  padding: '0.35rem 0',
                  fontSize: '0.85rem',
                  color: isDone ? '#059669' : isCurrent ? '#0f172a' : '#94a3b8',
                  fontWeight: isCurrent ? 600 : 400
                }}
              >
                {isDone ? (
                  <CheckCircle2 size={16} color="#10b981" />
                ) : isCurrent ? (
                  <div style={{
                    width: '14px',
                    height: '14px',
                    borderRadius: '50%',
                    border: '2px solid #10b981',
                    borderTopColor: 'transparent',
                    animation: 'spin 1s linear infinite'
                  }} />
                ) : (
                  <div style={{ width: '14px', height: '14px', borderRadius: '50%', background: '#cbd5e1' }} />
                )}
                <span>{step.label}</span>
              </div>
            );
          })}
        </div>

        {/* Cold Start Awareness Notice (Visible after 3s) */}
        {isColdStarting && (
          <div style={{
            background: '#fffbeb',
            border: '1px solid #fef3c7',
            borderRadius: '12px',
            padding: '0.9rem 1.1rem',
            textAlign: 'left',
            marginBottom: '1.5rem',
            display: 'flex',
            gap: '0.75rem',
            alignItems: 'flex-start'
          }}>
            <Server size={20} color="#d97706" style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <div style={{ fontSize: '0.88rem', fontWeight: 700, color: '#92400e', marginBottom: '0.2rem' }}>
                Waking up AI Inference Engine (Free-Tier Hosting)
              </div>
              <p style={{ fontSize: '0.8rem', color: '#b45309', margin: 0, lineHeight: 1.4 }}>
                If the server was idle, PyTorch and ML models are booting into memory. This initial spin-up takes ~10-25 seconds and subsequent scans will be instant!
              </p>
            </div>
          </div>
        )}

        {/* Cancel Button */}
        <button
          onClick={onCancel}
          className="btn btn-ghost"
          style={{ fontSize: '0.85rem', color: '#64748b' }}
        >
          <XCircle size={16} />
          <span>Cancel Analysis</span>
        </button>

      </div>
    </div>
  );
}
