import React, { useState } from 'react';
import { Card, Button, Alert } from 'react-bootstrap';
import { TripItinerary, Activity } from '../types';
import { BsArrowRepeat, BsCheck, BsX, BsTrash, BsGeoAlt } from 'react-icons/bs';
import { FaMapMarkerAlt, FaUtensils, FaBed, FaLandmark, FaTheaterMasks, FaInfoCircle, FaExpandAlt, FaCompressAlt, FaWalking, FaClock } from 'react-icons/fa';
import { toast } from 'react-toastify';
import '../styles/Itinerary.css';

interface ItineraryProps {
  itinerary: TripItinerary;
  onActivityUpdate: (dayIndex: number, activityIndex: number, updatedActivity: Activity) => void;
  onActivityDelete: (dayIndex: number, activityIndex: number) => void;
  onActivityRefresh: (dayIndex: number, activityIndex: number, activity: Activity) => Promise<void>;
  isLoading: boolean;
  isOwner?: boolean;
}

const Itinerary: React.FC<ItineraryProps> = ({ 
  itinerary, 
  onActivityUpdate,
  onActivityDelete,
  onActivityRefresh,
  isLoading,
  isOwner = false
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

  // Function to get Google Maps URL from coordinates
  const getGoogleMapsUrl = (coordinates: string, location?: string) => {
    if (!coordinates) return '#';
    
    // If location is available, use it for a more accurate search
    const locationString = location || '';
    const [placeName, city, state, country] = locationString.split(',').map((part: string) => part.trim());
    
    // Build the search query with available location details
    let searchQuery = '';
    if (placeName) searchQuery += placeName;
    if (city) searchQuery += (searchQuery ? ', ' : '') + city;
    if (state) searchQuery += (searchQuery ? ', ' : '') + state;
    if (country) searchQuery += (searchQuery ? ', ' : '') + country;
    
    // If we have a formatted location, use it; otherwise, fall back to coordinates
    const query = searchQuery || coordinates;
    return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`;
  };

  // Function to format meal descriptions to highlight restaurant options
  const formatMealDescription = (description: string) => {
    // Check if the description contains restaurant options
    if (description.includes(':')) {
      const parts = description.split(':');
      const intro = parts[0];
      const options = parts.slice(1).join(':');
      
      // Try to identify restaurant options
      const restaurantRegex = /([\w\s'&-]+)(?:\s*-\s*|\s*–\s*)(.*?)(?=\s*\d+\.|$)/g;
      let formattedOptions = options;
      
      // If we can identify restaurant options with descriptions, format them
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const testMatch = restaurantRegex.exec(options);
      if (testMatch !== null) {
        restaurantRegex.lastIndex = 0; // Reset regex
        formattedOptions = options.replace(restaurantRegex, (match, restaurant, description) => {
          return `<div class="restaurant-option">
                    <strong>${restaurant.trim()}</strong> - ${description.trim()}
                  </div>`;
        });
        
        return (
          <div>
            <p>{intro}:</p>
            <div className="restaurant-options" dangerouslySetInnerHTML={{ __html: formattedOptions }} />
          </div>
        );
      }
    }
    
    // Default return if no special formatting is needed
    return <p>{description}</p>;
  };

  const getPriceLevelDisplay = (priceLevel?: string) => {
    switch (priceLevel) {
      case 'free':
        return <span className="badge bg-success">Free</span>;
      case '$':
        return <span className="badge bg-info">$</span>;
      case '$$':
        return <span className="badge bg-warning">$$</span>;
      case '$$$':
        return <span className="badge bg-danger">$$$</span>;
      default:
        return null;
    }
  };

  // Check if itinerary or itinerary.days is undefined
  if (!itinerary || !itinerary.days) {
    return (
      <Alert variant="warning">
        This trip has an invalid itinerary format. Please try generating a new itinerary.
      </Alert>
    );
  }

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
              const isMeal = activity.type === 'meal' || activity.type === 'food';

              return (
                <Card key={activity.id} className="mb-2 shadow-sm">
                  <Card.Body>
                    <div className="d-flex justify-content-between align-items-start">
                      <div className="activity-content flex-grow-1">
                        <div className="d-flex justify-content-between align-items-center">
                          <div className="activity-time fw-bold">{activity.time}</div>
                          <div className="d-flex gap-2 align-items-center">
                            <span className={`badge ${isMeal ? 'bg-success' : 'bg-light text-primary'}`}>
                              {activity.type}
                            </span>
                            {getPriceLevelDisplay(activity.priceLevel)}
                          </div>
                        </div>
                        <div className="activity-description">
                          {isMeal 
                            ? formatMealDescription(activity.description)
                            : (
                                <>
                                  {activity.description}
                                  {activity.why && (
                                    <span className="activity-why">{activity.why}</span>
                                  )}
                                </>
                              )
                          }
                          
                          {activity.location && (
                            <div className="activity-location mt-2">
                              <span className="text-muted">
                                <BsGeoAlt className="me-1" />
                                {activity.location}
                              </span>
                              
                              {activity.coordinates && (
                                <a 
                                  href={getGoogleMapsUrl(activity.coordinates, activity.location)} 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  className="ms-2 text-primary"
                                >
                                  View on Map
                                </a>
                              )}
                            </div>
                          )}
                          
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
                      </div>
                      <div className="d-flex gap-2">
                        {isOwner && (
                          <>
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
                          </>
                        )}
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