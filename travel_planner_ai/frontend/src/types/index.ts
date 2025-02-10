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
  | 'nightlife';     // For evening entertainment

export interface Stop {
  destination: string;
  days: number;
}

export interface TripFormData {
  travelType: TravelType;
  departure: string;
  destination: string;
  startDate: string;
  endDate: string;
  adults: number;
  children: number;
  infants: number;
  intermediateStops: Stop[];
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