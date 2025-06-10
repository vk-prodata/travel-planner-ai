import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ExternalBrowserDemo from '../components/ExternalBrowserDemo';
import {
  detectBrowserCapabilities,
  openInExternalBrowser,
  shareWithExternalBrowser
} from '../utils/externalBrowser';

// Mock the external browser utilities
jest.mock('../utils/externalBrowser', () => ({
  detectBrowserCapabilities: jest.fn(),
  openInExternalBrowser: jest.fn(),
  shareWithExternalBrowser: jest.fn(),
}));

const mockDetectBrowserCapabilities = detectBrowserCapabilities as jest.MockedFunction<typeof detectBrowserCapabilities>;
const mockOpenInExternalBrowser = openInExternalBrowser as jest.MockedFunction<typeof openInExternalBrowser>;
const mockShareWithExternalBrowser = shareWithExternalBrowser as jest.MockedFunction<typeof shareWithExternalBrowser>;

describe('ExternalBrowser Professional Implementation', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock default browser capabilities
    mockDetectBrowserCapabilities.mockReturnValue({
      supportsWindowOpen: true,
      supportsClipboard: true,
      supportsDeepLinks: true,
      isEmbedded: false,
      platform: 'browser'
    });
  });

  describe('Browser Detection', () => {
    test('detects standard browser correctly', () => {
      mockDetectBrowserCapabilities.mockReturnValue({
        supportsWindowOpen: true,
        supportsClipboard: true,
        supportsDeepLinks: true,
        isEmbedded: false,
        platform: 'browser'
      });

      render(<ExternalBrowserDemo />);

      expect(screen.getByText('Standard Browser')).toBeInTheDocument();
      expect(screen.getByText('Platform: browser')).toBeInTheDocument();
      expect(screen.getByText(/Window\.open: Supported/)).toBeInTheDocument();
      expect(screen.getByText(/Clipboard: Available/)).toBeInTheDocument();
    });

    test('detects Telegram embedded browser correctly', () => {
      mockDetectBrowserCapabilities.mockReturnValue({
        supportsWindowOpen: false,
        supportsClipboard: true,
        supportsDeepLinks: true,
        isEmbedded: true,
        platform: 'telegram'
      });

      render(<ExternalBrowserDemo />);

      expect(screen.getByText('Embedded Browser')).toBeInTheDocument();
      expect(screen.getByText('Platform: telegram')).toBeInTheDocument();
      expect(screen.getByText(/Window\.open: Blocked/)).toBeInTheDocument();
    });

    test('detects limited capabilities correctly', () => {
      mockDetectBrowserCapabilities.mockReturnValue({
        supportsWindowOpen: false,
        supportsClipboard: false,
        supportsDeepLinks: false,
        isEmbedded: true,
        platform: 'whatsapp'
      });

      render(<ExternalBrowserDemo />);

      expect(screen.getByText(/Window\.open: Blocked/)).toBeInTheDocument();
      expect(screen.getByText(/Clipboard: Limited/)).toBeInTheDocument();
    });
  });

  describe('External Browser Opening', () => {
    test('handles successful external browser opening', async () => {
      mockOpenInExternalBrowser.mockResolvedValue(true);

      render(<ExternalBrowserDemo />);

      const testButton = screen.getByText('Test External Browser');
      fireEvent.click(testButton);

      await waitFor(() => {
        expect(mockOpenInExternalBrowser).toHaveBeenCalledWith({
          url: window.location.href,
          fallbackMessage: 'Professional external browser opening test',
          trackingParams: {
            test: 'external_browser_demo',
            timestamp: expect.any(String)
          }
        });
      });

      await waitFor(() => {
        expect(screen.getByText(/External browser test: SUCCESS/)).toBeInTheDocument();
      });
    });

    test('handles external browser opening fallback', async () => {
      mockOpenInExternalBrowser.mockResolvedValue(false);

      render(<ExternalBrowserDemo />);

      const testButton = screen.getByText('Test External Browser');
      fireEvent.click(testButton);

      await waitFor(() => {
        expect(screen.getByText(/External browser test: FALLBACK/)).toBeInTheDocument();
      });
    });
  });

  describe('Social Media Sharing', () => {
    test('handles successful Telegram sharing', async () => {
      mockShareWithExternalBrowser.mockResolvedValue(true);

      render(<ExternalBrowserDemo />);

      const telegramButton = screen.getByText('Test Telegram');
      fireEvent.click(telegramButton);

      await waitFor(() => {
        expect(mockShareWithExternalBrowser).toHaveBeenCalledWith('telegram', {
          url: window.location.href,
          title: 'Travel Planner AI - External Browser Test',
          description: 'Testing professional external browser functionality'
        });
      });

      await waitFor(() => {
        expect(screen.getByText(/telegram share: SUCCESS/)).toBeInTheDocument();
      });
    });

    test('handles successful WhatsApp sharing', async () => {
      mockShareWithExternalBrowser.mockResolvedValue(true);

      render(<ExternalBrowserDemo />);

      const whatsappButton = screen.getByText('Test WhatsApp');
      fireEvent.click(whatsappButton);

      await waitFor(() => {
        expect(mockShareWithExternalBrowser).toHaveBeenCalledWith('whatsapp', {
          url: window.location.href,
          title: 'Travel Planner AI - External Browser Test',
          description: 'Testing professional external browser functionality'
        });
      });

      await waitFor(() => {
        expect(screen.getByText(/whatsapp share: SUCCESS/)).toBeInTheDocument();
      });
    });

    test('handles sharing fallback scenarios', async () => {
      mockShareWithExternalBrowser.mockResolvedValue(false);

      render(<ExternalBrowserDemo />);

      const facebookButton = screen.getByText('Test Facebook');
      fireEvent.click(facebookButton);

      await waitFor(() => {
        expect(screen.getByText(/facebook share: FALLBACK/)).toBeInTheDocument();
      });
    });
  });

  describe('Implementation Features Display', () => {
    test('displays implementation features correctly', () => {
      render(<ExternalBrowserDemo />);

      expect(screen.getByText('Implementation Features:')).toBeInTheDocument();
      expect(screen.getByText(/Multi-method fallback system/)).toBeInTheDocument();
      expect(screen.getByText(/Platform-specific optimizations/)).toBeInTheDocument();
      expect(screen.getByText(/Enhanced meta tags/)).toBeInTheDocument();
      expect(screen.getByText(/Automatic tracking parameters/)).toBeInTheDocument();
      expect(screen.getByText(/Graceful degradation/)).toBeInTheDocument();
    });

    test('displays info alert correctly', () => {
      render(<ExternalBrowserDemo />);

      expect(screen.getByText(/This demo showcases the professional external browser functionality/)).toBeInTheDocument();
    });
  });

  describe('Test Results Management', () => {
    test('accumulates and displays test results', async () => {
      mockOpenInExternalBrowser.mockResolvedValue(true);
      mockShareWithExternalBrowser.mockResolvedValue(true);

      render(<ExternalBrowserDemo />);

      // Perform multiple tests
      fireEvent.click(screen.getByText('Test External Browser'));
      await waitFor(() => {
        expect(screen.getByText(/External browser test: SUCCESS/)).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Test Telegram'));
      await waitFor(() => {
        expect(screen.getByText(/telegram share: SUCCESS/)).toBeInTheDocument();
      });

      // Should show both results
      expect(screen.getByText('Recent Test Results:')).toBeInTheDocument();
    });

    test('limits test results to prevent overflow', async () => {
      mockOpenInExternalBrowser.mockResolvedValue(true);

      render(<ExternalBrowserDemo />);

      // Perform many tests (more than the limit of 5)
      for (let i = 0; i < 7; i++) {
        fireEvent.click(screen.getByText('Test External Browser'));
        await waitFor(() => {
          expect(screen.getByText(/External browser test: SUCCESS/)).toBeInTheDocument();
        });
      }

      // Should only show recent results (not all 7)
      const resultElements = screen.getAllByText(/External browser test: SUCCESS/);
      expect(resultElements.length).toBeLessThanOrEqual(5);
    });
  });
});

describe('ExternalBrowser Utilities Unit Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset DOM
    document.body.innerHTML = '';
    
    // Mock window.open
    global.open = jest.fn();
    
    // Mock navigator.clipboard
    Object.assign(navigator, {
      clipboard: {
        writeText: jest.fn(() => Promise.resolve()),
      },
    });
  });

  describe('detectBrowserCapabilities', () => {
    test('detects browser capabilities correctly', () => {
      // Test with original implementation
      jest.unmock('../utils/externalBrowser');
      const { detectBrowserCapabilities } = require('../utils/externalBrowser');
      
      const capabilities = detectBrowserCapabilities();
      
      expect(capabilities).toHaveProperty('supportsWindowOpen');
      expect(capabilities).toHaveProperty('supportsClipboard');
      expect(capabilities).toHaveProperty('supportsDeepLinks');
      expect(capabilities).toHaveProperty('isEmbedded');
      expect(capabilities).toHaveProperty('platform');
      
      expect(typeof capabilities.supportsWindowOpen).toBe('boolean');
      expect(typeof capabilities.supportsClipboard).toBe('boolean');
      expect(typeof capabilities.supportsDeepLinks).toBe('boolean');
      expect(typeof capabilities.isEmbedded).toBe('boolean');
      expect(typeof capabilities.platform).toBe('string');
    });
  });

  describe('Error Handling', () => {
    test('handles errors gracefully in openInExternalBrowser', async () => {
      jest.unmock('../utils/externalBrowser');
      const { openInExternalBrowser } = require('../utils/externalBrowser');
      
      // Mock window.open to throw error
      global.open = jest.fn(() => {
        throw new Error('Blocked by browser');
      });
      
      const result = await openInExternalBrowser({
        url: 'https://example.com',
        fallbackMessage: 'Test fallback'
      });
      
      // Should not throw error, should return boolean
      expect(typeof result).toBe('boolean');
    });

    test('handles clipboard errors gracefully', async () => {
      jest.unmock('../utils/externalBrowser');
      const { openInExternalBrowser } = require('../utils/externalBrowser');
      
      // Mock all methods to fail
      global.open = jest.fn(() => null);
      global.alert = jest.fn();
      
      // Mock clipboard to fail
      Object.assign(navigator, {
        clipboard: {
          writeText: jest.fn(() => Promise.reject(new Error('Clipboard blocked'))),
        },
      });
      
      const result = await openInExternalBrowser({
        url: 'https://example.com'
      });
      
      // Should still return a boolean and not throw
      expect(typeof result).toBe('boolean');
      expect(global.alert).toHaveBeenCalled();
    });
  });
}); 