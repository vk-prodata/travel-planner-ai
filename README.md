# Travel Planner AI

Travel Planner AI generates personalized travel itineraries using AI (default: GPT-4o) with options for extra intermediate stops, budget preferences, editable activities with alternative suggestions, and multi-language support (affecting AI output). The project is built with a FastAPI backend and a React frontend.

## Features

- **AI-Powered Itinerary:** Generates travel itineraries using GPT-4o with an easy switch to Gemini.
- **Intermediate Stops:** Users can add multiple intermediate cities/places to stay.
- **Budget Preferences:** Uses an enum with icon buttons for Budget, Mid-range, and Luxury.
- **Editable Activities:** Each activity has a "Suggest Alternative" and "Edit" option. Editing is done via a rich text editor in a modal (React Quill).
- **Caching:** AI requests are cached (TTL 1 hour) to reduce repeated API calls.
- **Responsive UI/UX:** Built with React and React-Bootstrap for a polished, user-friendly experience.

## Tech Stack

- **Backend:** Python 3.12, FastAPI, Motor (MongoDB), OpenAI, cachetools, python-dotenv
- **Frontend:** React, Axios, React-Bootstrap, React-Icons, React-Quill, Bootstrap
- **Database:** MongoDB Atlas free tier (alternatives: Firebase Firestore, CouchDB)
- **Dependency Management:** Poetry
- **Testing:** Pytest

## Local Deployment on macOS

### Prerequisites

- Python 3.12 and Poetry ([Poetry Installation Guide](https://python-poetry.org/docs/#installation))
- Node.js and npm

### Backend Setup

1. Navigate to the `backend` directory.
2. Install dependencies:
   ```bash
   poetry install
