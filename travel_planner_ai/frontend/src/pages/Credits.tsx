import React, { useEffect, useState } from 'react';
import { Container, Row, Col, Card, Button, Alert, Navbar, Spinner } from 'react-bootstrap';
import { FaCoins, FaArrowLeft, FaPlane } from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { getUserCredits, purchaseCredits, CREDIT_PACKAGES } from '../services/creditsService';
import { notifyError, notifySuccess } from '../services/errorService';
import LoggingToggle from '../components/LoggingToggle';
import '../styles/Credits.css';

const Credits: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [purchasing, setPurchasing] = useState(false);
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
    
    fetchCredits();
  }, [user]);
  
  const handlePurchase = async (packageId: string) => {
    if (!user) return;
    
    try {
      setPurchasing(true);
      setError(null);
      
      console.log(`Purchasing package ${packageId} for user ${user.id}`);
      const result = await purchaseCredits(user.id, packageId);
      console.log('Purchase result:', result);
      
      // Handle both naming conventions from backend
      setAvailableCredits(
        result.availableCredits !== undefined 
          ? result.availableCredits 
          : result.available_credits || 0
      );
      
      notifySuccess('Credits purchased successfully!');
    } catch (err) {
      console.error('Failed to purchase credits:', err);
      setError('Failed to purchase credits. Please try again later.');
      notifyError(err, user?.email);
    } finally {
      setPurchasing(false);
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
                        onClick={() => handlePurchase(pkg.id)}
                        disabled={purchasing}
                      >
                        {purchasing ? (
                          <>
                            <Spinner size="sm" animation="border" className="me-2" />
                            Processing...
                          </>
                        ) : (
                          <>Purchase</>
                        )}
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