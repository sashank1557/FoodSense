import React, { useState, useEffect, useRef } from 'react';
import Navbar from './components/Navbar';
import UploadScreen from './components/UploadScreen';
import ImagePreview from './components/ImagePreview';
import AnalyzingState from './components/AnalyzingState';
import ResultsScreen from './components/ResultsScreen';
import ErrorBoundary from './components/ErrorBoundary';
import MealHistoryModal from './components/MealHistoryModal';
import AuthModal from './components/AuthModal';
import {
  checkBackendHealth,
  analyzeMealImage,
  fetchSupportedClasses,
  fetchCurrentUser,
  setAuthToken
} from './services/api';
import confetti from 'canvas-confetti';
import { Server, AlertTriangle, RefreshCw } from 'lucide-react';

export default function App() {
  const [screenState, setScreenState] = useState('upload'); // 'upload' | 'preview' | 'analyzing' | 'results'
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [analysisData, setAnalysisData] = useState(null);
  const [serverStatus, setServerStatus] = useState('waking');
  const [errorInfo, setErrorInfo] = useState(null); // { message, isColdStart, isValidationError }
  const [allClasses, setAllClasses] = useState([]);
  
  // Auth & Modal States
  const [user, setUser] = useState(null);
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);

  const abortControllerRef = useRef(null);

  // Restore authenticated session on mount
  useEffect(() => {
    fetchCurrentUser().then(userData => {
      if (userData) {
        setUser(userData);
      }
    });
  }, []);

  // Poll server health on mount
  useEffect(() => {
    const checkStatus = async () => {
      const health = await checkBackendHealth();
      if (health.success) {
        setServerStatus('healthy');
      } else {
        setServerStatus('waking');
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 15000);

    // Fetch classes
    fetchSupportedClasses().then(data => {
      if (data?.classes) {
        setAllClasses(data.classes);
      }
    });

    return () => clearInterval(interval);
  }, []);

  // Handle image selected from gallery or camera
  const handleImageSelected = (file, dataUrl) => {
    setSelectedFile(file);
    setPreviewUrl(dataUrl);
    setErrorInfo(null);
    setScreenState('preview');
  };

  // Start analysis
  const handleStartAnalysis = async () => {
    if (!selectedFile) return;

    setScreenState('analyzing');
    setErrorInfo(null);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const result = await analyzeMealImage(selectedFile, {
        signal: controller.signal
      });

      setAnalysisData(result);
      setScreenState('results');

      // Confetti celebration
      try {
        confetti({
          particleCount: 60,
          spread: 70,
          origin: { y: 0.7 }
        });
      } catch (e) {}

    } catch (err) {
      if (err.isCanceled) {
        setScreenState('upload');
      } else {
        setErrorInfo({
          message: err.message || 'Analysis failed. Please check server connection.',
          isColdStart: Boolean(err.isColdStart),
          isValidationError: Boolean(err.isValidationError)
        });
        setScreenState('preview');
      }
    } finally {
      abortControllerRef.current = null;
    }
  };

  // Cancel running analysis
  const handleCancelAnalysis = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setScreenState('upload');
  };

  // Reset to upload screen
  const handleReset = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setAnalysisData(null);
    setErrorInfo(null);
    setScreenState('upload');
  };

  // Select meal from history modal
  const handleSelectHistoryMeal = (mealData) => {
    setAnalysisData({
      status: 'success',
      meal_id: mealData.meal_id,
      items: mealData.items,
      meal_summary: mealData.meal_summary,
      processing_time_ms: 120
    });
    setPreviewUrl(null);
    setScreenState('results');
  };

  // Handle logout
  const handleLogout = () => {
    setAuthToken(null);
    setUser(null);
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: '#f8fafc' }}>
      {/* Top Navbar */}
      <Navbar
        serverStatus={serverStatus}
        onOpenHistory={() => setIsHistoryOpen(true)}
        onReset={handleReset}
        hasResults={screenState === 'results'}
        user={user}
        onOpenAuth={() => setIsAuthOpen(true)}
        onLogout={handleLogout}
      />

      {/* Main Content Area */}
      <main className="app-container" style={{ flex: 1, paddingTop: '1rem' }}>
        
        {/* Contextual Error Banner */}
        {errorInfo && (
          <div style={{
            maxWidth: '640px',
            margin: '1rem auto',
            padding: '1rem 1.25rem',
            background: errorInfo.isColdStart ? '#fffbeb' : '#fee2e2',
            border: `1px solid ${errorInfo.isColdStart ? '#fde68a' : '#fca5a5'}`,
            borderRadius: '12px',
            color: errorInfo.isColdStart ? '#92400e' : '#b91c1c',
            fontSize: '0.9rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '0.75rem',
            boxShadow: '0 4px 12px rgba(0,0,0,0.05)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
              {errorInfo.isColdStart ? (
                <Server size={20} color="#d97706" style={{ flexShrink: 0 }} />
              ) : (
                <AlertTriangle size={20} color="#dc2626" style={{ flexShrink: 0 }} />
              )}
              <div>
                <strong>{errorInfo.isColdStart ? 'Backend Waking Up:' : 'Upload Notice:'}</strong> {errorInfo.message}
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexShrink: 0 }}>
              {errorInfo.isColdStart && (
                <button
                  onClick={handleStartAnalysis}
                  className="btn btn-primary"
                  style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
                >
                  <RefreshCw size={13} />
                  <span>Retry Now</span>
                </button>
              )}
              <button
                onClick={() => setErrorInfo(null)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: errorInfo.isColdStart ? '#92400e' : '#b91c1c',
                  fontWeight: 700,
                  cursor: 'pointer',
                  fontSize: '1rem',
                  padding: '0.2rem'
                }}
              >
                ✕
              </button>
            </div>
          </div>
        )}

        {/* Screen Routing */}
        {screenState === 'upload' && (
          <UploadScreen onImageSelected={handleImageSelected} />
        )}

        {screenState === 'preview' && (
          <ImagePreview
            file={selectedFile}
            previewUrl={previewUrl}
            onAnalyze={handleStartAnalysis}
            onCancel={handleReset}
          />
        )}

        {screenState === 'analyzing' && (
          <AnalyzingState
            previewUrl={previewUrl}
            onCancel={handleCancelAnalysis}
          />
        )}

        {screenState === 'results' && analysisData && (
          <ErrorBoundary onReset={handleReset}>
            <ResultsScreen
              analysisData={analysisData}
              previewUrl={previewUrl}
              onReset={handleReset}
              allClasses={allClasses}
            />
          </ErrorBoundary>
        )}
      </main>

      {/* Auth Modal */}
      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        onAuthSuccess={(userData) => setUser(userData)}
      />

      {/* Meal History & Daily Dashboard Modal */}
      <MealHistoryModal
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        user={user}
        onOpenAuth={() => setIsAuthOpen(true)}
        onSelectMeal={handleSelectHistoryMeal}
      />
    </div>
  );
}
