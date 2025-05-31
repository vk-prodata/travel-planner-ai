import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import TripLoadingHints from '../TripLoadingHints';

// Mock the icons to avoid issues in tests
jest.mock('react-icons/fa', () => ({
  FaLightbulb: () => <span data-testid="icon-lightbulb">💡</span>,
  FaSync: () => <span data-testid="icon-sync">🔄</span>,
  FaCog: () => <span data-testid="icon-cog">⚙️</span>,
  FaClock: () => <span data-testid="icon-clock">🕐</span>,
  FaMapMarkerAlt: () => <span data-testid="icon-map">📍</span>,
  FaUtensils: () => <span data-testid="icon-utensils">🍽️</span>,
  FaTheaterMasks: () => <span data-testid="icon-theater">🎭</span>,
  FaWallet: () => <span data-testid="icon-wallet">💰</span>,
  FaLanguage: () => <span data-testid="icon-language">🌍</span>,
  FaStar: () => <span data-testid="icon-star">⭐</span>,
}));

describe('TripLoadingHints', () => {
  beforeEach(() => {
    jest.clearAllTimers();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test('renders the first hint initially', () => {
    render(<TripLoadingHints />);
    
    expect(screen.getByText('Choose Entertainment Activities')).toBeInTheDocument();
    expect(screen.getByText(/Always select Entertainment preferences/)).toBeInTheDocument();
    expect(screen.getByText('Tip 1 of 10')).toBeInTheDocument();
  });

  test('shows progress indicator with correct number of dots', () => {
    render(<TripLoadingHints />);
    
    // Should have 10 dots for 10 hints
    const dots = screen.getByText('Tip 1 of 10').parentElement?.querySelectorAll('span[style*="width: 6px"]');
    expect(dots).toHaveLength(10);
  });

  test('displays entertainment activities hint with correct icon', () => {
    render(<TripLoadingHints />);
    
    expect(screen.getByTestId('icon-theater')).toBeInTheDocument();
    expect(screen.getByText('Choose Entertainment Activities')).toBeInTheDocument();
  });

  test('changes hint after interval', async () => {
    render(<TripLoadingHints />);
    
    // Initially shows first hint
    expect(screen.getByText('Choose Entertainment Activities')).toBeInTheDocument();
    
    // Fast-forward time to trigger hint change (20 seconds + 500ms transition)
    jest.advanceTimersByTime(20500);
    
    // Should now show second hint
    await waitFor(() => {
      expect(screen.getByText('Refresh Any Activity')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Tip 2 of 10')).toBeInTheDocument();
  });

  test('cycles through all hints correctly', async () => {
    render(<TripLoadingHints />);
    
    // Test cycling through first few hints
    const expectedHints = [
      'Choose Entertainment Activities',
      'Refresh Any Activity', 
      'Advanced Settings Available',
      'Processing Time'
    ];
    
    for (let i = 0; i < expectedHints.length; i++) {
      if (i > 0) {
        jest.advanceTimersByTime(20500);
        await waitFor(() => {
          expect(screen.getByText(expectedHints[i])).toBeInTheDocument();
        });
      } else {
        expect(screen.getByText(expectedHints[i])).toBeInTheDocument();
      }
      expect(screen.getByText(`Tip ${i + 1} of 10`)).toBeInTheDocument();
    }
  });

  test('applies custom className', () => {
    const { container } = render(<TripLoadingHints className="custom-class" />);
    
    expect(container.firstChild).toHaveClass('custom-class');
  });

  test('shows all required hint content', () => {
    render(<TripLoadingHints />);
    
    // Check that the first hint has all required elements
    expect(screen.getByText('Choose Entertainment Activities')).toBeInTheDocument();
    expect(screen.getByText(/Always select Entertainment preferences/)).toBeInTheDocument();
    expect(screen.getByTestId('icon-theater')).toBeInTheDocument();
    expect(screen.getByText('Tip 1 of 10')).toBeInTheDocument();
  });
}); 