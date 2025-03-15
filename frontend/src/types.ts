// User related types
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

// Trip related types
export interface Activity {
  id: string;
  time: string;
  description: string;
  type: string;
}

export interface Day {
  date: string;
  activities: Activity[];
}

export interface TripItinerary {
  tripId: string;
  days: Day[];
}

export interface Stop {
  destination: string;
  days: number;
}

export type TravelType = 'flight' | 'train' | 'car' | 'bus' | 'cruise';

export type EntertainmentPreference = 
  | 'family-friendly'
  | 'cultural'
  | 'outdoor'
  | 'nightlife'
  | 'shopping'
  | 'relaxation';

export interface TripFormData {
  origin?: string;
  destination: string;
  startDate: string;
  endDate: string;
  travelType: TravelType;
  adults: number;
  children: number;
  infants: number;
  budget: string;
  budgetLevel: 'budget' | 'mid-range' | 'luxury';
  language: string;
  entertainmentPreferences: EntertainmentPreference[];
  intermediateStops: Stop[];
  notes?: string;
}

export type BudgetLevel = 'budget' | 'mid-range' | 'luxury';

export interface TripHash {
  userId: string;
  origin: string;
  destination: string;
  startDate: string;
  endDate: string;
} 