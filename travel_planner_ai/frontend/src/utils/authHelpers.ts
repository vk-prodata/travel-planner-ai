/**
 * Authentication Helper Utilities
 * Centralized logic for OAuth flows and token management
 */

import { getBrowserInfo } from './browserDetection';

export interface AuthState {
  returnUrl: string;
  embedded: boolean;
  timestamp: number;
}

/**
 * Build Google OAuth redirect URL for embedded browsers
 */
export const buildGoogleAuthUrl = (clientId: string, returnUrl: string): string => {
  const redirectUri = encodeURIComponent(window.location.origin + '/auth/callback');
  const scope = encodeURIComponent('email profile openid');
  const state = encodeURIComponent(JSON.stringify({
    returnUrl,
    embedded: true,
    timestamp: Date.now()
  }));

  return `https://accounts.google.com/o/oauth2/v2/auth?` +
    `client_id=${clientId}&` +
    `redirect_uri=${redirectUri}&` +
    `scope=${scope}&` +
    `response_type=code&` +
    `state=${state}&` +
    `access_type=offline&` +
    `prompt=consent`;
};

/**
 * Store auth state for restoration after redirect
 */
export const storeAuthState = (returnUrl: string): void => {
  const authState: AuthState = {
    returnUrl,
    timestamp: Date.now(),
    embedded: true
  };
  localStorage.setItem('auth_redirect_state', JSON.stringify(authState));
};

/**
 * Retrieve and clean up stored auth state
 */
export const getAndClearAuthState = (): AuthState | null => {
  const stored = localStorage.getItem('auth_redirect_state');
  if (!stored) return null;

  try {
    const parsed = JSON.parse(stored);
    localStorage.removeItem('auth_redirect_state');
    return parsed;
  } catch (e) {
    console.warn('Could not parse auth redirect state:', e);
    localStorage.removeItem('auth_redirect_state');
    return null;
  }
};

/**
 * Initiate redirect-based authentication for embedded browsers
 */
export const initiateRedirectAuth = async (returnUrl?: string): Promise<void> => {
  const clientId = process.env.REACT_APP_GOOGLE_CLIENT_ID;
  if (!clientId) {
    throw new Error('Google Client ID not found');
  }

  const currentUrl = returnUrl || window.location.href;
  const googleAuthUrl = buildGoogleAuthUrl(clientId, currentUrl);
  
  console.log('Redirecting to Google Auth:', googleAuthUrl);
  
  // Store current state for restoration after redirect
  storeAuthState(currentUrl);

  // Redirect to Google OAuth
  window.location.href = googleAuthUrl;
};

/**
 * Get optimal OAuth configuration based on browser type
 */
export const getOAuthConfig = (clientId: string, callback: any) => {
  const browserInfo = getBrowserInfo();
  
  const baseConfig = {
    client_id: clientId,
    scope: 'email profile openid',
    callback,
    access_type: 'offline',
    prompt: 'consent'
  };

  // Enhanced configuration for embedded browsers
  if (browserInfo.requiresRedirectAuth) {
    return {
      ...baseConfig,
      ux_mode: 'redirect',
      redirect_uri: window.location.origin + '/auth/callback',
      state: 'embedded_browser'
    };
  }

  return baseConfig;
};

/**
 * Get optimal request options for token requests based on browser
 */
export const getTokenRequestOptions = (browserInfo: any) => {
  if (browserInfo.requiresRedirectAuth) {
    return {
      prompt: 'consent',
      hint: localStorage.getItem('userEmail') || '',
      ux_mode: 'redirect',
      redirect_uri: window.location.origin + '/auth/callback'
    };
  }

  return {
    prompt: 'consent'
  };
};

/**
 * Handle OAuth callback URL parameters
 */
export const parseOAuthCallback = () => {
  const urlParams = new URLSearchParams(window.location.search);
  return {
    code: urlParams.get('code'),
    state: urlParams.get('state'),
    error: urlParams.get('error')
  };
};

/**
 * Parse state parameter safely
 */
export const parseStateParameter = (state: string | null): any => {
  if (!state) return null;
  
  try {
    return JSON.parse(decodeURIComponent(state));
  } catch (e) {
    console.warn('Could not parse state parameter:', e);
    return null;
  }
};

/**
 * Store user tokens and data in localStorage
 */
export const storeUserTokens = (tokenData: any, jwtAccessToken?: string, jwtRefreshToken?: string): void => {
  // Store JWT tokens primarily
  if (jwtAccessToken) {
    localStorage.setItem('token', jwtAccessToken);
    localStorage.setItem('tokenType', 'jwt');
  }

  if (jwtRefreshToken) {
    localStorage.setItem('jwtRefreshToken', jwtRefreshToken);
  }

  // Store user data
  localStorage.setItem('userEmail', tokenData.email);
  localStorage.setItem('userId', tokenData.id);
  localStorage.setItem('userName', tokenData.name || '');
  localStorage.setItem('tokenTimestamp', Date.now().toString());
};

/**
 * Clean up URL after OAuth callback
 */
export const cleanupCallbackUrl = (returnUrl: string = '/'): void => {
  window.history.replaceState({}, document.title, returnUrl);
};

/**
 * Open current URL in external browser (for embedded browser fallback)
 */
export const openInExternalBrowser = (): void => {
  const currentUrl = window.location.href;
  window.open(currentUrl, '_blank', 'noopener,noreferrer');
}; 