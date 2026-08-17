import React from 'react';
import { AlertTriangle, RotateCcw } from 'lucide-react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[FoodSense ErrorBoundary] Caught render error:', error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    if (this.props.onReset) {
      this.props.onReset();
    } else {
      window.location.reload();
    }
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          maxWidth: '680px',
          margin: '3rem auto',
          padding: '2.5rem 2rem',
          background: '#ffffff',
          borderRadius: '16px',
          border: '1px solid #fee2e2',
          boxShadow: '0 10px 25px rgba(239, 68, 68, 0.08)',
          textAlign: 'center'
        }}>
          <div style={{
            width: '56px',
            height: '56px',
            borderRadius: '50%',
            background: '#fee2e2',
            color: '#dc2626',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1.25rem'
          }}>
            <AlertTriangle size={28} />
          </div>

          <h2 style={{ fontSize: '1.4rem', color: '#0f172a', fontWeight: 700, marginBottom: '0.5rem' }}>
            Something went wrong displaying results
          </h2>

          <p style={{ fontSize: '0.92rem', color: '#64748b', lineHeight: 1.5, marginBottom: '1.75rem' }}>
            An unexpected error occurred while rendering the meal analysis view. Please try analyzing again or upload a different image.
          </p>

          <div style={{ display: 'flex', justifyContent: 'center', gap: '0.75rem' }}>
            <button
              onClick={this.handleReset}
              className="btn btn-primary"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.65rem 1.25rem',
                fontSize: '0.9rem'
              }}
            >
              <RotateCcw size={16} />
              <span>Try Again</span>
            </button>
          </div>

          {this.state.error && (
            <details style={{
              marginTop: '1.75rem',
              textAlign: 'left',
              background: '#f8fafc',
              padding: '0.75rem 1rem',
              borderRadius: '8px',
              border: '1px solid #e2e8f0',
              fontSize: '0.75rem',
              color: '#94a3b8'
            }}>
              <summary style={{ cursor: 'pointer', fontWeight: 600, color: '#64748b' }}>
                Technical Error Details
              </summary>
              <pre style={{ marginTop: '0.5rem', whiteSpace: 'pre-wrap', color: '#dc2626', overflowX: 'auto' }}>
                {this.state.error?.toString()}
              </pre>
            </details>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}
