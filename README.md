# Notes App

A full-stack notes application built with **React** + **FastAPI** + **MongoDB**. Features include user authentication with JWT, CRUD operations for notes, search functionality, and optimistic concurrency control.

## 🚀 Features

### Backend (FastAPI)
- **JWT Authentication** - Secure user authentication and session management
- **MongoDB Integration** - Async MongoDB operations with Motor
- **CRUD Operations** - Complete notes management (Create, Read, Update, Delete)
- **Optimistic Concurrency Control** - Version-based conflict resolution
- **Search Functionality** - Full-text search across notes
- **Error Handling** - Comprehensive error handling and validation
- **API Documentation** - Auto-generated OpenAPI/Swagger docs

### Frontend (React)
- **Modern React** - Built with React 18 and Vite
- **Responsive Design** - Tailwind CSS for beautiful, responsive UI
- **Authentication Context** - JWT token management with React Context
- **Route Protection** - Public/private route guards
- **Search & Filter** - Real-time note search with debouncing
- **Optimistic Updates** - Smooth UX with optimistic UI updates

## 🛠️ Tech Stack

**Backend:**
- FastAPI - Modern, fast Python web framework
- MongoDB - NoSQL database with Motor (async driver)
- JWT - JSON Web Token authentication
- Pydantic - Data validation and serialization
- Bcrypt - Password hashing

**Frontend:**
- React 18 - UI library
- Vite - Fast development server and bundler
- React Router - Client-side routing
- Tailwind CSS - Utility-first CSS framework
- Axios - HTTP client

## 📁 Project Structure

```
notes-app/
├── backend/                 # FastAPI backend
│   ├── main.py             # Application entry point
│   ├── database.py         # MongoDB connection and configuration
│   ├── schemas.py          # Pydantic models for validation
│   ├── auth.py             # Authentication utilities
│   ├── crud.py             # Database CRUD operations
│   ├── routers/            # API route handlers
│   │   ├── auth.py         # Authentication routes
│   │   └── notes.py        # Notes CRUD routes
│   ├── requirements.txt    # Python dependencies
│   └── .env.example        # Environment variables template
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # Reusable React components
│   │   ├── pages/          # Page components
│   │   ├── context/        # React context providers
│   │   ├── utils/          # Utility functions and API client
│   │   ├── App.jsx         # Main app component
│   │   └── main.jsx        # Application entry point
│   ├── package.json        # Node.js dependencies
│   ├── vite.config.js      # Vite configuration
│   ├── tailwind.config.js  # Tailwind CSS configuration
│   └── .env.example        # Environment variables template
└── README.md              # This file
```

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+**
- **Node.js 16+**
- **MongoDB** (local installation or MongoDB Atlas)

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd notes-app
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Edit .env file with your configuration
# Make sure to set a secure SECRET_KEY and MongoDB connection string
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory (from project root)
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env

# The default settings should work if backend runs on localhost:8000
```

### 4. Database Setup

**Option A: Local MongoDB**
```bash
# Install MongoDB locally and start the service
# On macOS with Homebrew:
brew install mongodb/brew/mongodb-community
brew services start mongodb/brew/mongodb-community

# On Ubuntu:
sudo systemctl start mongod

# On Windows:
# Install MongoDB Community Server and start the service
```

**Option B: MongoDB Atlas (Cloud)**
1. Create a free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a new cluster
3. Get your connection string
4. Update `MONGODB_URL` in `backend/.env`

### 5. Run the Application

**Start Backend (from backend directory):**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Start Frontend (from frontend directory):**
```bash
npm run dev
```

### 6. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (Swagger UI)

## 📝 API Endpoints

### Authentication
- `POST /auth/signup` - Register new user
- `POST /auth/login` - Login user
- `GET /auth/me` - Get current user info

### Notes
- `GET /notes/` - Get user's notes (with search and pagination)
- `POST /notes/` - Create new note
- `GET /notes/{id}` - Get specific note
- `PUT /notes/{id}` - Update note (with version control)
- `DELETE /notes/{id}` - Delete note

## 🔐 Authentication

The app uses JWT (JSON Web Tokens) for authentication:

1. Users register/login with email and password
2. Server returns a JWT token
3. Token is stored in localStorage and sent with API requests
4. Protected routes require valid JWT token

## 🔄 Optimistic Concurrency Control

Notes include version numbers to prevent conflicts:

1. Each note has a `version` field that increments on updates
2. Update requests must include the current version
3. If versions don't match, the update fails with a 409 Conflict
4. Frontend handles conflicts by prompting user to refresh

## 🔍 Features in Detail

### Search
- Real-time search across note titles, content, and tags
- Debounced input (500ms) to avoid excessive API calls
- Search results update automatically

### Tags
- Add tags to organize notes
- Tags are displayed as badges on note cards
- Search includes tag matching

### Favorites
- Mark notes as favorites with star icon
- Quick toggle functionality
- Visual indication on note cards

## 🧪 Testing

**Backend Testing:**
```bash
cd backend
pytest
```

**Frontend Testing:**
```bash
cd frontend
npm run test
```

## 🚀 Production Deployment

### Backend Deployment

1. **Environment Variables:**
   - Set secure `SECRET_KEY`
   - Configure production MongoDB URL
   - Set appropriate CORS origins

2. **Docker (Optional):**
   ```dockerfile
   FROM python:3.9-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

3. **Deploy to platforms like:**
   - Heroku
   - Railway
   - DigitalOcean App Platform
   - AWS Lambda (with Mangum)

### Frontend Deployment

1. **Build for production:**
   ```bash
   npm run build
   ```

2. **Deploy to platforms like:**
   - Vercel
   - Netlify
   - AWS S3 + CloudFront
   - GitHub Pages

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent Python web framework
- React team for the amazing UI library
- MongoDB for the flexible database solution
- Tailwind CSS for the utility-first CSS framework

---

**Happy note-taking! 📝✨**
