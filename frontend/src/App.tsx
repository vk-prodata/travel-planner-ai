import * as React from 'react';
import { useState, useEffect } from 'react';
import { Container, Row, Col, Button } from 'react-bootstrap';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate, useLocation, useSearchParams } from 'react-router-dom';
import TripForm from './components/TripForm';
import Itinerary from './components/Itinerary';
import TripExport from './components/TripExport';
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

// ... existing code ...

                  <div className="d-flex gap-2">
                    {user ? (
                      <>
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
                        <TripExport itinerary={itinerary} formData={formData} />
                      </>
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
// ... rest of the code ... 