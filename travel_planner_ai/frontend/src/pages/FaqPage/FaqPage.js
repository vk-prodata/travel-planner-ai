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
            <li>Navigate to the main page: travelplannerai.org</li>
            <li>Enter your destination, travel dates, and interests.</li>
            <li>Our AI will generate a personalized itinerary for you.</li>
            <li>You can review and customize the plan further.</li>
          </ol>
          <p>You need credits to generate a plan. See below for how to get credits.</p>
        </FaqItem>

        <FaqItem question="How do I buy credits?">
          <p>You can purchase credits through our secure payment portal.</p>
          <ol>
            <li>Go to your credits section (image with number of credits next to 'My Trips').</li>
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

        <FaqItem question="How can I get the best results from the Travel Planner AI?">
          <p>To make the most out of our AI-powered travel planner, consider the following tips:</p>
          <ul>
            <li><strong>Be Specific with Interests:</strong> The more details you provide about your interests (including "Advanced Settings" like cousine, bugget, etc.), the better the AI can tailor the itinerary to your preferences."</li>
            <li><strong>Provide Clear Travel Dates:</strong> Accurate start and end dates help the AI plan a realistic schedule, considering travel times and opening hours of attractions.</li>
            <li><strong>Choose Your Entertainment Preferences:</strong> Are you looking for a outdoor family-friendly activity with visitin must see place. Be sure that you've chosen: Outdoor, Family-friendly and Must see.</li>
            <li><strong>List "Must-See" Attractions:</strong> If there are specific places you definitely want to visit, list them. The AI will try to incorporate these into your plan.</li>
          </ul>
        </FaqItem>

        <FaqItem question="How can I view and manage my saved trips?">
          <p>You can see all your created trips by clicking on the "My Trips" button in the header. From there, you'll be able to view the details of each trip or delete any trips you no longer need.</p>
        </FaqItem>

        <FaqItem question="How are credits deducted when I create a travel plan?">
          <p>Credits are used to generate your personalized itineraries. Typically, <strong>1 credit is used for each full day</strong> of your travel plan. For example, a 7-day trip will usually require 7 credits. New users also receive 10 free credits to get started!</p>
        </FaqItem>

        <FaqItem question="What if I want to change a specific activity in my generated plan?">
          <p>If an activity in your generated itinerary isn't quite right, you can use the "Refresh Activity" feature. This allows the AI to suggest an alternative for that specific part of your day. You can even provide custom preferences (e.g., "something less crowded" or "an outdoor option") when refreshing to get a more tailored suggestion. Note: it doesn't cost any credits to refresh an activity.</p>
        </FaqItem>

      </Container>
    </Container>
  );
};

export default FaqPage; 