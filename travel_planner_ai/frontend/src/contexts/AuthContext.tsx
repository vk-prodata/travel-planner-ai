import React, { createContext, useContext, useEffect, useState } from 'react';
import { User } from '../types';
import { getUserCredits } from '../services/creditsService';

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

            const client = window.google.accounts.oauth2.initTokenClient({
              client_id: clientId,
              scope: 'email profile openid',
              callback: handleCredentialResponse,
            });
            
            setTokenClient(client);
            setLoading(false);
          } catch (error) {
            console.error('Error initializing Google Auth:', error);
            setLoading(false);
          }
        }
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

      // Store the token, email, ID, and name
      localStorage.setItem('token', token);
      localStorage.setItem('userEmail', userData.email);
      localStorage.setItem('userId', userData.id);
      localStorage.setItem('userName', userData.name || '');
      console.log('Saved auth data to localStorage');
    } catch (error) {
      console.error('Error handling credential:', error);
      throw error;
    }
  };

  const signIn = async () => {
    if (tokenClient) {
      return new Promise<void>((resolve) => {
        tokenClient.callback = async (response: any) => {
          if (response.error) {
            console.error('Sign in error:', response.error);
            return;
          }

          try {
            console.log('Auth Response:', {
              tokenType: response.token_type,
              scope: response.scope,
              // Don't log the full token for security
              tokenLength: response.access_token?.length
            });

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

            // Store the token, email, ID, and name
            localStorage.setItem('token', token);
            localStorage.setItem('userEmail', userData.email);
            localStorage.setItem('userId', userData.id);
            localStorage.setItem('userName', userData.name || '');
            console.log('Saved auth data to localStorage');
            
            resolve();
          } catch (error) {
            console.error('Error during sign in:', error);
            throw error;
          }
        };

        tokenClient.requestAccessToken({
          prompt: 'consent'
        });
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
      localStorage.removeItem('userEmail');
      localStorage.removeItem('userId');
      localStorage.removeItem('userName');
      return Promise.resolve();
    }
  };

  // Add token refresh function
  const refreshToken = async (): Promise<string | null> => {
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
          console.log('Token refreshed successfully');
          
          // Update stored token
          localStorage.setItem('token', newToken);
          
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
    if (!currentToken) {
      console.log('No token found');
      return null;
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