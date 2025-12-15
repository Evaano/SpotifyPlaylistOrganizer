# Spotify Playlist Sorter

A modern web application to analyze your Spotify usage and create sorted playlists by genre.

## Features

- **Dashboard**: View all your playlists and "Liked Songs" with track counts.
- **Multi-Select**: Choose multiple sources to merge and analyze.
- **Analysis**: See a visual breakdown of your top genres.
- **Playlist Creation**: One-click create new playlists for specific genres (e.g., "Pop Punk Mix") with duplicate prevention.
- **Smart Deduplication**: Merges tracks from multiple playlists and avoids adding duplicates to existing mixes.

## Tech Stack

- **Frontend**: React, Vite, Tailwind CSS, Lucide Icons.
- **Backend**: Python, FastAPI, Spotipy.
- **Deployment**: Vercel (Serverless).

## Setup (Local)

1.  **Backend**:
    ```bash
    cd backend
    pip install -r requirements.txt
    uvicorn main:app --reload
    ```
2.  **Frontend**:
    ```bash
    cd frontend
    npm install
    npm run dev
    ```
3.  **Environment Variables** (`.env`):
    ```
    SPOTIPY_CLIENT_ID=your_id
    SPOTIPY_CLIENT_SECRET=your_secret
    SPOTIPY_REDIRECT_URI=http://localhost:8000/callback
    ```

## Deployment (Vercel)

This project is configured for Vercel deployment with a Python backend and React frontend.

1.  Install Vercel CLI: `npm i -g vercel`
2.  Deploy: `vercel`
3.  **Important**: In Vercel Project Settings, add your Environment Variables:
    - `SPOTIPY_CLIENT_ID`
    - `SPOTIPY_CLIENT_SECRET`
    - `SPOTIPY_REDIRECT_URI` (Set this to `https://your-app.vercel.app/callback`)
4.  Update your Spotify Developer Dashboard with the new Redirect URI.

## How it works

The app uses the Spotify API to fetch track metadata. Since Spotify API doesn't allow "filtering by genre" directly for tracks, we:

1.  Fetch tracks from playlists.
2.  Fetch artist metadata for those tracks (which contains the genre info).
3.  Map genres to tracks and aggregate the data.
4.  Allow sorting/filtering based on this aggregated data.
