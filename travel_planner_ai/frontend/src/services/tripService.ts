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

    const response = await fetch(`${API_URL}/api/trips`, {
      method: 'POST',
      headers: getAuthHeaders(),
      credentials: 'include',
      body: JSON.stringify(tripData),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      
      if (response.status === 409) {
        throw new Error('You already have a similar trip planned. Please modify the existing trip or change the dates/destination.');
      }

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
    console.log('Updating trip:', {
      tripId,
      userId: tripData.userId,
      destination: tripData.formData.destination,
      itinerary: tripData.itinerary
    });

    const headers = getAuthHeaders();
    const response = await fetch(`${API_URL}/api/trips/${tripId}`, {
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
        sentData: tripData
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
    console.log('Trip updated successfully:', updatedTrip);
    return updatedTrip;
  } catch (error) {
    console.error('Error updating trip:', error);
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