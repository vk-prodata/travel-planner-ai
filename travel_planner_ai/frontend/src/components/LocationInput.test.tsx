import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import LocationInput from './LocationInput';

// Mock geolocation
const mockGeolocation = {
  getCurrentPosition: jest.fn(),
  watchPosition: jest.fn(),
  clearWatch: jest.fn()
};

// Mock fetch for autocomplete
global.fetch = jest.fn();

describe('LocationInput Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    Object.defineProperty(global.navigator, 'geolocation', {
      value: mockGeolocation,
      writable: true
    });
  });

  test('renders input field with label', () => {
    render(
      <LocationInput
        label="From"
        value=""
        onChange={jest.fn()}
        placeholder="Enter origin"
      />
    );

    expect(screen.getByLabelText(/from/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/enter origin/i)).toBeInTheDocument();
  });

  test('shows use current location button for origin field', () => {
    render(
      <LocationInput
        label="From"
        value=""
        onChange={jest.fn()}
        placeholder="Enter origin"
        showGeolocation={true}
      />
    );

    expect(screen.getByTitle(/use current location/i)).toBeInTheDocument();
  });

  test('does not show geolocation button when showGeolocation is false', () => {
    render(
      <LocationInput
        label="To"
        value=""
        onChange={jest.fn()}
        placeholder="Enter destination"
        showGeolocation={false}
      />
    );

    expect(screen.queryByTitle(/use current location/i)).not.toBeInTheDocument();
  });

  test('handles geolocation success', async () => {
    const mockOnChange = jest.fn();
    const mockPosition = {
      coords: {
        latitude: 40.7128,
        longitude: -74.0060
      }
    };

    // Mock reverse geocoding response
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        display_name: "New York, NY, USA"
      })
    });

    mockGeolocation.getCurrentPosition.mockImplementationOnce((success) => {
      success(mockPosition);
    });

    render(
      <LocationInput
        label="From"
        value=""
        onChange={mockOnChange}
        placeholder="Enter origin"
        showGeolocation={true}
      />
    );

    const geoButton = screen.getByTitle(/use current location/i);
    fireEvent.click(geoButton);

    await waitFor(() => {
      expect(mockOnChange).toHaveBeenCalledWith("New York, NY, USA");
    });
  });

  test('shows autocomplete suggestions when typing', async () => {
    const mockOnChange = jest.fn();

    // Mock autocomplete API response
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ([
        {
          place_id: 1,
          display_name: "Paris, France",
          type: "city"
        },
        {
          place_id: 2,
          display_name: "Paris, Texas, USA",
          type: "city"
        }
      ])
    });

    render(
      <LocationInput
        label="To"
        value=""
        onChange={mockOnChange}
        placeholder="Enter destination"
        showAutocomplete={true}
      />
    );

    const input = screen.getByPlaceholderText(/enter destination/i);
    fireEvent.change(input, { target: { value: 'Paris' } });

    await waitFor(() => {
      expect(screen.getByText("Paris, France")).toBeInTheDocument();
      expect(screen.getByText("Paris, Texas, USA")).toBeInTheDocument();
    });
  });

  test('allows disabling autocomplete', () => {
    render(
      <LocationInput
        label="To"
        value=""
        onChange={jest.fn()}
        placeholder="Enter destination"
        showAutocomplete={false}
      />
    );

    const input = screen.getByPlaceholderText(/enter destination/i);
    fireEvent.change(input, { target: { value: 'Paris' } });

    // Should not show autocomplete suggestions
    expect(screen.queryByText("Paris, France")).not.toBeInTheDocument();
  });

  test('handles autocomplete selection', async () => {
    const mockOnChange = jest.fn();

    // Mock autocomplete API response
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ([
        {
          place_id: 1,
          display_name: "Paris, France",
          type: "city"
        }
      ])
    });

    render(
      <LocationInput
        label="To"
        value=""
        onChange={mockOnChange}
        placeholder="Enter destination"
        showAutocomplete={true}
      />
    );

    const input = screen.getByPlaceholderText(/enter destination/i);
    fireEvent.change(input, { target: { value: 'Paris' } });

    await waitFor(() => {
      expect(screen.getByText("Paris, France")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Paris, France"));

    expect(mockOnChange).toHaveBeenCalledWith("Paris, France");
  });

  test('handles geolocation error gracefully', async () => {
    const mockOnChange = jest.fn();
    const mockError = { 
      code: 1, // PERMISSION_DENIED
      message: "Permission denied",
      PERMISSION_DENIED: 1,
      POSITION_UNAVAILABLE: 2,
      TIMEOUT: 3
    };

    mockGeolocation.getCurrentPosition.mockImplementationOnce((success, error) => {
      error(mockError);
    });

    render(
      <LocationInput
        label="From"
        value=""
        onChange={mockOnChange}
        placeholder="Enter origin"
        showGeolocation={true}
      />
    );

    const geoButton = screen.getByTitle(/use current location/i);
    fireEvent.click(geoButton);

    await waitFor(() => {
      expect(screen.getByText(/Location access denied/i)).toBeInTheDocument();
    });

    expect(mockOnChange).not.toHaveBeenCalled();
  });
}); 