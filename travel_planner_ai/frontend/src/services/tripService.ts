import { TripItinerary, TripFormData, SavedTrip } from '../types';
import { notifyError } from './errorService';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  
  if (!token) {
    throw new Error('No authentication token found');
  }

  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  };
};

export const saveTrip = async (tripData: {
  userId: string;
  formData: TripFormData;
  itinerary: TripItinerary;
}): Promise<SavedTrip> => {
  try {
    const response = await fetch(`${API_URL}/trips`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      credentials: 'include',
      body: JSON.stringify(tripData),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to save trip');
    }

    const savedTrip = await response.json();
    if (!savedTrip || !savedTrip.id) {
      throw new Error('Invalid response from server');
    }
    return savedTrip as SavedTrip;
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : 'Failed to save trip';
    console.error('Error saving trip:', error);
    notifyError(errorMsg, tripData.userId);
    throw error;
  }
};

export const updateTrip = async (
  tripId: string,
  tripData: {
    itinerary: TripItinerary;
    formData: TripFormData;
    userId: string;
  }
) => {
  try {
    console.log('Updating trip:', {
      tripId,
      userId: tripData.userId,
      destination: tripData.formData.destination,
      itineraryDays: tripData.itinerary?.days?.length || 0,
      formDataKeys: Object.keys(tripData.formData),
      itineraryKeys: Object.keys(tripData.itinerary || {})
    });

    // Validate itinerary before sending
    if (!tripData.itinerary || !tripData.itinerary.days) {
      console.error('Invalid itinerary structure for update:', tripData.itinerary);
      throw new Error('Invalid itinerary structure. Please regenerate your itinerary.');
    }

    const headers = getAuthHeaders();
    const response = await fetch(`${API_URL}/trips/${tripId}`, {
      method: 'PUT',
      headers,
      credentials: 'include',
      body: JSON.stringify(tripData),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      console.error('Update trip error:', {
        status: response.status,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries()),
        error: errorData,
        sentData: {
          tripId,
          userId: tripData.userId,
          hasItinerary: !!tripData.itinerary,
          itineraryDays: tripData.itinerary?.days?.length || 0
        }
      });

      if (response.status === 401) {
        throw new Error('Please sign in again to update your trip');
      } else if (response.status === 403) {
        throw new Error('You do not have permission to update this trip');
      } else if (response.status === 404) {
        throw new Error('Trip not found');
      } else {
        throw new Error(errorData?.detail || `Failed to update trip: ${response.statusText}`);
      }
    }

    const updatedTrip = await response.json();
    console.log('Trip updated successfully:', {
      id: updatedTrip.id,
      hasItinerary: !!updatedTrip.itinerary,
      itineraryDays: updatedTrip.itinerary?.days?.length || 0
    });
    return updatedTrip;
  } catch (error) {
    console.error('Error updating trip:', error);
    const userEmail = localStorage.getItem('userEmail');
    notifyError(error, userEmail);
    throw error;
  }
};

export const getUserTrips = async (userId: string): Promise<SavedTrip[]> => {
  try {
    const response = await fetch(`${API_URL}/trips?userId=${userId}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      credentials: 'include',
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch trips');
    }

    return await response.json();
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : 'Failed to fetch trips';
    console.error('Error fetching trips:', error);
    notifyError(errorMsg, userId);
    throw error;
  }
}; 