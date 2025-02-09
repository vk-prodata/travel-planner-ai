// src/components/ItineraryDisplay.js
import React, { useState } from 'react';
import { Card, Button, Modal } from 'react-bootstrap';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css';
import { AiOutlineReload, AiFillEdit } from 'react-icons/ai';

function ItineraryDisplay({ itinerary }) {
  const [showModal, setShowModal] = useState(false);
  const [currentActivity, setCurrentActivity] = useState(null);
  const [currentDayIndex, setCurrentDayIndex] = useState(null);
  const [currentActIndex, setCurrentActIndex] = useState(null);
  const [editedText, setEditedText] = useState("");

  const handleEdit = (dayIdx, actIdx, description) => {
    setCurrentDayIndex(dayIdx);
    setCurrentActIndex(actIdx);
    setEditedText(description);
    setShowModal(true);
  };

  const handleSave = () => {
    // In a full implementation, update backend or global state.
    itinerary.itinerary[currentDayIndex].activities[currentActIndex].description = editedText;
    setShowModal(false);
  };

  const handleSuggestAlternative = (dayIdx, actIdx) => {
    // Dummy logic for alternative suggestion.
    const currentDesc = itinerary.itinerary[dayIdx].activities[actIdx].description;
    const alternative = currentDesc + " - Alternative suggestion";
    itinerary.itinerary[dayIdx].activities[actIdx].description = alternative;
  };

  return (
    <div className="mt-4">
      <h2>Generated Itinerary</h2>
      {itinerary.itinerary.map((day, dayIdx) => (
        <Card key={dayIdx} className="mb-3">
          <Card.Header><strong>{day.date}</strong></Card.Header>
          <Card.Body>
            {day.activities.map((activity, actIdx) => (
              <div key={actIdx} className="mb-3">
                <div><strong>{activity.time}:</strong> <span dangerouslySetInnerHTML={{ __html: activity.description }} /></div>
                <div className="mt-2">
                  <Button variant="secondary" size="sm" onClick={() => handleSuggestAlternative(dayIdx, actIdx)}>
                    <AiOutlineReload /> Suggest Alternative
                  </Button>{" "}
                  <Button variant="outline-primary" size="sm" onClick={() => handleEdit(dayIdx, actIdx, activity.description)}>
                    <AiFillEdit /> Edit
                  </Button>
                </div>
              </div>
            ))}
          </Card.Body>
        </Card>
      ))}

      <Modal show={showModal} onHide={() => setShowModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Edit Activity</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <ReactQuill theme="snow" value={editedText} onChange={setEditedText} />
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowModal(false)}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleSave}>
            Save Changes
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
}

export default ItineraryDisplay;
