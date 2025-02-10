import * as React from 'react';
import { useState } from 'react';
import { Form, Button, Container, Row, Col, Badge } from 'react-bootstrap';
import { TripFormData, TravelType, EntertainmentPreference } from '../types';

interface TripFormProps {
  onSubmit: (data: TripFormData) => void;
  isLoading: boolean;
}

const TripForm: React.FC<TripFormProps> = ({ onSubmit, isLoading }) => {
  const [formData, setFormData] = useState<TripFormData>({
    travelType: 'flight',
    departure: '',
    destination: '',
    startDate: '',
    endDate: '',
    adults: 1,
    children: 0,
    infants: 0,
    intermediateStops: [],
    entertainmentPreferences: [],
    budgetLevel: 'mid-range',
    language: 'en'
  });

  const [newStop, setNewStop] = useState('');

  const addIntermediateStop = () => {
    if (newStop) {
      setFormData({
        ...formData,
        intermediateStops: [...formData.intermediateStops, newStop]
      });
      setNewStop('');
    }
  };

  const removeStop = (index: number) => {
    setFormData({
      ...formData,
      intermediateStops: formData.intermediateStops.filter((_, i) => i !== index)
    });
  };

  const togglePreference = (pref: EntertainmentPreference) => {
    const newPrefs = formData.entertainmentPreferences.includes(pref)
      ? formData.entertainmentPreferences.filter(p => p !== pref)
      : [...formData.entertainmentPreferences, pref];
    setFormData({ ...formData, entertainmentPreferences: newPrefs });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <Form onSubmit={handleSubmit} className="p-3">
      {/* Travel Type */}
      <Form.Group className="mb-3">
        <Form.Label>Travel Type</Form.Label>
        <Form.Select
          value={formData.travelType}
          onChange={(e) => setFormData({...formData, travelType: e.target.value as TravelType})}
        >
          <option value="road">Road Trip</option>
          <option value="flight">Flight</option>
          <option value="train">Train</option>
          <option value="cruise">Cruise</option>
        </Form.Select>
      </Form.Group>

      {/* Departure & Destination */}
      <Row className="mb-3">
        <Col md={6}>
          <Form.Group>
            <Form.Label>From</Form.Label>
            <Form.Control
              type="text"
              value={formData.departure}
              onChange={(e) => setFormData({...formData, departure: e.target.value})}
              required
            />
          </Form.Group>
        </Col>
        <Col md={6}>
          <Form.Group>
            <Form.Label>To</Form.Label>
            <Form.Control
              type="text"
              value={formData.destination}
              onChange={(e) => setFormData({...formData, destination: e.target.value})}
              required
            />
          </Form.Group>
        </Col>
      </Row>

      {/* Dates */}
      <Row className="mb-3">
        <Col md={6}>
          <Form.Group>
            <Form.Label>Start Date</Form.Label>
            <Form.Control
              type="date"
              value={formData.startDate}
              onChange={(e) => setFormData({...formData, startDate: e.target.value})}
              required
            />
          </Form.Group>
        </Col>
        <Col md={6}>
          <Form.Group>
            <Form.Label>End Date</Form.Label>
            <Form.Control
              type="date"
              value={formData.endDate}
              onChange={(e) => setFormData({...formData, endDate: e.target.value})}
              required
            />
          </Form.Group>
        </Col>
      </Row>

      {/* Travelers */}
      <Row className="mb-3">
        <Col md={4}>
          <Form.Group>
            <Form.Label>Adults</Form.Label>
            <Form.Control
              type="number"
              min="1"
              value={formData.adults}
              onChange={(e) => setFormData({...formData, adults: parseInt(e.target.value)})}
            />
          </Form.Group>
        </Col>
        <Col md={4}>
          <Form.Group>
            <Form.Label>Children</Form.Label>
            <Form.Control
              type="number"
              min="0"
              value={formData.children}
              onChange={(e) => setFormData({...formData, children: parseInt(e.target.value)})}
            />
          </Form.Group>
        </Col>
        <Col md={4}>
          <Form.Group>
            <Form.Label>Infants</Form.Label>
            <Form.Control
              type="number"
              min="0"
              value={formData.infants}
              onChange={(e) => setFormData({...formData, infants: parseInt(e.target.value)})}
            />
          </Form.Group>
        </Col>
      </Row>

      {/* Intermediate Stops */}
      <Form.Group className="mb-3">
        <Form.Label>Intermediate Stops</Form.Label>
        <div className="d-flex gap-2 mb-2">
          <Form.Control
            type="text"
            value={newStop}
            onChange={(e) => setNewStop(e.target.value)}
            placeholder="Add a stop"
          />
          <Button onClick={addIntermediateStop} variant="outline-secondary">Add</Button>
        </div>
        <div className="d-flex flex-wrap gap-2">
          {formData.intermediateStops.map((stop, index) => (
            <Badge 
              key={index} 
              bg="secondary" 
              className="d-flex align-items-center p-2"
            >
              {stop}
              <Button 
                variant="link" 
                className="p-0 ms-2 text-light" 
                onClick={() => removeStop(index)}
              >
                ×
              </Button>
            </Badge>
          ))}
        </div>
      </Form.Group>

      {/* Entertainment Preferences */}
      <Form.Group className="mb-3">
        <Form.Label>Entertainment Preferences</Form.Label>
        <div className="d-flex flex-wrap gap-2">
          {['outdoor', 'cultural', 'relaxation', 'family-friendly', 'food'].map((pref) => (
            <Button
              key={pref}
              variant={formData.entertainmentPreferences.includes(pref as EntertainmentPreference) ? 'primary' : 'outline-primary'}
              onClick={() => togglePreference(pref as EntertainmentPreference)}
              size="sm"
            >
              {pref}
            </Button>
          ))}
        </div>
      </Form.Group>

      {/* Budget Level */}
      <Form.Group className="mb-3">
        <Form.Label>Budget Level</Form.Label>
        <div className="d-flex gap-2">
          {['budget', 'mid-range', 'luxury'].map((level) => (
            <Button
              key={level}
              variant={formData.budgetLevel === level ? 'success' : 'outline-success'}
              onClick={() => setFormData({...formData, budgetLevel: level as any})}
            >
              {level}
            </Button>
          ))}
        </div>
      </Form.Group>

      {/* Language */}
      <Form.Group className="mb-4">
        <Form.Label>Language</Form.Label>
        <Form.Select
          value={formData.language}
          onChange={(e) => setFormData({...formData, language: e.target.value})}
        >
          <option value="en">English</option>
          <option value="es">Spanish</option>
          <option value="fr">French</option>
          <option value="de">German</option>
          <option value="it">Italian</option>
          <option value="ru">Russian</option>
        </Form.Select>
      </Form.Group>

      <Button type="submit" disabled={isLoading} className="w-100">
        {isLoading ? 'Generating Itinerary...' : 'Plan My Trip'}
      </Button>
    </Form>
  );
};

export default TripForm; 