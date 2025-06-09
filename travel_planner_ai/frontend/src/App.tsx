import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Button, Dropdown } from 'react-bootstrap';
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation, useSearchParams } from 'react-router-dom';
import TripForm from './components/TripForm';
import Itinerary from './components/Itinerary';
import TripTitleExport from './components/TripTitleExport';
import { TripFormData, TripItinerary, Activity, User } from './types';
import 'bootstrap/dist/css/bootstrap.min.css';
import { FaPlaneDeparture, FaEdit, FaSave, FaList, FaShareAlt, FaWhatsapp, FaTelegram, FaFacebook, FaCopy, FaFileDownload, FaFileAlt, FaCalendarAlt } from 'react-icons/fa';
import { useAuth } from './contexts/AuthContext';
import AuthForm from './components/AuthForm';
import AuthCallback from './components/AuthCallback';
import { saveTrip, updateTrip, getTripById } from './services/tripService';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import TripList from './pages/TripList';
import Credits from './pages/Credits';
import CreditsDisplay from './components/CreditsDisplay';
import LoggingToggle from './components/LoggingToggle';
import { notifyError, notifySuccess } from './services/errorService';
import { generateItinerary } from './services/itineraryService';
import './styles/App.css';
import FaqPage from './pages/FaqPage/FaqPage';
import ical from 'ical-generator';
import SEO from './components/SEO';
import TripLoadingHints from './components/TripLoadingHints';

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const UserAvatar: React.FC<{ name: string }> = ({ name }) => {
  const initials = name
    .split(' ')
    .slice(0, 2) // Take first two words
    .map(word => word.charAt(0).toUpperCase()) // Get first letter of each word
    .join(''); // Join them together

  return (
    <div
      className="d-flex align-items-center justify-content-center rounded-circle bg-primary bg-opacity-10 text-primary"
      style={{ 
        width: '32px', 
        height: '32px',
        fontSize: '0.875rem', // Slightly smaller font for two letters
        fontWeight: '500'
      }}
    >
      {initials}
    </div>
  );
};

const ReadOnlyBanner: React.FC<{ isReadOnlyMode?: boolean; user: User | null }> = ({ isReadOnlyMode = true, user }) => {
  return (
    <div className="alert alert-info mb-4 d-flex justify-content-between align-items-center">
      <div>
        {isReadOnlyMode ? (
          <span><strong>Read-only mode</strong> - You're viewing a shared trip.</span>
        ) : (
          <span><strong>Sign in</strong> to save your trips and access them later.</span>
        )}
      </div>
      {!user && <AuthForm />}
    </div>
  );
};

const MainApp = () => {
  const { user, signOut, refreshUserCredits, ensureValidToken } = useAuth();
  const navigate = useNavigate();
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const [isLoading, setIsLoading] = useState(false);
  const [itinerary, setItinerary] = useState<TripItinerary | null>(null);
  const [formData, setFormData] = useState<TripFormData | null>(null);
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [editedTitle, setEditedTitle] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [currentTripId, setCurrentTripId] = useState<string | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [localItinerary, setLocalItinerary] = useState<TripItinerary | null>(null);
  const [isReadOnlyMode, setIsReadOnlyMode] = useState(false);

  // Use location in a comment to avoid the unused variable warning
  // Current path: ${location.pathname}
  
  // Load trip if tripId is in URL
  useEffect(() => {
    const tripId = searchParams.get('tripId');
    if (tripId) {
      const loadTrip = async () => {
        console.log("Starting to load trip with ID:", tripId);
        console.log("User authentication status:", user ? "Authenticated" : "Not authenticated");
        
        setIsLoading(true);
        try {
          console.log(`Loading trip with ID: ${tripId}`);
          
          // Use the new getTripById function that works for both authenticated and unauthenticated users
          const trip = await getTripById(tripId);
          console.log('Trip loaded successfully:', trip);
          
          if (trip) {
            if (!trip.formData) {
              console.error('Trip is missing formData:', trip);
              if (user) {
                notifyError('Trip data is incomplete', user?.email);
              }
              setIsLoading(false);
              return;
            }
            
            if (!trip.itinerary || !trip.itinerary.days) {
              console.error('Trip is missing itinerary or days:', trip);
              if (user) {
                notifyError('Trip itinerary is incomplete', user?.email);
              }
              setIsLoading(false);
              return;
            }
            
            // Ensure isOwner flag is set in the itinerary
            const itineraryWithOwnership = {
              ...trip.itinerary,
              isOwner: trip.isOwner ?? (user && trip.user_id === user.id) ?? false
            };
            
            console.log('Setting itinerary with ownership:', {
              isOwner: itineraryWithOwnership.isOwner,
              userId: trip.user_id,
              currentUserId: user?.id || 'not logged in'
            });
            
            setFormData(trip.formData);
            setItinerary(itineraryWithOwnership);
            setLocalItinerary(itineraryWithOwnership);
            setCurrentTripId(trip.id);
            setHasUnsavedChanges(false);
            
            // Only show success message if user is logged in and coming from the trips list page
            if (user && document.referrer.includes('/trips')) {
              notifySuccess('Trip loaded successfully!');
            }
            
            // Set read-only mode for unauthenticated users or if user is not the owner
            setIsReadOnlyMode(!user || !trip.isOwner);
          } else {
            console.error('Trip not found in response');
            if (user) {
              notifyError('Trip not found', user?.email);
            }
          }
        } catch (error) {
          console.error('Error loading trip:', error);
          if (user) {
            notifyError(error instanceof Error ? error.message : 'Failed to load trip', user?.email);
          }
        } finally {
          setIsLoading(false);
        }
      };
      
      loadTrip();
    }
  }, [searchParams, user]);

  const handleSubmit = async (data: TripFormData) => {
    setIsLoading(true);
    // Reset all existing trip data to ensure UI is refreshed
    setItinerary(null);
    setLocalItinerary(null);
    setFormData(data);
    setCurrentTripId(null);
    // Clear any URL parameters
    setSearchParams({});
    // Clear any cached itinerary in localStorage
    localStorage.removeItem('unsavedItinerary');

    try {
      if (!user) {
        // Use mock data only for non-signed-in users
        const mockItinerary = {
          tripId: String(Date.now()),
          days: [
            {
              date: new Date(data.startDate).toLocaleDateString(),
              activities: [
                {
                  id: '1',
                  time: '9:00 AM',
                  description: 'Start your journey to ' + data.destination,
                  type: 'travel'
                },
                {
                  id: '2',
                  time: '12:00 PM',
                  description: 'Lunch at local restaurant',
                  type: 'food'
                },
                {
                  id: '3',
                  time: '2:00 PM',
                  description: 'Explore city center',
                  type: 'activity'
                }
              ]
            }
          ]
        };
        setItinerary(mockItinerary);
        setLocalItinerary(mockItinerary);
        setHasUnsavedChanges(true);
        setIsLoading(false);
        return;
      }

      // Validate form data
      if (!data.destination || !data.startDate || !data.endDate) {
        throw new Error('Please fill in all required fields');
      }

      // Check dates
      const start = new Date(data.startDate);
      const end = new Date(data.endDate);
      if (end < start) {
        throw new Error('End date must be after start date');
      }

      const newItinerary = await generateItinerary(data, user.id);
      if (newItinerary) {
        // Ensure the isOwner flag is set
        const itineraryWithOwnership = {
          ...newItinerary,
          isOwner: true // User is always the owner of a newly generated itinerary
        };
        
        setItinerary(itineraryWithOwnership);
        setLocalItinerary(itineraryWithOwnership);
        
        // Refresh user credits after generating itinerary
        if (user) {
          try {
            await refreshUserCredits();
            console.log('User credits refreshed after generating itinerary');
          } catch (err) {
            console.error('Failed to refresh credits after generating itinerary:', err);
          }
        }
        
        // Auto-save the trip
        try {
          const tripData = {
            userId: user.id,
            formData: {
              ...data,
              updateExisting: true // Always try to update if exists
            },
            itinerary: itineraryWithOwnership
          };
          
          const savedTrip = await saveTrip(tripData);
          setCurrentTripId(savedTrip.id);
          setHasUnsavedChanges(false);
          notifySuccess('Trip generated and saved successfully!');
          // Update URL without redirecting
          window.history.replaceState(null, '', `/?tripId=${savedTrip.id}`);
          
          // Refresh user credits after auto-saving trip
          try {
            await refreshUserCredits();
            console.log('User credits refreshed after auto-saving trip');
          } catch (err) {
            console.error('Failed to refresh credits after auto-saving trip:', err);
          }
        } catch (error: any) {
          console.error('Error saving trip:', error);
          setHasUnsavedChanges(true);
          
          // If it's not a conflict error, show generic error
          if (!error.message?.includes('similar trip already exists')) {
            notifyError('Failed to save trip. Please try saving manually.', user?.email);
            return;
          }

          // For conflict errors, ask user what to do
          const confirmUpdate = window.confirm(
            'A similar trip already exists. Would you like to update the existing trip instead?'
          );
          
          if (confirmUpdate) {
            try {
              const tripData = {
                userId: user.id,
                formData: {
                  ...data,
                  updateExisting: true
                },
                itinerary: itineraryWithOwnership
              };
              
              const savedTrip = await saveTrip(tripData);
              setCurrentTripId(savedTrip.id);
              setHasUnsavedChanges(false);
              notifySuccess('Existing trip updated successfully!');
              window.history.replaceState(null, '', `/?tripId=${savedTrip.id}`);
              
              // Refresh user credits after updating existing trip
              try {
                await refreshUserCredits();
                console.log('User credits refreshed after updating existing trip');
              } catch (err) {
                console.error('Failed to refresh credits after updating existing trip:', err);
              }
            } catch (updateError: any) {
              console.error('Error updating trip:', updateError);
              setHasUnsavedChanges(true);
              notifyError('Failed to update existing trip. Please try saving manually.', user?.email);
            }
          } else {
            setHasUnsavedChanges(true);
            notifyError('Trip generated but not saved. Please try saving with a different destination or dates.', user?.email);
          }
        }
      }
    } catch (error: any) {
      console.error('Error generating trip:', error);
      
      // Handle enhanced error responses from AI generation
      if (error.errorType) {
        let errorMessage = error.message;
        
        // Add specific guidance based on error type
        if (error.errorType === 'incomplete_response' && error.partialDaysReceived) {
          errorMessage += `\n\nPartial Result: Generated ${error.partialDaysReceived} out of ${error.requestedDays} requested days.`;
        }
        
        // Add suggestions if available
        if (error.suggestions && error.suggestions.length > 0) {
          errorMessage += '\n\nSuggestions:\n• ' + error.suggestions.join('\n• ');
        }
        
        notifyError(errorMessage, user?.email);
      } else {
        // Generic error handling for other types of errors
        notifyError(error instanceof Error ? error.message : 'Failed to generate trip', user?.email);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const getTripTitle = () => {
    if (itinerary?.title) {
      return itinerary.title;
    }
    
    if (!formData) return 'New Trip';
    
    const destination = formData.destination;
    
    // Get dates directly from formData to avoid any timezone issues
    const startDate = formData.startDate || '';
    const endDate = formData.endDate || '';
    
    let title = destination;
    if (startDate && endDate) {
      title += ` (${startDate} - ${endDate})`;
    }
    
    return title;
  };

  const handleActivityUpdate = (dayIndex: number, activityIndex: number, updatedActivity: Activity) => {
    if (!itinerary) return; // Guard clause for null itinerary

    // Initialize localItinerary if it's null
    if (!localItinerary) {
      setLocalItinerary(itinerary);
    }

    const currentItinerary = localItinerary || itinerary;

    const updatedItinerary: TripItinerary = {
      ...currentItinerary,
      tripId: currentItinerary.tripId,
      days: currentItinerary.days.map((day, dIdx) => {
        if (dIdx !== dayIndex) return day;
        return {
          ...day,
          activities: day.activities.map((activity, aIdx) => {
            if (aIdx !== activityIndex) return activity;
            return updatedActivity;
          })
        };
      })
    };

    setLocalItinerary(updatedItinerary);
    setHasUnsavedChanges(true);

    // Save to localStorage
    localStorage.setItem('unsavedItinerary', JSON.stringify(updatedItinerary));
  };

  const handleSaveTrip = async () => {
    if (isReadOnlyMode) {
      return;
    }

    if (!user || !localItinerary || !formData) {
      console.error('Cannot save trip: Missing required data', {
        hasUser: !!user,
        hasLocalItinerary: !!localItinerary,
        hasFormData: !!formData
      });
      notifyError('Please log in and generate an itinerary first', user?.email);
      return;
    }

    console.log('Starting trip save process', {
      currentTripId: currentTripId,
      destination: formData.destination,
      startDate: formData.startDate,
      endDate: formData.endDate,
      userId: user.id,
      itineraryDays: localItinerary?.days?.length || 0
    });

    setIsSaving(true);
    try {
      // Ensure we have a valid token before making the request
      const validToken = await ensureValidToken();
      if (!validToken) {
        notifyError('Authentication expired. Please sign in again.', user?.email);
        return;
      }
      
      // Ensure the itinerary has a tripId and isOwner flag
      const itineraryWithId = {
        ...localItinerary,
        tripId: currentTripId || 'temp-' + Date.now(),
        isOwner: true // We're the owner when saving a new trip
      };
      
      // Add updateExisting flag for Tahoe trips or when user confirms overwrite
      const updatedFormData = {
        ...formData,
        updateExisting: formData.destination?.toLowerCase().includes('tahoe') || false
      };
      
      const tripData = {
        userId: user.id,
        formData: updatedFormData,
        itinerary: itineraryWithId
      };
      
      console.log('Prepared trip data for saving:', {
        userId: tripData.userId,
        destination: tripData.formData.destination,
        updateExisting: tripData.formData.updateExisting,
        hasItinerary: !!tripData.itinerary,
        itineraryDays: tripData.itinerary?.days?.length || 0
      });
      
      let savedTrip;
      if (currentTripId) {
        console.log(`Updating existing trip with ID: ${currentTripId}`);
        savedTrip = await updateTrip(currentTripId, tripData);
        notifySuccess('Trip updated successfully!');
      } else {
        console.log('Creating new trip');
        try {
          savedTrip = await saveTrip(tripData);
          console.log('New trip created with ID:', savedTrip.id);
          setCurrentTripId(savedTrip.id);
          notifySuccess('Trip saved successfully!');
          
          // Refresh user credits after saving a new trip
          // Only refresh if this is a new trip (might deduct credits)
          if (user) {
            try {
              await refreshUserCredits();
              console.log('User credits refreshed after saving trip');
            } catch (err) {
              console.error('Failed to refresh credits after saving trip:', err);
            }
          }
          
        } catch (error: any) {
          // If we get a 409 conflict error, ask the user if they want to update the existing trip
          if (error.message && error.message.includes('similar trip already exists')) {
            console.log('Trip already exists, asking user if they want to update it');
            
            // Set updateExisting flag to true and try again
            const confirmUpdate = window.confirm(
              'A similar trip already exists. Would you like to update the existing trip instead?'
            );
            
            if (confirmUpdate) {
              const updatedTripData = {
                ...tripData,
                formData: {
                  ...tripData.formData,
                  updateExisting: true
                }
              };
              
              console.log('Updating existing trip with same hash');
              savedTrip = await saveTrip(updatedTripData);
              console.log('Existing trip updated with ID:', savedTrip.id);
              setCurrentTripId(savedTrip.id);
              notifySuccess('Existing trip updated successfully!');
            } else {
              throw error; // Re-throw the error if user doesn't want to update
            }
          } else {
            throw error; // Re-throw other errors
          }
        }
      }

      // Clear unsaved changes after successful save
      setHasUnsavedChanges(false);
      setItinerary(localItinerary);
      localStorage.removeItem('unsavedItinerary');
      
      console.log('Trip save process completed successfully', {
        tripId: savedTrip.id,
        destination: savedTrip.formData?.destination,
        hasItinerary: !!savedTrip.itinerary,
        itineraryDays: savedTrip.itinerary?.days?.length || 0
      });
    } catch (error: any) {
      console.error('Error saving trip:', error);
      console.error('Error details:', {
        message: error.message,
        stack: error.stack,
        name: error.name
      });
      
      // Check if it's an auth error and provide better feedback
      if (error instanceof Error && (error.message.includes('401') || error.message.includes('expired') || error.message.includes('Authentication'))) {
        notifyError('Your session has expired. Please sign in again to save changes.', user?.email);
      } else {
        notifyError(error.message || 'Failed to save trip. Please try again.', user?.email);
      }
    } finally {
      setIsSaving(false);
    }
  };

  // Add useEffect to restore unsaved changes from localStorage
  useEffect(() => {
    // If we've explicitly set both state values to null, don't restore from localStorage
    // This case happens when we're creating a new trip
    if (itinerary === null && localItinerary === null) {
      console.log('Skipping localStorage restoration as we are creating a new trip');
      return;
    }
    
    const unsavedItinerary = localStorage.getItem('unsavedItinerary');
    if (unsavedItinerary) {
      try {
        console.log('Found unsaved itinerary in localStorage');
        const parsed = JSON.parse(unsavedItinerary) as TripItinerary;
        if (parsed && typeof parsed === 'object') {
          console.log('Restored unsaved itinerary:', {
            hasItinerary: !!parsed,
            hasDays: Array.isArray(parsed.days),
            daysCount: Array.isArray(parsed.days) ? parsed.days.length : 0
          });
          setLocalItinerary(parsed);
          setHasUnsavedChanges(true);
        } else {
          console.error('Invalid unsaved itinerary format:', parsed);
          localStorage.removeItem('unsavedItinerary');
        }
      } catch (e) {
        console.error('Error restoring unsaved changes:', e);
        localStorage.removeItem('unsavedItinerary');
      }
    } else if (itinerary && !localItinerary) {
      // Initialize localItinerary with itinerary if it exists
      console.log('Initializing localItinerary with current itinerary');
      setLocalItinerary(itinerary);
    }
  }, [itinerary, localItinerary]);

  const refreshActivity = async (dayIndex: number, activityIndex: number, activity: Activity, customPreferences?: string) => {
    if (!user || !formData) {
      notifyError('Please sign in to refresh activities', user?.email);
      return;
    }

    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/refresh-activity`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          day_index: dayIndex,
          activity_index: activityIndex,
          activity: activity,
          custom_preferences: customPreferences || ''
        })
      });

      if (!response.ok) {
        throw new Error('Failed to refresh activity');
      }

      const data = await response.json();
      
      if (data.success && data.activity && itinerary) {
        // Create new itinerary with updated activity
        const newItinerary = {
          ...itinerary,
          days: itinerary.days.map((day, dIndex) => {
            if (dIndex === dayIndex) {
              return {
                ...day,
                activities: day.activities.map((act, aIndex) => {
                  if (aIndex === activityIndex) {
                    return data.activity;
                  }
                  return act;
                })
              };
            }
            return day;
          })
        };

        // Update both states
        setItinerary(newItinerary);
        setLocalItinerary(newItinerary);
        setHasUnsavedChanges(true);
        
        notifySuccess('Activity refreshed successfully!');
      } else {
        throw new Error('Invalid response format');
      }
    } catch (error: any) {
      console.error('Error refreshing activity:', error);
      notifyError('Failed to refresh activity. Please try again.', user?.email);
      throw error;
    }
  };

  const handleActivityDelete = (dayIndex: number, activityIndex: number) => {
    if (!itinerary) return;
    
    const newItinerary = {
      ...itinerary,
      days: itinerary.days.map((day, dIndex) => {
        if (dIndex === dayIndex) {
          return {
            ...day,
            activities: day.activities.filter((_, aIndex) => aIndex !== activityIndex)
          };
        }
        return day;
      })
    };
    
    setItinerary(newItinerary);
    setLocalItinerary(newItinerary);
    setHasUnsavedChanges(true);
  };

  const handleTitleSave = async () => {
    if (!itinerary || !editedTitle || !currentTripId || !user || !formData) {
      notifyError('Cannot save title: Missing required data', user?.email);
      return;
    }
    
    try {
      setIsSaving(true);
      
      // Ensure we have a valid token before making the request
      const validToken = await ensureValidToken();
      if (!validToken) {
        notifyError('Authentication expired. Please sign in again.', user?.email);
        return;
      }
      
      const newItinerary = {
        ...itinerary,
        title: editedTitle,
        days: itinerary.days.map(day => ({ ...day })), // Deep clone days
        isOwner: itinerary.isOwner // Preserve ownership
      };
      
      // Save to backend
      const tripData = {
        userId: user.id,
        formData: formData,
        itinerary: newItinerary
      };
      
      await updateTrip(currentTripId, tripData);
      
      // Update both local and main itinerary states
      setItinerary(newItinerary);
      setLocalItinerary(newItinerary);
      setIsEditingTitle(false);
      setHasUnsavedChanges(false);
      notifySuccess('Title updated successfully');
      
      // Force a page refresh for the trips list if we're on that page
      if (window.location.pathname === '/trips') {
        window.location.reload();
      }
    } catch (error: any) {
      console.error('Error saving title:', error);
      
      // Check if it's an auth error and provide better feedback
      if (error instanceof Error && error.message.includes('401')) {
        notifyError('Authentication expired. Please sign in again.', user?.email);
      } else {
        notifyError('Failed to save title', user?.email);
      }
    } finally {
      setIsSaving(false);
    }
  };

  // Create dynamic SEO data based on the current trip
  const getSeoData = () => {
    if (!formData) {
      return {
        title: 'Create Your Travel Itinerary - Travel Planner AI',
        description: 'Plan your perfect trip with our AI-powered travel planner. Create personalized itineraries based on your preferences.',
        url: '/'
      };
    }
    
    const destination = formData.destination;
    const tripDates = formData.startDate && formData.endDate 
      ? `${new Date(formData.startDate).toLocaleDateString()} - ${new Date(formData.endDate).toLocaleDateString()}`
      : 'Upcoming trip';
    
    return {
      title: `${destination} Trip Itinerary - Travel Planner AI`,
      description: `View your personalized travel itinerary for ${destination} (${tripDates}). Day-by-day activities and recommendations.`,
      url: currentTripId ? `/?tripId=${currentTripId}` : '/'
    };
  };

  const seoData = getSeoData();

  return (
    <div className="App">
      <SEO 
        title={seoData.title}
        description={seoData.description}
        url={seoData.url}
      />
      
      <Container fluid className="p-0 min-vh-100 d-flex flex-column">
        <Row className="g-0">
          <Col md={4} className="border-end shadow-sm order-2 order-md-1" style={{ maxHeight: '100vh', overflowY: 'auto' }}>
            <div className="p-2">
              <div className="bg-light p-2 rounded shadow-sm">
                <div className="d-flex justify-content-end align-items-center mb-3">
                  <div className="d-flex align-items-center">
                    <LoggingToggle />
                    {!user ? (
                      !isReadOnlyMode && (
                        <div className="d-flex align-items-center">
                          <Button
                            variant="outline-primary"
                            size="sm"
                            onClick={() => navigate('/faq')}
                            className="rounded-pill me-2"
                          >
                            FAQ
                          </Button>
                        </div>
                      )
                    ) : (
                      <div className="d-flex flex-wrap align-items-center gap-2">
                        <CreditsDisplay />
                        <Button 
                          variant="outline-primary" 
                          size="sm" 
                          onClick={() => navigate('/trips')}
                          className="rounded-pill"
                        >
                          <FaList className="me-1" /> My Trips
                        </Button>
                        <Button 
                          variant="outline-primary"
                          size="sm" 
                          onClick={() => navigate('/faq')}
                          className="rounded-pill"
                        >
                          FAQ
                        </Button>
                        <Button 
                          variant="outline-danger" 
                          size="sm" 
                          onClick={signOut}
                          className="rounded-pill"
                        >
                          Sign Out
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
                <div className="mb-4">
                  <div className="d-flex align-items-center">
                    <FaPlaneDeparture className="me-2 text-secondary" size={20} />
                    <h2 className="text-primary-dark m-0 fs-4">Travel Planner AI</h2>
                  </div>
                </div>
                <TripForm onSubmit={handleSubmit} isLoading={isLoading} user={user} />
              </div>
            </div>
          </Col>

          <Col md={8} className="bg-light order-1 order-md-2">
            <div className="p-4">
              {isLoading ? (
                <div className="text-center py-5">
                  <div className="spinner-border text-primary mb-4" role="status" style={{ width: '3rem', height: '3rem' }}>
                    <span className="visually-hidden">Loading...</span>
                  </div>
                  <h4 className="text-primary-dark mb-4">Generating your perfect trip...</h4>
                  <TripLoadingHints className="mt-4" />
                </div>
              ) : itinerary ? (
                <div>
                  {(isReadOnlyMode || !user) && (
                    <ReadOnlyBanner isReadOnlyMode={isReadOnlyMode} user={user} />
                  )}
                  <div className="d-flex align-items-center justify-content-between flex-wrap gap-3 mb-4">
                    {isEditingTitle ? (
                      <div className="d-flex align-items-center gap-2">
                        <input
                          type="text"
                          className="form-control"
                          value={editedTitle}
                          onChange={(e) => setEditedTitle(e.target.value)}
                          autoFocus
                        />
                        <Button 
                          variant="outline-primary"
                          size="sm"
                          onClick={handleTitleSave}
                        >
                          <FaSave size={14} />
                        </Button>
                      </div>
                    ) : (
                      <div className="d-flex align-items-center gap-2 flex-wrap">
                        <div className="d-flex align-items-center gap-2">
                          <h3 className="text-primary-dark m-0 fs-5">
                            {getTripTitle()}
                          </h3>
                          <div className="d-flex gap-2 align-items-center">
                            <Button 
                              variant="link"
                              size="sm"
                              className="p-0 text-secondary"
                              onClick={() => {
                                setEditedTitle(getTripTitle());
                                setIsEditingTitle(true);
                              }}
                            >
                              <FaEdit size={14} />
                            </Button>
                            {itinerary && formData && (
                              <TripTitleExport itinerary={itinerary} formData={formData} />
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                    <div className="d-flex gap-2 flex-wrap">
                      {user ? (
                        <>
                          <Button
                            variant="primary"
                            onClick={handleSaveTrip}
                            disabled={isSaving || !hasUnsavedChanges || isReadOnlyMode}
                            className="d-flex align-items-center justify-content-center"
                            style={{ width: '40px', height: '40px', padding: '0' }}
                            title="Save Changes"
                          >
                            {isSaving ? (
                              <span className="spinner-border spinner-border-sm" />
                            ) : (
                              <FaSave size={18} />
                            )}
                          </Button>
                          {currentTripId && itinerary && formData && (
                            <Dropdown>
                              <Dropdown.Toggle
                                variant="outline-primary"
                                id="share-dropdown-button"
                                className="d-flex align-items-center justify-content-center"
                                style={{ width: '40px', height: '40px', padding: '0' }}
                                title="Share"
                              >
                                <FaShareAlt size={18} />
                              </Dropdown.Toggle>
                              <Dropdown.Menu>
                                <Dropdown.Item
                                  onClick={() => {
                                    const shareUrl = `${window.location.origin}/?tripId=${currentTripId}`;
                                    navigator.clipboard.writeText(shareUrl);
                                    notifySuccess('Share URL copied to clipboard!');
                                  }}
                                >
                                  <FaCopy className="me-2" />
                                  Copy Link
                                </Dropdown.Item>
                                <Dropdown.Divider />
                                <Dropdown.Item 
                                  as="button" 
                                  onClick={() => { 
                                    const shareUrl = encodeURIComponent(window.location.href);
                                    const shareTitle = encodeURIComponent(`Check out my trip to ${formData.destination}!`);
                                    const whatsappUrl = `https://wa.me/?text=${shareTitle}%20${shareUrl}`;
                                    window.open(whatsappUrl, '_blank', 'noopener,noreferrer');
                                    notifySuccess('WhatsApp share window opened!');
                                  }}
                                >
                                  <FaWhatsapp className="me-2 text-success" />
                                  Share via WhatsApp
                                </Dropdown.Item>
                                <Dropdown.Item 
                                  as="button" 
                                  onClick={() => { 
                                    const shareUrl = encodeURIComponent(window.location.href);
                                    const shareTitle = encodeURIComponent(`Check out my trip to ${formData.destination}!`);
                                    const telegramUrl = `https://t.me/share/url?url=${shareUrl}&text=${shareTitle}`;
                                    window.open(telegramUrl, '_blank', 'noopener,noreferrer');
                                    notifySuccess('Telegram share window opened!');
                                  }}
                                >
                                  <FaTelegram className="me-2 text-primary" />
                                  Share via Telegram
                                </Dropdown.Item>
                                <Dropdown.Item 
                                  as="button" 
                                  onClick={() => { 
                                    // For Facebook, we only need the URL
                                    const shareUrl = encodeURIComponent(window.location.href);
                                    const facebookUrl = `https://www.facebook.com/sharer/sharer.php?u=${shareUrl}`;
                                    window.open(facebookUrl, '_blank', 'noopener,noreferrer');
                                    notifySuccess('Facebook share window opened!');
                                  }}
                                >
                                  <FaFacebook className="me-2 text-primary" />
                                  Share via Facebook
                                </Dropdown.Item>
                                <Dropdown.Divider />
                                <Dropdown.Item 
                                  as="button" 
                                  onClick={() => { 
                                    // Generate trip description
                                    let description = `Trip to ${formData.destination}\n`;
                                    description += `${formData.startDate} - ${formData.endDate}\n\n`;
                                    
                                    itinerary.days.forEach((day, index) => {
                                      description += `Day ${index + 1} - ${day.date}:\n`;
                                      day.activities.forEach(activity => {
                                        description += `  ${activity.time} - ${activity.description}\n`;
                                      });
                                      description += '\n';
                                    });
                                    
                                    // Create and download text file
                                    const blob = new Blob([description], { type: 'text/plain' });
                                    const url = window.URL.createObjectURL(blob);
                                    const link = document.createElement('a');
                                    link.href = url;
                                    link.setAttribute('download', `trip-to-${formData.destination}.txt`);
                                    document.body.appendChild(link);
                                    link.click();
                                    document.body.removeChild(link);
                                    window.URL.revokeObjectURL(url);
                                    notifySuccess('Text file exported successfully!');
                                  }}
                                >
                                  <FaFileAlt className="me-2" />
                                  Export as Text
                                </Dropdown.Item>
                                <Dropdown.Item 
                                  as="button" 
                                  onClick={() => { 
                                    // Create and download JSON file
                                    const data = {
                                      formData,
                                      itinerary
                                    };
                                    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                                    const url = window.URL.createObjectURL(blob);
                                    const link = document.createElement('a');
                                    link.href = url;
                                    link.setAttribute('download', `trip-to-${formData.destination}.json`);
                                    document.body.appendChild(link);
                                    link.click();
                                    document.body.removeChild(link);
                                    window.URL.revokeObjectURL(url);
                                    notifySuccess('JSON file exported successfully!');
                                  }}
                                >
                                  <FaFileDownload className="me-2" />
                                  Export as JSON
                                </Dropdown.Item>
                                <Dropdown.Item 
                                  as="button" 
                                  onClick={() => { 
                                    // Generate trip description for calendar
                                    let description = `Trip to ${formData.destination}\n\n`;
                                    
                                    itinerary.days.forEach((day, index) => {
                                      description += `Day ${index + 1} - ${day.date}:\n`;
                                      day.activities.forEach(activity => {
                                        description += `  ${activity.time} - ${activity.description}\n`;
                                      });
                                      description += '\n';
                                    });
                                    
                                    // Create calendar file
                                    const calendar = ical();
                                    const startDate = new Date(formData.startDate);
                                    const endDate = new Date(formData.endDate);
                                    
                                    calendar.createEvent({
                                      start: startDate,
                                      end: endDate,
                                      summary: `Trip to ${formData.destination}`,
                                      description: description,
                                      location: formData.destination
                                    });
                                    
                                    // Download calendar file
                                    const blob = new Blob([calendar.toString()], { type: 'text/calendar' });
                                    const url = window.URL.createObjectURL(blob);
                                    const link = document.createElement('a');
                                    link.href = url;
                                    link.setAttribute('download', `trip-to-${formData.destination}.ics`);
                                    document.body.appendChild(link);
                                    link.click();
                                    document.body.removeChild(link);
                                    window.URL.revokeObjectURL(url);
                                    notifySuccess('Calendar file exported successfully!');
                                  }}
                                >
                                  <FaCalendarAlt className="me-2" />
                                  Add to Calendar (ICS)
                                </Dropdown.Item>
                                <Dropdown.Item 
                                  as="button" 
                                  onClick={async () => { 
                                    try {
                                      // Generate trip description
                                      let description = `Trip to ${formData.destination}\n`;
                                      description += `${formData.startDate} - ${formData.endDate}\n\n`;
                                      
                                      itinerary.days.forEach((day, index) => {
                                        description += `Day ${index + 1} - ${day.date}:\n`;
                                        day.activities.forEach(activity => {
                                          description += `  ${activity.time} - ${activity.description}\n`;
                                        });
                                        description += '\n';
                                      });
                                      
                                      // Copy to clipboard
                                      await navigator.clipboard.writeText(description);
                                      notifySuccess('Trip details copied to clipboard!');
                                    } catch (error) {
                                      notifyError('Failed to copy trip details to clipboard', user?.email);
                                    }
                                  }}
                                >
                                  <FaCopy className="me-2" />
                                  Copy to Clipboard
                                </Dropdown.Item>
                              </Dropdown.Menu>
                            </Dropdown>
                          )}
                        </>
                      ) : (
                        <div className="d-flex align-items-center gap-2">
                          <Button
                            variant="outline-primary"
                            disabled
                            className="d-flex align-items-center gap-2"
                            style={{ minWidth: '140px' }}
                          >
                            <FaSave />
                            Save Trip
                          </Button>
                          <small className="text-muted">
                            Sign in to save
                          </small>
                        </div>
                      )}
                    </div>
                  </div>
                  <Itinerary 
                    itinerary={itinerary}
                    onActivityUpdate={handleActivityUpdate}
                    onActivityDelete={handleActivityDelete}
                    onActivityRefresh={refreshActivity}
                    isLoading={isLoading}
                    isOwner={itinerary?.isOwner}
                    isReadOnly={isReadOnlyMode}
                    formData={formData || undefined}
                  />
                </div>
              ) : (
                <div className="text-center py-1">
                  {!user && (
                    <ReadOnlyBanner isReadOnlyMode={false} user={user} />
                  )}
                  <div className="bg-white p-5 rounded shadow-sm">
                    <h3 className="text-primary-dark mb-3">Plan Your Dream Trip</h3>
                    <p className="text-secondary mb-4">Fill out the form to get your personalized travel itinerary</p>
                    <div className="text-center">
                      <FaPlaneDeparture size={100} className="text-secondary opacity-50" />
                    </div>
                  </div>
                </div>
              )}
            </div>
          </Col>
        </Row>
        <ToastContainer
          position="top-right"
          autoClose={3000}
          hideProgressBar={false}
          newestOnTop
          closeOnClick
          rtl={false}
          pauseOnFocusLoss
          draggable
          pauseOnHover
          theme="colored"
          toastStyle={{
            backgroundColor: '#363636',
            color: '#fff'
          }}
        />
      </Container>
    </div>
  );
};

const App = () => {
  return (
    <Router>
      <div className="App">
        <ToastContainer position="top-right" autoClose={5000} />
        <Routes>
          <Route path="/auth/callback" element={<AuthCallback />} />
          <Route path="/" element={<MainApp />} />
          <Route path="/trips" element={<TripList />} />
          <Route path="/credits" element={<Credits />} />
          <Route path="/faq" element={
            <>
              <SEO 
                title="FAQ - Travel Planner AI"
                description="Frequently asked questions about Travel Planner AI. Learn how to use our platform effectively."
                url="/faq"
              />
              <FaqPage />
            </>
          } />
        </Routes>
      </div>
    </Router>
  );
};

export default App;