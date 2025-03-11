import * as React from 'react';
import { useState, useEffect } from 'react';
import { Container, Row, Col, Button } from 'react-bootstrap';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate, useLocation, useSearchParams } from 'react-router-dom';
import TripForm from './components/TripForm';
import Itinerary from './components/Itinerary';
import { TripFormData, TripItinerary, Activity } from './types';
import 'bootstrap/dist/css/bootstrap.min.css';
import { FaPlaneDeparture, FaEdit, FaSave, FaList } from 'react-icons/fa';
import { useAuth } from './contexts/AuthContext';
import AuthForm from './components/AuthForm';
import { saveTrip, updateTrip, getUserTrips } from './services/tripService';
import { toast } from 'react-toastify';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import TripList from './pages/TripList';

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

  // Load trip if tripId is in URL
  useEffect(() => {
    const tripId = searchParams.get('tripId');
    if (tripId && user) {
      const loadTrip = async () => {
        setIsLoading(true);
        try {
          // Direct API call to get a specific trip instead of filtering from all trips
          const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/trips/${tripId}`, {
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
            },
            credentials: 'include',
          });
          
          if (!response.ok) {
            throw new Error(`Failed to load trip: ${response.statusText}`);
          }
          
          const trip = await response.json();
          
          if (trip) {
            setFormData(trip.formData);
            setItinerary(trip.itinerary);
            setLocalItinerary(trip.itinerary);
            setCurrentTripId(trip.id);
            setHasUnsavedChanges(false);
            toast.success('Trip loaded successfully!');
          } else {
            toast.error('Trip not found');
          }
        } catch (error) {
          console.error('Error loading trip:', error);
          toast.error('Failed to load trip');
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

      const newItinerary = await generateItinerary(data);
      if (newItinerary) {
        setItinerary(newItinerary);
        setLocalItinerary(newItinerary);
        setHasUnsavedChanges(true);
        toast.success('Trip generated successfully!');
      }
    } catch (error) {
      console.error('Error:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to generate itinerary');
    } finally {
      setIsLoading(false);
    }
  };

  const getTripTitle = () => {
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
      toast.error('Please log in and generate an itinerary first');
      return;
    }

    setIsSaving(true);
    try {
      const tripData = {
        userId: user.id,
        formData,
        itinerary: localItinerary
      };
      
      let savedTrip;
      if (currentTripId) {
        savedTrip = await updateTrip(currentTripId, tripData);
        toast.success('Trip updated successfully!');
      } else {
        savedTrip = await saveTrip(tripData);
        setCurrentTripId(savedTrip.id);
        toast.success('Trip saved successfully!');
      }

      // Clear unsaved changes after successful save
      setHasUnsavedChanges(false);
      setItinerary(localItinerary);
      localStorage.removeItem('unsavedItinerary');
    } catch (error: any) {
      console.error('Error saving trip:', error);
      toast.error(error.message || 'Failed to save trip. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  // Add useEffect to restore unsaved changes from localStorage
  useEffect(() => {
    const unsavedItinerary = localStorage.getItem('unsavedItinerary');
    if (unsavedItinerary && itinerary) { // Add itinerary check
      try {
        const parsed = JSON.parse(unsavedItinerary) as TripItinerary;
        if (parsed.tripId && Array.isArray(parsed.days)) { // Validate structure
          setLocalItinerary(parsed);
          setHasUnsavedChanges(true);
        }
      } catch (e) {
        console.error('Error restoring unsaved changes:', e);
        localStorage.removeItem('unsavedItinerary');
      }
    }
  }, [itinerary]); // Add itinerary as dependency

  const generateItinerary = async (formData: TripFormData) => {
    if (!user) {
      toast.error('Please sign in to generate an itinerary');
      return null;
    }

    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/generate-itinerary`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          userId: user.id,
          formData: {
            ...formData,
            origin: formData.origin || '',
            destination: formData.destination,
            startDate: formData.startDate,
            endDate: formData.endDate,
            travelType: formData.travelType,
            adults: formData.adults,
            children: formData.children || 0,
            infants: formData.infants || 0,
            budgetLevel: formData.budgetLevel,
            entertainmentPreferences: formData.entertainmentPreferences || [],
            intermediateStops: formData.intermediateStops || []
          }
        })
      });

      let errorMessage = 'Failed to generate itinerary';
      
      try {
        const data = await response.json();
        
        if (!response.ok) {
          errorMessage = `Error (${response.status}): ${data.detail || 'Unknown error'}`;
          console.error('API Error:', {
            status: response.status,
            data: data,
            user: user.email
          });
          throw new Error(errorMessage);
        }

        if (!data.success || !data.itinerary) {
          throw new Error('Invalid response format from server');
        }

        return data.itinerary;
      } catch (parseError) {
        console.error('Response parsing error:', parseError);
        throw new Error(`Server error: ${errorMessage}. Please try again later.`);
      }
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Unknown error occurred';
      console.error('Trip generation error:', {
        error,
        user: user.email,
        formData
      });
      toast.error(`Dear ${user.email}, there was an error: ${errorMsg}`);
      throw error;
    }
  };

  const refreshActivity = async (dayIndex: number, activityIndex: number, activity: Activity) => {
    if (!user || !formData) {
      toast.error('Please sign in to refresh activities');
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
        
        toast.success('Activity refreshed successfully!');
      } else {
        throw new Error('Invalid response format');
      }
    } catch (error) {
      console.error('Error refreshing activity:', error);
      toast.error('Failed to refresh activity. Please try again.');
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
    if (!itinerary || !editedTitle) return;
    
    try {
      setIsSaving(true);
      const newItinerary = {
        ...itinerary,
        title: editedTitle
      };
      
      setItinerary(newItinerary);
      setLocalItinerary(newItinerary);
      setIsEditingTitle(false);
      setHasUnsavedChanges(true);
      toast.success('Title updated successfully');
    } catch (error) {
      console.error('Error saving title:', error);
      toast.error('Failed to save title');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Container fluid className="p-0 min-vh-100 d-flex flex-column">
      <Row className="g-0">
        <Col md={4} className="border-end shadow-sm" style={{ maxHeight: '100vh', overflowY: 'auto' }}>
          <div className="p-2">
            <div className="bg-light p-2 rounded shadow-sm">
              <div className="d-flex align-items-center justify-content-between mb-2">
                <div className="d-flex align-items-center">
                  <FaPlaneDeparture className="me-2 text-secondary" size={20} />
                  <h2 className="text-primary-dark m-0 fs-4">Travel Planner AI</h2>
                </div>
                {!user ? (
                  <AuthForm />
                ) : (
                  <div className="d-flex align-items-center gap-2">
                    <UserAvatar name={user.name} />
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
                  </div>
                )}
              </div>
              <TripForm onSubmit={handleSubmit} isLoading={isLoading} />
              {!user && <SignInPrompt />}
            </div>
          </div>
        </Col>

        <Col md={8} className="bg-light">
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
                <div className="d-flex align-items-center justify-content-between mb-4">
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
                    <div className="d-flex align-items-center gap-2">
                      <h3 className="text-primary-dark m-0">
                        {getTripTitle()}
                      </h3>
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
                    </div>
                  )}
                  <div className="d-flex gap-2">
                    {user ? (
                      <Button
                        variant="primary"
                        onClick={handleSaveTrip}
                        disabled={isSaving || !hasUnsavedChanges}
                        className="d-flex align-items-center gap-2"
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
                    ) : (
                      <div className="d-flex align-items-center gap-2">
                        <Button
                          variant="outline-primary"
                          disabled
                          className="d-flex align-items-center gap-2"
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