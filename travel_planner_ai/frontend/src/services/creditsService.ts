import { API_BASE_URL } from './config';

export const getUserCredits = async (userId: string) => {
  try {
    console.log(`Fetching credits for user ID: ${userId}`);
    const response = await fetch(`${API_BASE_URL}/credits/${userId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.text();
      console.error('Error response:', errorData);
      throw new Error(`Failed to fetch user credits: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching user credits:', error);
    throw error;
  }
};

// For future Stripe implementation
export const createPaymentIntent = async (packageId: string, quantity: number = 1) => {
  try {
    const response = await fetch(`${API_BASE_URL}/credits/payment-intent`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        package_id: packageId,
        quantity
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to create payment intent');
    }

    return await response.json();
  } catch (error) {
    console.error('Error creating payment intent:', error);
    throw error;
  }
};

// Credit packages
export const CREDIT_PACKAGES = [
  {
    id: 'basic',
    name: 'Basic',
    credits: 10,
    price: 4.99,
    currency: 'USD',
  },
  {
    id: 'premium',
    name: 'Premium',
    credits: 100,
    price: 39.99,
    currency: 'USD',
  },
]; 