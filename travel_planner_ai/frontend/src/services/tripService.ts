import { TripItinerary, TripFormData } from '../types';
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
  itinerary: TripItinerary;
  formData: TripFormData;
  userId: string;
}) => {
  try {
    console.log('Saving trip with data:', {
      userId: tripData.userId,
      destination: tripData.formData.destination,
      startDate: tripData.formData.startDate,
      endDate: tripData.formData.endDate,
      itineraryDays: tripData.itinerary?.days?.length || 0,
      formDataKeys: Object.keys(tripData.formData),
      itineraryKeys: Object.keys(tripData.itinerary || {})
    });

    // Validate itinerary before sending
    if (!tripData.itinerary || !tripData.itinerary.days) {
      console.error('Invalid itinerary structure:', tripData.itinerary);
      throw new Error('Invalid itinerary structure. Please regenerate your itinerary.');
    }

    console.log('Request payload:', JSON.stringify(tripData, null, 2));

    const response = await fetch(`${API_URL}/trips`, {
      method: 'POST',
      headers: getAuthHeaders(),
      credentials: 'include',
      body: JSON.stringify(tripData),
    });

    console.log('Save trip response status:', response.status);
    console.log('Save trip response headers:', Object.fromEntries(response.headers.entries()));

    if (!response.ok) {
      const errorData = await response.json().catch(() => {
        console.error('Failed to parse error response as JSON');
        return null;
      });
      
      console.error('Save trip error details:', errorData);
      
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
    console.log('Trip saved successfully:', {
      id: savedTrip.id,
      destination: savedTrip.formData?.destination,
      hasItinerary: !!savedTrip.itinerary,
      itineraryDays: savedTrip.itinerary?.days?.length || 0,
      responseData: JSON.stringify(savedTrip, null, 2)
    });
    return savedTrip;
  } catch (error) {
    console.error('Error saving trip:', error);
    const userEmail = localStorage.getItem('userEmail');
    notifyError(error, userEmail);
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

export const getUserTrips = async (userId: string): Promise<any[]> => {
  try {
    const response = await fetch(`${API_URL}/trips/user/${userId}`, {
      headers: getAuthHeaders(),
      credentials: 'include',
    });

    if (!response.ok) {
      console.error(`Failed to fetch trips: ${response.status} ${response.statusText}`);
      throw new Error(`Failed to fetch trips: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching trips:', error);
    const userEmail = localStorage.getItem('userEmail');
    notifyError(error, userEmail);
    throw error;
  }
}; 