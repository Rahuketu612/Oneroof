# OneRoof - Setup & Development Guide

## Prerequisites

Before you begin, install these tools on your Windows laptop:

### 1. Python (for Backend)
- Download from: https://www.python.org/downloads/
- **Important**: Check ✅ "Add Python to PATH" during installation
- Verify: Open CMD and type `python --version`

### 2. Node.js (for Frontend)
- Download from: https://nodejs.org/ (LTS version)
- Verify: Open CMD and type `node --version`

### 3. Git (for Version Control)
- Download from: https://git-scm.com/download/win
- Verify: Open CMD and type `git --version`

---

## Step 1: Download the Project

**Option A - Direct Download:**
1. Go to: https://github.com/Rahuketu612/oneroof
2. Click the green "Code" button
3. Click "Download ZIP"
4. Extract the ZIP file to your desired location

**Option B - Git Clone:**
```cmd
git clone https://github.com/Rahuketu612/oneroof.git
cd oneroof
```

---

## Step 2: Setup Backend (Python/FastAPI)

Open Command Prompt and run:

```cmd
cd oneroof

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn oneroof.main:app --reload
```

You'll see something like:
```
Uvicorn running on http://127.0.0.1:8000
```

---

## Step 3: Setup Frontend (React/Node.js)

Open a **new** Command Prompt window (keep backend running):

```cmd
cd oneroof\frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```

You'll see something like:
```
VITE v5.x.x ready in 1234 ms
➜ Local: http://localhost:3000/
```

---

## Step 4: View the Application

1. Open your browser (Chrome/Edge)
2. Go to: http://localhost:3000
3. Login with demo credentials (after we create them)

---

## Step 5: Database Setup (PostgreSQL)

For production, you'll need PostgreSQL:

1. Download: https://www.postgresql.org/download/windows/
2. Install with default settings
3. Create database named `oneroof`
4. Update `oneroof/core/config.py` with your database URL

For development/testing, the app uses SQLite automatically.

---

## Project Structure

```
oneroof/
├── oneroof/           # Backend (Python/FastAPI)
│   ├── main.py       # App entry point
│   ├── api/          # API endpoints
│   └── core/         # Config, DB, Security
├── frontend/         # Frontend (React/TypeScript)
│   └── src/
│       ├── pages/    # Page components
│       └── context/  # Auth & state management
└── requirements.txt  # Python dependencies
```

---

## Common Commands

```cmd
# Backend
venv\Scripts\activate
uvicorn oneroof.main:app --reload

# Frontend
cd frontend
npm run dev

# Stop servers
Ctrl+C
```

---

## What's Next?

After running the basic setup:

1. **Create demo users** - I can add registration endpoints
2. **Add database models** - Run migrations
3. **Implement missing pages** - Build out UI
4. **Add authentication** - Secure the app
5. **Deploy** - Host it online

Tell me which part you want to work on next!