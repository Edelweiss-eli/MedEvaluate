import os
import sys
import random
import firebase
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.image import Image, AsyncImage
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy_garden.mapview import MapView, MapMarker
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.clock import Clock
from kivy.uix.spinner import Spinner
from kivy.properties import ListProperty
import webbrowser
import cloudinary
import cloudinary.uploader
import cloudinary.api
import requests
import json
from threading import Thread

firebase_config = {
    "apiKey": "AIzaSyC9m4h3RF0GdL0RQnTwD9AaMvZiuH9N3VE",
    "authDomain": "medievaluate.firebaseapp.com",
    "databaseURL": "https://medievaluate-default-rtdb.asia-southeast1.firebasedatabase.app/",
    "projectId": "medievaluate",
    "storageBucket": "medievaluate.firebasestorage.app",
    "messagingSenderId": "502606281800",
    "appId": "1:502606281800:android:6ed693b039cddec765ac7d"
}

cloudinary.config(
    cloud_name="dechgx4dz",
    api_key="922215974557931",
    api_secret="hg6Q2UKcZyRlBEZZmTqr5XXuUdw",
    secure = "True"
)

firebase = firebase.initialize_app(firebase_config)
auth = firebase.auth()
db = firebase.database()

FIREBASE_API_KEY = "AIzaSyC9m4h3RF0GdL0RQnTwD9AaMvZiuH9N3VE"
FIREBASE_AUTH_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
FIREBASE_DB_URL = "https://medievaluate-default-rtdb.asia-southeast1.firebasedatabase.app"
auth_token = None

def resource_path(relative_path):
    """Get the absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_resource_path(relative_path):
    """Return the path to the resource, whether running in development or as a frozen app."""
    if getattr(sys, 'frozen', False):  # Running as a frozen executable
        base_path = sys._MEIPASS  # _MEIPASS is where PyInstaller stores resources
    else:
        base_path = os.path.abspath(".")  # Use the current working directory for development
    return os.path.join(base_path, relative_path)

class LoginScreen(Screen):
    loginscreen_path = StringProperty(get_resource_path("loginscreen.png"))
    def login(self):
        email = self.ids.email_input.text
        password = self.ids.password_input.text

        data = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }

        response = requests.post(f"{FIREBASE_AUTH_URL}?key={FIREBASE_API_KEY}", json=data)
        
        if response.status_code == 200:
            user_data = response.json()
            user_id = user_data["localId"]
            id_token = user_data["idToken"]

            # Save user ID and token locally
            with open("user_token.json", "w") as file:
                json.dump({"localId": user_id, "idToken": id_token}, file)

            print("Login successful")
            self.manager.current = "main_screen"
        else:
            print("Login failed:", response.json().get("error", {}).get("message", "Unknown error"))

    def go_to_signup(self):
        self.manager.current = "signup_screen"

class MainScreen(Screen):
    home_logo_path = StringProperty(get_resource_path("logos/home_logo.png"))
    article_logo_path = StringProperty(get_resource_path("logos/article_logo.png"))
    game_logo_path = StringProperty(get_resource_path("logos/game_logo.png"))
    map_logo_path = StringProperty(get_resource_path("logos/map_logo.png"))
    man_logo_path = StringProperty(get_resource_path("logos/man_logo.png"))
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class SearchMedicineScreen(Screen):
    def __init__(self, **kwargs):
        super(SearchMedicineScreen, self).__init__(**kwargs)
        self.medicines = {}  # Initialize as empty
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.add_widget(self.layout)

    def on_enter(self):
        # Start a thread to fetch data from Firebase without blocking the UI
        thread = Thread(target=self.fetch_medicines_from_firebase)
        thread.start()

    def fetch_medicines_from_firebase(self):
        """Fetch medicines from Firebase in a background thread."""
        medicines = db.child("medicines").get().val() or {}
        self.medicines = medicines  # Store the fetched data
        Clock.schedule_once(self.populate_categories, 0)  # Schedule to update the UI

    def populate_categories(self, dt):
        """Populate category spinner after fetching data."""
        if self.medicines:
            self.ids.category_spinner.values = list(self.medicines.keys())

    def on_category_select(self, spinner, text):
        self.ids.generic_spinner.text = 'Select Generic Name'
        self.ids.generic_spinner.disabled = False
        category_data = self.medicines.get(text, {})
        self.ids.generic_spinner.values = list(category_data.keys()) if category_data else []

        # Reset other spinners
        self.ids.strength_spinner.text = 'Select Dosage Strength and Form'
        self.ids.strength_spinner.disabled = True
        self.ids.strength_spinner.values = []
        
        self.ids.form_spinner.text = 'Select Dosage Form'
        self.ids.form_spinner.disabled = True
        self.ids.form_spinner.values = []

        self.ids.brand_spinner.text = 'Select Brand Name'
        self.ids.brand_spinner.disabled = True
        self.ids.brand_spinner.values = []

    def on_generic_select(self, spinner, text):
        category = self.ids.category_spinner.text
        category_data = self.medicines.get(category, {})
        generic_data = category_data.get(text, {})

        # Populate strength spinner
        self.ids.strength_spinner.text = 'Select Dosage Strength and Form'
        self.ids.strength_spinner.disabled = False
        self.ids.strength_spinner.values = list(generic_data.keys()) if generic_data else []

        # Reset other spinners
        self.ids.form_spinner.text = 'Select Dosage Form'
        self.ids.form_spinner.disabled = True
        self.ids.form_spinner.values = []
        
        self.ids.brand_spinner.text = 'Select Brand Name'
        self.ids.brand_spinner.disabled = True
        self.ids.brand_spinner.values = []

    def on_strength_select(self, spinner, text):
        category = self.ids.category_spinner.text
        generic = self.ids.generic_spinner.text
        generic_data = self.medicines.get(category, {}).get(generic, {})
        strength_data = generic_data.get(text, {})

        # Populate form spinner
        self.ids.form_spinner.text = 'Select Dosage Form'
        self.ids.form_spinner.disabled = False
        self.ids.form_spinner.values = list(strength_data.keys()) if strength_data else []

        # Reset brand spinner
        self.ids.brand_spinner.text = 'Select Brand Name'
        self.ids.brand_spinner.disabled = True
        self.ids.brand_spinner.values = []

    def on_form_select(self, spinner, text):
        category = self.ids.category_spinner.text
        generic = self.ids.generic_spinner.text
        strength = self.ids.strength_spinner.text
        form_data = self.medicines.get(category, {}).get(generic, {}).get(strength, {}).get(text, [])

        # Populate brand spinner
        self.ids.brand_spinner.text = 'Select Brand Name'
        self.ids.brand_spinner.disabled = False
        self.ids.brand_spinner.values = form_data


class SignUpScreen(Screen):
    def sign_up(self):
        email = self.ids.email_input.text
        password = self.ids.password_input.text

        # Step 1: Sign up the user with Firebase Authentication
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
        payload = {"email": email, "password": password, "returnSecureToken": True}

        response = requests.post(url, json=payload)

        if response.status_code == 200:
            user_data = response.json()
            user_id = user_data.get("localId")

            # Step 2: Add user to Realtime Database with initial score under "users"
            db_url = f"https://medievaluate-default-rtdb.asia-southeast1.firebasedatabase.app//users/{user_id}.json"
            db_payload = {"email": email, "score": 0}  # Initial score set to 0

            db_response = requests.put(db_url, json=db_payload)
            if db_response.status_code == 200:
                self.ids.message_label.text = "Account created successfully!"
                App.get_running_app().root.current = 'login_screen'
            else:
                self.ids.message_label.text = "Account created but failed to add score."

        else:
            error_msg = response.json().get("error", {}).get("message", "Unknown error")
            self.ids.message_label.text = f"Error: {error_msg}"

class SearchArticlesScreen(Screen):
    def on_enter(self):
        self.load_articles()

    def load_articles(self):
        article_list = self.ids.article_list
        article_list.clear_widgets()

        articles_ref = db.child("articles")
        articles = articles_ref.get().val()

        if articles:
            for article_key, article_data in articles.items():
                article_box = ArticleBox(
                    headline=article_data["headline"],
                    description=article_data["description"],
                    link=article_data["link"],
                )
                article_list.add_widget(article_box)

class WeGamingScreen(Screen):
    image_source = StringProperty("")
    score = NumericProperty(0)

    def on_enter(self):
        self.load_question()
        self.load_score()
    
    def load_question(self):
        game_ref = db.child("game")
        game_data = game_ref.child("AvC").get().val()

        question = random.choice(list(game_data.values()))

        self.image_source = (question["img"])
        correct_answer = question["answer"]
        choices = [correct_answer, question["choice1"]]
        random.shuffle(choices)

        self.ids.img.source = self.image_source
        for i, choice in enumerate(choices):
            btn = self.ids[f"choice_{i+1}"]
            btn.text = choice
            btn.correct = (choice == correct_answer)
            btn.background_color = (0,0,0,0)

    def check_answer(self, button):
        if button.correct:
            button.background_color = (0,1,0,1)
            self.score += 1
            self.save_score()
            print(f"Score: {self.score}")
            Clock.schedule_once(lambda dt: self.load_question(), 0.5)
        else:
            button.background_color = (1, 0, 0, 1)
            Clock.schedule_once(lambda dt: self.load_question(), 1.0)

    def save_score(self):
        if not auth_token:
            print("User not authenticated")
            return

        user_id = "some_user_id"  # Retrieve actual user ID from login response
        url = f"{FIREBASE_DB_URL}/users/{user_id}.json?auth={auth_token}"
        payload = {"score": self.score}

        response = requests.patch(url, json=payload)

        if response.status_code == 200:
            print("Score saved successfully!")
        else:
            print("Error saving score:", response.json())

    def load_score(self):
        user_id = self.get_user_id()  # Fetch the authenticated user ID
        if user_id:
            url = f"{FIREBASE_DB_URL}/users/{user_id}.json"
            response = requests.get(url)

            if response.status_code == 200:
                user_data = response.json()
                if user_data and "score" in user_data:
                    self.score = user_data["score"]
                    self.ids.score_label.text = f"Your Score: {self.score}"
                    print("Score loaded:", self.score)
                else:
                    self.ids.score_label.text = "No score found"
            else:
                print("Error loading score:", response.text)

    def get_user_id(self):
        global auth_token  # Add this to set the global variable
        try:
            with open("user_token.json", "r") as file:
                user_data = json.load(file)
            auth_token = user_data.get("idToken")  # Set the auth token globally
            return user_data.get("localId") if user_data else None
        except FileNotFoundError:
            print("User token file not found.")
            return None
        except json.JSONDecodeError:
            print("Error decoding user token JSON.")
            return None

class MapScreen(Screen):
    def on_enter(self):
        # Start a new thread to load map data
        Thread(target=self.load_map_data).start()

    def load_map_data(self):
        location_ref = db.child("map_location")
        locations = location_ref.get().val()

        if locations:
            for location_key, location_data in locations.items():
                try:
                    lat = float(location_data['Latitude'])
                    lon = float(location_data['Longitude'])
                    Clock.schedule_once(lambda dt, lat=lat, lon=lon: self.add_marker(lat, lon))
                except Exception as e:
                    print(f"Error processing location {location_key}: {e}")

    def add_marker(self, lat, lon):
        map_view = self.ids.map_view
        marker_path = get_resource_path("logos/marker.png")

        # Create marker and add to map view
        marker = MapMarker(lat=lat, lon=lon, source=marker_path)
        map_view.add_marker(marker)

class ProfileScreen(Screen):
    score = NumericProperty(0)

    def on_enter(self):
        self.load_score()  # Load the score when the screen is entered

    def load_score(self):
        user_id = self.get_user_id()  # Fetch the authenticated user ID
        if user_id:
            url = f"{FIREBASE_DB_URL}/users/{user_id}.json"
            response = requests.get(url)

            if response.status_code == 200:
                user_data = response.json()
                if user_data and "score" in user_data:
                    self.score = user_data["score"]
                    self.ids.score_label.text = f"Your Score: {self.score}"
                    print("Score loaded:", self.score)
                else:
                    self.ids.score_label.text = "No score found"
            else:
                print("Error loading score:", response.text)

    def get_user_id(self):
        """Retrieve the currently authenticated user's ID."""
        try:
            with open("user_token.json", "r") as file:
                user_data = json.load(file)
            return user_data.get("localId") if user_data else None
        except FileNotFoundError:
            print("User token file not found.")
            return None
        except json.JSONDecodeError:
            print("Error decoding user token JSON.")
            return None

class MediEvaluateApp(App):
    def build(self):
        Window.size = (360, 800)
        if getattr(sys, 'frozen', False):
            kv_path = os.path.join(sys._MEIPASS, 'test.kv')
        else:
            kv_path = 'test.kv'

        Builder.load_file(kv_path)
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name="login_screen"))
        sm.add_widget(SignUpScreen(name="signup_screen"))
        sm.add_widget(MainScreen(name="main_screen"))
        sm.add_widget(SearchMedicineScreen(name="search_medicine_screen"))
        sm.add_widget(WeGamingScreen(name="we_game_screen"))
        return sm
    
class ArticleBox(BoxLayout):
    def __init__(self, headline, description, link, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = 150
        self.padding = 10
        self.spacing = 5

        with self.canvas.before:
            Color(0.247, 0.517, 0.631, 1)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[20])

        self.bind(pos=self.update_rect, size=self.update_rect)

        self.headline_label = Label(
            text=headline,
            bold=True,
            font_size="16sp",
            size_hint_y=None,
            height=30,
            halign="left",
            valign="top",
            text_size=(self.width - 20, None)  # Adjusting for padding
        )
        self.add_widget(self.headline_label)

        self.description_label = Label(
            text=description,
            font_size="14sp",
            size_hint_y=None,
            height=60,
            halign="left",
            valign="top",
            text_size=(self.width - 20, None)  # Adjusting for padding
        )
        self.add_widget(self.description_label)

        link_button = Button(
            text="Read More",
            size_hint_y=None,
            height=35,
            background_color=(0, 0.5, 1, 1)
        )
        link_button.bind(on_release=lambda x: self.open_link(link))
        self.add_widget(link_button)

        # Bind size updates
        self.bind(size=self.update_text_sizes)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def update_text_sizes(self, *args):
        self.headline_label.text_size = (self.width - 20, None)
        self.description_label.text_size = (self.width - 20, None)

    def open_link(self, link):
        webbrowser.open(link)


if __name__ == "__main__":
    MediEvaluateApp().run()
