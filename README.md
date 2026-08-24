# Sol-Sight

Sol-Sight is an intelligent solar panel inspection and monitoring platform designed to help identify solar panel issues, manage inspections, and provide actionable insights through a web-based application.

The project is structured into a backend API and a frontend application, with Docker support for simplified deployment.

## Project Structure

```text
SolSight/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/
│   │   └── ...
│   ├── requirements.txt
│   └── ...
│
├── frontend/
│   ├── src/
│   ├── package.json
│   └── ...
│
├── docker-compose.yml
├── README.md
└── ...
```

## Technology Stack

### Backend

* Python
* FastAPI
* Uvicorn
* REST API
* Database integration
* AI/ML integration for solar panel inspection

### Frontend

* React
* JavaScript/TypeScript
* Modern component-based UI
* REST API integration

### Infrastructure

* Docker
* Docker Compose
* Git
* GitHub

## Prerequisites

Install the following software before starting:

* Git
* Python 3.10 or later
* Node.js 18 or later
* npm
* Docker Desktop

Verify the installations:

```bash
git --version
python --version
node --version
npm --version
docker --version
docker compose version
```

## Clone the Repository

Clone the project from GitHub:

```bash
git clone https://github.com/SaikatxAlpha/Sol-Sight.git
```

Move into the project directory:

```bash
cd Sol-Sight
```

## Backend Setup

Move into the backend directory:

```bash
cd backend
```

Create a Python virtual environment:

### Windows

```powershell
python -m venv venv
```

Activate it:

```powershell
venv\Scripts\activate
```

### Linux/macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

Install the backend dependencies:

```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file inside the backend directory if the project requires environment variables.

Example:

```env
DATABASE_URL=your_database_url
SECRET_KEY=your_secret_key
API_KEY=your_api_key
```

Do not commit `.env` files containing passwords, API keys, tokens, or other secrets.

Add `.env` to `.gitignore`:

```gitignore
.env
venv/
__pycache__/
*.pyc
```

## Start the Backend

From the `backend` directory:

```bash
uvicorn app.main:app --reload
```

The backend will normally be available at:

```text
http://127.0.0.1:8000
```

FastAPI documentation will be available at:

```text
http://127.0.0.1:8000/docs
```

Alternative ReDoc documentation:

```text
http://127.0.0.1:8000/redoc
```

## Frontend Setup

Open a new terminal and return to the project root:

```bash
cd Sol-Sight
```

Move into the frontend:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The frontend URL will be displayed in the terminal. Depending on the frontend configuration, it will commonly be:

```text
http://localhost:5173
```

## Running Backend and Frontend Together

You need two terminals during local development.

### Terminal 1

```bash
cd Sol-Sight/backend
```

Activate the virtual environment if required:

```powershell
venv\Scripts\activate
```

Start FastAPI:

```bash
uvicorn app.main:app --reload
```

### Terminal 2

```bash
cd Sol-Sight/frontend
npm install
npm run dev
```

The frontend communicates with the backend through the configured API URL.

## Docker Setup

Sol-Sight also includes a Docker Compose configuration.

From the project root:

```bash
docker compose up --build
```

To run the containers in detached mode:

```bash
docker compose up --build -d
```

Check running containers:

```bash
docker compose ps
```

View logs:

```bash
docker compose logs
```

Stop the application:

```bash
docker compose down
```

Rebuild the containers:

```bash
docker compose build --no-cache
docker compose up
```

## API Documentation

Once the backend is running, FastAPI automatically provides interactive API documentation.

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

ReDoc:

```text
http://127.0.0.1:8000/redoc
```

The Swagger interface can be used to test API endpoints directly.

## Development Workflow

After cloning the repository:

```bash
git clone https://github.com/SaikatxAlpha/Sol-Sight.git
cd Sol-Sight
```

Make your changes and test them locally.

Check the changed files:

```bash
git status
```

Stage the changes:

```bash
git add .
```

Create a commit:

```bash
git commit -m "Describe your changes"
```

Push the changes:

```bash
git push
```

## Pulling the Latest Changes

Before starting work, update your local repository:

```bash
git pull origin main
```

If you have local changes that have not been committed, commit or stash them before pulling.

## Creating a New Branch

For feature development, create a separate branch:

```bash
git checkout -b feature-name
```

Example:

```bash
git checkout -b solar-panel-detection
```

Push the branch:

```bash
git push -u origin solar-panel-detection
```

## Recommended Git Workflow

```bash
git pull origin main
git checkout -b feature-name

# Make changes

git status
git add .
git commit -m "Implement feature"
git push -u origin feature-name
```

After testing, create a Pull Request on GitHub to merge the feature into `main`.

## API and Frontend Configuration

If the frontend requires a backend URL, configure it using the frontend environment configuration.

Example:

```env
VITE_API_URL=http://127.0.0.1:8000
```

The exact environment variable depends on the frontend implementation.

Do not hard-code production credentials or private API keys into the source code.

## Common Problems

### Git is not recognized

If Windows reports:

```text
git is not recognized
```

Install Git and restart VS Code.

Verify:

```powershell
git --version
```

### Python is not recognized

Verify Python:

```powershell
python --version
```

If Python is not available, install Python and ensure it is added to the system PATH.

### npm is not recognized

Install Node.js and restart the terminal.

Verify:

```powershell
node --version
npm --version
```

### Backend dependency errors

Activate the virtual environment:

```powershell
venv\Scripts\activate
```

Then reinstall dependencies:

```powershell
pip install -r requirements.txt
```

### Frontend dependency errors

Delete the existing dependency directory and lock file if necessary:

```bash
rm -rf node_modules package-lock.json
npm install
```

On Windows PowerShell:

```powershell
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install
```

### Docker problems

Check Docker:

```bash
docker --version
docker compose version
```

Then rebuild:

```bash
docker compose down
docker compose build --no-cache
docker compose up
```

## Security

Never commit sensitive information to GitHub.

Do not commit:

```text
.env
*.key
*.pem
credentials.json
service-account.json
```

Use environment variables for:

* Database credentials
* API keys
* Authentication secrets
* Cloud credentials
* Third-party service credentials

## Contribution

1. Fork the repository.
2. Create a feature branch.
3. Implement your changes.
4. Test the backend and frontend.
5. Commit your changes.
6. Push your branch.
7. Create a Pull Request.

## License

Add the appropriate project license here.

## Repository

GitHub:

https://github.com/SaikatxAlpha/Sol-Sight.git
