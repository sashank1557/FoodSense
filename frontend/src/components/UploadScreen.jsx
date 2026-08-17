import React, { useState, useRef, useEffect } from 'react';
import { Camera, Upload, Sparkles, RefreshCw, X, AlertCircle } from 'lucide-react';

// Preset sample food images generated via SVG Canvas data URLs for instant zero-dependency testing
const PRESET_MEALS = [
  {
    id: 'thali_deluxe',
    title: 'North Indian Thali',
    desc: 'Roti, Dal Tadka, Paneer Butter Masala, Rice & Gulab Jamun',
    items: ['Roti', 'Dal Tadka', 'Paneer Butter Masala', 'Steamed Rice', 'Gulab Jamun'],
    svgBg: '#fff7ed',
    color1: '#f59e0b',
    color2: '#ef4444'
  },
  {
    id: 'south_breakfast',
    title: 'South Indian Breakfast',
    desc: 'Crispy Dosa, Steamed Idli & Medu Vada with Chutney',
    items: ['Dosa', 'Idli', 'Medu Vada'],
    svgBg: '#f0fdf4',
    color1: '#10b981',
    color2: '#06b6d4'
  },
  {
    id: 'biryani_meal',
    title: 'Hyderabadi Dum Biryani',
    desc: 'Spiced Dum Biryani with Raita & Salad',
    items: ['Biryani', 'Roti', 'Chole'],
    svgBg: '#fef2f2',
    color1: '#ea580c',
    color2: '#8b5cf6'
  },
  {
    id: 'evening_snack',
    title: 'Tea-time Street Snacks',
    desc: 'Golden Samosa, Crispy Pakora & Hot Jalebi',
    items: ['Samosa', 'Pakora', 'Jalebi'],
    svgBg: '#fefce8',
    color1: '#eab308',
    color2: '#ec4899'
  }
];

export default function UploadScreen({ onImageSelected }) {
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const fileInputRef = useRef(null);

  // Stop camera when unmounting or switching
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, []);

  const startCamera = async () => {
    setCameraError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 960 } },
        audio: false
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setIsCameraActive(true);
    } catch (err) {
      console.error('Camera access error:', err);
      setCameraError('Camera permission denied or camera not available on this device.');
      setIsCameraActive(false);
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setIsCameraActive(false);
  };

  const capturePhoto = () => {
    if (!videoRef.current) return;
    
    const video = videoRef.current;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth || 800;
    canvas.height = video.videoHeight || 600;
    
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    canvas.toBlob((blob) => {
      if (blob) {
        const file = new File([blob], `meal_capture_${Date.now()}.jpg`, { type: 'image/jpeg' });
        stopCamera();
        onImageSelected(file, canvas.toDataURL('image/jpeg'));
      }
    }, 'image/jpeg', 0.92);
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      processSelectedFile(file);
    }
  };

  const processSelectedFile = (file) => {
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file (JPEG, PNG, WEBP).');
      return;
    }
    const reader = new FileReader();
    reader.onload = (event) => {
      onImageSelected(file, event.target.result);
    };
    reader.readAsDataURL(file);
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processSelectedFile(e.dataTransfer.files[0]);
    }
  };

  // Generate a high-quality stylized meal canvas for preset click
  const handleSelectPreset = (preset) => {
    const canvas = document.createElement('canvas');
    canvas.width = 700;
    canvas.height = 700;
    const ctx = canvas.getContext('2d');

    // Background
    ctx.fillStyle = preset.svgBg;
    ctx.fillRect(0, 0, 700, 700);

    // Large plate
    ctx.beginPath();
    ctx.arc(350, 350, 320, 0, 2 * Math.PI);
    ctx.fillStyle = '#e2e8f0';
    ctx.fill();
    ctx.lineWidth = 12;
    ctx.strokeStyle = '#94a3b8';
    ctx.stroke();

    // Inner plate surface
    ctx.beginPath();
    ctx.arc(350, 350, 300, 0, 2 * Math.PI);
    ctx.fillStyle = '#f8fafc';
    ctx.fill();

    // Bowls / food items based on preset
    const dishes = [
      { x: 230, y: 230, r: 90, color: '#f59e0b', stroke: '#d97706', label: preset.items[0] || 'Dish 1' },
      { x: 470, y: 230, r: 90, color: '#ea580c', stroke: '#c2410c', label: preset.items[1] || 'Dish 2' },
      { x: 230, y: 470, r: 95, color: '#10b981', stroke: '#059669', label: preset.items[2] || 'Dish 3' },
      { x: 470, y: 470, r: 95, color: '#8b5cf6', stroke: '#7c3aed', label: preset.items[3] || 'Dish 4' }
    ];

    dishes.forEach(d => {
      ctx.beginPath();
      ctx.arc(d.x, d.y, d.r, 0, 2 * Math.PI);
      ctx.fillStyle = d.color;
      ctx.fill();
      ctx.lineWidth = 6;
      ctx.strokeStyle = d.stroke;
      ctx.stroke();

      // Inner texture
      ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
      ctx.beginPath();
      ctx.arc(d.x - 20, d.y - 20, d.r * 0.4, 0, 2 * Math.PI);
      ctx.fill();
    });

    canvas.toBlob((blob) => {
      if (blob) {
        const file = new File([blob], `${preset.id}.jpg`, { type: 'image/jpeg' });
        onImageSelected(file, canvas.toDataURL('image/jpeg'));
      }
    }, 'image/jpeg', 0.92);
  };

  return (
    <div style={{ maxWidth: '840px', margin: '2rem auto 0 auto' }}>
      {/* Hero Header */}
      <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.45rem',
          padding: '0.35rem 0.9rem',
          borderRadius: '9999px',
          background: '#ecfdf5',
          color: '#047857',
          border: '1px solid #a7f3d0',
          fontSize: '0.82rem',
          fontWeight: 700,
          marginBottom: '1rem'
        }}>
          <Sparkles size={15} /> Multi-Item Food Localization & Macro Intelligence
        </div>
        <h1 style={{ fontSize: '2.5rem', lineHeight: 1.2, marginBottom: '0.75rem', color: '#0f172a' }}>
          Analyze Any Indian Meal in <span style={{ color: '#10b981' }}>Seconds</span>
        </h1>
        <p style={{ fontSize: '1.05rem', color: '#64748b', maxWidth: '580px', margin: '0 auto' }}>
          Upload or capture a photo of your plate. Our AI detects each item, calculates exact calories & macros, and suggests healthier substitutes.
        </p>
      </div>

      {/* Main Upload Box */}
      <div className="glass-card" style={{ padding: '2rem', marginBottom: '2.5rem' }}>
        {isCameraActive ? (
          /* Live Camera View */
          <div style={{ position: 'relative', borderRadius: '12px', overflow: 'hidden', background: '#000' }}>
            <video
              ref={videoRef}
              autoPlay
              playsInline
              style={{ width: '100%', height: '380px', objectFit: 'cover' }}
            />
            {/* Grid Overlay */}
            <div style={{
              position: 'absolute',
              inset: 0,
              display: 'grid',
              gridTemplateColumns: '1fr 1fr 1fr',
              gridTemplateRows: '1fr 1fr 1fr',
              border: '1px solid rgba(255,255,255,0.2)',
              pointerEvents: 'none'
            }}>
              <div style={{ borderRight: '1px solid rgba(255,255,255,0.2)', borderBottom: '1px solid rgba(255,255,255,0.2)' }} />
              <div style={{ borderRight: '1px solid rgba(255,255,255,0.2)', borderBottom: '1px solid rgba(255,255,255,0.2)' }} />
              <div style={{ borderBottom: '1px solid rgba(255,255,255,0.2)' }} />
              <div style={{ borderRight: '1px solid rgba(255,255,255,0.2)', borderBottom: '1px solid rgba(255,255,255,0.2)' }} />
              <div style={{ borderRight: '1px solid rgba(255,255,255,0.2)', borderBottom: '1px solid rgba(255,255,255,0.2)' }} />
              <div style={{ borderBottom: '1px solid rgba(255,255,255,0.2)' }} />
            </div>

            {/* Camera Controls */}
            <div style={{
              position: 'absolute',
              bottom: '1rem',
              left: 0,
              right: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '1.5rem'
            }}>
              <button
                onClick={stopCamera}
                className="btn btn-secondary"
                style={{ borderRadius: '50%', width: '46px', height: '46px', padding: 0, background: 'rgba(255,255,255,0.9)' }}
                title="Cancel Camera"
              >
                <X size={20} />
              </button>
              
              <button
                onClick={capturePhoto}
                className="btn btn-primary"
                style={{
                  borderRadius: '50%',
                  width: '68px',
                  height: '68px',
                  padding: 0,
                  boxShadow: '0 0 20px rgba(16, 185, 129, 0.6)'
                }}
                title="Capture Photo"
              >
                <Camera size={30} />
              </button>
            </div>
          </div>
        ) : (
          /* Drag & Drop / File Select */
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            style={{
              border: `2px dashed ${dragActive ? '#10b981' : '#cbd5e1'}`,
              borderRadius: '16px',
              padding: '3rem 2rem',
              textAlign: 'center',
              backgroundColor: dragActive ? '#ecfdf5' : '#f8fafc',
              transition: 'all 200ms ease',
              cursor: 'pointer'
            }}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={handleFileChange}
              style={{ display: 'none' }}
            />

            <div style={{
              width: '64px',
              height: '64px',
              borderRadius: '16px',
              background: '#ecfdf5',
              color: '#059669',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 1.25rem auto'
            }}>
              <Upload size={32} />
            </div>

            <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem', color: '#1e293b' }}>
              Drag & Drop your meal photo here
            </h3>
            <p style={{ fontSize: '0.9rem', color: '#64748b', marginBottom: '1.5rem' }}>
              Supports JPG, PNG, WEBP up to 15MB
            </p>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
              <button
                type="button"
                className="btn btn-primary"
                onClick={(e) => {
                  e.stopPropagation();
                  fileInputRef.current?.click();
                }}
              >
                <Upload size={18} />
                Browse Gallery
              </button>

              <button
                type="button"
                className="btn btn-secondary"
                onClick={(e) => {
                  e.stopPropagation();
                  startCamera();
                }}
              >
                <Camera size={18} />
                Live Camera
              </button>
            </div>
          </div>
        )}

        {cameraError && (
          <div style={{
            marginTop: '1rem',
            padding: '0.75rem 1rem',
            borderRadius: '8px',
            background: '#fee2e2',
            color: '#b91c1c',
            fontSize: '0.85rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}>
            <AlertCircle size={16} />
            <span>{cameraError}</span>
          </div>
        )}
      </div>

      {/* Instant Test Presets */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
          <h3 style={{ fontSize: '1.1rem', color: '#334155' }}>
            Or try with sample Indian meal plates:
          </h3>
          <span style={{ fontSize: '0.8rem', color: '#10b981', fontWeight: 600 }}>1-Click Instant Test</span>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '1rem'
        }}>
          {PRESET_MEALS.map((preset) => (
            <div
              key={preset.id}
              onClick={() => handleSelectPreset(preset)}
              className="glass-card"
              style={{
                padding: '1.2rem',
                cursor: 'pointer',
                borderLeft: `4px solid ${preset.color1}`,
                transition: 'all 200ms ease'
              }}
              onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-3px)'}
              onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
            >
              <div style={{ fontSize: '1rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.35rem' }}>
                {preset.title}
              </div>
              <p style={{ fontSize: '0.82rem', color: '#64748b', marginBottom: '0.75rem', lineHeight: 1.4 }}>
                {preset.desc}
              </p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                {preset.items.slice(0, 3).map((it, idx) => (
                  <span
                    key={idx}
                    style={{
                      fontSize: '0.72rem',
                      background: '#f1f5f9',
                      color: '#475569',
                      padding: '0.15rem 0.45rem',
                      borderRadius: '4px',
                      fontWeight: 500
                    }}
                  >
                    {it}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
