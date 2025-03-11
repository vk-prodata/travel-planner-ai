import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import TripList from './TripList';
import { useAuth } from '../contexts/AuthContext';
import * as tripService from '../services/tripService';

// Mock the tripService and the Auth context
jest.mock('../services/tripService');
jest.mock('../contexts/AuthContext');

// Mock data for testing
const mockTrips = [
  {
    id: 'trip1',
    user_id: 'user1',
    formData: {
      destination: 'Paris',
      origin: 'New York',
      startDate: '2024-07-15',
      endDate: '2024-07-22',
      travelType: 'flight',
      adults: 2,
      children: 1,
      infants: 0,
      budget: 'Medium'
    },
    itinerary: {
      days: []
    }
  },
  {
    id: 'trip2',
    user_id: 'user1',
    formData: {
      destination: 'Tokyo',
      origin: 'Los Angeles',
      startDate: '2024-08-10',
      endDate: '2024-08-20',
      travelType: 'flight',
      adults: 1,
      children: 0,
      infants: 0,
      budget: 'Luxury'
    },
    itinerary: {
      days: []
    }
  }
];

describe('TripList Component', () => {
  beforeEach(() => {
    // Reset all mocks before each test
    jest.clearAllMocks();
    
    // Setup default mocks
    (useAuth as jest.Mock).mockReturnValue({
      user: { id: 'user1', name: 'Test User', email: 'test@example.com' },
      signOut: jest.fn()
    });
    
    (tripService.getUserTrips as jest.Mock).mockResolvedValue(mockTrips);
    
    // Mock fetch for the delete functionality
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: jest.fn().mockResolvedValue({ success: true })
    });
  });

  test('should render loading state initially', () => {
    render(
      <BrowserRouter>
        <TripList />
      </BrowserRouter>
    );
    
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  test('should display trips after loading', async () => {
    render(
      <BrowserRouter>
        <TripList />
      </BrowserRouter>
    );
    
    // Wait for loading to finish
    await waitFor(() => {
      expect(screen.queryByRole('status')).not.toBeInTheDocument();
    });
    
    // Check if trips are displayed
    expect(screen.getByText('Paris')).toBeInTheDocument();
    expect(screen.getByText('Tokyo')).toBeInTheDocument();
  });

  test('should show sign in message when user is not authenticated', () => {
    (useAuth as jest.Mock).mockReturnValue({
      user: null,
      signOut: jest.fn()
    });
    
    render(
      <BrowserRouter>
        <TripList />
      </BrowserRouter>
    );
    
    expect(screen.getByText('Please sign in to see your trips.')).toBeInTheDocument();
  });

  test('should navigate to trip details when View Trip is clicked', async () => {
    const mockNavigate = jest.fn();
    jest.mock('react-router-dom', () => ({
      ...jest.requireActual('react-router-dom'),
      useNavigate: () => mockNavigate
    }));
    
    render(
      <BrowserRouter>
        <TripList />
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.queryByRole('status')).not.toBeInTheDocument();
    });
    
    // Find and click the View Trip button for Paris
    const viewButtons = screen.getAllByText('View Trip');
    fireEvent.click(viewButtons[0]);
    
    // Verify navigation was called
    expect(mockNavigate).toHaveBeenCalledWith('/?tripId=trip1');
  });

  test('should show empty state when no trips are available', async () => {
    (tripService.getUserTrips as jest.Mock).mockResolvedValue([]);
    
    render(
      <BrowserRouter>
        <TripList />
      </BrowserRouter>
    );
    
    await waitFor(() => {
      expect(screen.queryByRole('status')).not.toBeInTheDocument();
    });
    
    expect(screen.getByText('You don\'t have any trips yet.')).toBeInTheDocument();
    expect(screen.getByText('Plan Your First Trip')).toBeInTheDocument();
  });
}); 