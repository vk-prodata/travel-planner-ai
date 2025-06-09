import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Spinner, Alert, Container } from 'react-bootstrap';
import { parseOAuthCallback, parseStateParameter, storeUserTokens, getAndClearAuthState } from '../utils/authHelpers';

const AuthCallback: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const processAuthCallback = async () => {
      try {
        const { code, state, error } = parseOAuthCallback();

        if (error) {
          console.error('OAuth error:', error);
          setError(`Authentication failed: ${error}`);
          setStatus('error');
          return;
        }

        if (!code) {
          console.error('No authorization code received');
          setError('No authorization code received from Google');
          setStatus('error');
          return;
        }

        console.log('Processing OAuth callback with code:', code.substring(0, 10) + '...');

        // Parse state using centralized utility
        const parsedState = parseStateParameter(state);

        // Exchange authorization code for access token
        const tokenResponse = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/auth/google/callback`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            code,
            redirect_uri: window.location.origin + '/auth/callback',
            state: parsedState
          })
        });

        if (!tokenResponse.ok) {
          const errorText = await tokenResponse.text();
          console.error('Token exchange failed:', errorText);
          setError(`Authentication failed: ${errorText}`);
          setStatus('error');
          return;
        }

        const tokenData = await tokenResponse.json();
        console.log('Token exchange successful');

        // Extract JWT tokens from response headers
        const jwtAccessToken = tokenResponse.headers.get('X-Access-Token');
        const jwtRefreshToken = tokenResponse.headers.get('X-Refresh-Token');

        // Store tokens and user data using centralized utility
        storeUserTokens(tokenData, jwtAccessToken || undefined, jwtRefreshToken || undefined);

        setStatus('success');

        // Get return URL from stored state or parsed state
        const authState = getAndClearAuthState();
        const returnUrl = authState?.returnUrl || parsedState?.returnUrl || '/';

        // Redirect back to the original page after a short delay
        setTimeout(() => {
          window.location.href = returnUrl;
        }, 2000);

      } catch (err) {
        console.error('Auth callback processing failed:', err);
        setError(err instanceof Error ? err.message : 'Unknown error occurred');
        setStatus('error');
      }
    };

    processAuthCallback();
  }, [searchParams]);

  const handleReturnToApp = () => {
    const authState = getAndClearAuthState();
    const returnUrl = authState?.returnUrl || '/';
    navigate(returnUrl);
  };

  return (
    <Container className="d-flex flex-column align-items-center justify-content-center" style={{ minHeight: '100vh' }}>
      {status === 'processing' && (
        <div className="text-center">
          <Spinner animation="border" role="status" className="mb-3">
            <span className="visually-hidden">Loading...</span>
          </Spinner>
          <h4>Completing Sign In...</h4>
          <p className="text-muted">Please wait while we complete your authentication.</p>
        </div>
      )}

      {status === 'success' && (
        <div className="text-center">
          <Alert variant="success">
            <Alert.Heading>✅ Sign In Successful!</Alert.Heading>
            <p>You have been successfully signed in. Redirecting you back to the app...</p>
          </Alert>
          <button className="btn btn-primary" onClick={handleReturnToApp}>
            Return to App
          </button>
        </div>
      )}

      {status === 'error' && (
        <div className="text-center">
          <Alert variant="danger">
            <Alert.Heading>❌ Sign In Failed</Alert.Heading>
            <p>{error}</p>
          </Alert>
          <button className="btn btn-primary" onClick={handleReturnToApp}>
            Return to App
          </button>
        </div>
      )}
    </Container>
  );
};

export default AuthCallback; 