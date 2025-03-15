import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Button, Spinner, Alert, Navbar } from 'react-bootstrap';
import { FaTrash, FaEye, FaPlane, FaTrain, FaCar, FaBus, FaShip, FaArrowLeft, FaClock } from 'react-icons/fa';
import { useAuth } from '../contexts/AuthContext';
import { getUserTrips } from '../services/tripService';
import { format, formatDistance } from 'date-fns';
import { useNavigate } from 'react-router-dom';
import '../styles/TripList.css';

// Define Trip interface based on API response
interface Trip {
  id: string;
  user_id: string;
  formData: {
    destination: string;
    origin?: string;
    startDate: string;
    endDate: string;
    travelType: string;
    adults: number;
    children: number;
    infants: number;
    budget: string;
  };
  itinerary: any;
  created_at?: string;
  updated_at?: string;
}

const TripList: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [trips, setTrips] = useState<Trip[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  useEffect(() => {
    const fetchTrips = async () => {
      if (!user) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        const fetchedTrips = await getUserTrips(user.id);
        setTrips(fetchedTrips);
      } catch (err) {
        console.error('Failed to fetch trips:', err);
        setError('Failed to load your trips. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchTrips();
  }, [user]);

  const handleRetry = () => {
    if (user) {
      setLoading(true);
      getUserTrips(user.id)
        .then(fetchedTrips => {
          setTrips(fetchedTrips);
          setError(null);
        })
        .catch(err => {
          console.error('Failed to fetch trips on retry:', err);
          setError('Failed to load your trips. Please try again later.');
        })
        .finally(() => {
          setLoading(false);
        });
    }
  };

  const handleViewTrip = (tripId: string) => {
    // Navigate to the main page with the selected trip ID
    navigate(`/?tripId=${tripId}`);
  };

  const handleDeleteTrip = async (tripId: string) => {
    if (deleteConfirm === tripId) {
      try {
        const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/trips/${tripId}`, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error('Failed to delete trip');
        }

        // Remove trip from state after successful deletion
        setTrips(trips.filter(trip => trip.id !== tripId));
        setDeleteConfirm(null);
      } catch (err) {
        console.error('Error deleting trip:', err);
        setError('Failed to delete trip. Please try again.');
      }
    } else {
      // Set this trip for delete confirmation
      setDeleteConfirm(tripId);
    }
  };

  const getTravelIcon = (travelType: string) => {
    switch (travelType.toLowerCase()) {
      case 'flight':
        return <FaPlane />;
      case 'train':
        return <FaTrain />;
      case 'car':
        return <FaCar />;
      case 'bus':
        return <FaBus />;
      case 'cruise':
        return <FaShip />;
      default:
        return <FaPlane />;
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'MMM dd, yyyy');
    } catch (e) {
      return dateString;
    }
  };

  const formatUpdatedTime = (dateString?: string) => {
    if (!dateString) return 'Never updated';
    
    try {
      const date = new Date(dateString);
      return formatDistance(date, new Date(), { addSuffix: true });
    } catch (e) {
      return 'Unknown';
    }
  };

  if (!user) {
    return (
      <>
        <Navbar bg="light" expand="lg" className="px-3 shadow-sm">
          <Navbar.Brand onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
            <FaPlane className="me-2" />
            Travel Planner AI
          </Navbar.Brand>
          <Button variant="outline-primary" size="sm" onClick={() => navigate('/')}>
            <FaArrowLeft className="me-1" /> Back to Planner
          </Button>
        </Navbar>
        <Container className="mt-5">
          <Alert variant="info">
            Please sign in to see your trips.
          </Alert>
        </Container>
      </>
    );
  }

  return (
    <>
      <Navbar bg="light" expand="lg" className="px-3 shadow-sm">
        <Navbar.Brand onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
          <FaPlane className="me-2" />
          Travel Planner AI
        </Navbar.Brand>
        <Button variant="outline-primary" size="sm" onClick={() => navigate('/')}>
          <FaArrowLeft className="me-1" /> Back to Planner
        </Button>
      </Navbar>
      
      <Container className="trip-list-container mt-4">
        <h1 className="mb-4">My Trips</h1>
        
        {error && (
          <Alert variant="danger" dismissible onClose={() => setError(null)}>
            {error}
            <div className="mt-2">
              <Button variant="outline-danger" size="sm" onClick={handleRetry}>
                Retry
              </Button>
            </div>
          </Alert>
        )}

        {loading ? (
          <div className="text-center my-5">
            <Spinner animation="border" role="status">
              <span className="visually-hidden">Loading...</span>
            </Spinner>
          </div>
        ) : trips.length === 0 && !error ? (
          <Alert variant="light" className="text-center">
            <p className="mb-3">You don't have any trips yet.</p>
            <Button variant="primary" onClick={() => navigate('/')}>
              Plan Your First Trip
            </Button>
          </Alert>
        ) : (
          <Row xs={1} md={2} lg={3} className="g-4">
            {trips.map((trip) => (
              <Col key={trip.id}>
                <Card className="trip-card h-100">
                  <Card.Body>
                    <div className="travel-type-icon">
                      {getTravelIcon(trip.formData.travelType)}
                    </div>
                    <Card.Title className="mb-3">{trip.formData.destination}</Card.Title>
                    <Card.Subtitle className="mb-2 text-muted">
                      {trip.formData.origin ? `From ${trip.formData.origin}` : ''}
                    </Card.Subtitle>
                    <div className="trip-dates mb-3">
                      <div>{formatDate(trip.formData.startDate)} - {formatDate(trip.formData.endDate)}</div>
                    </div>
                    <div className="trip-details mb-3">
                      <div>Travelers: {trip.formData.adults + (trip.formData.children || 0) + (trip.formData.infants || 0)}</div>
                      <div>Budget: {trip.formData.budget}</div>
                    </div>
                    
                    {/* Last Updated Information */}
                    {trip.updated_at && (
                      <div className="trip-updated-info text-muted small mb-3 d-flex align-items-center">
                        <FaClock className="me-1" />
                        Updated: {formatUpdatedTime(trip.updated_at)}
                      </div>
                    )}
                    
                    <div className="d-flex justify-content-between mt-auto">
                      <Button 
                        variant="outline-danger" 
                        size="sm" 
                        onClick={() => handleDeleteTrip(trip.id)}
                        className="d-flex align-items-center"
                      >
                        <FaTrash className="me-1" />
                        {deleteConfirm === trip.id ? 'Confirm' : 'Delete'}
                      </Button>
                      <Button 
                        variant="primary" 
                        size="sm" 
                        onClick={() => handleViewTrip(trip.id)}
                        className="d-flex align-items-center"
                      >
                        <FaEye className="me-1" />
                        View Trip
                      </Button>
                    </div>
                  </Card.Body>
                </Card>
              </Col>
            ))}
          </Row>
        )}
      </Container>
    </>
  );
};

export default TripList; 