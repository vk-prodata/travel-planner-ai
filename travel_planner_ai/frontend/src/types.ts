// User related types
export interface User {
  id: string;
  email: string;
  name: string;
  availableCredits?: number;
  totalCreditsPurchased?: number;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface SignupData extends LoginData {
  name: string;
}

// AI provider type
export type AIProvider = 'openai' | 'deepseek';

// Trip related types
export interface Activity {
  id?: string; // TODO: Deprecated Activity ID June 2025 - no longer generated or used
  time: string;
  description: string;
  type: string;
  location?: string;
  coordinates?: { // TODO: Deprecated Coordinates June 2025 - no longer generated or used for maps
    latitude: number;
    longitude: number;
  } | string; // Support both object format and string format for backward compatibility
  price?: PriceLevel;
  why?: string;
}

export interface Day {
  date: string;
  activities: Activity[];
}

export interface TripItinerary {
  tripId: string;
  title?: string;
  isOwner?: boolean;
  days: {
    date: string;
    activities: Activity[];
  }[];
}

export interface Stop {
  destination: string;
  startDate: string;
  days: number;
}

export type TravelType = 'flight' | 'train' | 'road' | 'bus' | 'cruise';

export type EntertainmentPreference = 'outdoor' | 'cultural' | 'relaxation' | 'family-friendly' | 'food' | 'adventure' | 'educational' | 'nightlife' | 'must-see' | 'hidden-gems';

export type CuisineType = 
  | 'any' 
  | 'local' 
  | 'international' 
  | 'vegetarian' 
  | 'vegan' 
  | 'halal' 
  | 'kosher' 
  | 'seafood' 
  | 'mediterranean' 
  | 'asian' 
  | 'european' 
  | 'american' 
  | 'mexican' 
  | 'japanese' 
  | 'italian' 
  | 'slavic' 
  | 'indian' 
  | 'thai';

export interface TripFormData {
  travelType: TravelType;
  origin?: string;
  destination: string;
  startDate: string;
  endDate: string;
  adults: number;
  children?: number;
  infants?: number;
  intermediateStops?: Stop[];
  entertainmentPreferences?: EntertainmentPreference[];
  budgetLevel: BudgetLevel;
  budget: string;
  language: string;
  cuisinePreference: CuisineType;
  aiProvider?: AIProvider;
}

export type BudgetLevel = 'budget' | 'mid-range' | 'luxury';

export interface TripHash {
  userId: string;
  origin: string;
  destination: string;
  startDate: string;
  endDate: string;
}

export type PriceLevel = 'free' | '$' | '$$' | '$$$';

export interface DailyItinerary {
  date: string;
  activities: Activity[];
}

export interface TripItinerary {
  tripId: string;
  days: DailyItinerary[];
  hotels?: string[];
  generated_at?: string;
}

export interface SavedTrip {
  id: string;
  user_id: string;
  formData: TripFormData;
  itinerary: TripItinerary;
  created_at?: string;
  updated_at?: string;
  isOwner?: boolean;
} 