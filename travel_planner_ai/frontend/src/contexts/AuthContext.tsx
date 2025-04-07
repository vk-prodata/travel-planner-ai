import React, { createContext, useContext, useEffect, useState } from 'react';
import { User } from '../types';
import { getUserCredits } from '../services/creditsService';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signIn: () => Promise<void>;
  signOut: () => Promise<void>;
}

// Create context with default values
const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  signIn: async () => {},
  signOut: async () => {}
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

    loadGoogleScript();
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

      // Store the token
      localStorage.setItem('token', token);
      localStorage.setItem('userEmail', userData.email);
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

            // Store the token
            localStorage.setItem('token', token);
            localStorage.setItem('userEmail', userData.email);
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
          // Remove user data from localStorage
          localStorage.removeItem('token');
          localStorage.removeItem('userEmail');
          resolve();
        });
      });
    } else {
      setUser(null);
      // Remove user data from localStorage
      localStorage.removeItem('token');
      localStorage.removeItem('userEmail');
      return Promise.resolve();
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, signIn, signOut }}>
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