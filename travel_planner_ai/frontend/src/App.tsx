import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Button } from 'react-bootstrap';
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation, useSearchParams } from 'react-router-dom';
import TripForm from './components/TripForm';
import Itinerary from './components/Itinerary';
import TripExport from './components/TripExport';
import TripTitleExport from './components/TripTitleExport';
import { TripFormData, TripItinerary, Activity } from './types';
import 'bootstrap/dist/css/bootstrap.min.css';
import { FaPlaneDeparture, FaEdit, FaSave, FaList, FaShare } from 'react-icons/fa';
import { useAuth } from './contexts/AuthContext';
import AuthForm from './components/AuthForm';
import { saveTrip, updateTrip } from './services/tripService';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import TripList from './pages/TripList';
import LoggingToggle from './components/LoggingToggle';
import { notifyError, notifySuccess } from './services/errorService';
import { generateItinerary } from './services/itineraryService';
import './styles/App.css';

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

const SignInPrompt: React.FC = () => (
  <div className="alert alert-warning d-flex align-items-center mt-3" role="alert">
    <div className="d-flex align-items-center">
      <i className="fas fa-exclamation-triangle me-2"></i>
      <div>
        Please <strong>sign in</strong> to save your trips and access them later.
      </div>
    </div>
    <AuthForm />
  </div>
);

const MainApp = () => {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const [isLoading, setIsLoading] = useState(false);
  const [itinerary, setItinerary] = useState<TripItinerary | null>(null);
  const [formData, setFormData] = useState<TripFormData | null>(null);
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [editedTitle, setEditedTitle] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [currentTripId, setCurrentTripId] = useState<string | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [localItinerary, setLocalItinerary] = useState<TripItinerary | null>(null);

  // Use location in a comment to avoid the unused variable warning
  // Current path: ${location.pathname}
  
  // Load trip if tripId is in URL
  useEffect(() => {
    const tripId = searchParams.get('tripId');
    if (tripId && user) {
      const loadTrip = async () => {
        setIsLoading(true);
        try {
          console.log(`Loading trip with ID: ${tripId}`);
          
          // Direct API call to get a specific trip instead of filtering from all trips
          const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/trips/${tripId}`, {
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
            },
            credentials: 'include',
          });
          
          if (!response.ok) {
            const errorText = await response.text();
            console.error(`Failed to load trip: ${response.status} ${response.statusText}`, errorText);
            throw new Error(`Failed to load trip: ${response.statusText}`);
          }
          
          const trip = await response.json();
          console.log('Trip loaded:', trip);
          
          if (trip) {
            if (!trip.formData) {
              console.error('Trip is missing formData:', trip);
              notifyError('Trip data is incomplete', user?.email);
              setIsLoading(false);
              return;
            }
            
            if (!trip.itinerary || !trip.itinerary.days) {
              console.error('Trip is missing itinerary or days:', trip);
              notifyError('Trip itinerary is incomplete', user?.email);
              setIsLoading(false);
              return;
            }
            
            // Ensure isOwner flag is set in the itinerary
            const itineraryWithOwnership = {
              ...trip.itinerary,
              isOwner: trip.isOwner ?? trip.user_id === user.id
            };
            
            console.log('Setting itinerary with ownership:', {
              isOwner: itineraryWithOwnership.isOwner,
              userId: trip.user_id,
              currentUserId: user.id
            });
            
            setFormData(trip.formData);
            setItinerary(itineraryWithOwnership);
            setLocalItinerary(itineraryWithOwnership);
            setCurrentTripId(trip.id);
            setHasUnsavedChanges(false);
            notifySuccess('Trip loaded successfully!');
          } else {
            console.error('Trip not found in response');
            notifyError('Trip not found', user?.email);
          }
        } catch (error) {
          console.error('Error loading trip:', error);
          notifyError(error instanceof Error ? error.message : 'Failed to load trip', user?.email);
        } finally {
          setIsLoading(false);
        }
      };
      
      loadTrip();
    }
  }, [searchParams, user]);

  const handleSubmit = async (data: TripFormData) => {
    setIsLoading(true);
    setFormData(data);
    setCurrentTripId(null);

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
        setItinerary(newItinerary);
        setLocalItinerary(newItinerary);
        
        // Auto-save the trip
        try {
          const tripData = {
            userId: user.id,
            formData: {
              ...data,
              updateExisting: true // Always try to update if exists
            },
            itinerary: newItinerary
          };
          
          const savedTrip = await saveTrip(tripData);
          setCurrentTripId(savedTrip.id);
          setHasUnsavedChanges(false);
          notifySuccess('Trip generated and saved successfully!');
          // Update URL without redirecting
          window.history.replaceState(null, '', `/?tripId=${savedTrip.id}`);
        } catch (saveError: any) {
          console.error('Error saving trip:', saveError);
          setHasUnsavedChanges(true);
          
          // If it's not a conflict error, show generic error
          if (!saveError.message?.includes('similar trip already exists')) {
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
                itinerary: newItinerary
              };
              
              const savedTrip = await saveTrip(tripData);
              setCurrentTripId(savedTrip.id);
              setHasUnsavedChanges(false);
              notifySuccess('Existing trip updated successfully!');
              window.history.replaceState(null, '', `/?tripId=${savedTrip.id}`);
            } catch (updateError) {
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
    } catch (error) {
      console.error('Error generating trip:', error);
      notifyError(error instanceof Error ? error.message : 'Failed to generate trip', user?.email);
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
    const startDate = formData.startDate ? new Date(formData.startDate).toLocaleDateString() : '';
    const endDate = formData.endDate ? new Date(formData.endDate).toLocaleDateString() : '';
    
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
      notifyError(error.message || 'Failed to save trip. Please try again.', user?.email);
    } finally {
      setIsSaving(false);
    }
  };

  // Add useEffect to restore unsaved changes from localStorage
  useEffect(() => {
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

  const refreshActivity = async (dayIndex: number, activityIndex: number, activity: Activity) => {
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
          activity: activity
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
    } catch (error) {
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
    } catch (error) {
      console.error('Error saving title:', error);
      notifyError('Failed to save title', user?.email);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Container fluid className="p-0 min-vh-100 d-flex flex-column">
      <Row className="g-0">
        <Col md={4} className="border-end shadow-sm order-2 order-md-1" style={{ maxHeight: '100vh', overflowY: 'auto' }}>
          <div className="p-2">
            <div className="bg-light p-2 rounded shadow-sm">
              <div className="d-flex justify-content-between align-items-center mb-4">
                <div className="d-flex align-items-center">
                  <FaPlaneDeparture className="me-2 text-secondary" size={20} />
                  <h2 className="text-primary-dark m-0 fs-4">Travel Planner AI</h2>
                </div>
                <div className="d-flex align-items-center">
                  <LoggingToggle />
                  {!user ? (
                    <AuthForm />
                  ) : (
                    <div className="d-flex">
                      <Button 
                        variant="outline-primary" 
                        size="sm" 
                        onClick={() => navigate('/trips')}
                        className="rounded-pill me-2"
                      >
                        <FaList className="me-1" /> My Trips
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
              <TripForm onSubmit={handleSubmit} isLoading={isLoading} />
              {!user && <SignInPrompt />}
            </div>
          </div>
        </Col>

        <Col md={8} className="bg-light order-1 order-md-2">
          <div className="p-4">
            {isLoading ? (
              <div className="text-center py-5">
                <div className="spinner-border text-primary" role="status">
                  <span className="visually-hidden">Loading...</span>
                </div>
                <p className="mt-2 text-primary-dark">Generating your perfect trip...</p>
              </div>
            ) : itinerary ? (
              <div>
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
                        <h3 className="text-primary-dark m-0">
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
                          disabled={isSaving || !hasUnsavedChanges}
                          className="d-flex align-items-center gap-2"
                          style={{ minWidth: '140px' }}
                        >
                          {isSaving ? (
                            <>
                              <span className="spinner-border spinner-border-sm" />
                              Saving...
                            </>
                          ) : (
                            <>
                              <FaSave />
                              {hasUnsavedChanges ? 'Save Changes' : 'Saved'}
                            </>
                          )}
                        </Button>
                        {currentTripId && itinerary && formData && (
                          <div className="dropdown">
                            <Button
                              variant="outline-primary"
                              className="dropdown-toggle d-flex align-items-center gap-2"
                              data-bs-toggle="dropdown"
                              aria-expanded="false"
                            >
                              <FaShare className="me-1" />
                              Share
                            </Button>
                            <ul className="dropdown-menu">
                              <li>
                                <Button
                                  variant="link"
                                  className="dropdown-item"
                                  onClick={() => {
                                    const shareUrl = `${window.location.origin}/?tripId=${currentTripId}`;
                                    navigator.clipboard.writeText(shareUrl);
                                    notifySuccess('Share URL copied to clipboard!');
                                  }}
                                >
                                  Copy Link
                                </Button>
                              </li>
                              <li>
                                <TripExport itinerary={itinerary} formData={formData} />
                              </li>
                            </ul>
                          </div>
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
                  isOwner={itinerary?.isOwner ?? false}
                />
              </div>
            ) : (
              <div className="text-center py-5">
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
  );
};

const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<MainApp />} />
        <Route path="/trips" element={<TripList />} />
      </Routes>
    </Router>
  );
};

export default App;