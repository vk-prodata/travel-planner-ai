import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Button, Spinner, Alert } from 'react-bootstrap';
import { FcGoogle } from 'react-icons/fc';
import { getBrowserInfo, getBrowserDisplayName } from '../utils/browserDetection';
import { openInExternalBrowser } from '../utils/authHelpers';
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
      
      // Show tip for embedded browsers
      if (browserInfo.isEmbedded) {
        setShowEmbeddedTip(true);
      }
      
      await signIn();
    } catch (error) {
      console.error('Sign-in error:', error);
      
      if (browserInfo.isEmbedded) {
        setError('Sign-in from embedded browsers may require additional steps. If this doesn\'t work, try copying the link to your regular browser.');
      } else {
        setError('Failed to sign in. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenInBrowser = () => {
    openInExternalBrowser();
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
        <Alert variant="info" className="small mb-2" dismissible onClose={() => setShowEmbeddedTip(false)}>
          <strong>Telegram User:</strong> If sign-in doesn't work, you may need to copy this link to your regular browser.
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
            <span>Sign in{browserInfo.isTelegram ? ` (${browserDisplayName})` : ''}</span>
          </>
        )}
      </Button>
      
      {browserInfo.isEmbedded && !error && !isLoading && (
        <div className="text-muted small mt-1">
          📱 Using {browserDisplayName} - enhanced compatibility enabled
        </div>
      )}
    </div>
  );
};

export default AuthForm; 