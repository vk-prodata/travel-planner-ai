import * as React from 'react';
import { useState } from 'react';
import { Form, Button, Row, Col, Badge, OverlayTrigger, Tooltip } from 'react-bootstrap';
import { TripFormData, TravelType, EntertainmentPreference, Stop, BudgetLevel } from '../types';
import { FaInfoCircle, FaPlus } from 'react-icons/fa';

interface TripFormProps {
  onSubmit: (data: TripFormData) => void;
  isLoading: boolean;
}

const TripForm: React.FC<TripFormProps> = ({ onSubmit, isLoading }) => {
  const [formData, setFormData] = useState<TripFormData>({
    travelType: 'flight',
    origin: '',
    destination: '',
    startDate: '',
    endDate: '',
    adults: 1,
    children: 0,
    infants: 0,
    intermediateStops: [],
    entertainmentPreferences: [],
    budget: 'mid-range',
    budgetLevel: 'mid-range',
    language: 'en'
  });

  const [newStop, setNewStop] = useState<Stop>({ destination: '', days: 1 });

  const addIntermediateStop = () => {
    if (newStop.destination) {
      setFormData({
        ...formData,
        intermediateStops: [...formData.intermediateStops, newStop]
      });
      setNewStop({ destination: '', days: 1 });
    }
  };

  const removeStop = (index: number) => {
    setFormData({
      ...formData,
      intermediateStops: formData.intermediateStops.filter((_: Stop, i: number) => i !== index)
    });
  };

  const togglePreference = (pref: EntertainmentPreference) => {
    const newPrefs = formData.entertainmentPreferences.includes(pref)
      ? formData.entertainmentPreferences.filter((p: EntertainmentPreference) => p !== pref)
      : [...formData.entertainmentPreferences, pref];
    setFormData({ ...formData, entertainmentPreferences: newPrefs });
  };

  const handleBudgetLevelChange = (level: BudgetLevel) => {
    setFormData({
      ...formData,
      budgetLevel: level,
      budget: level
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <Form onSubmit={handleSubmit} className="p-2">
      {/* Travel Type */}
      <Form.Group className="mb-2">
        <Form.Label className="text-secondary fw-bold small">Travel Type</Form.Label>
        <Form.Select
          className="shadow-sm"
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
      <Row className="mb-4">
        <Col md={6}>
          <Form.Group>
            <Form.Label className="text-secondary fw-bold">From</Form.Label>
            <Form.Control
              className="shadow-sm"
              type="text"
              value={formData.origin}
              onChange={(e) => setFormData({...formData, origin: e.target.value})}
              required
            />
          </Form.Group>
        </Col>
        <Col md={6}>
          <Form.Group>
            <Form.Label className="text-secondary fw-bold">To</Form.Label>
            <Form.Control
              className="shadow-sm"
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
            <Form.Label className="d-flex align-items-center">
              Adults
              <span style={{ cursor: 'help' }}>
                <OverlayTrigger
                  placement="top"
                  trigger={['hover', 'focus']}
                  overlay={<Tooltip id={`adults-tooltip`}>Age 12 and above</Tooltip>}
                >
                  <FaInfoCircle className="ms-2 text-secondary" size={14} />
                </OverlayTrigger>
              </span>
            </Form.Label>
            <Form.Control
              className="shadow-sm"
              type="number"
              min="1"
              value={formData.adults}
              onChange={(e) => setFormData({...formData, adults: parseInt(e.target.value)})}
            />
          </Form.Group>
        </Col>
        <Col md={4}>
          <Form.Group>
            <Form.Label className="d-flex align-items-center">
              Children
              <span style={{ cursor: 'help' }}>
                <OverlayTrigger
                  placement="top"
                  trigger={['hover', 'focus']}
                  overlay={<Tooltip id={`children-tooltip`}>Age 2-11</Tooltip>}
                >
                  <FaInfoCircle className="ms-2 text-secondary" size={14} />
                </OverlayTrigger>
              </span>
            </Form.Label>
            <Form.Control
              className="shadow-sm"
              type="number"
              min="0"
              value={formData.children}
              onChange={(e) => setFormData({...formData, children: parseInt(e.target.value)})}
            />
          </Form.Group>
        </Col>
        <Col md={4}>
          <Form.Group>
            <Form.Label className="d-flex align-items-center">
              Infants
              <span style={{ cursor: 'help' }}>
                <OverlayTrigger
                  placement="top"
                  trigger={['hover', 'focus']}
                  overlay={<Tooltip id={`infants-tooltip`}>Under 2 years</Tooltip>}
                >
                  <FaInfoCircle className="ms-2 text-secondary" size={14} />
                </OverlayTrigger>
              </span>
            </Form.Label>
            <Form.Control
              className="shadow-sm"
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
        <Form.Label className="d-flex align-items-center">
          Intermediate Stops
          <OverlayTrigger
            placement="top"
            overlay={<Tooltip>Add locations you want to visit during your trip</Tooltip>}
          >
            <FaInfoCircle className="ms-2 text-secondary" size={14} />
          </OverlayTrigger>
        </Form.Label>
        <div className="d-flex gap-2 mb-2">
          <Form.Control
            type="text"
            value={newStop.destination}
            onChange={(e) => setNewStop({ ...newStop, destination: e.target.value })}
            placeholder="City/Location"
            className="flex-grow-1 shadow-sm"
          />
          <Form.Control
            type="number"
            min="1"
            value={newStop.days}
            onChange={(e) => setNewStop({ ...newStop, days: parseInt(e.target.value) })}
            placeholder="Days"
            className="shadow-sm"
            style={{ width: '70px' }}
          />
          <Button 
            onClick={addIntermediateStop} 
            variant="outline-primary" 
            className="shadow-sm d-flex align-items-center justify-content-center"
            style={{ width: '36px', height: '36px', padding: 0 }}
          >
            <FaPlus size={12} />
          </Button>
        </div>
        <div className="d-flex flex-wrap gap-2">
          {formData.intermediateStops.map((stop: Stop, index: number) => (
            <Badge key={index} bg="secondary" className="d-flex align-items-center p-2">
              {stop.destination} ({stop.days} {stop.days === 1 ? 'day' : 'days'})
              <Button variant="link" className="p-0 ms-2 text-light" onClick={() => removeStop(index)}>×</Button>
            </Badge>
          ))}
        </div>
      </Form.Group>

      {/* Entertainment Preferences */}
      <Form.Group className="mb-3">
        <Form.Label>Entertainment Preferences</Form.Label>
        <div className="d-flex flex-wrap gap-2">
          {[
            'outdoor',
            'cultural',
            'relaxation',
            'family-friendly',
            'food',
            'adventure',
            'educational',
            'nightlife',
            'hidden-gems',
            'must-see'
          ].map((pref) => (
            <Button
              key={pref}
              variant={formData.entertainmentPreferences.includes(pref as EntertainmentPreference) ? 'primary' : 'outline-primary'}
              onClick={() => togglePreference(pref as EntertainmentPreference)}
              size="sm"
              className="text-capitalize"
            >
              {pref.replace('-', ' ')}
            </Button>
          ))}
        </div>
      </Form.Group>

      {/* Budget Level */}
      <Form.Group className="mb-3">
        <Form.Label>Budget Level</Form.Label>
        <div className="d-flex gap-2">
          {(['budget', 'mid-range', 'luxury'] as BudgetLevel[]).map((level) => (
            <Button
              key={level}
              variant={formData.budgetLevel === level ? 'success' : 'outline-success'}
              onClick={() => handleBudgetLevelChange(level)}
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
          className="shadow-sm"
          value={formData.language}
          onChange={(e) => setFormData({...formData, language: e.target.value})}
        >
          <option value="en">English</option>
          <option value="es">Spanish (Español)</option>
          <option value="fr">French (Français)</option>
          <option value="de">German (Deutsch)</option>
          <option value="it">Italian (Italiano)</option>
          <option value="ru">Russian (Русский)</option>
          <option value="zh">Chinese (中文)</option>
        </Form.Select>
      </Form.Group>

      <Button 
        type="submit" 
        disabled={isLoading} 
        className="w-100 shadow-sm py-2"
      >
        {isLoading ? (
          <>
            <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            Generating Itinerary...
          </>
        ) : (
          'Plan My Trip'
        )}
      </Button>
    </Form>
  );
};

export default TripForm; 