# Frames - Picture Wall Visualizer

A web application that lets users photograph picture frames, specify their real-world dimensions, and visualize them on captured walls using 3D and AR technology.

## Features

- **Capture Picture Frames**: Take photos of artwork and specify dimensions in inches or centimeters
- **Generate 3D Models**: Automatically create 3D representations of framed pictures
- **Capture Walls**: Photograph walls where you want to hang pictures
- **Virtual Placement**: Place 3D frames on virtual walls to preview arrangements
- **AR Visualization**: View frames on real walls using WebXR (Unity integration)
- **Save & Manage**: Save walls and pictures for future reference

## Tech Stack

- **Frontend**: Vue 3 + Vite + Tailwind CSS + Three.js
- **Backend**: Flask + SQLAlchemy + PostgreSQL
- **3D/AR**: Three.js for web 3D, Unity WebXR for AR features

## Project Structure

```
frames/
├── backend/                 # Flask API
│   ├── app/
│   │   ├── models/         # Database models
│   │   ├── routes/         # API endpoints
│   │   ├── services/       # Business logic
│   │   └── utils/          # Helpers
│   ├── requirements.txt
│   └── run.py
├── frontend/               # Vue.js app
│   ├── src/
│   │   ├── components/     # Reusable components
│   │   ├── views/          # Page components
│   │   ├── store/          # Pinia stores
│   │   ├── router/         # Vue Router
│   │   └── services/       # API client
│   └── package.json
├── unity/                  # Unity WebXR docs
├── docker-compose.yml
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL (or use SQLite for development)

### Development Setup

1. **Clone and setup backend**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your settings
```

2. **Initialize database**:
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

3. **Run backend**:
```bash
python run.py
```

4. **Setup frontend** (in a new terminal):
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

5. **Access the app**:
   - Frontend: http://localhost:5173
   - API: http://localhost:5000/api

### Docker Setup

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user

### Pictures
- `GET /api/pictures` - List user's pictures
- `POST /api/pictures` - Upload new picture
- `POST /api/pictures/:id/frames` - Create 3D frame for picture
- `DELETE /api/pictures/:id` - Delete picture

### Walls
- `GET /api/walls` - List user's walls
- `POST /api/walls` - Upload new wall
- `PUT /api/walls/:id` - Update wall (name, placements)
- `POST /api/walls/:id/placements` - Add frame to wall
- `DELETE /api/walls/:id` - Delete wall

### Models
- `GET /api/models/:id` - Download 3D model file

## Unity WebXR Integration

For AR features, you'll need to build a Unity WebXR project. See [unity/README.md](unity/README.md) for detailed instructions.

The Vue app communicates with Unity via:
- **Vue → Unity**: `unityInstance.SendMessage()`
- **Unity → Vue**: Custom jslib plugin calling `window.unityToVue()`

## Environment Variables

### Backend (.env)
```
FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@localhost:5432/frames_db
JWT_SECRET_KEY=your-jwt-secret
CORS_ORIGINS=http://localhost:5173
```

### Frontend (.env)
```
VITE_API_URL=http://localhost:5000/api
VITE_UNITY_BUILD_PATH=/unity
```

## Development

### Backend
```bash
# Run tests
pytest

# Format code
black app/

# Lint
flake8 app/
```

### Frontend
```bash
# Run dev server
npm run dev

# Build for production
npm run build

# Lint
npm run lint
```

## Deployment

### Vercel (Frontend)

The frontend can be easily deployed to Vercel:

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/frames)

For detailed instructions, see [VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md)

**Quick Start:**
1. Push your code to GitHub/GitLab/Bitbucket
2. Import the project in [Vercel Dashboard](https://vercel.com/new)
3. Set environment variable: `VITE_API_URL=https://your-backend-api.com/api`
4. Deploy!

**Note**: The backend needs to be deployed separately (see Backend Deployment below).

### Backend Deployment

Deploy the Flask backend to a Python-compatible platform:
- **Railway** (recommended): [railway.app](https://railway.app/)
- **Render**: [render.com](https://render.com/)
- **Heroku**: [heroku.com](https://heroku.com/)
- **DigitalOcean App Platform**: [digitalocean.com](https://www.digitalocean.com/products/app-platform)

### Production Build

1. **Frontend**:
```bash
cd frontend
npm run build
# Output in dist/
```

2. **Backend**:
```bash
# Use gunicorn
gunicorn --bind 0.0.0.0:5000 run:app
```

### Docker Production

```bash
docker-compose --profile production up -d
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details
