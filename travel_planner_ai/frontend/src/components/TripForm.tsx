import React, { useState, useEffect, useCallback } from 'react';
import { useForm, Controller, SubmitHandler } from 'react-hook-form';
import { Form, Button, Row, Col, Spinner, Alert, OverlayTrigger, Tooltip, Accordion, Badge } from 'react-bootstrap';
import { FaPlaneDeparture, FaPlaneArrival, FaCalendarAlt, FaUsers, FaUtensils, FaHotel, FaLandmark, FaTheaterMasks, FaInfoCircle, FaPlus } from 'react-icons/fa';
import { TripFormData, TravelType, EntertainmentPreference, Stop, BudgetLevel, CuisineType } from '../types';

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
    budgetLevel: 'mid-range',
    budget: 'mid-range',
    language: 'en',
    cuisinePreference: 'any'
  });

  const [newStop, setNewStop] = useState<Stop>({ 
    destination: '', 
    startDate: '', 
    days: 1 
  });

  const [dateError, setDateError] = useState<string | null>(null);
  const [stopError, setStopError] = useState<string | null>(null);

  const addIntermediateStop = () => {
    if (!newStop.destination) {
      setStopError('Please enter a destination');
      return;
    }
    
    if (!newStop.startDate) {
      setStopError('Please select a start date');
      return;
    }
    
    // Validate that stop dates are within trip dates
    const stopStart = new Date(newStop.startDate);
    const stopEnd = new Date(newStop.startDate);
    stopEnd.setDate(stopEnd.getDate() + (newStop.days)- 1);
    
    const tripStart = new Date(formData.startDate);
    const tripEnd = new Date(formData.endDate);
    
    if (stopStart < tripStart || stopEnd > tripEnd) {
      setStopError('Stop dates must be within trip dates');
      return;
    }
    
    // Add the stop with the exact date selected
    setFormData({
      ...formData,
      intermediateStops: [...(formData.intermediateStops || []), newStop]
    });
    setNewStop({ destination: '', startDate: '', days: 1 });
    setStopError(null);
  };

  const removeStop = (index: number) => {
    setFormData({
      ...formData,
      intermediateStops: formData.intermediateStops?.filter((_: Stop, i: number) => i !== index) || []
    });
  };

  const togglePreference = (pref: EntertainmentPreference) => {
    const currentPrefs = formData.entertainmentPreferences || [];
    const newPrefs = currentPrefs.includes(pref)
      ? currentPrefs.filter((p: EntertainmentPreference) => p !== pref)
      : [...currentPrefs, pref];
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
    
    // Validate dates before submitting
    const start = new Date(formData.startDate);
    const end = new Date(formData.endDate);
    
    if (end < start) {
      setDateError('End date must be after start date');
      return;
    }
    
    setDateError(null);
    onSubmit(formData);
  };

  // Calculate the maximum allowed days for an intermediate stop based on selected start date
  const calculateMaxDays = (): number => {
    if (!newStop.startDate || !formData.endDate) return 1;
    
    const stopStart = new Date(newStop.startDate);
    const tripEnd = new Date(formData.endDate);
    
    // Calculate days difference (including the start day)
    const diffTime = tripEnd.getTime() - stopStart.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
    
    return Math.max(1, diffDays);
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
              onChange={(e) => {
                const newStartDate = e.target.value;
                
                // If end date is empty, set default end date to start date + 7 days
                if (!formData.endDate) {
                  const defaultEndDate = new Date(newStartDate);
                  defaultEndDate.setDate(defaultEndDate.getDate() + 7);
                  
                  // Format the date as YYYY-MM-DD for the input
                  const formattedEndDate = defaultEndDate.toISOString().split('T')[0];
                  
                  setFormData({...formData, startDate: newStartDate, endDate: formattedEndDate});
                  setDateError(null);
                }
                // If end date exists and is now before start date, update end date
                else if (new Date(formData.endDate) < new Date(newStartDate)) {
                  setFormData({...formData, startDate: newStartDate, endDate: newStartDate});
                  setDateError(null);
                } else {
                  setFormData({...formData, startDate: newStartDate});
                  setDateError(null);
                }
              }}
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
              min={formData.startDate} // Prevent selecting dates before start date
              onChange={(e) => {
                const newEndDate = e.target.value;
                setFormData({...formData, endDate: newEndDate});
                
                // Validate end date is after start date
                if (formData.startDate && new Date(newEndDate) < new Date(formData.startDate)) {
                  setDateError('End date must be after start date');
                } else {
                  setDateError(null);
                }
              }}
              required
              isInvalid={!!dateError}
            />
            <Form.Control.Feedback type="invalid">
              {dateError}
            </Form.Control.Feedback>
          </Form.Group>
        </Col>
      </Row>

      {/* Travelers */}
      <Form.Group className="mb-3">
        <div className="d-flex gap-3">
          <div>
            <Form.Label className="d-flex align-items-center gap-2">
              Adults
              <OverlayTrigger
                placement="top"
                trigger={['hover', 'focus', 'click']}
                overlay={(
                  <Tooltip id="adults-tooltip">
                    <div className="text-start">
                      <strong>Age 12+</strong>
                      <div>Full-fare passengers age 12 and older</div>
                      <div className="small text-muted mt-1">Example: Parents, teens</div>
                    </div>
                  </Tooltip>
                )}
              >
                <span style={{ cursor: 'pointer' }}>
                  <FaInfoCircle className="text-primary" size={16} />
                </span>
              </OverlayTrigger>
            </Form.Label>
            <Form.Control
              type="number"
              min="1"
              value={formData.adults}
              onChange={(e) => setFormData({ ...formData, adults: parseInt(e.target.value) })}
            />
          </div>
          <div>
            <Form.Label className="d-flex align-items-center gap-2">
              Children
              <OverlayTrigger
                placement="top"
                trigger={['hover', 'focus', 'click']}
                overlay={(
                  <Tooltip id="children-tooltip">
                    <div className="text-start">
                      <strong>Age 2-11</strong>
                      <div>Child passengers between 2 and 11 years old</div>
                      <div className="small text-muted mt-1">Example: School-age kids</div>
                    </div>
                  </Tooltip>
                )}
              >
                <span style={{ cursor: 'pointer' }}>
                  <FaInfoCircle className="text-primary" size={16} />
                </span>
              </OverlayTrigger>
            </Form.Label>
            <Form.Control
              type="number"
              min="0"
              value={formData.children}
              onChange={(e) => setFormData({ ...formData, children: parseInt(e.target.value) })}
            />
          </div>
          <div>
            <Form.Label className="d-flex align-items-center gap-2">
              Infants
              <OverlayTrigger
                placement="top"
                trigger={['hover', 'focus', 'click']}
                overlay={(
                  <Tooltip id="infants-tooltip">
                    <div className="text-start">
                      <strong>Under 2 years</strong>
                      <div>Infant passengers under 2 years old</div>
                      <div className="small text-muted mt-1">Example: Babies, toddlers</div>
                    </div>
                  </Tooltip>
                )}
              >
                <span style={{ cursor: 'pointer' }}>
                  <FaInfoCircle className="text-primary" size={16} />
                </span>
              </OverlayTrigger>
            </Form.Label>
            <Form.Control
              type="number"
              min="0"
              value={formData.infants}
              onChange={(e) => setFormData({ ...formData, infants: parseInt(e.target.value) })}
            />
          </div>
        </div>
      </Form.Group>

      {/* Advanced Settings Panel */}
      <Accordion className="mb-3">
        <Accordion.Item eventKey="0">
          <Accordion.Header>Advanced Settings</Accordion.Header>
          <Accordion.Body>
            {/* Intermediate Stops */}
            <Form.Group className="mb-3">
              <Form.Label className="d-flex align-items-center">
                Intermediate Stops
                <OverlayTrigger
                  placement="top"
                  overlay={<Tooltip id="stops-tooltip">Add locations you want to visit during your trip</Tooltip>}
                >
                  <span className="ms-2">
                    <FaInfoCircle className="text-secondary" size={14} />
                  </span>
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
                <div className="d-flex flex-column" style={{ width: '140px' }}>
                  <Form.Control
                    type="date"
                    value={newStop.startDate}
                    min={formData.startDate}
                    max={formData.endDate}
                    onChange={(e) => {
                      const newStartDate = e.target.value;
                      setNewStop({ ...newStop, startDate: newStartDate });
                      setStopError(null);
                    }}
                    placeholder="Start Date"
                    className="shadow-sm"
                    disabled={!formData.startDate || !formData.endDate}
                  />
                </div>
                <Form.Control
                  type="number"
                  min="1"
                  max={calculateMaxDays()}
                  value={newStop.days}
                  onChange={(e) => {
                    const days = parseInt(e.target.value);
                    setNewStop({ ...newStop, days });
                    setStopError(null);
                  }}
                  placeholder="Days"
                  className="shadow-sm"
                  style={{ width: '70px' }}
                />
                <Button 
                  onClick={addIntermediateStop} 
                  variant="outline-primary" 
                  className="shadow-sm d-flex align-items-center justify-content-center"
                  style={{ width: '36px', height: '36px', padding: 0 }}
                  disabled={!formData.startDate || !formData.endDate}
                >
                  <FaPlus size={12} />
                </Button>
              </div>
              {stopError && (
                <div className="text-danger mb-2 small">{stopError}</div>
              )}
              <div className="d-flex flex-wrap gap-2">
                {formData.intermediateStops?.map((stop: Stop, index: number) => (
                  <Badge key={index} bg="secondary" className="d-flex align-items-center p-2">
                    {stop.destination} {stop.startDate && new Date(stop.startDate).toLocaleDateString()} ({stop.days} {stop.days === 1 ? 'day' : 'days'})
                    <Button variant="link" className="p-0 ms-2 text-light" onClick={() => removeStop(index)}>×</Button>
                  </Badge>
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
                    variant={formData.budgetLevel === level ? 'primary' : 'outline-primary'}
                    onClick={() => handleBudgetLevelChange(level as BudgetLevel)}
                    className="text-capitalize"
                  >
                    {level}
                  </Button>
                ))}
              </div>
            </Form.Group>

            {/* Cuisine Preference */}
            <Form.Group className="mb-3">
              <Form.Label className="d-flex align-items-center">
                Café & Restaurant Preferences
                <OverlayTrigger
                  placement="top"
                  overlay={<Tooltip id="cuisine-tooltip">Select your preferred type of cuisine for restaurant recommendations</Tooltip>}
                >
                  <span className="ms-2">
                    <FaInfoCircle className="text-secondary" size={14} />
                  </span>
                </OverlayTrigger>
              </Form.Label>
              <Form.Select
                className="shadow-sm"
                value={formData.cuisinePreference}
                onChange={(e) => setFormData({...formData, cuisinePreference: e.target.value as CuisineType})}
              >
                <option value="any">Any Cuisine</option>
                <option value="local">Local/Traditional</option>
                <option value="international">International</option>
                <option value="vegetarian">Vegetarian</option>
                <option value="vegan">Vegan</option>
                <option value="halal">Halal</option>
                <option value="kosher">Kosher</option>
                <option value="seafood">Seafood</option>
                <option value="mediterranean">Mediterranean</option>
                <option value="asian">Asian</option>
                <option value="european">European</option>
                <option value="american">American</option>
                <option value="mexican">Mexican</option>
                <option value="japanese">Japanese</option>
                <option value="italian">Italian</option>
                <option value="slavic">Slavic</option>
                <option value="indian">Indian</option>
                <option value="thai">Thai</option>
              </Form.Select>
            </Form.Group>
          </Accordion.Body>
        </Accordion.Item>
      </Accordion>

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
            'must-see'
          ].map((pref) => (
            <Button
              key={pref}
              variant={(formData.entertainmentPreferences || []).includes(pref as EntertainmentPreference) ? 'primary' : 'outline-primary'}
              onClick={() => togglePreference(pref as EntertainmentPreference)}
              size="sm"
              className="text-capitalize"
            >
              {pref.replace('-', ' ')}
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