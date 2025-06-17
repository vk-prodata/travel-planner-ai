import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import TripForm from '../TripForm';
import { TripFormData } from '../../types';

describe('TripForm Photoshoot Feature', () => {
  const mockOnSubmit = jest.fn();

  beforeEach(() => {
    mockOnSubmit.mockClear();
  });

  test('shows photoshoot mode dropdown when photoshoot preference is selected', () => {
    render(<TripForm onSubmit={mockOnSubmit} isLoading={false} />);
    
    // Initially, photoshoot settings should not be visible
    expect(screen.queryByText(/📸 Photoshoot Mode/i)).not.toBeInTheDocument();
    
    // Click on photoshoot preference
    const photoshootButton = screen.getByText(/photoshoot/i);
    fireEvent.click(photoshootButton);
    
    // Now photoshoot settings should be visible
    expect(screen.getByText(/📸 Photoshoot Mode/i)).toBeInTheDocument();
    expect(screen.getByText(/Select a photoshoot focus.../i)).toBeInTheDocument();
  });

  test('hides photoshoot mode dropdown when photoshoot preference is deselected', () => {
    render(<TripForm onSubmit={mockOnSubmit} isLoading={false} />);
    
    // Select photoshoot preference
    const photoshootButton = screen.getByText(/photoshoot/i);
    fireEvent.click(photoshootButton);
    expect(screen.getByText(/📸 Photoshoot Mode/i)).toBeInTheDocument();
    
    // Deselect photoshoot preference
    fireEvent.click(photoshootButton);
    expect(screen.queryByText(/📸 Photoshoot Mode/i)).not.toBeInTheDocument();
  });

  test('shows Instagram handle input when insta-blogger mode is selected', () => {
    render(<TripForm onSubmit={mockOnSubmit} isLoading={false} />);
    
    // Select photoshoot preference
    const photoshootButton = screen.getByText(/photoshoot/i);
    fireEvent.click(photoshootButton);
    
    // Find the photoshoot mode select - it appears after clicking photoshoot preference
    const modeSelect = screen.getAllByRole('combobox').find(select => {
      const parentGroup = select.closest('.mb-3');
      return parentGroup?.textContent?.includes('📸 Photoshoot Mode');
    });
    
    expect(modeSelect).toBeInTheDocument();
    fireEvent.change(modeSelect!, { target: { value: 'insta-blogger' } });
    
    // Instagram handle input should now be visible
    expect(screen.getByText(/Instagram Handle/i)).toBeInTheDocument();
    expect(screen.getByDisplayValue('@elenakudry_usa')).toBeInTheDocument();
  });

  test('hides Instagram handle input when other modes are selected', () => {
    render(<TripForm onSubmit={mockOnSubmit} isLoading={false} />);
    
    // Select photoshoot preference
    const photoshootButton = screen.getByText(/photoshoot/i);
    fireEvent.click(photoshootButton);
    
    // Find the photoshoot mode select
    const modeSelect = screen.getAllByRole('combobox').find(select => {
      const parentGroup = select.closest('.mb-3');
      return parentGroup?.textContent?.includes('📸 Photoshoot Mode');
    });
    
    // Select insta-blogger mode first
    fireEvent.change(modeSelect!, { target: { value: 'insta-blogger' } });
    expect(screen.getByText(/Instagram Handle/i)).toBeInTheDocument();
    
    // Change to nature mode
    fireEvent.change(modeSelect!, { target: { value: 'nature' } });
    expect(screen.queryByText(/Instagram Handle/i)).not.toBeInTheDocument();
  });

  test('includes photoshoot settings in form submission', async () => {
    render(<TripForm onSubmit={mockOnSubmit} isLoading={false} />);
    
    // Fill in required fields - start with destination
    fireEvent.change(screen.getByPlaceholderText(/Enter your destination/i), { target: { value: 'Paris' } });
    
    // Find and fill date inputs using input type selector
    const dateInputs = screen.getAllByDisplayValue('').filter(input => input.getAttribute('type') === 'date');
    const startDateInput = dateInputs[0]; // First date input is start date
    const endDateInput = dateInputs[1]; // Second date input is end date
    
    fireEvent.change(startDateInput, { target: { value: '2024-07-01' } });
    fireEvent.change(endDateInput, { target: { value: '2024-07-10' } });
    
    // Select photoshoot preference
    const photoshootButton = screen.getByText(/photoshoot/i);
    fireEvent.click(photoshootButton);
    
    // Find and select nature mode
    const modeSelect = screen.getAllByRole('combobox').find(select => {
      const parentGroup = select.closest('.mb-3');
      return parentGroup?.textContent?.includes('📸 Photoshoot Mode');
    });
    fireEvent.change(modeSelect!, { target: { value: 'nature' } });
    
    // Submit the form
    fireEvent.click(screen.getByText(/Plan My Trip/i));
    
    // Check if onSubmit was called with photoshoot settings
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          entertainmentPreferences: expect.arrayContaining(['photoshoot']),
          photoshootSettings: expect.objectContaining({
            mode: 'nature'
          })
        })
      );
    });
  });

  test('includes Instagram handle in form submission for insta-blogger mode', async () => {
    render(<TripForm onSubmit={mockOnSubmit} isLoading={false} />);
    
    // Fill in required fields - start with destination
    fireEvent.change(screen.getByPlaceholderText(/Enter your destination/i), { target: { value: 'Paris' } });
    
    // Find and fill date inputs using input type selector
    const dateInputs = screen.getAllByDisplayValue('').filter(input => input.getAttribute('type') === 'date');
    const startDateInput = dateInputs[0]; // First date input is start date
    const endDateInput = dateInputs[1]; // Second date input is end date
    
    fireEvent.change(startDateInput, { target: { value: '2024-07-01' } });
    fireEvent.change(endDateInput, { target: { value: '2024-07-10' } });
    
    // Select photoshoot preference
    const photoshootButton = screen.getByText(/photoshoot/i);
    fireEvent.click(photoshootButton);
    
    // Find and select insta-blogger mode
    const modeSelect = screen.getAllByRole('combobox').find(select => {
      const parentGroup = select.closest('.mb-3');
      return parentGroup?.textContent?.includes('📸 Photoshoot Mode');
    });
    fireEvent.change(modeSelect!, { target: { value: 'insta-blogger' } });
    
    // Change Instagram handle
    const instagramInput = screen.getByDisplayValue('@elenakudry_usa');
    fireEvent.change(instagramInput, { target: { value: '@test_blogger' } });
    
    // Submit the form
    fireEvent.click(screen.getByText(/Plan My Trip/i));
    
    // Check if onSubmit was called with Instagram handle
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          entertainmentPreferences: expect.arrayContaining(['photoshoot']),
          photoshootSettings: expect.objectContaining({
            mode: 'insta-blogger',
            instagramHandle: '@test_blogger'
          })
        })
      );
    });
  });

  test('shows all photoshoot mode options', () => {
    render(<TripForm onSubmit={mockOnSubmit} isLoading={false} />);
    
    // Select photoshoot preference
    const photoshootButton = screen.getByText(/photoshoot/i);
    fireEvent.click(photoshootButton);
    
    // Check that all mode options are present
    expect(screen.getByText(/🌲 Nature Mode - Landscapes, forests, mountains, waterfalls/i)).toBeInTheDocument();
    expect(screen.getByText(/🏛️ Architecture Mode - Historic buildings, modern structures, bridges/i)).toBeInTheDocument();
    expect(screen.getByText(/📸 Local Mode - Candid urban moments, local markets, daily life/i)).toBeInTheDocument();
    expect(screen.getByText(/👨‍👩‍👧‍👦 Fun with Kids - Family-friendly activities with beautiful photoshoots/i)).toBeInTheDocument();
    expect(screen.getByText(/🦋 Wildlife Mode - Animals in natural habitat/i)).toBeInTheDocument();
    expect(screen.getByText(/📱 Follow Insta Blogger - Travel in the style of an influencer/i)).toBeInTheDocument();
  });

  test('shows helpful tooltip for photoshoot mode', () => {
    render(<TripForm onSubmit={mockOnSubmit} isLoading={false} />);
    
    // Select photoshoot preference
    const photoshootButton = screen.getByText(/photoshoot/i);
    fireEvent.click(photoshootButton);
    
    // Check that the photoshoot mode section is visible with tooltip
    expect(screen.getByText(/📸 Photoshoot Mode/i)).toBeInTheDocument();
    
    // Check for tooltip trigger - the FaInfoCircle component renders as an SVG
    const photoshootSection = screen.getByText(/📸 Photoshoot Mode/i).closest('.mb-3');
    const infoIcon = photoshootSection?.querySelector('svg[fill="currentColor"]');
    expect(infoIcon).toBeInTheDocument();
  });
}); 