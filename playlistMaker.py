#Library importd and setup
import os
import spotipy
import time

#Third-part imports
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session, redirect, render_template_string
from dotenv import load_dotenv
from collections import Counter

#Load environment variables from a .env file as to not expose sensitive information
load_dotenv()

#Initialising Flask application and setting secret key for sessionn security
app = Flask(__name__)
app.secret_key = os.getenv("secretKey")
#Customise the session cookie name for clarity
app.config["SESSION_COOKIE_NAME"] = "spotify-login-session"

#Constant for storing token info in session
TOKEN_INFO = "token_info"

# Server-side cache to store genre data (since session cookies are too small, this helps avoid storing large data in session cookies)
genre_data_cache = {}

@app.route("/")
def login():
    #Generates Spotify OAuth URL and redirects user to Spotify's login page
    auth_url = create_spotify_oauth().get_authorize_url()
    #Redirects the user to Spotify's authorization page to log in and authorize the app
    return redirect(auth_url)

@app.route("/redirect")
def redirect_page():
    #Clears any existing session data for a new login
    session.clear()
    #Retrieves the temporary authorization code from the URL parameters
    code = request.args.get("code")
    #Exchanges the authorization code for an access token and refresh token
    token_info = create_spotify_oauth().get_access_token(code, as_dict=True)
    #Stores the token info securely in the session
    session[TOKEN_INFO] = token_info
    #Redirects the user to the dashboard page after successful login
    return redirect(url_for("dashboard", _external=True))

@app.route("/dashboard")
def dashboard():
    #Rendering the main dashboard page showing the users music statistic and genre analysis
    try:
        #Retrieves valid token info, if login is unnsuccessful/expired it will then redirect to login
        token_info = get_token()
        if not isinstance(token_info, dict):
            return token_info
        
        #Creating Spotipy client with the user access token
        sp = spotipy.Spotify(auth=token_info['access_token'])
        
        #Fetching the current users profile information
        user = sp.me()
        username = user['display_name']
        user_id = user['id']
        
        #Retrieving cached genre data if available from the user to avoid repeated API calls 
        genre_data = genre_data_cache.get(user_id)
        
        #If no cached data, perform full genre analysis across the users playlist
        if not genre_data:
            print("\n" + "="*50)
            print("Starting genre analysis...")
            print("="*50)
            genre_data = analyse_genres(sp)
            
            #If there is no genres being found would then print a message
            if not genre_data['genres']:
                print("No genres found!")

            #Store the data in server cache, otherwise would have problems acessing the data as its too large for session cookies
            genre_data_cache[user_id] = genre_data
            #Purpose is to check terminal for progress
            print("Analysis complete!")
            print("Data cached for user")
        else:
            print("Using cached data for user")
        
        #If no genres found, display a message prompting the user to add music
        if not genre_data['genres']:
            return render_error("No genres found in your playlists")
        
        #Extracting the top 10 genres for visualisation and display
        top_genres = genre_data['top_genres'][:10]
        genre_labels = [g[0] for g in top_genres]
        genre_counts = [g[1] for g in top_genres]
        
        #Stores the genre data in session for potential future use (routes)
        session['genre_data'] = genre_data
        
        #HTML dashboard with embedded charts and sstatistics for the user to view 
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Your Music Statistics</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background: linear-gradient(135deg, #1DB954 0%, #191414 100%);
                    min-height: 100vh;
                }}
                .container {{
                    background: white;
                    border-radius: 15px;
                    padding: 30px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                }}
                h1 {{
                    color: #191414;
                    text-align: center;
                    margin-bottom: 10px;
                }}
                .subtitle {{
                    text-align: center;
                    color: #666;
                    margin-bottom: 30px;
                }}
                .stats-box {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                .stat {{
                    background: #f0f0f0;
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center;
                }}
                .stat-number {{
                    font-size: 2em;
                    font-weight: bold;
                    color: #1DB954;
                }}
                .stat-label {{
                    color: #666;
                    margin-top: 5px;
                }}
                .charts {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 30px;
                    margin-bottom: 30px;
                }}
                .chart-container {{
                    background: #f9f9f9;
                    padding: 20px;
                    border-radius: 10px;
                }}
                canvas {{
                    max-height: 400px;
                }}
                .genre-list {{
                    margin-top: 30px;
                }}
                .genre-item {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 15px;
                    margin: 10px 0;
                    background: #f9f9f9;
                    border-radius: 8px;
                    transition: all 0.3s;
                }}
                .genre-item:hover {{
                    background: #e8f5e9;
                    transform: translateX(5px);
                }}
                .genre-name {{
                    font-weight: bold;
                    color: #333;
                }}
                .genre-count {{
                    color: #666;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background: #1DB954;
                    color: white;
                    text-decoration: none;
                    border-radius: 25px;
                    font-weight: bold;
                    transition: all 0.3s;
                    border: none;
                    cursor: pointer;
                    font-size: 14px;
                }}
                .button:hover {{
                    background: #1ed760;
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(29, 185, 84, 0.3);
                }}
                .button-secondary {{
                    background: #535353;
                }}
                .button-secondary:hover {{
                    background: #404040;
                }}
                .actions {{
                    text-align: center;
                    margin-top: 30px;
                }}
                @media (max-width: 768px) {{
                    .charts {{
                        grid-template-columns: 1fr;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Your Music Statistics</h1>
                <p class="subtitle">Welcome, {username}!</p>
                
                <div class="stats-box">
                    <div class="stat">
                        <div class="stat-number">{genre_data['total_tracks']}</div>
                        <div class="stat-label">Total Tracks</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">{genre_data['total_playlists']}</div>
                        <div class="stat-label">Playlists</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">{len(genre_data['genres'])}</div>
                        <div class="stat-label">Unique Genres</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">{genre_data['total_artists']}</div>
                        <div class="stat-label">Unique Artists</div>
                    </div>
                </div>
                
                <div class="charts">
                    <div class="chart-container">
                        <h3>Top Genres (Bar Chart)</h3>
                        <canvas id="barChart"></canvas>
                    </div>
                    <div class="chart-container">
                        <h3>Genre Distribution (Pie Chart)</h3>
                        <canvas id="pieChart"></canvas>
                    </div>
                </div>
                
                <div class="genre-list">
                    <h3>Your Top Genres</h3>
                    {''.join([f'''
                    <div class="genre-item">
                        <span class="genre-name">{i+1}. {genre}</span>
                        <div>
                            <span class="genre-count">{count} tracks</span>
                            <a href="/create-genre-playlist?genre={genre.replace(' ', '+')}" class="button" style="margin-left: 15px;">Create Playlist</a>
                        </div>
                    </div>
                    ''' for i, (genre, count) in enumerate(top_genres)])}
                </div>
                
                <div class="actions">
                    <a href="/custom-genre" class="button button-secondary">Search Custom Genre</a>
                    <a href="/refresh-analysis" class="button button-secondary">Refresh Analysis</a>
                </div>
            </div>
            
            <script>
                const genres = {genre_labels};
                const counts = {genre_counts};
                
                // Generate colors
                const colors = [
                    '#1DB954', '#1ed760', '#169c46', '#117a37',
                    '#0d5c2a', '#535353', '#b3b3b3', '#ffffff',
                    '#ff6b6b', '#4ecdc4'
                ];
                
                // Bar Chart
                new Chart(document.getElementById('barChart'), {{
                    type: 'bar',
                    data: {{
                        labels: genres,
                        datasets: [{{
                            label: 'Number of Tracks',
                            data: counts,
                            backgroundColor: colors,
                            borderWidth: 0
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {{
                            legend: {{ display: false }}
                        }},
                        scales: {{
                            y: {{
                                beginAtZero: true,
                                ticks: {{ precision: 0 }}
                            }}
                        }}
                    }}
                }});
                
                // Pie Chart
                new Chart(document.getElementById('pieChart'), {{
                    type: 'pie',
                    data: {{
                        labels: genres,
                        datasets: [{{
                            data: counts,
                            backgroundColor: colors
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {{
                            legend: {{
                                position: 'bottom'
                            }}
                        }}
                    }}
                }});
            </script>
        </body>
        </html>
        '''
        
        return html
    
    except spotipy.exceptions.SpotifyException as e:
        #Handles Spotify API errors
        return render_error(f"Spotify API Error: {str(e)}")
    except Exception as e:
        #Handles unexpected errors
        return render_error(f"Error: {str(e)}")

@app.route("/analyse")
def analyse():
    try:
        #Ensures the user has a valid access token
        token_info = get_token()
        if not isinstance(token_info, dict):
            return token_info #Redirects to login if token is invalid
        
        sp = spotipy.Spotify(auth=token_info['access_token'])
        user_id = sp.me()['id'] #Fetches the user's Spotify ID
        
        #Remove cached genre data so next dashboard load will re-analyse
        if user_id in genre_data_cache:
            del genre_data_cache[user_id]
            #print(f"Cleared cache for user: {user_id}") #Debugging purpose
        
        return redirect(url_for("dashboard")) #Trigger dashboard reload
    except:
        #Safely redirect to dashboard on any error
        return redirect(url_for("dashboard"))

@app.route("/refresh-analysis")
def refresh_analysis():
    try:
        #Ensures valid spotify token
        token_info = get_token()
        if not isinstance(token_info, dict):
            return token_info
        
        sp = spotipy.Spotify(auth=token_info['access_token'])
        user_id = sp.me()['id']
        
        #Remove cached genre data so next dashboard load will re-analyse
        if user_id in genre_data_cache:
            del genre_data_cache[user_id]
            print(f"Cleared cache for user: {user_id}")
        
        return redirect(url_for("dashboard"))
    except:
        return redirect(url_for("dashboard"))

@app.route("/create-genre-playlist")
def create_genre_playlist():
    genre = request.args.get("genre", "").lower().strip()
    if not genre:
        #Early exit if genre is missing
        return render_error("No genre specified")
    
    try:
        #Validate user session and token
        token_info = get_token()
        if not isinstance(token_info, dict):
            return token_info
        
        sp = spotipy.Spotify(auth=token_info['access_token'])
        user_id = sp.me()['id']
        
        #Retrives cached analysis data
        genre_data = genre_data_cache.get(user_id)
        
        if not genre_data:
            print(f"No cached data for user {user_id}, redirecting to dashboard")
            return redirect(url_for("dashboard"))
        
        print(f"\n{'='*50}")
        print(f"Creating playlist for genre: '{genre}'")
        print(f"User: {user_id}")
        print(f"{'='*50}")
        
        #Filter tracks matching the specified genre
        track_uris = []
        #Progess checker in terminal
        print(f"Searching through {len(genre_data['track_genres'])}")
        
        for track_genre, uri in genre_data['track_genres']:
            #Check if the genre matches
            if genre == track_genre.lower() or genre in track_genre.lower():
                track_uris.append(uri)
        
        #Removing duplicates
        track_uris = list(set(track_uris))
        #Print the matching tracks found in terminal 
        print(f"Found {len(track_uris)} matching tracks")
        
        if not track_uris:
            print(f"No tracks found for genre '{genre}'")
            #Show available genres for debugging
            all_genres = set([g for g, _ in genre_data['track_genres']])
            print(f"Available genres: {sorted(all_genres)}")
            return render_error(f"No tracks found for genre '{genre}'. Try another genre from the list.")
        
        #Create playlist
        user_id = sp.me()['id']
        playlist_name = f"{genre.title()} - My Collection"
        
        print(f"Creating playlist '{playlist_name}'...")
        
        new_playlist = sp.user_playlist_create(
            user_id, 
            playlist_name, 
            public=False, 
            description=f"Curated {genre} playlist created by Genre Analyser"
        )
        
        print(f"Playlist created with ID: {new_playlist['id']}")
        
        #Add tracks in batches of 100 for Spotify API limits
        added_count = 0
        for i in range(0, len(track_uris), 100):
            batch = track_uris[i:i+100]
            sp.user_playlist_add_tracks(user_id, new_playlist['id'], batch)
            added_count += len(batch)
            print(f"Added batch: {added_count}/{len(track_uris)} tracks")
        
        playlist_url = new_playlist['external_urls']['spotify']
        
        print(f"Playlist created successfully!")
        print(f"URL: {playlist_url}")
        print(f"{'='*50}\n")
        
        return render_success(
            f"Created playlist '{playlist_name}' with {len(track_uris)} tracks!",
            playlist_url
        )
        
    except spotipy.exceptions.SpotifyException as e:
        print(f"Spotify API Error: {e}")
        import traceback
        traceback.print_exc()
        return render_error(f"Spotify API Error: {str(e)}. Check the terminal for details.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return render_error(f"Error creating playlist: {str(e)}. Check the terminal for details.")

@app.route("/search-new-songs")
def search_new_songs():
    genre = request.args.get("genre", "")
    
    if not genre:
        #No genre provided, show selection interface using cached session data
        genre_data = session.get('genre_data', {})
        top_genres = genre_data.get('top_genres', [])[:10]
    
    #Search for songs
    try:
        token_info = get_token()
        if not isinstance(token_info, dict):
            return token_info
        
        sp = spotipy.Spotify(auth=token_info['access_token'])
        
        #Search for tracks in this genre
        results = sp.search(q=f'genre:"{genre}"', type='track', limit=50)
        tracks = results['tracks']['items']
        
        if not tracks:
            return render_error(f"No tracks found for genre '{genre}'")
        
        #Creating the HTML for track selection
        track_html = ''.join([f'''
        <div class="track-item">
            <input type="checkbox" name="tracks" value="{track['uri']}" id="track{i}">
            <label for="track{i}">
                <strong>{track['name']}</strong><br>
                <small>{', '.join([artist['name'] for artist in track['artists']])}</small>
            </label>
        </div>
        ''' for i, track in enumerate(tracks)])
        
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>New {genre.title()} Songs</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    max-width: 900px;
                    margin: 20px auto;
                    padding: 20px;
                    background: linear-gradient(135deg, #1DB954 0%, #191414 100%);
                    min-height: 100vh;
                }}
                .container {{
                    background: white;
                    border-radius: 15px;
                    padding: 30px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                }}
                h1 {{ color: #191414; }}
                .track-item {{
                    padding: 15px;
                    margin: 10px 0;
                    background: #f9f9f9;
                    border-radius: 8px;
                    display: flex;
                    align-items: center;
                    gap: 15px;
                }}
                .track-item:hover {{
                    background: #e8f5e9;
                }}
                input[type="checkbox"] {{
                    width: 20px;
                    height: 20px;
                    cursor: pointer;
                }}
                label {{
                    cursor: pointer;
                    flex: 1;
                }}
                .button {{
                    padding: 15px 30px;
                    background: #1DB954;
                    color: white;
                    border: none;
                    border-radius: 25px;
                    font-size: 16px;
                    font-weight: bold;
                    cursor: pointer;
                    margin: 10px 5px;
                }}
                .button:hover {{
                    background: #1ed760;
                }}
                .button-secondary {{
                    background: #535353;
                }}
                .button-secondary:hover {{
                    background: #404040;
                }}
                .actions {{
                    position: sticky;
                    bottom: 0;
                    background: white;
                    padding: 20px;
                    margin: 20px -30px -30px -30px;
                    border-radius: 0 0 15px 15px;
                    box-shadow: 0 -5px 15px rgba(0,0,0,0.1);
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>New {genre.title()} Songs</h1>
                <p style="color: #666;">Found {len(tracks)} tracks. Select the ones you want to add to a new playlist:</p>
                
                <form method="POST" action="/add-to-playlist">
                    <input type="hidden" name="genre" value="{genre}">
                    <button type="button" onclick="selectAll()" class="button button-secondary">Select All</button>
                    <button type="button" onclick="deselectAll()" class="button button-secondary">Deselect All</button>
                    
                    <div style="margin: 20px 0;">
                        {track_html}
                    </div>
                    
                    <div class="actions">
                        <button type="submit" class="button">Create Playlist with Selected</button>
                        <a href="/search-new-songs" class="button button-secondary">← Back</a>
                    </div>
                </form>
            </div>
            
            <script>
                function selectAll() {{
                    document.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = true);
                }}
                function deselectAll() {{
                    document.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
                }}
            </script>
        </body>
        </html>
        '''
        return html
        
    except Exception as e:
        return render_error(f"Error searching songs: {str(e)}")

@app.route("/add-to-playlist", methods=["POST"])
def add_to_playlist():
    try:
        token_info = get_token()
        if not isinstance(token_info, dict):
            return token_info
        
        sp = spotipy.Spotify(auth=token_info['access_token'])
        
        genre = request.form.get('genre', 'Music')
        track_uris = request.form.getlist('tracks')
        
        if not track_uris:
            return render_error("No tracks selected!")
        
        #Creating playlist
        user_id = sp.me()['id']
        playlist_name = f"Discover {genre.title()} - {time.strftime('%Y-%m-%d')}"
        new_playlist = sp.user_playlist_create(user_id, playlist_name, public=False)
        
        #Adding tracks
        for i in range(0, len(track_uris), 100):
            batch = track_uris[i:i+100]
            sp.user_playlist_add_tracks(user_id, new_playlist['id'], batch)
        
        playlist_url = new_playlist['external_urls']['spotify']
        
        return render_success(
            f"Created playlist '{playlist_name}' with {len(track_uris)} tracks!",
            playlist_url
        )
        
    except Exception as e:
        return render_error(f"Error creating playlist: {str(e)}")

@app.route("/custom-genre")
def custom_genre():
    genre = request.args.get("genre", "")
    
    if not genre:
        html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Custom Genre Search</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    max-width: 600px;
                    margin: 100px auto;
                    padding: 20px;
                    background: linear-gradient(135deg, #1DB954 0%, #191414 100%);
                    min-height: 100vh;
                }
                .container {
                    background: white;
                    border-radius: 15px;
                    padding: 40px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                }
                h1 { color: #191414; text-align: center; }
                input[type="text"] {
                    width: 100%;
                    padding: 15px;
                    font-size: 16px;
                    border: 2px solid #e0e0e0;
                    border-radius: 10px;
                    margin: 20px 0;
                    box-sizing: border-box;
                }
                input[type="text"]:focus {
                    outline: none;
                    border-color: #1DB954;
                }
                .button {
                    width: 100%;
                    padding: 15px;
                    background: #1DB954;
                    color: white;
                    border: none;
                    border-radius: 25px;
                    font-size: 16px;
                    font-weight: bold;
                    cursor: pointer;
                }
                .button:hover {
                    background: #1ed760;
                }
                .back-link {
                    display: block;
                    text-align: center;
                    margin-top: 20px;
                    color: #666;
                    text-decoration: none;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Search Custom Genre</h1>
                <form method="get">
                    <input type="text" name="genre" placeholder="Enter genre" required>
                    <button type="submit" class="button">Search in My Library</button>
                </form>
                <a href="/dashboard" class="back-link">← Back to Dashboard</a>
            </div>
        </body>
        </html>
        '''
        return html
    
    # Search in user's library
    return redirect(url_for("create_genre_playlist", genre=genre))

def analyse_genres(sp):
    print("Fetching playlists")
    #Retrieves all the playlists from the user library (handling pagination)
    playlists = []
    results = sp.current_user_playlists()
    playlists.extend(results['items'])
    while results['next']:
        results = sp.next(results)
        playlists.extend(results['items'])
    
    print(f"Found {len(playlists)} playlists")
    
    #Initialise counters and caches
    genre_counter = Counter() #Tracks the genre counts
    track_genres = []  #Stores (genre, track_uri) pairs for playlist creation
    artist_cache = {} #Cache artist genre data to reduce API calls
    seen_tracks = set() #Prevents duplicate track processing
    total_tracks = 0
    unique_artists = set() #Track unique artist ID
    
    #Iterate through each playlist to fetch tracks and their genres
    for idx, playlist in enumerate(playlists):
        #Checking in terminal for progess of it checking each playlist
        print(f"Processing playlist {idx+1}/{len(playlists)}: {playlist['name']}")
        try:
            #Fetch all tracks in the playlist (handling pagination)
            results = sp.playlist_items(playlist['id'])
            tracks = results['items']
            while results['next']:
                results = sp.next(results)
                tracks.extend(results['items'])
            print(f"  - Found {len(tracks)} tracks in this playlist")
            
            #Process each track to get artist and genre information
            for item in tracks:
                track = item.get('track')
                if not track or not track.get('id') or track['id'] in seen_tracks:
                    continue #Skipping invalid or duplicate tracks
                seen_tracks.add(track['id'])
                total_tracks += 1
                
                if not track.get('artists') or not track['artists'][0].get('id'):
                    continue #Skipping tracks without artist information
                
                artist_id = track['artists'][0]['id']
                unique_artists.add(artist_id)
                
                #Use cached genres if available, otherwise fetch from Spotify
                if artist_id in artist_cache:
                    artist_genres = artist_cache[artist_id]
                else:
                    try:
                        artist = sp.artist(artist_id)
                        artist_genres = artist.get('genres', [])
                        artist_cache[artist_id] = artist_genres
                        
                        if artist_genres:
                            print(f"Found genres for {track['artists'][0]['name']}: {artist_genres}")
                        
                        time.sleep(0.1)  #Respect rate limits
                    except Exception as e:
                        print(f"Error fetching artist {artist_id}: {e}")
                        continue
                
                #Count genres and map tracs to genres
                if artist_genres:
                    for genre in artist_genres:
                        genre_counter[genre] += 1
                        track_genres.append((genre, track['uri']))
                    
        except Exception as e:
            print(f"Error processing playlist {playlist['name']}: {e}")
            continue
        
    #Final summary of the analysis in terminal to check the progess and results
    print(f"\n=== Analysis Complete ===")
    print(f"Total tracks processed: {total_tracks}")
    print(f"Unique artists: {len(unique_artists)}")
    print(f"Genres found: {len(genre_counter)}")
    print(f"Top 5 genres: {genre_counter.most_common(5)}")
    
    return {
        'genres': dict(genre_counter),
        'top_genres': genre_counter.most_common(),
        'track_genres': track_genres,
        'total_tracks': total_tracks,
        'total_playlists': len(playlists),
        'total_artists': len(unique_artists)
    }

def render_error(message):
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Error</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 600px;
                margin: 100px auto;
                padding: 20px;
                background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
                min-height: 100vh;
            }}
            .container {{
                background: white;
                border-radius: 15px;
                padding: 40px;
                text-align: center;
            }}
            h1 {{ color: #e74c3c; }}
            .button {{
                display: inline-block;
                padding: 12px 24px;
                background: #535353;
                color: white;
                text-decoration: none;
                border-radius: 25px;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Error</h1>
            <p>{message}</p>
            <a href="/dashboard" class="button">Back to Dashboard</a>
        </div>
    </body>
    </html>
    '''

def render_success(message, playlist_url=None):
    playlist_link = f'<a href="{playlist_url}" class="button" target="_blank">Open in Spotify</a>' if playlist_url else ''
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Success</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 600px;
                margin: 100px auto;
                padding: 20px;
                background: linear-gradient(135deg, #1DB954 0%, #169c46 100%);
                min-height: 100vh;
            }}
            .container {{
                background: white;
                border-radius: 15px;
                padding: 40px;
                text-align: center;
            }}
            h1 {{ color: #1DB954; }}
            .button {{
                display: inline-block;
                padding: 12px 24px;
                background: #1DB954;
                color: white;
                text-decoration: none;
                border-radius: 25px;
                margin: 10px;
                font-weight: bold;
            }}
            .button:hover {{
                background: #1ed760;
            }}
            .button-secondary {{
                background: #535353;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Success</h1>
            <p>{message}</p>
            {playlist_link}
            <a href="/dashboard" class="button button-secondary">Back to Dashboard</a>
        </div>
    </body>
    </html>
    '''

def get_token():
    #Retrieves the Spotify access token information from the flask sesion
    token_info = session.get(TOKEN_INFO, None)
    #If not token info is found in the session, redirects the user to the login page
    if not token_info:
        return redirect(url_for("login", _external=True))
    
    #Get the current time in seconds
    now = int(time.time())
    
    #Checks if the token is about to expire 
    is_expired = token_info['expires_at'] - now < 60
    
    if is_expired:
        spotify_oauth = create_spotify_oauth() #Creates a SpotifyOAuth object if the token is/about to expired
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token']) #Refresh the acess token using the stored refresh token
        session[TOKEN_INFO] = token_info #Updates the session with the new token information
    return token_info #Returns the valid token information for use in API calls

def create_spotify_oauth():
    #Creates and returns a SpotifyOAuth object using the client ID, client secret, and redirect URI from environment variables
    return SpotifyOAuth(
        client_id=os.getenv('clientID'),
        client_secret=os.getenv("clientSecret"),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
        scope="user-library-read playlist-modify-public playlist-modify-private playlist-read-private"
    )

if __name__ == "__main__":
    app.run(debug=True)