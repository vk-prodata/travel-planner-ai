// src/components/TripForm.js
import React, { useState } from 'react';
import axios from 'axios';
import { Form, Button, InputGroup, ListGroup, Row, Col } from 'react-bootstrap';
import { AiOutlinePlus } from 'react-icons/ai';

function TripForm({ setItinerary, setError, setLoading }) {
  const [formData, setFormData] = useState({
    travel_type: "road_trip",
    departure: "",
    destination: "",
    start_date: "",
    end_date: "",
    num_adults: 1,
    num_children: 0,
    num_infants: 0,
    language: "en",
    outdoor: false,
    cultural: false,
    relaxation: false,
    family_friendly: false,
    food_tours: false,
    budget: "budget",
    ai_model: "GPT-4o"
  });
  
  const [intermediateStopInput, setIntermediateStopInput] = useState("");
  const [intermediateStops, setIntermediateStops] = useState([]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value
    }));
  };

  const handleAddStop = () => {
    if (intermediateStopInput.trim() !== "") {
      setIntermediateStops([...intermediateStops, intermediateStopInput.trim()]);
      setIntermediateStopInput("");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    const tripData = {
      trip_details: {
        travel_type: formData.travel_type,
        departure: formData.departure,
        destination: formData.destination,
        start_date: formData.start_date,
        end_date: formData.end_date,
        num_adults: Number(formData.num_adults),
        num_children: Number(formData.num_children),
        num_infants: Number(formData.num_infants),
        intermediate_stops: intermediateStops
      },
      preferences: {
        outdoor: formData.outdoor,
        cultural: formData.cultural,
        relaxation: formData.relaxation,
        family_friendly: formData.family_friendly,
        food_tours: formData.food_tours,
      },
      budget: {
        level: formData.budget
      },
      ai_model: {
        model: formData.ai_model
      },
      language: formData.language
    };

    try {
      const response = await axios.post("http://localhost:8000/api/generate-trip", tripData);
      setItinerary(response.data);
      // Cache locally as a fallback option.
      localStorage.setItem("lastItinerary", JSON.stringify(response.data));
    } catch (error) {
      setError("Failed to generate trip. Please try again.");
      console.error("Error generating trip:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Form onSubmit={handleSubmit}>
      {/* Trip Details */}
      <Form.Group className="mb-3">
        <Form.Label>Travel Type</Form.Label>
        <Form.Select name="travel_type" value={formData.travel_type} onChange={handleChange}>
          <option value="road_trip">Road Trip</option>
          <option value="flight">Flight</option>
          <option value="train">Train</option>
          <option value="cruise">Cruise</option>
        </Form.Select>
      </Form.Group>
      <Form.Group className="mb-3">
        <Form.Label>Departure</Form.Label>
        <Form.Control type="text" name="departure" placeholder="City or Airport" required onChange={handleChange} />
      </Form.Group>
      <Form.Group className="mb-3">
        <Form.Label>Destination</Form.Label>
        <Form.Control type="text" name="destination" placeholder="City or Destination" required onChange={handleChange} />
      </Form.Group>
      <Row className="mb-3">
        <Col>
          <Form.Group>
            <Form.Label>Start Date</Form.Label>
            <Form.Control type="date" name="start_date" required onChange={handleChange} />
          </Form.Group>
        </Col>
        <Col>
          <Form.Group>
            <Form.Label>End Date</Form.Label>
            <Form.Control type="date" name="end_date" required onChange={handleChange} />
          </Form.Group>
        </Col>
      </Row>
      <Row className="mb-3">
        <Col>
          <Form.Group>
            <Form.Label>Adults</Form.Label>
            <Form.Control type="number" name="num_adults" min="1" defaultValue="1" required onChange={handleChange} />
          </Form.Group>
        </Col>
        <Col>
          <Form.Group>
            <Form.Label>Children</Form.Label>
            <Form.Control type="number" name="num_children" min="0" defaultValue="0" onChange={handleChange} />
          </Form.Group>
        </Col>
        <Col>
          <Form.Group>
            <Form.Label>Infants</Form.Label>
            <Form.Control type="number" name="num_infants" min="0" defaultValue="0" onChange={handleChange} />
          </Form.Group>
        </Col>
      </Row>
      <Form.Group className="mb-3">
        <Form.Label>Language</Form.Label>
        <Form.Select name="language" value={formData.language} onChange={handleChange}>
          <option value="en">English</option>
          {/* TODO: Add more languages as needed */}
        </Form.Select>
      </Form.Group>
      {/* Intermediate Stops */}
      <Form.Group className="mb-3">
        <Form.Label>Intermediate Stops (Cities to Stay)</Form.Label>
        <InputGroup>
          <Form.Control
            type="text"
            value={intermediateStopInput}
            placeholder="Add a city"
            onChange={(e) => setIntermediateStopInput(e.target.value)}
          />
          <Button variant="secondary" onClick={handleAddStop}>
            <AiOutlinePlus /> Add
          </Button>
        </InputGroup>
        {intermediateStops.length > 0 && (
          <ListGroup className="mt-2">
            {intermediateStops.map((stop, idx) => (
              <ListGroup.Item key={idx}>{stop}</ListGroup.Item>
            ))}
          </ListGroup>
        )}
      </Form.Group>
      {/* Preferences */}
      <fieldset className="mb-3">
        <legend>Preferences</legend>
        <Form.Check type="checkbox" label="Outdoor" name="outdoor" onChange={handleChange} />
        <Form.Check type="checkbox" label="Cultural" name="cultural" onChange={handleChange} />
        <Form.Check type="checkbox" label="Relaxation" name="relaxation" onChange={handleChange} />
        <Form.Check type="checkbox" label="Family Friendly" name="family_friendly" onChange={handleChange} />
        <Form.Check type="checkbox" label="Food Tours" name="food_tours" onChange={handleChange} />
      </fieldset>
      {/* Budget Preferences as Icon Buttons */}
      <Form.Group className="mb-3">
        <Form.Label>Budget Level</Form.Label>
        <div className="d-flex">
          <Button variant={formData.budget === "budget" ? "primary" : "outline-primary"} className="me-2" onClick={() => setFormData(prev => ({ ...prev, budget: "budget" }))}>
            <i className="bi bi-currency-dollar"></i> Budget
          </Button>
          <Button variant={formData.budget === "mid_range" ? "primary" : "outline-primary"} className="me-2" onClick={() => setFormData(prev => ({ ...prev, budget: "mid_range" }))}>
            <i className="bi bi-currency-exchange"></i> Mid-range
          </Button>
          <Button variant={formData.budget === "luxury" ? "primary" : "outline-primary"} onClick={() => setFormData(prev => ({ ...prev, budget: "luxury" }))}>
            <i className="bi bi-gem"></i> Luxury
          </Button>
        </div>
      </Form.Group>
      {/* AI Model Selection */}
      <Form.Group className="mb-3">
        <Form.Label>AI Model</Form.Label>
        <Form.Select name="ai_model" value={formData.ai_model} onChange={handleChange}>
          <option value="GPT-4o">GPT-4o</option>
          <option value="Gemini">Gemini</option>
          <option value="DeepSeek">DeepSeek</option>
        </Form.Select>
      </Form.Group>
      <Button type="submit" variant="primary">Generate Trip</Button>
    </Form>
  );
}

export default TripForm;
