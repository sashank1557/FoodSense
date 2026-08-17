import React from 'react';
import { ArrowRight, RotateCcw, Image as ImageIcon, Sparkles } from 'lucide-react';

export default function ImagePreview({ file, previewUrl, onAnalyze, onCancel }) {
  const fileSizeKB = file ? (file.size / 1024).toFixed(1) : '0';

  return (
    <div style={{ maxWidth: '640px', margin: '2rem auto', textAlign: 'center' }}>
      <div className="glass-card" style={{ padding: '2rem', overflow: 'hidden' }}>
        <h2 style={{ fontSize: '1.4rem', marginBottom: '0.5rem', color: '#0f172a' }}>
          Ready to Analyze Your Meal
        </h2>
        <p style={{ fontSize: '0.88rem', color: '#64748b', marginBottom: '1.5rem' }}>
          Preview your photo below and click analyze to start multi-item AI detection.
        </p>

        {/* Image Preview Container */}
        <div style={{
          position: 'relative',
          borderRadius: '16px',
          overflow: 'hidden',
          maxHeight: '420px',
          background: '#0f172a',
          boxShadow: '0 10px 25px -5px rgba(0,0,0,0.15)',
          marginBottom: '1.5rem'
        }}>
          <img
            src={previewUrl}
            alt="Meal Preview"
            style={{
              width: '100%',
              height: '100%',
              maxHeight: '400px',
              objectFit: 'contain',
              display: 'block'
            }}
          />
        </div>

        {/* File Meta Pill */}
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0.35rem 0.85rem',
          borderRadius: '9999px',
          background: '#f1f5f9',
          color: '#475569',
          fontSize: '0.8rem',
          fontWeight: 500,
          marginBottom: '1.75rem'
        }}>
          <ImageIcon size={14} />
          <span>{file?.name || 'meal_photo.jpg'} ({fileSizeKB} KB)</span>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '1rem' }}>
          <button
            onClick={onCancel}
            className="btn btn-secondary"
            style={{ padding: '0.75rem 1.25rem' }}
          >
            <RotateCcw size={16} />
            <span>Retake / Change</span>
          </button>

          <button
            onClick={onAnalyze}
            className="btn btn-primary"
            style={{ padding: '0.75rem 2rem', fontSize: '1.05rem' }}
          >
            <Sparkles size={18} />
            <span>Analyze Meal Now</span>
            <ArrowRight size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
