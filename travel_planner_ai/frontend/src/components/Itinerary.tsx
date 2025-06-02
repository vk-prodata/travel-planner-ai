import React, { useState } from 'react';
import { Card, Button, Alert, Form, InputGroup, Collapse } from 'react-bootstrap';
import { TripItinerary, Activity, TripFormData } from '../types';
import { BsArrowRepeat, BsCheck, BsX, BsTrash, BsGeoAlt, BsChevronUp, BsChevronDown, BsInfoCircle } from 'react-icons/bs';
import { FaPaperPlane, FaTimes } from 'react-icons/fa';
import { toast } from 'react-toastify';
import '../styles/Itinerary.css';

interface ItineraryProps {
  itinerary: TripItinerary;
  onActivityUpdate: (dayIndex: number, activityIndex: number, updatedActivity: Activity) => void;
  onActivityDelete: (dayIndex: number, activityIndex: number) => void;
  onActivityRefresh: (dayIndex: number, activityIndex: number, activity: Activity, customPreferences?: string) => Promise<void>;
  isLoading: boolean;
  isOwner?: boolean;
  isReadOnly?: boolean;
  formData?: TripFormData;
}

const Itinerary: React.FC<ItineraryProps> = ({ 
  itinerary, 
  onActivityUpdate,
  onActivityDelete,
  onActivityRefresh,
  isLoading,
  isOwner = false,
  isReadOnly = false,
  formData
}) => {
  const [altSuggestions, setAltSuggestions] = useState<{[key: string]: string}>({});
  const [refreshingActivities, setRefreshingActivities] = useState<{[key: string]: boolean}>({});
  const [expandedDays, setExpandedDays] = useState<{[key: string]: boolean}>({});
  const [showCustomPreferences, setShowCustomPreferences] = useState<{[key: string]: boolean}>({});
  const [customPreferences, setCustomPreferences] = useState<{[key: string]: string}>({});
  const [showTripInfo, setShowTripInfo] = useState<boolean>(false);

  const toggleDayExpanded = (dayIndex: number) => {
    setExpandedDays(prev => ({
      ...prev,
      [dayIndex]: !(prev[dayIndex] ?? true)
    }));
  };

  const isDayExpanded = (dayIndex: number) => {
    return expandedDays[dayIndex] ?? true;
  };

  const toggleCustomPreferences = (activityKey: string, e?: React.MouseEvent) => {
    e?.stopPropagation();
    setShowCustomPreferences(prev => ({
      ...prev,
      [activityKey]: !prev[activityKey]
    }));
  };

  const handleCustomPreferencesChange = (activityKey: string, value: string) => {
    setCustomPreferences(prev => ({
      ...prev,
      [activityKey]: value
    }));
  };

  const handleRefreshActivity = async (dayIndex: number, activityIndex: number, activity: Activity, e?: React.MouseEvent) => {
    // Prevent the click from triggering the collapse
    e?.stopPropagation();
    
    const activityKey = `${dayIndex}-${activityIndex}`;
    
    // If custom preferences are not shown, show the input field
    if (!showCustomPreferences[activityKey]) {
      toggleCustomPreferences(activityKey, e);
      return;
    }
    
    try {
      setRefreshingActivities(prev => ({ ...prev, [activityKey]: true }));
      await onActivityRefresh(dayIndex, activityIndex, activity, customPreferences[activityKey]);
      
      // Reset and hide the custom preferences input after successful refresh
      setCustomPreferences(prev => ({
        ...prev,
        [activityKey]: ''
      }));
      setShowCustomPreferences(prev => ({
        ...prev,
        [activityKey]: false
      }));
    } catch (error) {
      console.error('Error refreshing activity:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to refresh activity');
    } finally {
      setRefreshingActivities(prev => ({ ...prev, [activityKey]: false }));
    }
  };

  const handleCancelCustomPreferences = (activityKey: string, e?: React.MouseEvent) => {
    e?.stopPropagation();
    setCustomPreferences(prev => ({
      ...prev,
      [activityKey]: ''
    }));
    setShowCustomPreferences(prev => ({
      ...prev,
      [activityKey]: false
    }));
  };

  const handleDeleteActivity = async (dayIndex: number, activityIndex: number, e?: React.MouseEvent) => {
    // Prevent the click from triggering the collapse
    e?.stopPropagation();
    
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
  const getGoogleMapsUrl = (coordinates: any, location?: string) => {
    // PRIORITIZE location name search for better accuracy
    if (location && location.trim() !== '' && location !== 'Location not specified') {
      // Use exact venue name - much more accurate than AI-generated coordinates
      return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(location)}`;
    }
    
    // TODO: Deprecated Coordinates June 2025 - coordinate-based map links no longer used
    // FALLBACK: Use coordinate object format only if no location name available
    // if (coordinates && typeof coordinates === 'object' && coordinates.latitude && coordinates.longitude) {
    //   const lat = coordinates.latitude;
    //   const lon = coordinates.longitude;
    //   return `https://www.google.com/maps/search/?api=1&query=${lat},${lon}`;
    // }
    // 
    // // FALLBACK: Handle string coordinate format
    // if (coordinates && typeof coordinates === 'string') {
    //   const coordMatch = coordinates.match(/^(-?\d+\.?\d*),\s*(-?\d+\.?\d*)$/);
    //   if (coordMatch) {
    //     return `https://www.google.com/maps/search/?api=1&query=${coordinates}`;
    //   }
    // }
    
    return '#';
  };

  // Function to format meal descriptions to highlight restaurant options
  const formatMealDescription = (description: string) => {
    // Check if the description contains restaurant options
    if (description.includes(':')) {
      const parts = description.split(':');
      const intro = parts[0];
      const options = parts.slice(1).join(':');
      
      // Check if we have a numbered list format
      if (options.includes('1.') && (options.includes('2.') || options.includes('3.'))) {
        // Split by number patterns but keep the numbers
        const listItems = options.split(/(?=\s*\d+\.\s+)/);
        
        return (
          <div>
            <p>{intro}:</p>
            <div className="restaurant-options">
              {listItems.filter(item => item.trim().length > 0).map((item, index) => (
                <div key={index} className="restaurant-option">
                  {item.trim()}
                </div>
              ))}
            </div>
          </div>
        );
      }
      
      // Try to identify restaurant options with dash separation
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

  const formatTripInfo = () => {
    if (!formData) return null;
    
    const formatDate = (date: string) => {
      return new Date(date).toLocaleDateString();
    };
    
    const formatTravelersCount = () => {
      const adults = formData.adults || 0;
      const children = formData.children || 0;
      const infants = formData.infants || 0;
      const total = adults + children + infants;
      
      let result = `${total} traveler${total > 1 ? 's' : ''}`;
      if (adults > 0) result += ` (${adults} adult${adults > 1 ? 's' : ''})`;
      if (children > 0) result += ` (${children} child${children > 1 ? 'ren' : ''})`;
      if (infants > 0) result += ` (${infants} infant${infants > 1 ? 's' : ''})`;
      
      return result;
    };

    const formatEntertainmentPreferences = () => {
      if (!formData.entertainmentPreferences || formData.entertainmentPreferences.length === 0) {
        return 'No specific preferences';
      }
      return formData.entertainmentPreferences
        .map(pref => pref.charAt(0).toUpperCase() + pref.slice(1).replace(/([A-Z])/g, ' $1'))
        .join(', ');
    };

    return {
      travelType: formData.travelType?.charAt(0).toUpperCase() + formData.travelType?.slice(1) || 'Not specified',
      origin: formData.origin || 'Not specified',
      destination: formData.destination || 'Not specified',
      dates: `${formatDate(formData.startDate)} - ${formatDate(formData.endDate)}`,
      travelers: formatTravelersCount(),
      budgetLevel: formData.budgetLevel?.charAt(0).toUpperCase() + formData.budgetLevel?.slice(1).replace('-', ' ') || 'Not specified',
      language: formData.language === 'en' ? 'English' : formData.language?.toUpperCase() || 'Not specified',
      cuisinePreference: formData.cuisinePreference?.charAt(0).toUpperCase() + formData.cuisinePreference?.slice(1) || 'Any',
      entertainmentPreferences: formatEntertainmentPreferences(),
      intermediateStops: formData.intermediateStops?.length || 0
    };
  };

  const tripInfo = formatTripInfo();

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
      {/* Trip Information Panel */}
      {tripInfo && (
        <div className="trip-info-panel mb-4">
          <Card className="shadow-sm">
            <Card.Header 
              className="bg-light cursor-pointer d-flex justify-content-between align-items-center"
              onClick={() => setShowTripInfo(!showTripInfo)}
              style={{ cursor: 'pointer' }}
            >
              <div className="d-flex align-items-center">
                <BsInfoCircle className="me-2 text-primary" />
                <span className="fw-bold text-secondary">Trip Details</span>
              </div>
              <div className="toggle-icon">
                {showTripInfo ? <BsChevronUp size={16} /> : <BsChevronDown size={16} />}
              </div>
            </Card.Header>
            <Collapse in={showTripInfo}>
              <Card.Body>
                <div className="row">
                  <div className="col-md-6 mb-3">
                    <div className="trip-info-item">
                      <strong>Travel Type:</strong> {tripInfo.travelType}
                    </div>
                    <div className="trip-info-item">
                      <strong>From:</strong> {tripInfo.origin}
                    </div>
                    <div className="trip-info-item">
                      <strong>To:</strong> {tripInfo.destination}
                    </div>
                    <div className="trip-info-item">
                      <strong>Dates:</strong> {tripInfo.dates}
                    </div>
                  </div>
                  <div className="col-md-6 mb-3">
                    <div className="trip-info-item">
                      <strong>Travelers:</strong> {tripInfo.travelers}
                    </div>
                    <div className="trip-info-item">
                      <strong>Budget Level:</strong> {tripInfo.budgetLevel}
                    </div>
                    <div className="trip-info-item">
                      <strong>Language:</strong> {tripInfo.language}
                    </div>
                    <div className="trip-info-item">
                      <strong>Cuisine:</strong> {tripInfo.cuisinePreference}
                    </div>
                  </div>
                </div>
                <div className="row">
                  <div className="col-12">
                    <div className="trip-info-item">
                      <strong>Entertainment Preferences:</strong> {tripInfo.entertainmentPreferences}
                    </div>
                    {tripInfo.intermediateStops > 0 && (
                      <div className="trip-info-item">
                        <strong>Intermediate Stops:</strong> {tripInfo.intermediateStops}
                      </div>
                    )}
                  </div>
                </div>
              </Card.Body>
            </Collapse>
          </Card>
        </div>
      )}
      
      {/* Itinerary Days */}
      {itinerary.days.map((day, dayIndex) => {
        const isExpanded = isDayExpanded(dayIndex);
        
        return (
          <div key={day.date} className="day-container mb-4">
            <div 
              className="day-header-container bg-primary text-white rounded"
              onClick={() => toggleDayExpanded(dayIndex)}
              style={{ cursor: 'pointer' }}
            >
              <div className="d-flex justify-content-between align-items-center p-2">
                <h3 className="day-header mb-0">{day.date}</h3>
                <div className="toggle-icon">
                  {isExpanded ? <BsChevronUp size={18} /> : <BsChevronDown size={18} />}
                </div>
              </div>
            </div>
            <div 
              className="activities-container overflow-hidden"
              style={{
                maxHeight: isExpanded ? '3000px' : '0',
                opacity: isExpanded ? 1 : 0,
                transition: 'max-height 0.5s ease-in-out, opacity 0.4s ease-in-out'
              }}
            >
              <div className="activities-list">
                {day.activities.map((activity, activityIndex) => {
                  const activityKey = `${dayIndex}-${activityIndex}`;
                  const suggestion = altSuggestions[activityKey];
                  const isRefreshing = refreshingActivities[activityKey];
                  const isMeal = activity.type === 'meal' || activity.type === 'food';
                  const showPreferences = showCustomPreferences[activityKey];

                  return (
                    <Card 
                      key={`${dayIndex}-${activityIndex}`} 
                      className="mb-2 shadow-sm"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <Card.Body>
                        <div className="d-flex justify-content-between align-items-start">
                          <div className="activity-content flex-grow-1">
                            <div className="d-flex justify-content-between align-items-center">
                              <div className="activity-time fw-bold">{activity.time}</div>
                              <div className="d-flex gap-2 align-items-center">
                                <span className={`badge ${isMeal ? 'bg-success' : 'bg-light text-primary'}`}>
                                  {activity.type}
                                </span>
                                {getPriceLevelDisplay(activity.price)}
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
                                  
                                  {/* TODO: Deprecated Coordinates June 2025 - coordinate-based map links no longer generated */}
                                  {/* {activity.coordinates && (
                                    <a 
                                      href={getGoogleMapsUrl(activity.coordinates, activity.location)} 
                                      target="_blank" 
                                      rel="noopener noreferrer"
                                      className="ms-2 text-primary"
                                      onClick={(e) => e.stopPropagation()}
                                    >
                                      View on Map
                                    </a>
                                  )} */}
                                  
                                  <a 
                                    href={getGoogleMapsUrl(null, activity.location)} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    className="ms-2 text-primary"
                                    onClick={(e) => e.stopPropagation()}
                                  >
                                    View on Map
                                  </a>
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
                                      onClick={(e) => {
                                        e.stopPropagation();
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
                                      onClick={(e) => {
                                        e.stopPropagation();
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
                              
                              {showPreferences && (
                                <div className="mt-3 custom-preferences-container">
                                  <Form onSubmit={(e) => {
                                    e.preventDefault();
                                    handleRefreshActivity(dayIndex, activityIndex, activity);
                                  }}>
                                    <Form.Group>
                                      <InputGroup>
                                        <Form.Control
                                          type="text"
                                          placeholder="e.g. something outdoors, kid-friendly"
                                          value={customPreferences[activityKey] || ''}
                                          onChange={(e) => handleCustomPreferencesChange(activityKey, e.target.value)}
                                        />
                                        <Button 
                                          type="submit"
                                          variant="primary" 
                                          disabled={isRefreshing}
                                          title="Submit"
                                          className="d-flex align-items-center justify-content-center"
                                          style={{ width: '40px', padding: '0' }}
                                        >
                                          {isRefreshing ? (
                                            <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                                          ) : (
                                            <FaPaperPlane />
                                          )}
                                        </Button>
                                        <Button 
                                          type="button"
                                          variant="outline-secondary"
                                          onClick={(e) => handleCancelCustomPreferences(activityKey, e)}
                                          title="Cancel"
                                          className="d-flex align-items-center justify-content-center"
                                          style={{ width: '40px', padding: '0' }}
                                        >
                                          <FaTimes />
                                        </Button>
                                      </InputGroup>
                                    </Form.Group>
                                  </Form>
                                </div>
                              )}
                            </div>
                          </div>
                          {!isReadOnly && isOwner && (
                            <div className="d-flex gap-2">
                              <Button
                                variant="outline-primary"
                                className="refresh-button d-flex align-items-center justify-content-center"
                                onClick={(e) => handleRefreshActivity(dayIndex, activityIndex, activity, e)}
                                disabled={isRefreshing || isLoading}
                                title="Refresh Activity"
                                style={{ width: '36px', height: '36px', padding: '0' }}
                              >
                                <BsArrowRepeat 
                                  size={20} 
                                  className={isRefreshing ? 'spin' : ''} 
                                />
                              </Button>
                              <Button
                                variant="outline-danger"
                                className="delete-button d-flex align-items-center justify-content-center"
                                onClick={(e) => handleDeleteActivity(dayIndex, activityIndex, e)}
                                disabled={isLoading}
                                title="Delete Activity"
                                style={{ width: '36px', height: '36px', padding: '0' }}
                              >
                                <BsTrash size={16} />
                              </Button>
                            </div>
                          )}
                        </div>
                      </Card.Body>
                    </Card>
                  );
                })}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default Itinerary;