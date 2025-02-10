export type TravelType = 'road' | 'flight' | 'train' | 'cruise';
export type BudgetLevel = 'budget' | 'mid-range' | 'luxury';
export type EntertainmentPreference = 'outdoor' | 'cultural' | 'relaxation' | 'family-friendly' | 'food';

export interface TripFormData {
  travelType: TravelType;
  departure: string;
  destination: string;
  startDate: string;
  endDate: string;
  adults: number;
  children: number;
  infants: number;
  intermediateStops: string[];
  entertainmentPreferences: EntertainmentPreference[];
  budgetLevel: BudgetLevel;
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