import React, { useRef, useEffect, useState, useCallback } from 'react';
import { calculateRenderedBox, getCategoryTheme } from '../utils/bboxScaler';

export default function BoundingBoxCanvas({
  imageUrl,
  imageMeta,
  items,
  selectedItemId,
  hoveredItemId,
  onSelectItem
}) {
  const containerRef = useRef(null);
  const canvasRef = useRef(null);
  const imageRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const [imgNaturalSize, setImgNaturalSize] = useState({ width: 600, height: 600 });

  // Update container dimensions on mount and resize
  const updateDimensions = useCallback(() => {
    if (containerRef.current) {
      const { clientWidth, clientHeight } = containerRef.current;
      if (clientWidth > 0 && clientHeight > 0) {
        setDimensions({ width: clientWidth, height: clientHeight });
      }
    }
  }, []);

  const handleImageLoad = (e) => {
    if (e.target) {
      setImgNaturalSize({
        width: e.target.naturalWidth || 600,
        height: e.target.naturalHeight || 600
      });
    }
    updateDimensions();
  };

  useEffect(() => {
    updateDimensions();
    const observer = new ResizeObserver(() => {
      updateDimensions();
    });
    if (containerRef.current) {
      observer.observe(containerRef.current);
    }
    window.addEventListener('resize', updateDimensions);
    return () => {
      observer.disconnect();
      window.removeEventListener('resize', updateDimensions);
    };
  }, [updateDimensions]);

  // Redraw canvas bounding boxes whenever dimensions, items, or selection changes
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || dimensions.width === 0 || dimensions.height === 0) return;

    const ctx = canvas.getContext('2d');
    canvas.width = dimensions.width;
    canvas.height = dimensions.height;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const origW = imageMeta?.width || imgNaturalSize.width || 600;
    const origH = imageMeta?.height || imgNaturalSize.height || 600;

    const safeItems = items || [];

    safeItems.forEach((det, idx) => {
      const itemId = det.item_id || det.label || `item_${idx}`;
      const isSelected = selectedItemId === itemId;
      const isHovered = hoveredItemId === itemId;
      const isHighlighted = isSelected || isHovered;
      const anyHighlighted = Boolean(selectedItemId || hoveredItemId);
      const isSuggested = Boolean(det.needs_confirmation);

      let theme = getCategoryTheme(det.category || 'Default');
      if (isSuggested) {
        theme = {
          fill: 'rgba(245, 158, 11, 0.18)',
          stroke: '#f59e0b',
          bg: '#d97706'
        };
      }

      const renderedBox = calculateRenderedBox({
        rawBox: det.bbox,
        origWidth: origW,
        origHeight: origH,
        containerWidth: dimensions.width,
        containerHeight: dimensions.height
      });

      const { x, y, width, height } = renderedBox;
      if (width <= 0 || height <= 0) return;

      ctx.save();

      // Bounding Box Rectangle Fill
      ctx.fillStyle = isHighlighted
        ? (isSuggested ? 'rgba(245, 158, 11, 0.35)' : theme.fill.replace('0.18', '0.35'))
        : (anyHighlighted ? 'rgba(0,0,0,0.05)' : theme.fill);
      ctx.fillRect(x, y, width, height);

      // Bounding Box Stroke
      ctx.strokeStyle = isHighlighted
        ? theme.stroke
        : (anyHighlighted ? 'rgba(150, 150, 150, 0.4)' : theme.stroke);
      ctx.lineWidth = isHighlighted ? 3 : (isSuggested ? 2.5 : 2);
      ctx.setLineDash(isSuggested ? [6, 4] : (isHighlighted ? [] : [6, 3]));
      ctx.strokeRect(x, y, width, height);

      // Bounding Box Corner Reticles if highlighted
      if (isHighlighted) {
        ctx.strokeStyle = theme.stroke;
        ctx.lineWidth = 4;
        ctx.setLineDash([]);
        const len = Math.min(16, width * 0.25, height * 0.25);
        
        // Top-Left
        ctx.beginPath();
        ctx.moveTo(x, y + len); ctx.lineTo(x, y); ctx.lineTo(x + len, y);
        ctx.stroke();

        // Top-Right
        ctx.beginPath();
        ctx.moveTo(x + width - len, y); ctx.lineTo(x + width, y); ctx.lineTo(x + width, y + len);
        ctx.stroke();

        // Bottom-Left
        ctx.beginPath();
        ctx.moveTo(x, y + height - len); ctx.lineTo(x, y + height); ctx.lineTo(x + len, y + height);
        ctx.stroke();

        // Bottom-Right
        ctx.beginPath();
        ctx.moveTo(x + width - len, y + height); ctx.lineTo(x + width, y + height); ctx.lineTo(x + width, y + height - len);
        ctx.stroke();
      }

      // Label Tag Background & Text
      const displayName = det.display_name || det.label?.replace(/_/g, ' ').toUpperCase() || 'Food';
      const labelText = isSuggested
        ? `? Possible: ${displayName} (Tap to confirm)`
        : `${displayName} (${Math.round((det.confidence || 0.9) * 100)}%)`;

      ctx.font = `600 ${isHighlighted ? '12px' : '11px'} 'Plus Jakarta Sans', sans-serif`;
      const textMetrics = ctx.measureText(labelText);
      const tagPadding = 6;
      const tagWidth = textMetrics.width + (tagPadding * 2);
      const tagHeight = 22;

      // Position label above box if space permits, else inside top
      let tagX = x;
      let tagY = y - tagHeight - 2;
      if (tagY < 4) {
        tagY = y + 4;
      }

      // Draw tag rounded pill
      ctx.fillStyle = isHighlighted ? theme.bg : (anyHighlighted ? '#64748b' : theme.bg);
      ctx.beginPath();
      ctx.roundRect ? ctx.roundRect(tagX, tagY, tagWidth, tagHeight, 4) : ctx.fillRect(tagX, tagY, tagWidth, tagHeight);
      ctx.fill();

      // Draw tag label text
      ctx.fillStyle = '#ffffff';
      ctx.fillText(labelText, tagX + tagPadding, tagY + 15);

      ctx.restore();
    });

  }, [dimensions, items, selectedItemId, hoveredItemId, imageMeta, imgNaturalSize]);

  // Handle canvas click to select corresponding food item
  const handleCanvasClick = (e) => {
    if (!canvasRef.current || !onSelectItem) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    const origW = imageMeta?.width || imgNaturalSize.width || 600;
    const origH = imageMeta?.height || imgNaturalSize.height || 600;

    const safeItems = items || [];

    for (let i = safeItems.length - 1; i >= 0; i--) {
      const det = safeItems[i];
      const box = calculateRenderedBox({
        rawBox: det.bbox,
        origWidth: origW,
        origHeight: origH,
        containerWidth: dimensions.width,
        containerHeight: dimensions.height
      });

      if (
        clickX >= box.x &&
        clickX <= box.x + box.width &&
        clickY >= box.y &&
        clickY <= box.y + box.height
      ) {
        onSelectItem(det.item_id || det.label || `item_${i}`);
        return;
      }
    }

    onSelectItem(null);
  };

  return (
    <div
      ref={containerRef}
      style={{
        position: 'relative',
        width: '100%',
        borderRadius: '16px',
        overflow: 'hidden',
        background: '#0f172a',
        boxShadow: 'var(--shadow-md)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '340px'
      }}
    >
      {/* Underlying Image */}
      {imageUrl && (
        <img
          ref={imageRef}
          src={imageUrl}
          alt="Analyzed Meal"
          onLoad={handleImageLoad}
          style={{
            width: '100%',
            height: 'auto',
            maxHeight: '480px',
            objectFit: 'contain',
            display: 'block'
          }}
        />
      )}

      {/* Interactive Overlay Canvas for Bounding Boxes */}
      <canvas
        ref={canvasRef}
        onClick={handleCanvasClick}
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          cursor: 'pointer',
          zIndex: 10
        }}
      />
    </div>
  );
}
