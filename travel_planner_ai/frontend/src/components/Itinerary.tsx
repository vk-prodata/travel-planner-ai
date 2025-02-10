import * as React from 'react';
import { Card, Button, Row, Col } from 'react-bootstrap';
import { TripItinerary } from '../types';
import { BsArrowRepeat } from 'react-icons/bs';
import { useState } from 'react';

interface ItineraryProps {
  itinerary: TripItinerary;
  onActivityUpdate: (dayIndex: number, activityIndex: number, updatedActivity: any) => void;
  onSuggestAlternative: (dayIndex: number, activityIndex: number) => void;
  alternatives: {
    [key: string]: string[];
  };
}

const Itinerary: React.FC<ItineraryProps> = ({ itinerary, alternatives }) => {
  const [altSuggestions, setAltSuggestions] = useState<{[key: string]: string}>({});

  const handleSuggestAlternative = (activityId: string, type: string) => {
    const mockAlts = alternatives[type] || [];
    const randomAlt = mockAlts[Math.floor(Math.random() * mockAlts.length)];
    setAltSuggestions(prev => ({
      ...prev,
      [activityId]: randomAlt
    }));
  };

  return (
    <div>
      {itinerary.days.map((day, dayIndex) => (
        <Card key={day.date} className="mb-3 shadow-sm">
          <Card.Header className="bg-primary-gradient text-white py-3">
            <h4 className="mb-0">{day.date}</h4>
          </Card.Header>
          <Card.Body className="bg-light">
            {day.activities.map((activity) => (
              <div key={activity.id} className="mb-3 bg-white p-3 rounded shadow-sm">
                <div className="d-flex justify-content-between align-items-start">
                  <div className="d-flex align-items-start">
                    <strong className="text-primary-dark me-3" style={{ minWidth: '80px' }}>
                      {activity.time}
                    </strong>
                    <div>
                      <p className="mb-1 text-secondary">{activity.description}</p>
                      <span className="badge bg-info-light text-info-dark">{activity.type}</span>
                    </div>
                  </div>
                  <Button 
                    variant="outline-primary"
                    size="sm"
                    className="ms-3 rounded-circle"
                    onClick={() => handleSuggestAlternative(activity.id, activity.type)}
                  >
                    <BsArrowRepeat />
                  </Button>
                </div>
                {altSuggestions[activity.id] && (
                  <div className="mt-2 ms-5 ps-3 border-start border-primary bg-light p-2 rounded">
                    <p className="mb-0 text-primary-dark">
                      <strong>Alternative:</strong> {altSuggestions[activity.id]}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </Card.Body>
        </Card>
      ))}
    </div>
  );
};

export default Itinerary; 