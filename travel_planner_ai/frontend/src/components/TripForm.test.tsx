import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import TripForm from './TripForm';

describe('TripForm Component', () => {
  const mockOnSubmit = jest.fn();
  
  beforeEach(() => {
    jest.clearAllMocks();
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
  
  test('intermediate stops section includes start date field', () => {
    render(<TripForm onSubmit={mockOnSubmit} isLoading={false} />);
    
    // Open the advanced settings accordion
    fireEvent.click(screen.getByText(/Advanced Settings/i));
    
    // Check for intermediate stops section
    expect(screen.getByText(/Intermediate Stops/i)).toBeInTheDocument();
    
    // Check for the three input fields: destination, start date, and days
    const inputFields = screen.getAllByRole('textbox');
    expect(inputFields.length).toBeGreaterThanOrEqual(1); // At least one for destination
    
    const dateInputs = document.querySelectorAll('input[type="date"]');
    expect(dateInputs.length).toBeGreaterThanOrEqual(3); // Main start/end dates + intermediate start date
    
    const numberInputs = screen.getAllByRole('spinbutton');
    expect(numberInputs.length).toBeGreaterThanOrEqual(4); // Adults, children, infants, and days
  });
  
  test('adding an intermediate stop with start date', async () => {
    render(<TripForm onSubmit={mockOnSubmit} isLoading={false} />);
    
    // Set main trip dates first
    const startDateInput = screen.getByLabelText(/Start Date/i);
    const endDateInput = screen.getByLabelText(/End Date/i);
    
    fireEvent.change(startDateInput, { target: { value: '2024-07-01' } });
    fireEvent.change(endDateInput, { target: { value: '2024-07-15' } });
    
    // Open the advanced settings accordion
    fireEvent.click(screen.getByText(/Advanced Settings/i));
    
    // Fill in intermediate stop details
    const destinationInput = screen.getByPlaceholderText(/City\/Location/i);
    fireEvent.change(destinationInput, { target: { value: 'Paris' } });
    
    // Find the date input for intermediate stop
    const dateInputs = document.querySelectorAll('input[type="date"]');
    // Find the intermediate stop date input (not the main start/end date inputs)
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
    
    // Set main trip dates
    const startDateInput = screen.getByLabelText(/Start Date/i);
    const endDateInput = screen.getByLabelText(/End Date/i);
    
    fireEvent.change(startDateInput, { target: { value: '2024-07-01' } });
    fireEvent.change(endDateInput, { target: { value: '2024-07-10' } });
    
    // Open the advanced settings accordion
    fireEvent.click(screen.getByText(/Advanced Settings/i));
    
    // Fill in intermediate stop details with invalid dates
    const destinationInput = screen.getByPlaceholderText(/City\/Location/i);
    fireEvent.change(destinationInput, { target: { value: 'Rome' } });
    
    // Find the date input for intermediate stop
    const dateInputs = document.querySelectorAll('input[type="date"]');
    // Find the intermediate stop date input (not the main start/end date inputs)
    const stopDateInput = Array.from(dateInputs).find(input => 
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
}); 