export type TravelType = 'road' | 'flight' | 'train' | 'cruise';
export type BudgetLevel = 'budget' | 'mid-range' | 'luxury';
export type EntertainmentPreference = 
  | 'outdoor' 
  | 'cultural' 
  | 'relaxation' 
  | 'family-friendly' 
  | 'food'
  | 'adventure'      // For thrill-seeking activities
  | 'educational'    // For museums, workshops, etc.
  | 'nightlife'
  | 'must-see';      // Add new option

export interface Stop {
  destination: string;
  startDate: string;
  days: number;
}

export interface TripFormData {
  travelType: TravelType;
  origin?: string;
  destination: string;
  startDate: string;
  endDate: string;
  adults: number;
  children: number;
  infants: number;
  intermediateStops: Stop[];
  entertainmentPreferences: EntertainmentPreference[];
  budgetLevel: BudgetLevel;
  budget: string;  // Keep this for now since it's used in the backend
  language: string;
}

export interface Activity {
  id: string;
  time: string;
  description: string;
  type: string;
}

export interface TripItinerary {
  tripId: string;
  days: {
    date: string;
    activities: Activity[];
  }[];
}

export interface User {
  id: string;
  email: string;
  name: string;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface SignupData extends LoginData {
  name: string;
} 