import React, { createContext, useContext, useEffect, useState } from 'react';
import { User } from '../types';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signIn: () => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

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
      // Use the access token to get user info
      const userInfo = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
        headers: {
          'Authorization': `Bearer ${response.access_token}`
        }
      }).then(res => res.json());

      setUser({
        id: userInfo.sub,  // Use the Google user ID
        name: userInfo.name,
        email: userInfo.email
      });

      // Store the token
      localStorage.setItem('token', response.credential);
    } catch (error) {
      console.error('Error handling credential:', error);
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
            localStorage.setItem('token', token);
            
            const userInfo = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
              headers: {
                'Authorization': `Bearer ${token}`
              }
            }).then(res => res.json());

            console.log('User Info:', {
              id: userInfo.sub,
              email: userInfo.email,
              name: userInfo.name
            });

            setUser({
              id: userInfo.sub,
              name: userInfo.name,
              email: userInfo.email
            });
            
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
          resolve();
        });
      });
    } else {
      setUser(null);
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
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}; 