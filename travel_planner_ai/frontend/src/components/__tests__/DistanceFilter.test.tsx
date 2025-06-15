import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import TripForm from '../TripForm';

// Mock LocationInput component
jest.mock('../LocationInput', () => {
  return function MockLocationInput({ label, value, onChange, placeholder, required }: any) {
    return (
      <div>
        <label>{label}</label>
        <input
          data-testid={`location-input-${label?.toLowerCase() || 'default'}`}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          required={required}
        />
      </div>
    );
  };
});

describe('Distance Filter Integration Tests', () => {
  const mockOnSubmit = jest.fn();
  const mockUser = { id: '1', email: 'test@example.com', name: 'Test User' };

  beforeEach(() => {
    mockOnSubmit.mockClear();
  });

  describe('Distance Slider Visibility', () => {
    it('should not show distance slider when origin field is hidden', () => {
      render(<TripForm onSubmit={mockOnSubmit} isLoading={false} user={mockUser} />);
      
      expect(screen.queryByTestId('distance-filter-container')).not.toBeInTheDocument();
      expect(screen.queryByTestId('distance-slider')).not.toBeInTheDocument();
    });

    it('should show distance slider when origin field is enabled', async () => {
      render(<TripForm onSubmit={mockOnSubmit} isLoading={false} user={mockUser} />);
      
      // Enable origin field
      const originToggle = screen.getByLabelText(/add starting location for route suggestions/i);
      fireEvent.click(originToggle);
      
      await waitFor(() => {
        expect(screen.getByTestId('distance-filter-container')).toBeInTheDocument();
        expect(screen.getByTestId('distance-slider')).toBeInTheDocument();
      });
    });

    it('should hide distance slider when origin field is disabled', async () => {
      render(<TripForm onSubmit={mockOnSubmit} isLoading={false} user={mockUser} />);
      
      // Enable then disable origin field
      const originToggle = screen.getByLabelText(/add starting location for route suggestions/i);
      fireEvent.click(originToggle);
      
      await waitFor(() => {
        expect(screen.getByTestId('distance-filter-container')).toBeInTheDocument();
      });
      
      fireEvent.click(originToggle);
      
      await waitFor(() => {
        expect(screen.queryByTestId('distance-filter-container')).not.toBeInTheDocument();
      });
    });
  });

  describe('Distance Slider Functionality', () => {
    beforeEach(async () => {
      render(<TripForm onSubmit={mockOnSubmit} isLoading={false} user={mockUser} />);
      
      // Enable origin field to show distance slider
      const originToggle = screen.getByLabelText(/add starting location for route suggestions/i);
      fireEvent.click(originToggle);
      
      await waitFor(() => {
        expect(screen.getByTestId('distance-filter-container')).toBeInTheDocument();
      });
    });

    it('should have default value of 80 km', () => {
      const slider = screen.getByTestId('distance-slider') as HTMLInputElement;
      expect(slider.value).toBe('80');
      
      const valueDisplay = screen.getByTestId('distance-value-display');
      expect(valueDisplay).toHaveTextContent('80 km');
    });

    it('should update distance value when slider changes', () => {
      const slider = screen.getByTestId('distance-slider') as HTMLInputElement;
      
      fireEvent.change(slider, { target: { value: '100' } });
      
      expect(slider.value).toBe('100');
      const valueDisplay = screen.getByTestId('distance-value-display');
      expect(valueDisplay).toHaveTextContent('100 miles');
    });

    it('should have correct range (0-500 km)', () => {
      const slider = screen.getByTestId('distance-slider') as HTMLInputElement;
      
      expect(slider.min).toBe('0');
      expect(slider.max).toBe('500');
      expect(slider.step).toBe('8'); // 8-km steps for finer control
    });

    it('should toggle between kilometers and miles', () => {
      const unitToggle = screen.getByTestId('distance-unit-toggle');
      const valueDisplay = screen.getByTestId('distance-value-display');
      
      // Initially should be km
      expect(valueDisplay).toHaveTextContent('80 km');
      
      // Switch to miles
      fireEvent.click(unitToggle);
      expect(valueDisplay).toHaveTextContent('50 miles'); // 80 km ≈ 50 miles
      
      // Switch back to km
      fireEvent.click(unitToggle);
      expect(valueDisplay).toHaveTextContent('80 km');
    });

    it('should convert values correctly between units', () => {
      const slider = screen.getByTestId('distance-slider') as HTMLInputElement;
      const unitToggle = screen.getByTestId('distance-unit-toggle');
      const valueDisplay = screen.getByTestId('distance-value-display');
      
      // Set to 160 km
      fireEvent.change(slider, { target: { value: '160' } });
      expect(valueDisplay).toHaveTextContent('160 km');
      
      // Switch to miles
      fireEvent.click(unitToggle);
      expect(valueDisplay).toHaveTextContent('99 miles'); // 160 km ≈ 99 miles
      
      // Switch back to km
      fireEvent.click(unitToggle);
      expect(valueDisplay).toHaveTextContent('160 km');
    });
  });

  describe('Form Submission Integration', () => {
    it('should include distance filter data in form submission when origin is provided', async () => {
      render(<TripForm onSubmit={mockOnSubmit} isLoading={false} user={mockUser} />);
      
      // Enable origin field and set values
      const originToggle = screen.getByLabelText(/add starting location for route suggestions/i);
      fireEvent.click(originToggle);
      
      await waitFor(() => {
        expect(screen.getByTestId('distance-filter-container')).toBeInTheDocument();
      });
      
      // Set form values
      const originInput = screen.getByTestId('location-input-from');
      const destinationInput = screen.getByTestId('location-input-to');
      const startDate = screen.getByLabelText(/start date/i);
      const endDate = screen.getByLabelText(/end date/i);
      const distanceSlider = screen.getByTestId('distance-slider');
      
      fireEvent.change(originInput, { target: { value: 'New York, NY' } });
      fireEvent.change(destinationInput, { target: { value: 'Boston, MA' } });
      fireEvent.change(startDate, { target: { value: '2024-06-01' } });
      fireEvent.change(endDate, { target: { value: '2024-06-05' } });
      fireEvent.change(distanceSlider, { target: { value: '75' } });
      
      // Submit form
      const submitButton = screen.getByRole('button', { name: /generate itinerary/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith(
          expect.objectContaining({
            origin: 'New York, NY',
            destination: 'Boston, MA',
            exclusionRadius: 75,
            exclusionUnit: 'km'
          })
        );
      });
    });

    it('should not include distance filter data when origin is not provided', async () => {
      render(<TripForm onSubmit={mockOnSubmit} isLoading={false} user={mockUser} />);
      
      // Set form values without enabling origin
      const destinationInput = screen.getByTestId('location-input-to');
      const startDate = screen.getByLabelText(/start date/i);
      const endDate = screen.getByLabelText(/end date/i);
      
      fireEvent.change(destinationInput, { target: { value: 'Boston, MA' } });
      fireEvent.change(startDate, { target: { value: '2024-06-01' } });
      fireEvent.change(endDate, { target: { value: '2024-06-05' } });
      
      // Submit form
      const submitButton = screen.getByRole('button', { name: /generate itinerary/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith(
          expect.objectContaining({
            destination: 'Boston, MA',
            origin: ''
          })
        );
        
        // Should not include exclusion radius fields
        expect(mockOnSubmit).toHaveBeenCalledWith(
          expect.not.objectContaining({
            exclusionRadius: expect.anything(),
            exclusionUnit: expect.anything()
          })
        );
      });
    });
  });

  describe('Distance Filter UI Elements', () => {
    beforeEach(async () => {
      render(<TripForm onSubmit={mockOnSubmit} isLoading={false} user={mockUser} />);
      
      // Enable origin field
      const originToggle = screen.getByLabelText(/add starting location for route suggestions/i);
      fireEvent.click(originToggle);
      
      await waitFor(() => {
        expect(screen.getByTestId('distance-filter-container')).toBeInTheDocument();
      });
    });

    it('should display helpful tooltip explaining the feature', () => {
      const tooltipTrigger = screen.getByTestId('distance-filter-tooltip');
      expect(tooltipTrigger).toBeInTheDocument();
      
      // Simulate hover to show tooltip
      fireEvent.mouseEnter(tooltipTrigger);
      
      expect(screen.getByText(/exclude activities within this distance/i)).toBeInTheDocument();
    });

    it('should show proper labels and descriptions', () => {
      expect(screen.getByText(/exclusion radius/i)).toBeInTheDocument();
      expect(screen.getByText(/skip recommendations within/i)).toBeInTheDocument();
    });

    it('should have accessible form elements', () => {
      const slider = screen.getByTestId('distance-slider');
      const unitToggle = screen.getByTestId('distance-unit-toggle');
      
      expect(slider).toHaveAttribute('aria-label');
      expect(unitToggle).toHaveAttribute('aria-label');
    });
  });

  describe('Error Handling', () => {
    it('should handle invalid distance values gracefully', async () => {
      render(<TripForm onSubmit={mockOnSubmit} isLoading={false} user={mockUser} />);
      
      // Enable origin field
      const originToggle = screen.getByLabelText(/add starting location for route suggestions/i);
      fireEvent.click(originToggle);
      
      await waitFor(() => {
        expect(screen.getByTestId('distance-slider')).toBeInTheDocument();
      });
      
      const slider = screen.getByTestId('distance-slider');
      
      // Try to set value outside range
      fireEvent.change(slider, { target: { value: '600' } });
      
      // Should clamp to maximum value
      expect((slider as HTMLInputElement).value).toBe('500');
    });
  });
}); 