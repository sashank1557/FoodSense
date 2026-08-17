/**
 * FoodSense - Centralized Error Handler Middleware
 * Formats uniform JSON error responses for the frontend.
 */

const errorHandler = (err, req, res, next) => {
  console.error('[Express Relay Error]:', err.message || err);

  if (err.name === 'MulterError') {
    if (err.code === 'LIMIT_FILE_SIZE') {
      return res.status(413).json({
        error: 'File Too Large',
        message: 'Image size exceeds maximum limit of 15MB. Please upload a smaller photo.'
      });
    }
    return res.status(400).json({
      error: 'Upload Error',
      message: err.message
    });
  }

  const statusCode = err.statusCode || (err.response ? err.response.status : 500);
  const message = err.response && err.response.data && err.response.data.message
    ? err.response.data.message
    : (err.message || 'Internal server error while processing food analysis.');

  res.status(statusCode).json({
    error: err.name || 'ServerError',
    message: message,
    timestamp: new Date().toISOString()
  });
};

module.exports = errorHandler;
