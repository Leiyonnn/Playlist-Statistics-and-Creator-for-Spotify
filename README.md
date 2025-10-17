# 🎵 Spotify Genre Analyzer

### A Data Science Project for Music Analytics and Playlist Generation

Spotify Genre Analyser is an interactive **Flask web app** that connects to the **Spotify Web API** to analyse a user's playlists and listening habits.  
It performs **data extraction**, **genre aggregation**, and **statistical visualisation** of your Spotify library — all within a visually interactive dashboard.

The app also allows users to **automatically create new playlists** based on specific genres, making it both an **analytical tool** and a **data-driven recommender system**.

---

## 🚀 Key Features

- 🔐 **OAuth 2.0 Authentication** — Secure Spotify login using `Spotipy` and session management via Flask.
- 🎧 **Playlist & Track Analysis** — Fetches all playlists, tracks, and associated artist data.
- 📊 **Genre Statistics Dashboard** — Displays real-time genre distribution through interactive **bar and pie charts** (powered by Chart.js).
- 🧠 **Data-Driven Insights** — Shows number of playlists, tracks, unique artists, and genre diversity.
- 🎼 **Genre-Based Playlist Creation** — Generate playlists automatically for any genre in your library.
- 🔍 **Custom Genre Search** — Search for new tracks by genre and instantly build new Spotify playlists.
- ⚡ **Caching System** — Reduces redundant API calls for efficient repeated analysis.
- 🌐 **Responsive Web Interface** — Clean, modern UI with dynamic visuals and user feedback.

---

## 🧠 Why This Project?

This project was developed as a **data science showcase**, highlighting the following competencies:

- **Data Extraction & Cleaning** using APIs (`Spotipy` client library)
- **Data Transformation & Aggregation**
- **Statistical Analysis** of user listening behavior
- **Data Visualisation** through web-embedded charts
- **Full-Stack Integration** combining Flask backend logic and frontend interactivity
- **Automation & Recommendation** — dynamic playlist creation based on insights

---

## ⚙️ Setup Instructions
Clone the repository
Create a file named .env in the project’s root directory and add the following lines:

clientID=your_spotify_client_id
clientSecret=your_spotify_client_secret
SPOTIPY_REDIRECT_URI=http://127.0.0.1:5000/redirect
secretKey= [CHANGE THIS]

You can obtain your secretKey by setting your own in the [CHANGE THIS], for the clientID and clientSecret this can be created on the Spotify Developer Dashboard website.
