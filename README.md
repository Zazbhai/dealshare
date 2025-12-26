# DealShare Automation Dashboard

A modern React-based dashboard with animations and an admin panel for managing DealShare automation workflows.

## Features

- 🎨 **Beautiful UI** with smooth animations and effects
- 📊 **Dashboard** for managing phone numbers and OTPs
- ⚙️ **Admin Panel** for monitoring and configuration
- 🔄 **Real-time Updates** with auto-refresh
- 📱 **API Integration** with Temporasms service

## Tech Stack

### Frontend
- React 18
- Vite
- Tailwind CSS
- Framer Motion (animations)
- React Router
- Axios
- Lucide React (icons)

### Backend
- Flask
- Flask-CORS
- Python API wrapper

## Setup

### Prerequisites
- Node.js 18+ and npm
- Python 3.8+

### Installation

1. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

2. **Install Node.js dependencies:**
```bash
npm install
```

3. **Start the backend server:**
```bash
python backend/server.py
```
The backend will run on `http://localhost:5000`

4. **Start the frontend development server:**
```bash
npm run dev
```
The frontend will run on `http://localhost:3000`

## Project Structure

```
.
├── backend/
│   └── server.py          # Flask API server
├── src/
│   ├── pages/
│   │   ├── Dashboard.jsx  # Main dashboard page
│   │   └── Admin.jsx      # Admin panel
│   ├── services/
│   │   └── api.js         # API service functions
│   ├── App.jsx            # Main app component
│   ├── main.jsx           # Entry point
│   └── index.css          # Global styles
├── api.py                 # Temporasms API wrapper
├── main.py                # Playwright automation script
├── package.json           # Node.js dependencies
└── requirements.txt       # Python dependencies
```

## Usage

1. Open `http://localhost:3000` in your browser
2. Navigate to the **Dashboard** to:
   - Get phone numbers
   - Retrieve OTPs
   - Manage automation workflow
3. Navigate to the **Admin** panel to:
   - Monitor API status
   - View account balance
   - Configure settings
   - View available services and prices

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/balance` - Get account balance
- `GET /api/price` - Get service price
- `GET /api/prices` - Get all prices
- `POST /api/number` - Request phone number
- `POST /api/otp` - Get OTP
- `POST /api/otp/new` - Request new OTP
- `POST /api/cancel` - Cancel number

## Development

- Frontend dev server: `npm run dev`
- Build for production: `npm run build`
- Preview production build: `npm run preview`

## License

MIT

