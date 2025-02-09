// src/App.js
import React, { useState } from 'react';
import TripForm from './components/TripForm';
import ItineraryDisplay from './components/ItineraryDisplay';
import { Container, Row, Col, Alert, Spinner } from 'react-bootstrap';

function App() {
  const [itinerary, setItinerary] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  return (
    <Container className="mt-5">
      <Row>
        <Col>
          <h1 className="mb-4">Travel Planner AI</h1>
        </Col>
      </Row>
      {error && (
        <Row>
          <Col>
            <Alert variant="danger" onClose={() => setError(null)} dismissible>
              {error}
            </Alert>
          </Col>
        </Row>
      )}
      <Row>
        <Col md={6}>
          <TripForm setItinerary={setItinerary} setError={setError} setLoading={setLoading} />
        </Col>
        <Col md={6}>
          {loading && <Spinner animation="border" variant="primary" />}
          {itinerary && <ItineraryDisplay itinerary={itinerary} />}
        </Col>
      </Row>
    </Container>
  );
}

export default App;
