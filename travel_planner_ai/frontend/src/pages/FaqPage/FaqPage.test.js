import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import FaqPage from './FaqPage'; // Assuming FaqPage is in the same directory for this example

// Mock the ContactForm component to isolate the FaqPage test
jest.mock('../../components/ContactForm/ContactForm', () => {
  // Mock implementation that renders a button like the real one
  return ({ defaultIsOpen = false }) => {
    const [isOpen, setIsOpen] = React.useState(defaultIsOpen);
    return (
      <div>
        <button onClick={() => setIsOpen(!isOpen)}>
          {isOpen ? 'Hide Contact Form' : 'Contact Us'}
        </button>
        {isOpen && <div data-testid="mock-contact-form-content">Contact Form Content</div>}
      </div>
    );
  };
});

describe('FaqPage', () => {
  test('renders the FAQ page title', () => {
    render(<FaqPage />);
    expect(screen.getByRole('heading', { name: /frequently asked questions/i })).toBeInTheDocument();
  });

  test('renders the Contact Us button (from mocked ContactForm)', () => {
    render(<FaqPage />);
    expect(screen.getByRole('button', { name: /contact us/i })).toBeInTheDocument();
  });

  test('contact form is initially collapsed', () => {
    render(<FaqPage />);
    expect(screen.queryByTestId('mock-contact-form-content')).not.toBeInTheDocument();
  });

  test('clicking Contact Us button expands the form', () => {
    render(<FaqPage />);
    const contactButton = screen.getByRole('button', { name: /contact us/i });
    fireEvent.click(contactButton);
    expect(screen.getByTestId('mock-contact-form-content')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /hide contact form/i })).toBeInTheDocument();
  });

  test('renders FAQ items', () => {
    render(<FaqPage />);
    expect(screen.getByText(/How do I create a trip plan?/i)).toBeInTheDocument();
    expect(screen.getByText(/How do I buy credits?/i)).toBeInTheDocument();
    expect(screen.getByText(/What is the value of credits?/i)).toBeInTheDocument();
  });

  test('FAQ items are initially collapsed', () => {
    render(<FaqPage />);
    expect(screen.queryByText(/Creating a trip plan is easy!/i)).not.toBeInTheDocument();
  });

  test('clicking an FAQ item expands it', () => {
    render(<FaqPage />);
    const question = screen.getByText(/How do I create a trip plan?/i);
    fireEvent.click(question);
    expect(screen.getByText(/Creating a trip plan is easy!/i)).toBeInTheDocument();
  });
}); 