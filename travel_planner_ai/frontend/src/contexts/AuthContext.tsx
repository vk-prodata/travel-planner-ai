import React, { createContext, useContext, useEffect, useState } from 'react';
import { User } from '../types';
import { getUserCredits } from '../services/creditsService';
import { getBrowserInfo, logBrowserInfo } from '../utils/browserDetection';
import { 
  initiateRedirectAuth, 
  getOAuthConfig, 
  getTokenRequestOptions,
  parseOAuthCallback,
  parseStateParameter,
  storeUserTokens,
  cleanupCallbackUrl,
  getAndClearAuthState
} from '../utils/authHelpers';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signIn: () => Promise<void>;
  signOut: () => Promise<void>;
  refreshUserCredits: () => Promise<void>;
  ensureValidToken: () => Promise<string | null>;
}

// Create context with default values
const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  signIn: async () => {},
  signOut: async () => {},
  refreshUserCredits: async () => {},
  ensureValidToken: async () => null
});

declare global {
  interface Window {
    google: any;
  }
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [tokenClient, setTokenClient] = useState<any>(null);

  useEffect(() => {
    const tryRestoreSession = async () => {
      // Check for OAuth callback parameters first
      const { code, state, error } = parseOAuthCallback();

      if (code) {
        console.log('OAuth callback detected, processing...');
        try {
          // Handle OAuth callback
          const tokenResponse = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/auth/google/callback`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              code,
              redirect_uri: window.location.origin + '/auth/callback',
              state: parseStateParameter(state)
            })
          });

          if (tokenResponse.ok) {
            const tokenData = await tokenResponse.json();
            const jwtAccessToken = tokenResponse.headers.get('X-Access-Token');
            const jwtRefreshToken = tokenResponse.headers.get('X-Refresh-Token');

            // Store tokens and user data using centralized utility
            storeUserTokens(tokenData, jwtAccessToken || undefined, jwtRefreshToken || undefined);

            // Update user state
            const userData: User = {
              id: tokenData.id,
              name: tokenData.name,
              email: tokenData.email,
              availableCredits: tokenData.available_credits,
              totalCreditsPurchased: tokenData.total_credits_purchased
            };
            setUser(userData);

            // Clean up URL and redirect using centralized utility
            const authState = getAndClearAuthState();
            const returnUrl = authState?.returnUrl || '/';
            cleanupCallbackUrl(returnUrl);
            
            console.log('OAuth callback processed successfully');
            return;
          } else {
            console.error('OAuth callback failed:', await tokenResponse.text());
          }
        } catch (error) {
          console.error('Error processing OAuth callback:', error);
        } finally {
          loadGoogleScript();
        }
        return;
      }

      if (error) {
        console.error('OAuth error:', error);
        loadGoogleScript();
        return;
      }

      const storedToken = localStorage.getItem('token');
      const storedEmail = localStorage.getItem('userEmail');
      const storedUserId = localStorage.getItem('userId');

      if (storedToken && storedEmail && storedUserId) {
        console.log('Restoring session for:', storedEmail);
        try {
          const creditsData = await getUserCredits(storedUserId);
          const restoredUser: User = {
            id: storedUserId,
            email: storedEmail,
            name: localStorage.getItem('userName') || '',
            availableCredits: creditsData.availableCredits !== undefined 
                                ? creditsData.availableCredits 
                                : creditsData.available_credits || 0,
            totalCreditsPurchased: creditsData.totalCreditsPurchased !== undefined
                                     ? creditsData.totalCreditsPurchased
                                     : creditsData.total_credits_purchased || 0,
          };
          setUser(restoredUser);
          console.log('Session restored successfully', restoredUser);
        } catch (error) {
          console.error('Failed to restore session (token likely invalid or user fetch failed):', error);
          localStorage.removeItem('token');
          localStorage.removeItem('userEmail');
          localStorage.removeItem('userId');
          localStorage.removeItem('userName');
          setUser(null);
        } finally {
          loadGoogleScript();
        }
      } else {
         console.log('No stored session found.');
         loadGoogleScript();
      }
    };

    const loadGoogleScript = () => {
      // Log browser information for debugging
      logBrowserInfo();

      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      script.onload = () => {
        if (window.google) {
          try {
            const clientId = process.env.REACT_APP_GOOGLE_CLIENT_ID;
            if (!clientId) {
              throw new Error('Google Client ID not found in environment variables');
            }

            // Use optimal configuration based on browser type
            const tokenClientConfig = getOAuthConfig(clientId, handleCredentialResponse);

            const client = window.google.accounts.oauth2.initTokenClient(tokenClientConfig);
            
            setTokenClient(client);
            setLoading(false);
          } catch (error) {
            console.error('Error initializing Google Auth:', error);
            setLoading(false);
          }
        }
      };
      
      script.onerror = () => {
        console.error('Failed to load Google Auth script');
        setLoading(false);
      };
      
      document.head.appendChild(script);
    };

    tryRestoreSession();
  }, []);

  const handleCredentialResponse = async (response: any) => {
    try {
      console.log('Handling credential response');
      const token = response.access_token;
      
      // First, verify with our backend
      console.log('Sending token to backend for verification');
      const backendResponse = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/auth/google`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token })
      });

      if (!backendResponse.ok) {
        console.error('Backend auth failed:', await backendResponse.text());
        throw new Error('Backend authentication failed');
      }

      const backendUser = await backendResponse.json();
      console.log('Backend auth successful:', backendUser);

      // Extract JWT tokens from response headers
      const jwtAccessToken = backendResponse.headers.get('X-Access-Token');
      const jwtRefreshToken = backendResponse.headers.get('X-Refresh-Token');

      // Create user data from backend response
      const userData: User = {
        id: backendUser.id,
        name: backendUser.name,
        email: backendUser.email,
        availableCredits: backendUser.available_credits,
        totalCreditsPurchased: backendUser.total_credits_purchased
      };

      console.log('Created user data object:', userData);

      setUser(userData);
      console.log('User state set:', userData);

      // Store the JWT tokens primarily, keep Google token as backup
      if (jwtAccessToken) {
        localStorage.setItem('token', jwtAccessToken);
        localStorage.setItem('tokenType', 'jwt');
        console.log('Stored JWT access token');
      } else {
        localStorage.setItem('token', token);
        localStorage.setItem('tokenType', 'google');
        console.log('Stored Google token as fallback');
      }

      if (jwtRefreshToken) {
        localStorage.setItem('jwtRefreshToken', jwtRefreshToken);
        console.log('Stored JWT refresh token');
      }

      localStorage.setItem('userEmail', userData.email);
      localStorage.setItem('userId', userData.id);
      localStorage.setItem('userName', userData.name || '');
      localStorage.setItem('tokenTimestamp', Date.now().toString());
      console.log('Saved auth data to localStorage');
    } catch (error) {
      console.error('Error handling credential:', error);
      throw error;
    }
  };

  const signIn = async () => {
    if (tokenClient) {
      const browserInfo = getBrowserInfo();
      console.log('Initiating sign-in:', browserInfo);

      return new Promise<void>((resolve, reject) => {
        tokenClient.callback = async (response: any) => {
          if (response.error) {
            console.error('Sign in error:', response.error);
            
            // For embedded browsers, try alternative approaches
            if (browserInfo.isEmbedded && response.error === 'popup_closed_by_user') {
              console.log('Popup blocked in embedded browser, attempting redirect flow');
              try {
                await initiateRedirectAuth();
                resolve();
                return;
              } catch (redirectError) {
                console.error('Redirect auth also failed:', redirectError);
                reject(new Error('Authentication failed in embedded browser'));
                return;
              }
            }
            
            reject(new Error(response.error));
            return;
          }

          try {
            console.log('Auth Response:', {
              tokenType: response.token_type,
              scope: response.scope,
              tokenLength: response.access_token?.length,
              hasRefreshToken: !!response.refresh_token,
              browserInfo
            });

            const token = response.access_token;
            const refreshToken = response.refresh_token;
            
            // First, verify with our backend
            console.log('Sending token to backend for verification');
            const backendResponse = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/auth/google`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({ 
                token,
                refresh_token: refreshToken 
              })
            });

            if (!backendResponse.ok) {
              console.error('Backend auth failed:', await backendResponse.text());
              throw new Error('Backend authentication failed');
            }

            const backendUser = await backendResponse.json();
            console.log('Backend auth successful:', backendUser);

            // Extract JWT tokens from response headers
            const jwtAccessToken = backendResponse.headers.get('X-Access-Token');
            const jwtRefreshToken = backendResponse.headers.get('X-Refresh-Token');

            // Create user data from backend response
            const userData: User = {
              id: backendUser.id,
              name: backendUser.name,
              email: backendUser.email,
              availableCredits: backendUser.available_credits,
              totalCreditsPurchased: backendUser.total_credits_purchased
            };

            console.log('Created user data object:', userData);

            setUser(userData);
            console.log('User state set:', userData);

            // Store the JWT tokens primarily, keep Google token as backup
            if (jwtAccessToken) {
              localStorage.setItem('token', jwtAccessToken);
              localStorage.setItem('tokenType', 'jwt');
              console.log('Stored JWT access token');
            } else {
              localStorage.setItem('token', token);
              localStorage.setItem('tokenType', 'google');
              console.log('Stored Google token as fallback');
            }

            if (jwtRefreshToken) {
              localStorage.setItem('jwtRefreshToken', jwtRefreshToken);
              console.log('Stored JWT refresh token');
            }

            localStorage.setItem('userEmail', userData.email);
            localStorage.setItem('userId', userData.id);
            localStorage.setItem('userName', userData.name || '');
            localStorage.setItem('tokenTimestamp', Date.now().toString());
            console.log('Saved auth data to localStorage');
            
            resolve();
          } catch (error) {
            console.error('Error during sign in:', error);
            throw error;
          }
        };

        // Use optimal request options based on browser type
        const requestOptions = getTokenRequestOptions(browserInfo);
        console.log('Using auth flow:', browserInfo.requiresRedirectAuth ? 'redirect' : 'popup');
        tokenClient.requestAccessToken(requestOptions);
      });
    }
    return Promise.resolve();
  };

  const signOut = async (): Promise<void> => {
    if (window.google) {
      return new Promise((resolve) => {
        window.google.accounts.oauth2.revoke(user?.email || '', () => {
          setUser(null);
          // Remove all user data from localStorage
          localStorage.removeItem('token');
          localStorage.removeItem('tokenType');
          localStorage.removeItem('refreshToken');
          localStorage.removeItem('jwtRefreshToken');
          localStorage.removeItem('tokenTimestamp');
          localStorage.removeItem('userEmail');
          localStorage.removeItem('userId');
          localStorage.removeItem('userName');
          resolve();
        });
      });
    } else {
      setUser(null);
      // Remove all user data from localStorage
      localStorage.removeItem('token');
      localStorage.removeItem('tokenType');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('jwtRefreshToken');
      localStorage.removeItem('tokenTimestamp');
      localStorage.removeItem('userEmail');
      localStorage.removeItem('userId');
      localStorage.removeItem('userName');
      return Promise.resolve();
    }
  };

  // Add token refresh function
  const refreshToken = async (): Promise<string | null> => {
    const jwtRefreshToken = localStorage.getItem('jwtRefreshToken');
    const tokenType = localStorage.getItem('tokenType');
    
    // Try JWT refresh first if we have a JWT refresh token
    if (jwtRefreshToken && tokenType === 'jwt') {
      try {
        console.log('Using JWT refresh token to get new access token');
        const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/auth/refresh`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            refresh_token: jwtRefreshToken
          })
        });

        if (response.ok) {
          const tokenData = await response.json();
          const newToken = tokenData.access_token;
          
          console.log('JWT token refreshed successfully');
          localStorage.setItem('token', newToken);
          localStorage.setItem('tokenTimestamp', Date.now().toString());
          
          return newToken;
        } else {
          console.error('JWT refresh token request failed:', response.status);
          // Fall through to try Google token refresh
        }
      } catch (error) {
        console.error('Error using JWT refresh token:', error);
        // Fall through to try Google token refresh
      }
    }

    const storedRefreshToken = localStorage.getItem('refreshToken');
    
    if (storedRefreshToken) {
      // Use Google refresh token to get new access token
      try {
        console.log('Using Google refresh token to get new access token');
        const response = await fetch('https://oauth2.googleapis.com/token', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: new URLSearchParams({
            client_id: process.env.REACT_APP_GOOGLE_CLIENT_ID || '',
            refresh_token: storedRefreshToken,
            grant_type: 'refresh_token'
          })
        });

        if (response.ok) {
          const tokenData = await response.json();
          const newToken = tokenData.access_token;
          
          console.log('Google token refreshed successfully');
          localStorage.setItem('token', newToken);
          localStorage.setItem('tokenType', 'google');
          localStorage.setItem('tokenTimestamp', Date.now().toString());
          
          return newToken;
        } else {
          console.error('Google refresh token request failed:', response.status);
        }
      } catch (error) {
        console.error('Error using Google refresh token:', error);
      }
    }

    // Fallback to requesting new token via Google OAuth flow
    if (!tokenClient) {
      console.log('No token client available for refresh');
      return null;
    }

    return new Promise((resolve) => {
      tokenClient.callback = async (response: any) => {
        if (response.error) {
          console.error('Token refresh error:', response.error);
          resolve(null);
          return;
        }

        try {
          const newToken = response.access_token;
          const newRefreshToken = response.refresh_token;
          
          console.log('Token refreshed successfully via OAuth flow');
          
          // Update stored tokens
          localStorage.setItem('token', newToken);
          localStorage.setItem('tokenType', 'google');
          localStorage.setItem('tokenTimestamp', Date.now().toString());
          if (newRefreshToken) {
            localStorage.setItem('refreshToken', newRefreshToken);
          }
          
          resolve(newToken);
        } catch (error) {
          console.error('Error handling refreshed token:', error);
          resolve(null);
        }
      };

      tokenClient.requestAccessToken({
        prompt: '', // Don't show consent screen for refresh
        hint: user?.email || localStorage.getItem('userEmail') || ''
      });
    });
  };

  // Check if token is expired and refresh if needed
  const ensureValidToken = async (): Promise<string | null> => {
    const currentToken = localStorage.getItem('token');
    const tokenTimestamp = localStorage.getItem('tokenTimestamp');
    const tokenType = localStorage.getItem('tokenType');
    
    if (!currentToken) {
      console.log('No token found');
      return null;
    }

    // JWT tokens last 7 days, Google tokens last 1 hour
    const TOKEN_LIFETIME = tokenType === 'jwt' 
      ? 6 * 24 * 60 * 60 * 1000  // 6 days (refresh 1 day early)
      : 50 * 60 * 1000;          // 50 minutes for Google tokens

    const now = Date.now();
    const tokenAge = tokenTimestamp ? now - parseInt(tokenTimestamp) : TOKEN_LIFETIME + 1;

    if (tokenAge > TOKEN_LIFETIME) {
      console.log(`${tokenType?.toUpperCase()} token is likely expired based on age, attempting refresh...`);
      const newToken = await refreshToken();
      
      if (!newToken) {
        console.log('Token refresh failed, signing out user');
        await signOut();
        return null;
      }
      
      return newToken;
    }

    try {
      // Test current token with a simple API call
      const testResponse = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/credits/${user?.id}`, {
        headers: {
          'Authorization': `Bearer ${currentToken}`
        }
      });

      if (testResponse.status === 401) {
        console.log('Token expired, attempting refresh...');
        const newToken = await refreshToken();
        
        if (!newToken) {
          console.log('Token refresh failed, signing out user');
          await signOut();
          return null;
        }
        
        return newToken;
      }

      if (testResponse.ok) {
        console.log('Current token is still valid');
        return currentToken;
      }

      console.log('Token validation failed with status:', testResponse.status);
      return currentToken; // Return current token for other errors
    } catch (error) {
      console.error('Error validating token:', error);
      return currentToken; // Return current token if validation fails
    }
  };

  // Function to refresh user credits
  const refreshUserCredits = async (): Promise<void> => {
    if (!user) return;
    
    try {
      console.log(`Refreshing credits for user: ${user.email}`);
      
      // Ensure we have a valid token before making the request
      const validToken = await ensureValidToken();
      if (!validToken) {
        console.log('No valid token available for credits refresh');
        return;
      }
      
      const creditsData = await getUserCredits(user.id);
      
      // Update user object with fresh credit data
      setUser(prevUser => {
        if (!prevUser) return null;
        
        return {
          ...prevUser,
          availableCredits: creditsData.availableCredits !== undefined 
                            ? creditsData.availableCredits 
                            : creditsData.available_credits || 0,
          totalCreditsPurchased: creditsData.totalCreditsPurchased !== undefined
                                ? creditsData.totalCreditsPurchased
                                : creditsData.total_credits_purchased || 0,
        };
      });
      
      console.log('User credits refreshed successfully');
    } catch (error) {
      console.error('Failed to refresh user credits:', error);
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, signIn, signOut, refreshUserCredits, ensureValidToken }}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}; 