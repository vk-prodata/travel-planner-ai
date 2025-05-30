import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import TripForm from './TripForm';

// Mock geolocation
const mockGeolocation = {
  getCurrentPosition: jest.fn(),
  watchPosition: jest.fn(),
  clearWatch: jest.fn()
};

// Mock fetch for autocomplete
global.fetch = jest.fn();

describe('TripForm Component', () => {
  const mockOnSubmit = jest.fn();
  
  beforeEach(() => {
    jest.clearAllMocks();
    Object.defineProperty(global.navigator, 'geolocation', {
      value: mockGeolocation,
      writable: true
    });
    (global.fetch as jest.Mock).mockClear();
  });
  
  test('renders the form with all required fields', () => {
    render(<TripForm onSubmit={mockOnSubmit} isLoading={false} />);
    
    // Check for main form elements
    expect(screen.getByLabelText(/Travel Type/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/From/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/To/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Start Date/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/End Date/i)).toBeInTheDocument();
    expect(screen.getByText(/Plan My Trip/i)).toBeInTheDocument();
  });

  test('shows geolocation button for origin field', () => {
    render(<TripForm onSubmit={mockOnSubmit} isLoading={false} />);
    
    // Check for geolocation button (should be present for "From" field)
    expect(screen.getByTitle(/use current location/i)).toBeInTheDocument();
  });

  test('shows autocomplete toggles for location fields', () => {
    render(<TripForm onSubmit={mockOnSubmit} isLoading={false} />);
    
    // Check for autocomplete toggles
    const autocompleteToggles = screen.getAllByLabelText(/Auto-complete/i);
    expect(autocompleteToggles).toHaveLength(3); // One for From, one for To, one for intermediate stops
  });

  test('geolocation works for origin field', async () => {
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

    render(<TripForm onSubmit={mockOnSubmit} isLoading={false} />);

    const geoButton = screen.getByTitle(/use current location/i);
    fireEvent.click(geoButton);

    await waitFor(() => {
      const fromInput = screen.getByPlaceholderText(/Enter your starting location/i);
      expect(fromInput).toHaveValue("New York, NY, USA");
    });
  });
  
  test('intermediate stops section works with new LocationInput', () => {
    render(<TripForm onSubmit={mockOnSubmit} isLoading={false} />);
    
    // Open the advanced settings accordion
    fireEvent.click(screen.getByText(/Advanced Settings/i));
    
    // Check for intermediate stops section
    expect(screen.getByText(/Intermediate Stops/i)).toBeInTheDocument();
    
    // Check for the location input in intermediate stops
    expect(screen.getByPlaceholderText(/City\/Location/i)).toBeInTheDocument();
  });
  
  test('adding an intermediate stop with new LocationInput', async () => {
    render(<TripForm onSubmit={mockOnSubmit} isLoading={false} />);
    
    // Set main trip dates first using their specific labels
    const startDateInput = screen.getByDisplayValue(''); // Find empty start date input
    const endDateInput = screen.getAllByDisplayValue('').find(input => 
      input.getAttribute('type') === 'date' && input !== startDateInput
    ); // Find the second empty date input
    
    fireEvent.change(startDateInput, { target: { value: '2024-07-01' } });
    fireEvent.change(endDateInput!, { target: { value: '2024-07-15' } });
    
    // Open the advanced settings accordion
    fireEvent.click(screen.getByText(/Advanced Settings/i));
    
    // Fill in intermediate stop details
    const destinationInput = screen.getByPlaceholderText(/City\/Location/i);
    fireEvent.change(destinationInput, { target: { value: 'Paris' } });
    
    // Find the date input for intermediate stop - it's the one that's disabled initially
    const dateInputs = document.querySelectorAll('input[type="date"]');
    const stopDateInput = Array.from(dateInputs).find(input => 
      input !== startDateInput && input !== endDateInput
    );
    
    if (stopDateInput) {
      fireEvent.change(stopDateInput, { target: { value: '2024-07-05' } });
    }
    
    // Set days
    const daysInput = screen.getByPlaceholderText(/Days/i);
    fireEvent.change(daysInput, { target: { value: '3' } });
    
    // Click the add button
    const addButton = screen.getByRole('button', { name: '+' });
    fireEvent.click(addButton);
    
    // Check if the stop was added with the correct format
    await waitFor(() => {
      expect(screen.getByText(/Paris/i)).toBeInTheDocument();
      // Check for date in the badge (format may vary based on locale)
      const stopBadge = screen.getByText(/Paris/i).closest('.badge');
      expect(stopBadge).toHaveTextContent(/7\/5\/2024|05\/07\/2024|2024-07-05/);
      expect(stopBadge).toHaveTextContent(/3 days/);
    });
  });
  
  test('validates that intermediate stop dates are within trip dates', async () => {
    render(<TripForm onSubmit={mockOnSubmit} isLoading={false} />);
    
    // Set main trip dates using display value
    const dateInputs = screen.getAllByDisplayValue('');
    const startDateInput = dateInputs.find(input => input.getAttribute('type') === 'date');
    const endDateInput = dateInputs.find(input => 
      input.getAttribute('type') === 'date' && input !== startDateInput
    );
    
    fireEvent.change(startDateInput!, { target: { value: '2024-07-01' } });
    fireEvent.change(endDateInput!, { target: { value: '2024-07-10' } });
    
    // Open the advanced settings accordion
    fireEvent.click(screen.getByText(/Advanced Settings/i));
    
    // Fill in intermediate stop details with invalid dates
    const destinationInput = screen.getByPlaceholderText(/City\/Location/i);
    fireEvent.change(destinationInput, { target: { value: 'Rome' } });
    
    // Find the date input for intermediate stop
    const allDateInputs = document.querySelectorAll('input[type="date"]');
    const stopDateInput = Array.from(allDateInputs).find(input => 
      input !== startDateInput && input !== endDateInput
    );
    
    if (stopDateInput) {
      // Set a date that's valid
      fireEvent.change(stopDateInput, { target: { value: '2024-07-08' } });
    }
    
    // Set days that would make the stop end after the trip end date
    const daysInput = screen.getByPlaceholderText(/Days/i);
    fireEvent.change(daysInput, { target: { value: '5' } });
    
    // Click the add button
    const addButton = screen.getByRole('button', { name: '+' });
    fireEvent.click(addButton);
    
    // Check for error message
    await waitFor(() => {
      expect(screen.getByText(/Stop dates must be within trip dates/i)).toBeInTheDocument();
    });
  });

  test('can disable autocomplete for destination field', () => {
    render(<TripForm onSubmit={mockOnSubmit} isLoading={false} />);
    
    // Find autocomplete toggles - get the one for destination ("To")
    const autocompleteToggles = screen.getAllByLabelText(/Auto-complete/i);
    const destinationAutocompleteToggle = autocompleteToggles[1]; // Second one is for "To"
    
    // Toggle off autocomplete
    fireEvent.click(destinationAutocompleteToggle);
    
    // Verify it's disabled
    expect(destinationAutocompleteToggle).not.toBeChecked();
  });

  test('cuisine preference selection works correctly', () => {
    render(<TripForm onSubmit={mockOnSubmit} isLoading={false} />);
    
    // Open the advanced settings accordion
    fireEvent.click(screen.getByText(/Advanced Settings/i));
    
    // Check if cuisine preference section exists
    expect(screen.getByText(/Café & Restaurant Preferences/i)).toBeInTheDocument();
    
    // Find the select element by looking for the one with cuisine options
    const allSelects = screen.getAllByRole('combobox');
    const cuisineSelect = allSelects.find(select => {
      const options = Array.from(select.querySelectorAll('option'));
      return options.some(option => option.textContent?.includes('Vegetarian'));
    });
    
    expect(cuisineSelect).toBeInTheDocument();
    
    // Check if default value is 'any'
    expect(cuisineSelect).toHaveValue('any');
    
    // Change the value and verify
    fireEvent.change(cuisineSelect!, { target: { value: 'vegetarian' } });
    expect(cuisineSelect).toHaveValue('vegetarian');
  });

  test('cuisine preference is included in form submission', async () => {
    render(<TripForm onSubmit={mockOnSubmit} isLoading={false} />);
    
    // Fill in required fields using placeholder text to be more specific
    fireEvent.change(screen.getByPlaceholderText(/Enter your starting location/i), { target: { value: 'New York' } });
    fireEvent.change(screen.getByPlaceholderText(/Enter your destination/i), { target: { value: 'Paris' } });
    
    // Find and fill date inputs
    const dateInputs = screen.getAllByDisplayValue('');
    const startDateInput = dateInputs.find(input => input.getAttribute('type') === 'date');
    const endDateInput = dateInputs.find(input => 
      input.getAttribute('type') === 'date' && input !== startDateInput
    );
    
    fireEvent.change(startDateInput!, { target: { value: '2024-07-01' } });
    fireEvent.change(endDateInput!, { target: { value: '2024-07-10' } });
    
    // Open advanced settings and change cuisine preference
    fireEvent.click(screen.getByText(/Advanced Settings/i));
    const allSelects = screen.getAllByRole('combobox');
    const cuisineSelect = allSelects.find(select => {
      const options = Array.from(select.querySelectorAll('option'));
      return options.some(option => option.textContent?.includes('Mediterranean'));
    });
    
    fireEvent.change(cuisineSelect!, { target: { value: 'mediterranean' } });
    
    // Submit the form
    fireEvent.click(screen.getByText(/Plan My Trip/i));
    
    // Check if onSubmit was called with the correct cuisine preference
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          cuisinePreference: 'mediterranean'
        })
      );
    });
  });
}); 