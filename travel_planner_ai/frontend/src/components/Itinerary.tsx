import * as React from 'react';
import { Card, Button } from 'react-bootstrap';
import { TripItinerary, Activity } from '../types';
import { BsArrowRepeat, BsCheck, BsX } from 'react-icons/bs';
import { useState, useEffect } from 'react';

interface ItineraryProps {
  itinerary: TripItinerary;
  onActivityUpdate: (dayIndex: number, activityIndex: number, updatedActivity: Activity) => void;
  onSuggestAlternative: (type: string) => void;
  alternatives: Record<string, string[]>;
}

const Itinerary: React.FC<ItineraryProps> = ({ 
  itinerary, 
  onActivityUpdate,
  alternatives 
}) => {
  const [altSuggestions, setAltSuggestions] = useState<{[key: string]: string}>({});
  const [localItinerary, setLocalItinerary] = useState(itinerary);

  // Update local itinerary when prop changes
  useEffect(() => {
    setLocalItinerary(itinerary);
  }, [itinerary]);

  // Save suggestions to localStorage
  useEffect(() => {
    if (Object.keys(altSuggestions).length > 0) {
      localStorage.setItem('activitySuggestions', JSON.stringify(altSuggestions));
    }
  }, [altSuggestions]);

  // Restore suggestions from localStorage
  useEffect(() => {
    const savedSuggestions = localStorage.getItem('activitySuggestions');
    if (savedSuggestions) {
      try {
        setAltSuggestions(JSON.parse(savedSuggestions));
      } catch (e) {
        console.error('Error restoring suggestions:', e);
        localStorage.removeItem('activitySuggestions');
      }
    }
  }, []);

  const handleSuggestAlternative = (dayIndex: number, activityIndex: number, activity: Activity) => {
    const mockAlts = alternatives[activity.type] || [];
    const randomAlt = mockAlts[Math.floor(Math.random() * mockAlts.length)];
    setAltSuggestions(prev => ({
      ...prev,
      [`${dayIndex}-${activityIndex}`]: randomAlt
    }));
  };

  const handleApplyAlternative = (dayIndex: number, activityIndex: number, activity: Activity, alternative: string) => {
    const updatedActivity = {
      ...activity,
      description: alternative
    };

    // Update local state immediately
    setLocalItinerary(prev => ({
      ...prev,
      days: prev.days.map((day, dIdx) => {
        if (dIdx !== dayIndex) return day;
        return {
          ...day,
          activities: day.activities.map((act, aIdx) => {
            if (aIdx !== activityIndex) return act;
            return updatedActivity;
          })
        };
      })
    }));
    
    // Remove the suggestion
    setAltSuggestions(prev => {
      const newState = { ...prev };
      delete newState[`${dayIndex}-${activityIndex}`];
      localStorage.setItem('activitySuggestions', JSON.stringify(newState));
      return newState;
    });

    // Notify parent component for saving to database later
    onActivityUpdate(dayIndex, activityIndex, updatedActivity);
  };

  const handleCancelAlternative = (dayIndex: number, activityIndex: number) => {
    setAltSuggestions(prev => {
      const newState = { ...prev };
      delete newState[`${dayIndex}-${activityIndex}`];
      localStorage.setItem('activitySuggestions', JSON.stringify(newState));
      return newState;
    });
  };

  return (
    <div className="itinerary">
      {localItinerary.days.map((day, dayIndex) => (
        <div key={day.date} className="day-container mb-4">
          <h2 className="day-header bg-primary text-white p-3 rounded">{day.date}</h2>
          <div className="activities-list">
            {day.activities.map((activity, activityIndex) => {
              const suggestionKey = `${dayIndex}-${activityIndex}`;
              const suggestion = altSuggestions[suggestionKey];

              return (
                <Card key={activity.id} className="mb-2 shadow-sm">
                  <Card.Body>
                    <div className="d-flex justify-content-between align-items-start">
                      <div className="activity-content flex-grow-1">
                        <div className="activity-time fw-bold">{activity.time}</div>
                        <div className="activity-description">
                          {activity.description}
                          {suggestion && (
                            <div className="mt-2 p-2 bg-light rounded">
                              <div className="text-muted small mb-1">Suggested alternative:</div>
                              <div className="suggestion-text">{suggestion}</div>
                              <div className="mt-2 d-flex gap-2">
                                <Button
                                  variant="success"
                                  size="sm"
                                  className="d-flex align-items-center gap-1"
                                  onClick={() => handleApplyAlternative(dayIndex, activityIndex, activity, suggestion)}
                                >
                                  <BsCheck size={16} />
                                  Accept
                                </Button>
                                <Button
                                  variant="outline-secondary"
                                  size="sm"
                                  className="d-flex align-items-center gap-1"
                                  onClick={() => handleCancelAlternative(dayIndex, activityIndex)}
                                >
                                  <BsX size={16} />
                                  Reject
                                </Button>
                              </div>
                            </div>
                          )}
                        </div>
                        <div className="activity-type mt-2">
                          <span className="badge bg-light text-primary">{activity.type}</span>
                        </div>
                      </div>
                      {!suggestion && (
                        <Button
                          variant="outline-primary"
                          className="ms-2 rounded-circle p-1"
                          onClick={() => handleSuggestAlternative(dayIndex, activityIndex, activity)}
                        >
                          <BsArrowRepeat size={16} />
                        </Button>
                      )}
                    </div>
                  </Card.Body>
                </Card>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
};

export default Itinerary; 