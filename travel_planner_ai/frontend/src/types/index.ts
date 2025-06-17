export type TravelType = 'road' | 'flight' | 'train' | 'cruise';
export type BudgetLevel = 'budget' | 'mid-range' | 'luxury';
export type EntertainmentPreference = 
  | 'outdoor' 
  | 'cultural' 
  | 'relax' 
  | 'family-friendly' 
  | 'shopping'      // Local markets, boutiques, crafts
  | 'adventure'     // For thrill-seeking activities
  | 'nightlife'
  | 'must-see'
  | 'hidden-gems'   // For lesser-known, highly-rated places
  | 'photoshoot';   // For photography-focused activities

export type PhotoshootMode = 'nature' | 'architecture' | 'local' | 'kids' | 'wildlife' | 'insta-blogger';

export interface PhotoshootSettings {
  mode?: PhotoshootMode;
  instagramHandle?: string; // Only used when mode is 'insta-blogger'
}

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
  exclusionRadius?: number;
  exclusionUnit?: 'miles' | 'km';
  excludeFood?: boolean;
  photoshootSettings?: PhotoshootSettings;
}

export interface Activity {
  id: string;
  time: string;
  description: string;
  type: string;
  photoTips?: string; // Photography tips for this location
  bestPhotoTime?: string; // Optimal time for photography
  viewpoints?: string[]; // Recommended viewpoints/angles
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