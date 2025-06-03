import { TripFormData, TripItinerary } from '../types';
import { notifyError } from './errorService';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const generateItinerary = async (formData: TripFormData, userId: string): Promise<TripItinerary> => {
  try {
    const response = await fetch(`${API_URL}/generate-itinerary`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        userId,
        formData: {
          ...formData,
          origin: formData.origin || '',
          destination: formData.destination,
          startDate: formData.startDate,
          endDate: formData.endDate,
          travelType: formData.travelType,
          adults: formData.adults,
          children: formData.children || 0,
          infants: formData.infants || 0,
          budgetLevel: formData.budgetLevel,
          entertainmentPreferences: formData.entertainmentPreferences || [],
          intermediateStops: formData.intermediateStops || []
        }
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to generate itinerary');
    }

    const data = await response.json();
    
    // Handle warning/error responses from AI generation
    if (!data.success) {
      const warningError = new Error(data.message || 'AI generation encountered an issue');
      // Attach additional info for the frontend to potentially display
      (warningError as any).errorType = data.error_type;
      (warningError as any).suggestions = data.suggestions || [];
      (warningError as any).partialData = data.partial_data;
      (warningError as any).requestedDays = data.requested_days;
      (warningError as any).partialDaysReceived = data.partial_days_received;
      throw warningError;
    }
    
    if (!data.itinerary) {
      throw new Error('Invalid response format from server');
    }

    return data.itinerary;
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : 'Failed to generate itinerary';
    console.error('Error generating itinerary:', error);
    notifyError(errorMsg, userId);
    throw error;
  }
}; 