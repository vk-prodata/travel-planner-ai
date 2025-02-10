import * as React from 'react';
import { Card } from 'react-bootstrap';
import { TripItinerary } from '../types';

interface ItineraryProps {
  itinerary: TripItinerary;
  onActivityUpdate: (dayIndex: number, activityIndex: number, updatedActivity: any) => void;
  onSuggestAlternative: (dayIndex: number, activityIndex: number) => void;
}

const Itinerary: React.FC<ItineraryProps> = ({ itinerary }) => {
  return (
    <div>
      {itinerary.days.map((day, dayIndex) => (
        <Card key={day.date} className="mb-3">
          <Card.Header>{day.date}</Card.Header>
          <Card.Body>
            {day.activities.map((activity) => (
              <div key={activity.id} className="mb-3">
                <strong>{activity.time}</strong>: {activity.description}
              </div>
            ))}
          </Card.Body>
        </Card>
      ))}
    </div>
  );
};

export default Itinerary; 