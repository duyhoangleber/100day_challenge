# 100 Day Challenge Tracker

A simple web application to track your 100-day challenge progress with a beautiful calendar interface.

## Features

- 📅 Calendar view showing all 100 days
- ✅ Mark/unmark tasks as completed
- 📝 Add notes for each day (double-click on a day)
- 📊 Real-time statistics (completed, remaining, progress percentage)
- 💾 SQLite database for data persistence
- 🎨 Beautiful, responsive UI

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://localhost:5001
```

## How to Use

- **Click** on a day card to mark/unmark it as completed
- **Double-click** on a day card to add/edit notes
- View your progress in the statistics section at the top

## Database

The application uses **Supabase (PostgreSQL)** to store data persistently:
- Tasks list
- Daily task completion status
- Day notes

**Setup Supabase:**

1. Go to your Supabase project: https://supabase.com/dashboard/project/pjjuiyfphwdopdotukpb
2. Navigate to **Settings** → **Database**
3. Find **Connection string** → **URI**
4. Copy the connection string (format: `postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres`)
5. Set it as environment variable `DATABASE_URL`

The database tables are automatically created when you first run the application.

## Project Structure

```
100day_challenge/
├── app.py              # Flask application
├── requirements.txt    # Python dependencies
├── Procfile            # For deployment (Render)
├── runtime.txt        # Python version specification
├── .gitignore         # Git ignore file
├── templates/          # HTML templates
│   └── index.html
└── static/            # Static files
    ├── css/
    │   └── style.css
    └── js/
        └── app.js
```

## Deployment to Render

This application is ready to deploy on [Render](https://render.com).

### Prerequisites

1. Push your code to a Git repository (GitHub, GitLab, or Bitbucket)
2. Have a Render account (free tier available)

### Deployment Steps

1. **Create a new Web Service on Render:**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect your repository

2. **Configure the service:**
   - **Name**: `100day-challenge` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Plan**: Free (or choose a paid plan)

3. **Set Environment Variables:**
   - Click "Environment" tab
   - Add `SECRET_KEY`: Generate a random string (e.g., use `openssl rand -hex 32`)
   - Add `DATABASE_URL`: Your Supabase connection string
     - Get it from: https://supabase.com/dashboard/project/pjjuiyfphwdopdotukpb → Settings → Database → Connection string (URI)
     - Format: `postgresql://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres`
   - `PORT` is automatically set by Render (no need to add)

4. **Deploy:**
   - Click "Create Web Service"
   - Render will automatically build and deploy your app
   - Wait for deployment to complete (usually 2-3 minutes)

5. **Access your app:**
   - Your app will be available at `https://your-app-name.onrender.com`
   - The database will be automatically created on first run

### Important Notes

- **Database**: Using Supabase (PostgreSQL) ensures data persistence. Your data will not be lost when the service restarts.

- **Auto-deploy**: Render automatically deploys on every push to your main branch

- **Free Tier Limitations**: 
  - Services spin down after 15 minutes of inactivity
  - First request after spin-down may take 30-60 seconds
  - Consider upgrading for production use

## License

Free to use for personal projects.

