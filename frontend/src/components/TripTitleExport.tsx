import React from 'react';
import { ButtonGroup, Button, OverlayTrigger, Tooltip } from 'react-bootstrap';
import { FaFilePdf, FaCalendarAlt, FaFileDownload } from 'react-icons/fa';
import { TripItinerary, TripFormData } from '../types';
import { PDFDownloadLink } from '@react-pdf/renderer';
import ical from 'ical-generator';
import TripPDF from './TripPDF';
import '../styles/TripExport.css';

interface TripTitleExportProps {
  itinerary: TripItinerary;
  formData: TripFormData;
}

const TripTitleExport: React.FC<TripTitleExportProps> = ({ itinerary, formData }) => {
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

  return (
    <ButtonGroup size="sm" className="title-export-buttons ms-2">
      <OverlayTrigger
        placement="top"
        overlay={<Tooltip id="pdf-tooltip">Export as PDF</Tooltip>}
      >
        <div className="d-inline-block">
          <PDFDownloadLink 
            document={<TripPDF itinerary={itinerary} formData={formData} />} 
            fileName={`trip-to-${formData.destination}.pdf`}
            className="btn btn-link p-0 text-secondary title-export-icon"
          >
            <FaFilePdf size={14} />
          </PDFDownloadLink>
        </div>
      </OverlayTrigger>
      
      <OverlayTrigger
        placement="top"
        overlay={<Tooltip id="calendar-tooltip">Add to Calendar</Tooltip>}
      >
        <Button 
          variant="link" 
          className="p-0 text-secondary title-export-icon"
          onClick={generateICS}
        >
          <FaCalendarAlt size={14} />
        </Button>
      </OverlayTrigger>
      
      <OverlayTrigger
        placement="top"
        overlay={<Tooltip id="json-tooltip">Export as JSON</Tooltip>}
      >
        <Button 
          variant="link" 
          className="p-0 text-secondary title-export-icon"
          onClick={exportJSON}
        >
          <FaFileDownload size={14} />
        </Button>
      </OverlayTrigger>
    </ButtonGroup>
  );
};

export default TripTitleExport; 