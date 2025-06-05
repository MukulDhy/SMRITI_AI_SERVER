. Setup Local Development
bash# Clone or create your project directory
mkdir flask-api-server
cd flask-api-server

# Create virtual environment

python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies

pip install -r requirements.txt

# Copy environment template

cp .env.example .env

# Edit .env with your configuration

# Run the application

python app.py

Environment Variables
Required:

SECRET_KEY - Flask secret key for sessions
FLASK_ENV - development/production
PORT - Server port (auto-set by Render)

Optional:

DEBUG - Enable debug mode (development only)
LOG_LEVEL - Logging level (DEBUG, INFO, WARNING, ERROR)
CORS_ORIGINS - Allowed CORS origins
DATABASE_URL - Database connection string
REDIS_URL - Redis connection string

API Endpoints
Health Checks

GET /health - Basic health check
GET /health/detailed - Detailed health with system metrics
GET /ready - Kubernetes readiness probe
GET /live - Kubernetes liveness probe

API v1

GET /api/v1/ - API information
POST /api/v1/echo - Echo service
GET /api/v1/users - Get users (example)
POST /api/v1/users - Create user (example)
POST /api/v1/process - Data processing service
GET /api/v1/status - API status
