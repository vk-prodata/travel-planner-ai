import * as React from 'react';
import { Card, Button } from 'react-bootstrap';
import { TripItinerary, Activity } from '../types';
import { BsArrowRepeat, BsCheck, BsX, BsTrash } from 'react-icons/bs';
import { useState } from 'react';
import { toast } from 'react-toastify';

interface ItineraryProps {
  itinerary: TripItinerary;
  onActivityUpdate: (dayIndex: number, activityIndex: number, updatedActivity: Activity) => void;
  onActivityDelete: (dayIndex: number, activityIndex: number) => void;
  onActivityRefresh: (dayIndex: number, activityIndex: number, activity: Activity) => Promise<void>;
  isLoading: boolean;
}

const Itinerary: React.FC<ItineraryProps> = ({ 
  itinerary, 
  onActivityUpdate,
  onActivityDelete,
  onActivityRefresh,
  isLoading 
}) => {
  const [altSuggestions, setAltSuggestions] = useState<{[key: string]: string}>({});
  const [refreshingActivities, setRefreshingActivities] = useState<{[key: string]: boolean}>({});

  const handleRefreshActivity = async (dayIndex: number, activityIndex: number, activity: Activity) => {
    try {
      setRefreshingActivities(prev => ({ ...prev, [`${dayIndex}-${activityIndex}`]: true }));
      await onActivityRefresh(dayIndex, activityIndex, activity);
    } catch (error) {
      console.error('Error refreshing activity:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to refresh activity');
    } finally {
      setRefreshingActivities(prev => ({ ...prev, [`${dayIndex}-${activityIndex}`]: false }));
    }
  };

  const handleDeleteActivity = async (dayIndex: number, activityIndex: number) => {
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/activities/${dayIndex}/${activityIndex}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to delete activity');
      }

      onActivityDelete(dayIndex, activityIndex);
    } catch (error) {
      console.error('Error deleting activity:', error);
      toast.error('Failed to delete activity');
    }
  };

  return (
    <div className="itinerary">
      {itinerary.days.map((day, dayIndex) => (
        <div key={day.date} className="day-container mb-4">
          <h2 className="day-header bg-primary text-white p-3 rounded">{day.date}</h2>
          <div className="activities-list">
            {day.activities.map((activity, activityIndex) => {
              const activityKey = `${dayIndex}-${activityIndex}`;
              const suggestion = altSuggestions[activityKey];
              const isRefreshing = refreshingActivities[activityKey];

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
                                  onClick={() => {
                                    onActivityUpdate(dayIndex, activityIndex, {
                                      ...activity,
                                      description: suggestion
                                    });
                                    setAltSuggestions(prev => {
                                      const newState = { ...prev };
                                      delete newState[activityKey];
                                      return newState;
                                    });
                                  }}
                                >
                                  <BsCheck size={16} />
                                  Accept
                                </Button>
                                <Button
                                  variant="outline-secondary"
                                  size="sm"
                                  className="d-flex align-items-center gap-1"
                                  onClick={() => {
                                    setAltSuggestions(prev => {
                                      const newState = { ...prev };
                                      delete newState[activityKey];
                                      return newState;
                                    });
                                  }}
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
                      <div className="d-flex gap-2">
                        <Button
                          variant="outline-primary"
                          className="refresh-button"
                          onClick={() => handleRefreshActivity(dayIndex, activityIndex, activity)}
                          disabled={isRefreshing || isLoading}
                        >
                          <BsArrowRepeat 
                            size={20} 
                            className={isRefreshing ? 'spin' : ''} 
                          />
                        </Button>
                        <Button
                          variant="outline-danger"
                          className="delete-button"
                          onClick={() => handleDeleteActivity(dayIndex, activityIndex)}
                          disabled={isLoading}
                        >
                          <BsTrash size={16} />
                        </Button>
                      </div>
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