import { TripItinerary, TripFormData } from '../types';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  console.log('Auth token:', token);
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
    console.log('Sending trip data:', tripData);
    const response = await fetch(`${API_URL}/api/trips`, {
      method: 'POST',
      headers: getAuthHeaders(),
      credentials: 'include',
      body: JSON.stringify(tripData),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to save trip');
    }

    return response.json();
  } catch (error) {
    console.error('Network error:', error);
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