/**
 * FoodSense - Bounding Box Coordinate Scaler & Color Theme Utility
 * Handles original-resolution to rendered-display coordinate scaling accurately.
 */

export const CATEGORY_COLORS = {
  Breads: {
    stroke: '#f59e0b',
    fill: 'rgba(245, 158, 11, 0.18)',
    text: '#ffffff',
    bg: '#d97706',
    border: '#f59e0b'
  },
  Grains: {
    stroke: '#3b82f6',
    fill: 'rgba(59, 130, 246, 0.18)',
    text: '#ffffff',
    bg: '#2563eb',
    border: '#3b82f6'
  },
  'Rice Dishes': {
    stroke: '#06b6d4',
    fill: 'rgba(6, 182, 212, 0.18)',
    text: '#ffffff',
    bg: '#0891b2',
    border: '#06b6d4'
  },
  Lentils: {
    stroke: '#eab308',
    fill: 'rgba(234, 179, 8, 0.18)',
    text: '#ffffff',
    bg: '#ca8a04',
    border: '#eab308'
  },
  Curries: {
    stroke: '#ea580c',
    fill: 'rgba(234, 88, 12, 0.18)',
    text: '#ffffff',
    bg: '#c2410c',
    border: '#ea580c'
  },
  Legumes: {
    stroke: '#84cc16',
    fill: 'rgba(132, 204, 22, 0.18)',
    text: '#ffffff',
    bg: '#65a30d',
    border: '#84cc16'
  },
  Snacks: {
    stroke: '#ec4899',
    fill: 'rgba(236, 72, 153, 0.18)',
    text: '#ffffff',
    bg: '#db2777',
    border: '#ec4899'
  },
  Breakfast: {
    stroke: '#10b981',
    fill: 'rgba(16, 185, 129, 0.18)',
    text: '#ffffff',
    bg: '#059669',
    border: '#10b981'
  },
  Sweets: {
    stroke: '#a855f7',
    fill: 'rgba(168, 85, 247, 0.18)',
    text: '#ffffff',
    bg: '#9333ea',
    border: '#a855f7'
  },
  Default: {
    stroke: '#10b981',
    fill: 'rgba(16, 185, 129, 0.18)',
    text: '#ffffff',
    bg: '#059669',
    border: '#10b981'
  }
};

export const getCategoryTheme = (category) => {
  return CATEGORY_COLORS[category] || CATEGORY_COLORS.Default;
};

/**
 * Calculates display bounding box with letterbox offset for object-fit: contain canvas
 */
export const calculateRenderedBox = ({
  rawBox,
  origWidth,
  origHeight,
  containerWidth,
  containerHeight
}) => {
  if (!rawBox || !origWidth || !origHeight || !containerWidth || !containerHeight) {
    return { x: 0, y: 0, width: 0, height: 0 };
  }

  // Calculate aspect ratios
  const imgAspect = origWidth / origHeight;
  const containerAspect = containerWidth / containerHeight;

  let renderWidth = containerWidth;
  let renderHeight = containerHeight;
  let offsetX = 0;
  let offsetY = 0;

  if (containerAspect > imgAspect) {
    // Letterbox on left & right
    renderHeight = containerHeight;
    renderWidth = containerHeight * imgAspect;
    offsetX = (containerWidth - renderWidth) / 2;
  } else {
    // Letterbox on top & bottom
    renderWidth = containerWidth;
    renderHeight = containerWidth / imgAspect;
    offsetY = (containerHeight - renderHeight) / 2;
  }

  const scaleX = renderWidth / origWidth;
  const scaleY = renderHeight / origHeight;

  const x_min = rawBox.x_min !== undefined ? rawBox.x_min : (rawBox[0] || 0);
  const y_min = rawBox.y_min !== undefined ? rawBox.y_min : (rawBox[1] || 0);
  const x_max = rawBox.x_max !== undefined ? rawBox.x_max : (rawBox[2] || origWidth);
  const y_max = rawBox.y_max !== undefined ? rawBox.y_max : (rawBox[3] || origHeight);

  const x = offsetX + (x_min * scaleX);
  const y = offsetY + (y_min * scaleY);
  const width = (x_max - x_min) * scaleX;
  const height = (y_max - y_min) * scaleY;

  return {
    x: Math.round(x),
    y: Math.round(y),
    width: Math.round(width),
    height: Math.round(height),
    scaleX,
    scaleY,
    offsetX,
    offsetY
  };
};
