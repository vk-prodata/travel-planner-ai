import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Container, Card, Form, Alert } from 'react-bootstrap';
import styles from './FaqPage.module.css';

const FaqItem = ({ question, children }) => {
  const [isOpen, setIsOpen] = useState(false);
  const toggleOpen = () => setIsOpen(!isOpen);

  return (
    <div className={styles.faqSection}>
      <div className={styles.faqQuestion} onClick={toggleOpen}>
        {isOpen ? '➖' : '➕'} {question}
      </div>
      {isOpen && <div className={styles.faqAnswer}>{children}</div>}
    </div>
  );
};

const FaqPage = () => {
  const navigate = useNavigate();
  const [isContactOpen, setIsContactOpen] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    message: '',
  });
  const [status, setStatus] = useState('');

  const toggleContactForm = () => setIsContactOpen(!isContactOpen);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prevData) => ({
      ...prevData,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus('sending');
    try {
      // Get API URL from environment variable or use default
      const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';

      // Make the actual API call
      const response = await fetch(`${apiUrl}/api/contact`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      // Check if the request was successful
      if (!response.ok) {
        // Try to parse error message from backend
        let errorMessage = "Failed to send message.";
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch (jsonError) {
          // If parsing fails, use the status text
          errorMessage = `${response.status}: ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }

      // Assuming success if response.ok is true
      console.log('Form Data Submitted:', formData);
      setStatus('success');
      setFormData({ name: '', email: '', message: '' }); // Clear form
      setIsContactOpen(false); // Close form on success
    } catch (error) {
      console.error('Form Submission Error:', error);
      // Display the error message from the caught error
      setStatus('error');
      // Optionally, display the error message to the user more explicitly
      // setErrorMessage(error.message);
    }
  };

  return (
    <Container fluid className="p-0 min-vh-100 d-flex flex-column">
      <div className="bg-light p-3 shadow-sm mb-4 d-flex justify-content-between align-items-center">
        <h2 className="text-primary-dark m-0 fs-4">Frequently Asked Questions</h2>
        <div className="d-flex gap-2">
          <Button variant="outline-primary" size="sm" onClick={toggleContactForm}>
            {isContactOpen ? 'Hide Contact Form' : 'Contact Us'}
          </Button>
          <Button variant="outline-secondary" size="sm" onClick={() => navigate('/')}>
            &larr; Back to Planner
          </Button>
        </div>
      </div>

      {isContactOpen && (
        <Container className="mb-4">
          <Card>
            <Card.Body>
              <Form onSubmit={handleSubmit}>
                <Form.Group className="mb-3" controlId="contactName">
                  <Form.Label>Name</Form.Label>
                  <Form.Control
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    required
                  />
                </Form.Group>
                <Form.Group className="mb-3" controlId="contactEmail">
                  <Form.Label>Email</Form.Label>
                  <Form.Control
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                  />
                </Form.Group>
                <Form.Group className="mb-3" controlId="contactMessage">
                  <Form.Label>Message</Form.Label>
                  <Form.Control
                    as="textarea"
                    rows={3}
                    name="message"
                    value={formData.message}
                    onChange={handleChange}
                    required
                  />
                </Form.Group>
                {status === 'success' && <Alert variant="success">Message sent successfully!</Alert>}
                {status === 'error' && <Alert variant="danger">Failed to send message. Please try again.</Alert>}
                {status === 'sending' && <Alert variant="info">Sending...</Alert>}
                <Button type="submit" variant="primary" disabled={status === 'sending'}>
                  {status === 'sending' ? 'Sending...' : 'Send Message'}
                </Button>
              </Form>
            </Card.Body>
          </Card>
        </Container>
      )}

      <Container className="mt-0">
        <FaqItem question="How do I create a trip plan?">
          <p>Creating a trip plan is easy!</p>
          <ol>
            <li>Navigate to the 'New Trip' page.</li>
            <li>Enter your destination, travel dates, and interests.</li>
            <li>Our AI will generate a personalized itinerary for you.</li>
            <li>You can review and customize the plan further.</li>
          </ol>
          <p>You need credits to generate a plan. See below for how to get credits.</p>
        </FaqItem>

        <FaqItem question="How do I buy credits?">
          <p>You can purchase credits through our secure payment portal.</p>
          <ol>
            <li>Go to your 'Account' or 'Billing' section (link usually in the header or sidebar).</li>
            <li>Select the credit package you wish to purchase.</li>
            <li>Follow the on-screen instructions to complete the payment via Stripe.</li>
          </ol>
          <p>We offer various packages to suit different needs.</p>
        </FaqItem>

        <FaqItem question="What is the value of credits?">
          <p>Credits are used to generate AI-powered travel itineraries.</p>
          <ul>
            <li>Typically, <strong>1 credit</strong> is required to generate <strong>one full day</strong> of a travel plan.</li>
            <li>For example, a 5-day trip would usually require 5 credits.</li>
            <li>The exact credit cost might vary slightly based on the complexity or specific features requested.</li>
          </ul>
          <p>Buying larger credit packages often comes with a discount per credit.</p>
        </FaqItem>

      </Container>
    </Container>
  );
};

export default FaqPage; 