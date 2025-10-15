import sys
import requests
import base64
import webbrowser
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QScrollArea, QFrame, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont

class SpotifyAPI:
    def __init__(self):
        self.client_id = "7b8fa041600c4fe48abe70263d5f5638"
        self.client_secret = "40ed4bc8bf9b4e7e8ab54b8e2c3ab847"
        self.access_token = None
        self.base_url = "https://api.spotify.com/v1"
        self.get_access_token()
    
    def get_access_token(self):
        auth_url = "https://accounts.spotify.com/api/token"
        auth_header = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        headers = {"Authorization": f"Basic {auth_header}"}
        data = {"grant_type": "client_credentials"}
        
        try:
            response = requests.post(auth_url, headers=headers, data=data)
            print(f"Auth Status Code: {response.status_code}")
            if response.status_code == 200:
                self.access_token = response.json()["access_token"]
                print(f"Access token obtained: {self.access_token[:20]}...")
                return True
            else:
                print(f"Auth Error: {response.text}")
            return False
        except Exception as e:
            print(f"Auth Exception: {e}")
            return False
    
    def search_track(self, query):
        if not self.access_token:
            print("No access token!")
            return None
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        params = {"q": query, "type": "track", "limit": 1}
        
        try:
            response = requests.get(f"{self.base_url}/search", headers=headers, params=params)
            print(f"Search Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                items = data["tracks"]["items"]
                return items[0] if items else None
            else:
                print(f"Search Error: {response.text}")
            return None
        except Exception as e:
            print(f"Search Exception: {e}")
            return None
    
    def get_recommendations(self, seed_track_id, limit=10):
        if not self.access_token:
            print("No access token for recommendations!")
            return []
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        params = {
            "seed_tracks": seed_track_id,
            "limit": limit,
            "market": "US"
        }
        
        try:
            response = requests.get(f"{self.base_url}/recommendations", headers=headers, params=params)
            print(f"Recommendations Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Got {len(data.get('tracks', []))} recommendations")
                return data.get("tracks", [])
            else:
                print(f"Recommendations Error: {response.text}")
                return self.get_artist_top_tracks_fallback(seed_track_id)
        except Exception as e:
            print(f"Recommendations Exception: {e}")
            return []
    
    def get_artist_top_tracks_fallback(self, track_id):
        if not self.access_token:
            return []
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            track_response = requests.get(f"{self.base_url}/tracks/{track_id}", headers=headers)
            if track_response.status_code == 200:
                track_data = track_response.json()
                if track_data.get("artists"):
                    artist_id = track_data["artists"][0]["id"]
                    
                    top_tracks_response = requests.get(
                        f"{self.base_url}/artists/{artist_id}/top-tracks",
                        headers=headers,
                        params={"market": "US"}
                    )
                    
                    if top_tracks_response.status_code == 200:
                        tracks = top_tracks_response.json().get("tracks", [])
                        print(f"Fallback: Got {len(tracks)} top tracks from artist")
                        return tracks[:10]
            return []
        except Exception as e:
            print(f"Fallback Exception: {e}")
            return []


class TrackCard(QFrame):
    def __init__(self, track_data, parent=None):
        super().__init__(parent)
        self.track_url = track_data.get("external_urls", {}).get("spotify", "")
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("""
            TrackCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2d2d2d, stop:1 #1a1a1a);
                border-radius: 15px;
                border: 2px solid #3d3d3d;
                padding: 15px;
                margin: 5px;
            }
            TrackCard:hover {
                border: 2px solid #1db954;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3d3d3d, stop:1 #2a2a2a);
                cursor: pointer;
            }
        """)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QHBoxLayout()
        layout.setSpacing(15)
        
        # Album art
        img_label = QLabel()
        img_label.setFixedSize(80, 80)
        img_label.setStyleSheet("border-radius: 10px; border: 2px solid #1db954;")
        
        if track_data.get("album", {}).get("images"):
            img_url = track_data["album"]["images"][0]["url"]
            try:
                img_data = requests.get(img_url).content
                pixmap = QPixmap()
                pixmap.loadFromData(img_data)
                img_label.setPixmap(pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            except:
                img_label.setText("🎵")
                img_label.setAlignment(Qt.AlignCenter)
                img_label.setStyleSheet("font-size: 36px; background: #1a1a1a; border-radius: 10px; border: 2px solid #1db954;")
        
        layout.addWidget(img_label)
        
        # Track info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        
        title = QLabel(track_data["name"])
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setStyleSheet("color: #ffffff; border: none;")
        title.setWordWrap(True)
        
        artists = ", ".join([artist["name"] for artist in track_data["artists"]])
        artist_label = QLabel(artists)
        artist_label.setFont(QFont("Arial", 10))
        artist_label.setStyleSheet("color: #b3b3b3; border: none;")
        
        album = QLabel(track_data["album"]["name"])
        album.setFont(QFont("Arial", 9))
        album.setStyleSheet("color: #808080; border: none;")
        
        info_layout.addWidget(title)
        info_layout.addWidget(artist_label)
        info_layout.addWidget(album)
        info_layout.addStretch()
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # Popularity indicator
        popularity = track_data.get("popularity", 0)
        pop_label = QLabel(f"{popularity}%")
        pop_label.setFont(QFont("Arial", 14, QFont.Bold))
        pop_label.setStyleSheet(f"color: #1db954; border: none;")
        pop_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(pop_label)
        
        # Play button
        play_btn = QPushButton("▶ Play")
        play_btn.setStyleSheet("""
            QPushButton {
                background: #1db954;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #1ed760;
            }
            QPushButton:pressed {
                background: #169c46;
            }
        """)
        play_btn.setCursor(Qt.PointingHandCursor)
        play_btn.clicked.connect(self.open_in_spotify)
        layout.addWidget(play_btn)
        
        self.setLayout(layout)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.open_in_spotify()
    
    def open_in_spotify(self):
        if self.track_url:
            webbrowser.open(self.track_url)
            print(f"Opening: {self.track_url}")


class SpotifyRecommender(QMainWindow):
    def __init__(self):
        super().__init__()
        self.spotify = SpotifyAPI()
        self.init_ui()
        QTimer.singleShot(500, self.load_featured_tracks)
        
    def init_ui(self):
        self.setWindowTitle("Spotify AI Music Recommender")
        self.setGeometry(100, 100, 1000, 700)
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0a0a0a, stop:1 #1a1a1a);
            }
        """)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Header
        header = QLabel("🎵 Spotify Music Recommender")
        header.setFont(QFont("Arial", 32, QFont.Bold))
        header.setStyleSheet("color: #1db954; padding: 20px;")
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)
        
        # Search section
        search_frame = QFrame()
        search_frame.setStyleSheet("""
            QFrame {
                background: #2d2d2d;
                border-radius: 20px;
                padding: 30px;
            }
        """)
        search_layout = QVBoxLayout(search_frame)
        
        search_title = QLabel("🔍 Search for Any Song or Artist")
        search_title.setFont(QFont("Arial", 16, QFont.Bold))
        search_title.setStyleSheet("color: #ffffff;")
        search_title.setAlignment(Qt.AlignCenter)
        search_layout.addWidget(search_title)
        
        search_input_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Try 'Peaches Justin Bieber', 'Blinding Lights', or any song...")
        self.search_input.setStyleSheet(self.input_style())
        self.search_input.returnPressed.connect(self.get_recommendations)
        
        search_btn = QPushButton("🎵 Get Recommendations")
        search_btn.clicked.connect(self.get_recommendations)
        search_btn.setStyleSheet(self.button_style())
        search_btn.setCursor(Qt.PointingHandCursor)
        search_btn.setFixedWidth(250)
        
        search_input_layout.addWidget(self.search_input)
        search_input_layout.addWidget(search_btn)
        search_layout.addLayout(search_input_layout)
        main_layout.addWidget(search_frame)
        
        # Results section
        self.results_label = QLabel("💡 Trending & Popular Tracks")
        self.results_label.setFont(QFont("Arial", 18, QFont.Bold))
        self.results_label.setStyleSheet("color: #1db954; padding: 10px;")
        main_layout.addWidget(self.results_label)
        
        # Scroll area for recommendations
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #1a1a1a;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #1db954;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background: #1ed760;
            }
        """)
        
        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout(self.results_widget)
        self.results_layout.setSpacing(10)
        self.results_layout.addStretch()
        
        scroll.setWidget(self.results_widget)
        main_layout.addWidget(scroll, 1)
        
        # Status bar
        self.status_label = QLabel("✅ Connected & Ready! Search for a song to get started...")
        self.status_label.setFont(QFont("Arial", 11))
        self.status_label.setStyleSheet("color: #1db954; padding: 10px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)
    
    def load_featured_tracks(self):
        """Load popular songs - simplified approach"""
        if not self.spotify.access_token:
            print("No access token for featured tracks!")
            return
        
        self.status_label.setText("🎵 Loading popular tracks...")
        QApplication.processEvents()
        
        # Search for popular songs one by one
        popular_queries = [
            "Blinding Lights The Weeknd",
            "Shape of You Ed Sheeran",
            "Someone Like You Adele",
            "Bohemian Rhapsody Queen",
            "Levitating Dua Lipa",
            "Starboy The Weeknd",
            "Perfect Ed Sheeran",
            "Radioactive Imagine Dragons"
        ]
        
        featured_tracks = []
        for query in popular_queries:
            try:
                print(f"Searching for: {query}")
                track = self.spotify.search_track(query)
                if track:
                    featured_tracks.append(track)
                    print(f"Found: {track['name']} by {track['artists'][0]['name']}")
            except Exception as e:
                print(f"Error searching for {query}: {e}")
        
        print(f"Total tracks found: {len(featured_tracks)}")
        
        if featured_tracks:
            print(f"Adding {len(featured_tracks)} track cards to UI...")
            for i, track_data in enumerate(featured_tracks):
                print(f"Adding track {i+1}: {track_data.get('name', 'Unknown')}")
                card = TrackCard(track_data)
                self.results_layout.insertWidget(self.results_layout.count() - 1, card)
            
            self.status_label.setText(f"✨ Showing {len(featured_tracks)} popular tracks! Search to discover more...")
            self.status_label.setStyleSheet("color: #1db954; padding: 10px;")
            print("Featured tracks loaded successfully!")
        else:
            print("No featured tracks to display")
            self.status_label.setText("⚠️ Couldn't load featured tracks. Try searching!")
    
    def input_style(self):
        return """
            QLineEdit {
                background: #1a1a1a;
                color: #ffffff;
                border: 2px solid #3d3d3d;
                border-radius: 12px;
                padding: 15px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 2px solid #1db954;
            }
        """
    
    def button_style(self):
        return """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1db954, stop:1 #1ed760);
                color: white;
                border: none;
                border-radius: 12px;
                padding: 15px 30px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1ed760, stop:1 #1fdf64);
            }
            QPushButton:pressed {
                background: #169c46;
            }
        """
    
    def get_recommendations(self):
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Empty Search", "Please enter a song name or artist!")
            return
        
        self.results_label.setText("💡 Recommended Tracks")
        
        self.status_label.setText("🔍 Searching for your track...")
        self.status_label.setStyleSheet("color: #1ed760; padding: 10px;")
        QApplication.processEvents()
        
        track = self.spotify.search_track(query)
        if not track:
            QMessageBox.warning(self, "Not Found", f"No track found for '{query}'. Try being more specific!")
            self.status_label.setText("❌ No results found. Try a different search!")
            self.status_label.setStyleSheet("color: #ff4444; padding: 10px;")
            return
        
        self.status_label.setText(f"🎵 Found '{track['name']}'! Getting recommendations...")
        self.status_label.setStyleSheet("color: #1ed760; padding: 10px;")
        QApplication.processEvents()
        
        recommendations = self.spotify.get_recommendations(track["id"], limit=10)
        
        # Clear previous results
        for i in reversed(range(self.results_layout.count())):
            widget = self.results_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # Add new results
        if recommendations:
            for track_data in recommendations:
                card = TrackCard(track_data)
                self.results_layout.insertWidget(self.results_layout.count() - 1, card)
            
            self.status_label.setText(f"✅ Found {len(recommendations)} awesome recommendations for you!")
            self.status_label.setStyleSheet("color: #1db954; padding: 10px;")
        else:
            self.status_label.setText("❌ No recommendations found. Try another song!")
            self.status_label.setStyleSheet("color: #ff4444; padding: 10px;")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpotifyRecommender()
    window.show()
    sys.exit(app.exec_())