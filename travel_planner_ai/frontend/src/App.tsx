import * as React from 'react';
import { useState } from 'react';
import { Container, Row, Col, Button } from 'react-bootstrap';
import TripForm from './components/TripForm';
import Itinerary from './components/Itinerary';
import { TripFormData, TripItinerary } from './types';
import 'bootstrap/dist/css/bootstrap.min.css';

const App = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [itinerary, setItinerary] = useState<TripItinerary | null>(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const handleSubmit = async (data: TripFormData) => {
    setIsLoading(true);
    setTimeout(() => {
      setItinerary({
        tripId: '123',
        days: [
          {
            date: '2024-02-20',
            activities: [
              {
                id: '1',
                time: '09:00',
                description: 'Breakfast at local café',
                type: 'food'
              }
            ]
          }
        ]
      });
      setIsLoading(false);
    }, 1500);
  };

  return (
    <Container fluid className="py-4">
      <Row>
        {/* Left Section - Filters and Auth */}
        <Col md={4} className="border-end">
          <div className="mb-4">
            <h2>Travel Planner AI</h2>
            {!isLoggedIn ? (
              <div className="d-grid gap-2 mb-4">
                <Button variant="outline-primary">Sign In</Button>
                <Button variant="primary">Sign Up</Button>
              </div>
            ) : (
              <div className="mb-4">
                <p>Welcome back!</p>
                <Button variant="outline-danger" size="sm">
                  Sign Out
                </Button>
              </div>
            )}
          </div>
          <TripForm onSubmit={handleSubmit} isLoading={isLoading} />
        </Col>

        {/* Right Section - Trip Info */}
        <Col md={8}>
          {isLoading ? (
            <div className="text-center py-5">
              <div className="spinner-border text-primary" role="status">
                <span className="visually-hidden">Loading...</span>
              </div>
              <p className="mt-2">Generating your perfect trip...</p>
            </div>
          ) : itinerary ? (
            <div>
              <h3>Your Itinerary</h3>
              <Itinerary 
                itinerary={itinerary}
                onActivityUpdate={() => {}}
                onSuggestAlternative={() => {}}
              />
            </div>
          ) : (
            <div className="text-center py-5 text-muted">
              <h3>Plan Your Dream Trip</h3>
              <p>Fill out the form to get your personalized travel itinerary</p>
            </div>
          )}
        </Col>
      </Row>
    </Container>
  );
};

export default App;