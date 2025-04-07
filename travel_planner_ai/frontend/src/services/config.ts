// Base URL for API calls
export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Stripe configuration
export const STRIPE_TEST_MODE = true;
export const STRIPE_TEST_CARDS = {
  success: '4242 4242 4242 4242', // Always succeeds
  decline: '4000 0000 0000 0002', // Always gets declined
  requires3dSecure: '4000 0025 0000 3155', // Requires 3D Secure authentication
  insufficient: '4000 0000 0000 9995' // Insufficient funds
}; 