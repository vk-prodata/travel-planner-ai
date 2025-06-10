import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Button, Spinner, Alert } from 'react-bootstrap';
import { FcGoogle } from 'react-icons/fc';
import { getBrowserInfo, getBrowserDisplayName } from '../utils/browserDetection';
import { openInExternalBrowser } from '../utils/externalBrowser';
import { testOAuthRedirect } from '../utils/debugAuth';

const AuthForm: React.FC = () => {
  const { signIn } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showEmbeddedTip, setShowEmbeddedTip] = useState(false);

  const browserInfo = getBrowserInfo();
  const browserDisplayName = getBrowserDisplayName();

  const handleSignIn = async () => {
    try {
      setError(null);
      setIsLoading(true);
      
      // Debug OAuth configuration
      const debugResult = testOAuthRedirect();
      console.log('OAuth Debug Result:', debugResult);
      
      // 🚀 PROACTIVE: For Telegram/embedded browsers, immediately try external browser
      if (browserInfo.isEmbedded || browserInfo.isTelegram) {
        console.log('[AUTH] Detected embedded browser, attempting external browser opening');
        
        const success = await openInExternalBrowser({
          url: window.location.href,
          fallbackMessage: 'Please open this link in your default browser (Safari/Chrome) to sign in',
          trackingParams: {
            auth_source: 'embedded_browser',
            platform: browserDisplayName.toLowerCase(),
            auth_attempt: Date.now().toString()
          }
        });
        
        if (success) {
          setIsLoading(false);
          return; // Don't proceed with embedded browser auth
        } else {
          // Show fallback tip if external browser opening failed
          setShowEmbeddedTip(true);
        }
      }
      
      // Show tip for embedded browsers (fallback scenario)
      if (browserInfo.isEmbedded) {
        setShowEmbeddedTip(true);
      }
      
      await signIn();
    } catch (error) {
      console.error('Sign-in error:', error);
      
      if (browserInfo.isEmbedded) {
        setError('Sign-in from embedded browsers may require opening in your default browser. Please use the "Open in browser instead" button below.');
      } else {
        setError('Failed to sign in. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenInBrowser = async () => {
    const success = await openInExternalBrowser({
      url: window.location.href,
      fallbackMessage: 'Please copy this link and open it in Safari, Chrome, or your default browser',
      trackingParams: {
        auth_source: 'manual_external_browser',
        platform: browserDisplayName.toLowerCase()
      }
    });
    
    if (!success) {
      // Ultimate fallback - copy to clipboard
      try {
        await navigator.clipboard.writeText(window.location.href);
        alert('Link copied to clipboard! Please paste it in Safari, Chrome, or your default browser to sign in.');
      } catch (e) {
        alert(`Please copy this link and open it in your default browser: ${window.location.href}`);
      }
    }
  };

  return (
    <div className="d-inline-block">
      {error && (
        <div className="text-danger small mb-2">
          {error}
          {browserInfo.isEmbedded && (
            <div className="mt-1">
              <Button 
                variant="link" 
                size="sm" 
                className="p-0 text-primary"
                onClick={handleOpenInBrowser}
              >
                Open in browser instead
              </Button>
            </div>
          )}
        </div>
      )}
      
      {showEmbeddedTip && browserInfo.isTelegram && (
        <Alert variant="warning" className="small mb-2" dismissible onClose={() => setShowEmbeddedTip(false)}>
          <strong>🔄 Telegram Authentication:</strong> We're trying to open this in your default browser (Safari/Chrome) for secure sign-in. If it doesn't open automatically, use the "Open in browser instead" button below.
        </Alert>
      )}
      
      {showEmbeddedTip && browserInfo.isEmbedded && !browserInfo.isTelegram && (
        <Alert variant="info" className="small mb-2" dismissible onClose={() => setShowEmbeddedTip(false)}>
          <strong>{browserDisplayName} User:</strong> For the best sign-in experience, we recommend opening this in your default browser.
        </Alert>
      )}
      
      <Button 
        variant="outline-primary"
        onClick={handleSignIn}
        disabled={isLoading}
        className="rounded-pill d-flex align-items-center"
        size="sm"
        style={{ 
          fontSize: '0.875rem',
          padding: '0.25rem 0.75rem'
        }}
      >
        {isLoading ? (
          <Spinner animation="border" size="sm" />
        ) : (
          <>
            <FcGoogle size={16} className="me-1" />
            <span>Sign in{browserInfo.isTelegram ? ` (will open in external browser)` : ''}</span>
          </>
        )}
      </Button>
      
      {browserInfo.isEmbedded && !error && !isLoading && (
        <div className="d-flex flex-column gap-1 mt-2">
          <div className="text-muted small">
            📱 Using {browserDisplayName} - for secure sign-in, we'll open your default browser
          </div>
          <Button 
            variant="outline-secondary" 
            size="sm" 
            onClick={handleOpenInBrowser}
            className="align-self-start"
            style={{ fontSize: '0.75rem', padding: '0.125rem 0.5rem' }}
          >
            Open in browser instead
          </Button>
        </div>
      )}
    </div>
  );
};

export default AuthForm; 