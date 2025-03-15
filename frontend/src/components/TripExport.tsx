import React, { useState } from 'react';
import { Button, ButtonGroup, Dropdown } from 'react-bootstrap';
import { FaFileDownload, FaShare, FaCopy, FaCheck } from 'react-icons/fa';
import { TripItinerary, TripFormData } from '../types';
import { PDFDownloadLink } from '@react-pdf/renderer';
import ical from 'ical-generator';
import {
  FacebookShareButton,
  TelegramShareButton,
  TwitterShareButton,
  WhatsappShareButton,
  FacebookIcon,
  TelegramIcon,
  TwitterIcon,
  WhatsappIcon
} from 'react-share';
import { toast } from 'react-toastify';
import TripPDF from './TripPDF';
import '../styles/TripExport.css';

interface TripExportProps {
  itinerary: TripItinerary;
  formData: TripFormData;
}

const TripExport: React.FC<TripExportProps> = ({ itinerary, formData }) => {
  const [copySuccess, setCopySuccess] = useState(false);

  const generateICS = () => {
    const calendar = ical();
    const startDate = new Date(formData.startDate);
    const endDate = new Date(formData.endDate);

    calendar.createEvent({
      start: startDate,
      end: endDate,
      summary: `Trip to ${formData.destination}`,
      description: generateTripDescription(),
      location: formData.destination
    });

    const blob = new Blob([calendar.toString()], { type: 'text/calendar' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `trip-to-${formData.destination}.ics`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  };

  const exportJSON = () => {
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
  };

  const copyToClipboard = async () => {
    try {
      const tripDescription = generateTripDescription();
      await navigator.clipboard.writeText(tripDescription);
      setCopySuccess(true);
      toast.success('Trip details copied to clipboard!');
      
      // Reset copy success state after animation
      setTimeout(() => {
        setCopySuccess(false);
      }, 2000);
    } catch (error) {
      toast.error('Failed to copy trip details');
    }
  };

  const generateTripDescription = (): string => {
    let description = `Trip to ${formData.destination}\n`;
    description += `${formData.startDate} - ${formData.endDate}\n\n`;
    
    itinerary.days.forEach(day => {
      description += `${day.date}:\n`;
      day.activities.forEach(activity => {
        description += `${activity.time} - ${activity.description}\n`;
      });
      description += '\n';
    });
    
    return description;
  };

  const shareUrl = window.location.href;
  const shareTitle = `Check out my trip to ${formData.destination}!`;

  return (
    <div className="d-flex gap-2 align-items-center">
      <ButtonGroup>
        <Dropdown>
          <Dropdown.Toggle variant="primary" id="export-dropdown" className="export-button">
            <FaFileDownload className="me-2" />
            Export
          </Dropdown.Toggle>
          <Dropdown.Menu>
            <Dropdown.Item as={PDFDownloadLink} document={<TripPDF itinerary={itinerary} formData={formData} />} fileName={`trip-to-${formData.destination}.pdf`}>
              Export as PDF
            </Dropdown.Item>
            <Dropdown.Item onClick={generateICS}>
              Add to Calendar (ICS)
            </Dropdown.Item>
            <Dropdown.Item onClick={exportJSON}>
              Export as JSON
            </Dropdown.Item>
          </Dropdown.Menu>
        </Dropdown>

        <Dropdown>
          <Dropdown.Toggle variant="info" id="share-dropdown" className="share-button">
            <FaShare className="me-2" />
            Share
          </Dropdown.Toggle>
          <Dropdown.Menu className="share-dropdown-menu">
            <div className="d-flex gap-2 p-2">
              <WhatsappShareButton url={shareUrl} title={shareTitle}>
                <WhatsappIcon size={32} round className="share-button" />
              </WhatsappShareButton>
              <TelegramShareButton url={shareUrl} title={shareTitle}>
                <TelegramIcon size={32} round className="share-button" />
              </TelegramShareButton>
              <FacebookShareButton url={shareUrl}>
                <FacebookIcon size={32} round className="share-button" />
              </FacebookShareButton>
              <TwitterShareButton url={shareUrl} title={shareTitle}>
                <TwitterIcon size={32} round className="share-button" />
              </TwitterShareButton>
            </div>
          </Dropdown.Menu>
        </Dropdown>

        <Button 
          variant="secondary" 
          onClick={copyToClipboard} 
          className={`copy-button ${copySuccess ? 'copy-success' : ''}`}
        >
          {copySuccess ? (
            <>
              <FaCheck className="me-2" />
              Copied!
            </>
          ) : (
            <>
              <FaCopy className="me-2" />
              Copy
            </>
          )}
        </Button>
      </ButtonGroup>
    </div>
  );
};

export default TripExport; 