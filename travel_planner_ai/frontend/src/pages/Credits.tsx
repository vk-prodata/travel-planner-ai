import React, { useEffect, useState } from 'react';
import { Container, Row, Col, Card, Button, Alert, Navbar, Spinner } from 'react-bootstrap';
import { FaCoins, FaArrowLeft, FaPlane } from 'react-icons/fa';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { getUserCredits, CREDIT_PACKAGES } from '../services/creditsService';
import { notifyError } from '../services/errorService';
import LoggingToggle from '../components/LoggingToggle';
import '../styles/Credits.css';

const Credits: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [availableCredits, setAvailableCredits] = useState(0);
  
  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }
    
    const fetchCredits = async () => {
      try {
        setLoading(true);
        setError(null);
        const creditsData = await getUserCredits(user.id);
        console.log('Credits data received from API:', creditsData);
        
        // Handle both naming conventions from backend
        setAvailableCredits(
          creditsData.availableCredits !== undefined 
            ? creditsData.availableCredits 
            : creditsData.available_credits || 0
        );
      } catch (err) {
        console.error('Failed to fetch credits:', err);
        setError('Failed to load your credits. Please try again later.');
        notifyError(err, user?.email);
      } finally {
        setLoading(false);
      }
    };
    
    const queryParams = new URLSearchParams(location.search);
    const purchaseStatus = queryParams.get('purchase');

    if (user && purchaseStatus === 'success') {
      console.log('Detected purchase success, fetching updated credits...');
      navigate(location.pathname, { replace: true });
      fetchCredits();
    } else if (user) {
      fetchCredits();
    } else {
      setLoading(false);
    }
  }, [user, location.search, navigate]);
  
  const handleStripeRedirect = (packageId: string) => {
    if (!user) {
      setError('You must be logged in to purchase credits.');
      return;
    }

    // Get link from environment variables based on package ID
    let stripeLink: string | undefined;
    if (packageId === 'basic') {
      stripeLink = process.env.REACT_APP_STRIPE_LINK_BASIC;
    } else if (packageId === 'premium') { // Check for 'premium' ID from frontend package list
      stripeLink = process.env.REACT_APP_STRIPE_LINK_PREMIUM;
    } else {
      // Handle potential future packages or log an error
      console.error(`No Stripe link configured for package ID: ${packageId}`);
    }

    if (!stripeLink) {
      setError('Sorry, this purchase option is currently unavailable. Please check configuration.');
      console.error('Stripe link environment variable not found or invalid for packageId:', packageId);
      return;
    }

    // Construct the redirect URL with user info
    const redirectUrl = `${stripeLink}?client_reference_id=${encodeURIComponent(user.id)}&prefilled_email=${encodeURIComponent(user.email)}`;
    
    console.log(`Redirecting user ${user.email} to Stripe for package ${packageId}: ${redirectUrl}`);
    window.location.href = redirectUrl;
  };
  
  if (!user) {
    return (
      <>
        <Navbar bg="light" expand="lg" className="px-3 shadow-sm">
          <Navbar.Brand onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
            <FaPlane className="me-2" />
            Travel Planner AI
          </Navbar.Brand>
          <div className="d-flex align-items-center">
            <LoggingToggle />
            <Button variant="outline-primary" size="sm" onClick={() => navigate('/')} className="ms-2">
              <FaArrowLeft className="me-1" /> Back to Planner
            </Button>
          </div>
        </Navbar>
        <Container className="mt-5">
          <Alert variant="info">
            Please sign in to manage your credits.
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
        <div className="d-flex align-items-center">
          <LoggingToggle />
          <Button variant="outline-primary" size="sm" onClick={() => navigate('/')} className="ms-2">
            <FaArrowLeft className="me-1" /> Back to Planner
          </Button>
        </div>
      </Navbar>
      
      <Container className="credits-container mt-4">
        <h1 className="mb-4 d-flex align-items-center">
          <FaCoins className="me-2 text-warning" /> My Credits
        </h1>
        
        {error && (
          <Alert variant="danger" dismissible onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
        
        {loading ? (
          <div className="text-center my-5">
            <Spinner animation="border" />
            <p className="mt-2">Loading your credits...</p>
          </div>
        ) : (
          <>
            <Card className="mb-4">
              <Card.Body>
                <Card.Title>Available Credits</Card.Title>
                <div className="d-flex align-items-center mt-3">
                  <div className="display-4 me-2 d-flex align-items-center">
                    <FaCoins className="text-warning me-2" style={{ fontSize: '2rem' }} />
                    <span>{availableCredits}</span>
                  </div>
                  <div className="text-muted ms-2">
                    Use 1 credit to create a new trip itinerary
                  </div>
                </div>
                <Card.Text className="mt-3">
                  {availableCredits > 0 ? 
                    `You have ${availableCredits} credit${availableCredits !== 1 ? 's' : ''} available to create new trips.` :
                    'You have no credits available. Purchase credits to create new trips.'}
                </Card.Text>
              </Card.Body>
            </Card>
            
            <Card className="mb-4">
              <Card.Body>
                <Card.Title>How Credits Work</Card.Title>
                <ul className="mt-3">
                  <li>Each day of your travel itinerary costs 1 credit</li>
                  <li>A 7-day trip will use 7 credits</li>
                  <li>Credits are deducted when you generate an itinerary</li>
                  <li>If you save a previously generated itinerary, no additional credits are used</li>
                </ul>
              </Card.Body>
            </Card>
            
            <h2 className="mb-3">Purchase Credits</h2>
            <Row>
              {CREDIT_PACKAGES.map(pkg => (
                <Col md={6} key={pkg.id} className="mb-3">
                  <Card>
                    <Card.Body>
                      <Card.Title>{pkg.name} Package</Card.Title>
                      <div className="d-flex justify-content-between align-items-center my-3">
                        <div className="d-flex align-items-center">
                          <FaCoins className="text-warning me-2" />
                          <span className="h3 mb-0">{pkg.credits} Credits</span>
                        </div>
                        <div className="h3 mb-0">${pkg.price.toFixed(2)}</div>
                      </div>
                      <Button 
                        variant="primary" 
                        className="w-100" 
                        onClick={() => handleStripeRedirect(pkg.id)}
                      >
                        Purchase
                      </Button>
                    </Card.Body>
                  </Card>
                </Col>
              ))}
            </Row>
          </>
        )}
      </Container>
    </>
  );
};

export default Credits; 