import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import AuthForm from '../components/AuthForm';
import AuthCallback from '../components/AuthCallback';
import { AuthProvider } from '../contexts/AuthContext';
import * as browserDetection from '../utils/browserDetection';
import * as authHelpers from '../utils/authHelpers';

// Mock useAuth hook
const mockSignIn = jest.fn();
jest.mock('../contexts/AuthContext', () => ({
  ...jest.requireActual('../contexts/AuthContext'),
  useAuth: () => ({
    signIn: mockSignIn,
    user: null,
    loading: false,
    signOut: jest.fn(),
    refreshUserCredits: jest.fn(),
    ensureValidToken: jest.fn()
  })
}));

// Mock navigator.userAgent for testing different browsers
const mockUserAgent = (userAgent: string) => {
  Object.defineProperty(navigator, 'userAgent', {
    writable: true,
    value: userAgent
  });
};

// Mock fetch for API calls
global.fetch = jest.fn();

// Mock window.open
global.open = jest.fn();

// Mock URLSearchParams
Object.defineProperty(window, 'URLSearchParams', {
  writable: true,
  value: jest.fn().mockImplementation((query) => ({
    get: jest.fn((key) => {
      if (query === '?code=test_code&state=test_state') {
        return key === 'code' ? 'test_code' : key === 'state' ? 'test_state' : null;
      }
      return null;
    })
  }))
});

describe('Telegram Authentication', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset to standard browser by default
    mockUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');
  });

  describe('Browser Detection', () => {
    test('detects Telegram browser correctly', () => {
      mockUserAgent('Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/86.0.4240.110 Mobile Safari/537.36 Telegram-Android/7.9.3');
      
      render(
        <BrowserRouter>
          <AuthForm />
        </BrowserRouter>
      );

      expect(screen.getByText(/Sign in \(Telegram\)/)).toBeInTheDocument();
      expect(screen.getByText(/📱 Using embedded browser - enhanced compatibility enabled/)).toBeInTheDocument();
    });

    test('detects regular browser correctly', () => {
      render(
        <BrowserRouter>
          <AuthForm />
        </BrowserRouter>
      );

      expect(screen.getByText('Sign in')).toBeInTheDocument();
      expect(screen.queryByText(/Telegram/)).not.toBeInTheDocument();
    });

    test('detects other embedded browsers', () => {
      mockUserAgent('Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 WhatsApp/21.8.4');
      
      render(
        <BrowserRouter>
          <AuthForm />
        </BrowserRouter>
      );

      expect(screen.getByText(/📱 Using embedded browser - enhanced compatibility enabled/)).toBeInTheDocument();
    });
  });

  describe('AuthForm Telegram Features', () => {
    beforeEach(() => {
      mockUserAgent('Mozilla/5.0 (Linux; Android 10) Telegram-Android/7.9.3');
    });

    test('shows Telegram-specific tip when sign-in is initiated', async () => {
      render(
        <BrowserRouter>
          <AuthForm />
        </BrowserRouter>
      );

      const signInButton = screen.getByRole('button', { name: /Sign in \(Telegram\)/ });
      fireEvent.click(signInButton);

      await waitFor(() => {
        expect(screen.getByText(/Telegram User:/)).toBeInTheDocument();
        expect(screen.getByText(/If sign-in doesn't work, you may need to copy this link to your regular browser/)).toBeInTheDocument();
      });
    });

    test('provides fallback option for embedded browser errors', async () => {
      mockSignIn.mockRejectedValue(new Error('popup_closed_by_user'));

      render(
        <BrowserRouter>
          <AuthForm />
        </BrowserRouter>
      );

      const signInButton = screen.getByRole('button');
      fireEvent.click(signInButton);

      await waitFor(() => {
        expect(screen.getByText(/Sign-in from embedded browsers may require additional steps/)).toBeInTheDocument();
        expect(screen.getByText('Open in browser instead')).toBeInTheDocument();
      });

      // Test the "Open in browser instead" functionality
      const openBrowserButton = screen.getByText('Open in browser instead');
      fireEvent.click(openBrowserButton);

      expect(window.open).toHaveBeenCalledWith(
        window.location.href,
        '_blank',
        'noopener,noreferrer'
      );
    });
  });

  describe('OAuth Callback Processing', () => {
    test('processes OAuth callback successfully', async () => {
      const mockFetch = fetch as jest.MockedFunction<typeof fetch>;
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: 'user123',
          email: 'test@example.com',
          name: 'Test User',
          available_credits: 10,
          total_credits_purchased: 0
        }),
        headers: {
          get: (key: string) => {
            if (key === 'X-Access-Token') return 'jwt_access_token';
            if (key === 'X-Refresh-Token') return 'jwt_refresh_token';
            return null;
          }
        }
      } as Response);

      // Mock location search params
      delete (window as any).location;
      (window as any).location = {
        search: '?code=test_code&state=test_state',
        origin: 'http://localhost:3000'
      };

      render(
        <BrowserRouter>
          <AuthProvider>
            <div>Test</div>
          </AuthProvider>
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          'http://localhost:8000/auth/google/callback',
          expect.objectContaining({
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              code: 'test_code',
              redirect_uri: 'http://localhost:3000/auth/callback',
              state: null
            })
          })
        );
      });
    });

    test('handles OAuth callback errors gracefully', async () => {
      const mockFetch = fetch as jest.MockedFunction<typeof fetch>;
      mockFetch.mockResolvedValueOnce({
        ok: false,
        text: async () => 'Authentication failed'
      } as Response);

      // Mock location with error
      delete (window as any).location;
      (window as any).location = {
        search: '?error=access_denied',
        origin: 'http://localhost:3000'
      };

      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      render(
        <BrowserRouter>
          <AuthProvider>
            <div>Test</div>
          </AuthProvider>
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('OAuth error:', 'access_denied');
      });

      consoleSpy.mockRestore();
    });
  });

  describe('AuthCallback Component', () => {
    test('shows processing state initially', () => {
      render(
        <BrowserRouter>
          <AuthCallback />
        </BrowserRouter>
      );

      expect(screen.getByText('Completing Sign In...')).toBeInTheDocument();
      expect(screen.getByText('Please wait while we complete your authentication.')).toBeInTheDocument();
    });

    test('handles successful authentication', async () => {
      const mockFetch = fetch as jest.MockedFunction<typeof fetch>;
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: 'user123',
          email: 'test@example.com',
          name: 'Test User',
          available_credits: 10,
          total_credits_purchased: 0
        }),
        headers: {
          get: (key: string) => {
            if (key === 'X-Access-Token') return 'jwt_access_token';
            if (key === 'X-Refresh-Token') return 'jwt_refresh_token';
            return null;
          }
        }
      } as Response);

      // Mock URLSearchParams for success case
      (window as any).URLSearchParams = jest.fn().mockImplementation(() => ({
        get: (key: string) => key === 'code' ? 'test_code' : null
      }));

      render(
        <BrowserRouter>
          <AuthCallback />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('✅ Sign In Successful!')).toBeInTheDocument();
      });
    });

    test('handles authentication failure', async () => {
      // Mock URLSearchParams for error case
      (window as any).URLSearchParams = jest.fn().mockImplementation(() => ({
        get: (key: string) => key === 'error' ? 'access_denied' : null
      }));

      render(
        <BrowserRouter>
          <AuthCallback />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('❌ Sign In Failed')).toBeInTheDocument();
        expect(screen.getByText('Authentication failed: access_denied')).toBeInTheDocument();
      });
    });
  });

  describe('Integration Tests', () => {
    test('complete Telegram authentication flow', async () => {
      // Set up Telegram browser
      mockUserAgent('Mozilla/5.0 (Linux; Android 10) Telegram-Android/7.9.3');
      
      const mockFetch = fetch as jest.MockedFunction<typeof fetch>;
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: 'user123',
          email: 'telegram@example.com',
          name: 'Telegram User',
          available_credits: 1,
          total_credits_purchased: 0
        }),
        headers: {
          get: (key: string) => {
            if (key === 'X-Access-Token') return 'telegram_jwt_token';
            if (key === 'X-Refresh-Token') return 'telegram_refresh_token';
            return null;
          }
        }
      } as Response);

      render(
        <BrowserRouter>
          <AuthForm />
        </BrowserRouter>
      );

      // Verify Telegram-specific UI
      expect(screen.getByText('Sign in (Telegram)')).toBeInTheDocument();
      expect(screen.getByText(/📱 Using embedded browser/)).toBeInTheDocument();

      // Simulate sign-in
      const signInButton = screen.getByRole('button', { name: /Sign in \(Telegram\)/ });
      fireEvent.click(signInButton);

      // Should show Telegram tip
      await waitFor(() => {
        expect(screen.getByText(/Telegram User:/)).toBeInTheDocument();
      });
    });
  });
}); 