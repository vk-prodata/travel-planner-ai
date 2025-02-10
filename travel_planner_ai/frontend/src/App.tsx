import * as React from 'react';
import { useState } from 'react';
import { Container, Row, Col, Button } from 'react-bootstrap';
import TripForm from './components/TripForm';
import Itinerary from './components/Itinerary';
import { TripFormData, TripItinerary } from './types';
import 'bootstrap/dist/css/bootstrap.min.css';
import { FaPlaneDeparture } from 'react-icons/fa';

const mockItinerary = {
  tripId: '123',
  days: [
    {
      date: 'April 16',
      activities: [
        {
          id: '1',
          time: '7:00 AM',
          description: 'Arrive in Orlando',
          type: 'travel'
        },
        {
          id: '2',
          time: '8:00 AM',
          description: 'Pick up your rental car; drive ~1.5–2 hours to Tampa/Dunedin area',
          type: 'travel'
        },
        {
          id: '3',
          time: '10:30 AM',
          description: 'Honeymoon Island State Park (near Dunedin). Entry fee: $8 per vehicle. Large sandy beaches, shallow areas for splashing, lots of shorebirds.',
          type: 'outdoor'
        },
        {
          id: '4',
          time: '12:30 PM',
          description: 'Slavic Lunch option: Pierogi Grill in Clearwater for family-friendly Polish food',
          type: 'food'
        },
        {
          id: '5',
          time: '1:30 PM',
          description: 'Head to St. Petersburg. Weedon Island Preserve for a nature boardwalk and optional kayak rentals',
          type: 'outdoor'
        },
        {
          id: '6',
          time: '4:30 PM',
          description: 'Drive to Tampa and check in to your hotel',
          type: 'travel'
        },
        {
          id: '7',
          time: '6:00 PM',
          description: 'Tampa Riverwalk - scenic walkway with street performers, splash pad and playground at Water Works Park, Pirate Water Taxi ride option',
          type: 'entertainment'
        },
        {
          id: '8',
          time: '7:30 PM',
          description: 'Dinner in Tampa. Options: Babushka\'s Hyde Park (Slavic) or Downtown/Ybor City for seafood/Cuban',
          type: 'food'
        }
      ]
    },
    {
      date: 'April 17',
      activities: [
        {
          id: '9',
          time: '8:00 AM',
          description: 'Breakfast near your hotel',
          type: 'food'
        },
        {
          id: '10',
          time: '9:00 AM',
          description: 'Hillsborough River State Park. Easy trails, turtle and alligator sightings, suspension bridge. Entry: $6 per vehicle',
          type: 'outdoor'
        },
        {
          id: '11',
          time: '11:00 AM',
          description: 'Drive to Sarasota (1-1.5 hours)',
          type: 'travel'
        },
        {
          id: '12',
          time: '12:30 PM',
          description: 'Lunch in Sarasota Downtown - casual cafes and outdoor spots',
          type: 'food'
        },
        {
          id: '13',
          time: '2:00 PM',
          description: 'Beach time at Siesta Key Beach or Lido Key Beach. White sand, shallow waters, perfect for families',
          type: 'outdoor'
        },
        {
          id: '14',
          time: '4:30 PM',
          description: 'Myakka River State Park - nature trails, canopy walkway, wildlife spotting. Entry: $6',
          type: 'outdoor'
        },
        {
          id: '15',
          time: '6:30 PM',
          description: 'Dinner in Sarasota - seafood, BBQ, or family-friendly international spots',
          type: 'food'
        }
      ]
    }
  ]
};

// Mock alternative suggestions
const mockAlternatives = {
  'food': [
    'Try local food trucks gathering - variety of cuisines, casual atmosphere',
    'Visit the International Food Court - multiple options under one roof',
    'Family-style Italian restaurant with kids menu and activities'
  ],
  'outdoor': [
    'Indoor adventure park - perfect backup for rainy weather',
    'Interactive museum with hands-on exhibits',
    'Botanical gardens with butterfly house'
  ],
  'entertainment': [
    'Local theater with family-friendly shows',
    'Arcade and gaming center',
    'Indoor trampoline park'
  ],
  'travel': [
    'Alternative scenic route with photo stops',
    'Public transport option with city views',
    'Private shuttle service'
  ]
};

const App = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [itinerary, setItinerary] = useState<TripItinerary | null>(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [formData, setFormData] = useState<TripFormData | null>(null);

  const handleSignIn = () => setIsLoggedIn(true);
  const handleSignOut = () => setIsLoggedIn(false);

  const handleSubmit = async (data: TripFormData) => {
    setIsLoading(true);
    setFormData(data);
    setTimeout(() => {
      setItinerary(mockItinerary);
      setIsLoading(false);
    }, 1500);
  };

  return (
    <Container fluid className="p-0">
      <Row className="g-0">
        {/* Left Section - Filters and Auth */}
        <Col md={4} className="border-end shadow-sm" style={{ maxHeight: '100vh', overflowY: 'auto' }}>
          <div className="p-3 bg-white">
            <h2 className="text-primary-dark mb-3 d-flex align-items-center fs-4">
              <FaPlaneDeparture className="me-2 text-secondary" size={20} />
              Travel Planner AI
            </h2>
            <div className="bg-light p-2 rounded shadow-sm mb-3">
              <h5 className="text-primary-dark mb-2 fs-6">Plan Your Trip</h5>
              <TripForm onSubmit={handleSubmit} isLoading={isLoading} />
            </div>
            <div className="mt-3 pt-2 border-top">
              {!isLoggedIn ? (
                <div className="d-flex gap-2">
                  <Button variant="outline-primary" onClick={handleSignIn} className="shadow-sm flex-grow-1" size="sm">
                    Sign In
                  </Button>
                  <Button variant="primary" onClick={handleSignIn} className="shadow-sm flex-grow-1" size="sm">
                    Sign Up
                  </Button>
                </div>
              ) : (
                <div className="d-flex align-items-center justify-content-between">
                  <span className="text-primary-dark">Welcome back!</span>
                  <Button 
                    variant="outline-danger" 
                    size="sm" 
                    onClick={handleSignOut}
                    className="shadow-sm"
                  >
                    Sign Out
                  </Button>
                </div>
              )}
            </div>
          </div>
        </Col>

        {/* Right Section - Trip Info */}
        <Col md={8} className="bg-light">
          <div className="p-4">
            {isLoading ? (
              <div className="text-center py-5">
                <div className="spinner-border text-primary" role="status">
                  <span className="visually-hidden">Loading...</span>
                </div>
                <p className="mt-2 text-primary-dark">Generating your perfect trip...</p>
              </div>
            ) : itinerary ? (
              <div>
                <h3 className="text-primary-dark mb-4">
                  Trip to {itinerary.days[0].activities[0].description.split('→')[1]?.trim() || 'Your Destination'}
                </h3>
                <Itinerary 
                  itinerary={itinerary}
                  onActivityUpdate={() => {}}
                  onSuggestAlternative={() => {}}
                  alternatives={mockAlternatives}
                />
              </div>
            ) : (
              <div className="text-center py-5">
                <div className="bg-white p-5 rounded shadow-sm">
                  <h3 className="text-primary-dark mb-3">Plan Your Dream Trip</h3>
                  <p className="text-secondary mb-4">Fill out the form to get your personalized travel itinerary</p>
                  <div className="text-center">
                    <FaPlaneDeparture size={100} className="text-secondary opacity-50" />
                  </div>
                </div>
              </div>
            )}
          </div>
        </Col>
      </Row>
    </Container>
  );
};

export default App;