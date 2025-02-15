import { TripItinerary, TripFormData } from '../types';

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
  itinerary: TripItinerary;
  formData: TripFormData;
  userId: string;
}) => {
  try {
    console.log('Saving trip with data:', {
      userId: tripData.userId,
      destination: tripData.formData.destination,
    });

    const headers = getAuthHeaders();
    const response = await fetch(`${API_URL}/api/trips`, {
      method: 'POST',
      headers,
      credentials: 'include',
      body: JSON.stringify(tripData),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      console.error('Save trip error:', {
        status: response.status,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries()),
        error: errorData
      });

      if (response.status === 401) {
        throw new Error('Please sign in again to save your trip');
      } else if (response.status === 403) {
        throw new Error('You do not have permission to save this trip');
      } else {
        throw new Error(errorData?.detail || `Failed to save trip: ${response.statusText}`);
      }
    }

    const savedTrip = await response.json();
    console.log('Trip saved successfully:', savedTrip);
    return savedTrip;
  } catch (error) {
    console.error('Error saving trip:', error);
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
    const response = await fetch(`${API_URL}/api/trips/${tripId}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      credentials: 'include',
      body: JSON.stringify(tripData),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || 'Failed to update trip');
    }

    return response.json();
  } catch (error) {
    console.error('Network error:', error);
    throw error;
  }
};

export const getUserTrips = async (userId: string) => {
  try {
    const response = await fetch(`${API_URL}/api/trips/user/${userId}`, {
      headers: getAuthHeaders(),
      credentials: 'include',
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch trips: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching user trips:', error);
    throw error;
  }
}; 