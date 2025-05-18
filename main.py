import os
import sys
import random
from supabase import create_client, Client
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
import requests
import json
from threading import Thread
from plyer import gps
from math import radians, cos, sin, sqrt, atan2
from kivy.utils import platform
from kivy.uix.popup import Popup
from android.permissions import request_permissions, Permission, check_permission
from android import activity
from kivy.animation import Animation

url = "https://jiyyjsflznrvruzjfqkl.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImppeXlqc2Zsem5ydnJ1empmcWtsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDIyMTE5MTMsImV4cCI6MjA1Nzc4NzkxM30.5m9P6Ub2Oa7WnOeWfh86LV-xzulz7klkYmx_lmNx0q0"
supabase = create_client(url, key)

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

def check_location_permission():
    if check_permission(Permission.ACCESS_FINE_LOCATION):
        print("Location permission granted")
        # Access location here
    else:
        print("Location permission not granted. Requesting now...")
        request_location_permission()

def request_location_permission():
    try:
        request_permissions([Permission.ACCESS_FINE_LOCATION, Permission.ACCESS_COARSE_LOCATION])
    except Exception as e:
        print(f"Error requesting permissions: {e}")

class SignUpScreen(Screen):
    def sign_up(self):
        email = self.ids.email_input.text
        password = self.ids.password_input.text

        try:
            # Sign up the user
            response = supabase.auth.sign_up({"email": email, "password": password})

            if response.user:
                # Get the user UUID
                user_id = response.user.id

                # Insert user data into 'users' table with UUID
                db_payload = {"uuid": user_id, "email": email, "score": 0}
                supabase.table("users").insert(db_payload).execute()

                self.ids.message_label.text = "Account created successfully!"
                App.get_running_app().root.current = 'login_screen'
            else:
                self.ids.message_label.text = "Error: Sign-up failed."

        except Exception as e:
            self.ids.message_label.text = f"Error: {str(e)}"

class LoginScreen(Screen):
    loginscreen_path = StringProperty(get_resource_path("logos/loginscreen.png"))

    def show_error_popup(self, message):
        layout = BoxLayout(orientation='vertical', spacing=10, padding=20)
        layout.add_widget(Label(text=message))

        close_button = Button(text="OK", size_hint=(None, None), size=(100, 40))
        close_button.bind(on_press=lambda *args: popup.dismiss())
        layout.add_widget(close_button)

        popup = Popup(title="Login Failed", content=layout, size_hint=(0.5, 0.5))
        popup.open()


    def login(self):
        email = self.ids.email_input.text
        password = self.ids.password_input.text

        try:
            # Sign in the user
            response = supabase.auth.sign_in_with_password({"email": email, "password": password})

            if response.user:
                user = response.user
                user_id = user.id  # Get the UUID from Supabase

                # Fetch user data from 'users' table using email
                user_data = supabase.table("users").select("id", "score").eq("email", email).single().execute()

                if user_data.data:
                    user_score = user_data.data.get("score", 0)
                    print(f"User score: {user_score}")

                    # Check if UUID is missing, and update the table if needed
                    if not user_data.data.get("id"):
                        supabase.table("users").update({"id": user_id}).eq("email", email).execute()
                        print(f"UUID updated for {email}")

                else:
                    print("No user data found or error retrieving user score.")

                # Save user token
                with open("user_token.json", "w") as file:
                    json.dump({"localId": user_id, "idToken": response.session.access_token}, file)

                # Navigate to the main screen
                self.manager.current = "main_screen"

            else:
                self.show_error_popup("Wrong password. Please try again.")

        except Exception as e:
            self.show_error_popup(f"Login error: {e}")

    def go_to_signup(self):
        self.manager.current = "signup_screen"

class MainScreen(Screen):
    home_logo_path = StringProperty(get_resource_path("logos/home_logo.png"))
    article_logo_path = StringProperty(get_resource_path("logos/article_logo.png"))
    game_logo_path = StringProperty(get_resource_path("logos/game_logo.png"))
    map_logo_path = StringProperty(get_resource_path("logos/map_logo.png"))
    man_logo_path = StringProperty(get_resource_path("logos/man_logo.png"))
    background_path = StringProperty(get_resource_path("logos/background_image.png"))
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    def on_enter(self):
        self.ids.main_screen_manager.current = self.current_screen


class SearchMedicineScreen(Screen):
    def __init__(self, **kwargs):
        super(SearchMedicineScreen, self).__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.add_widget(self.layout)
        self.selected_ids = {}  # Store selected ids

    def on_enter(self):
        # Start a thread to fetch categories without blocking the UI
        thread = Thread(target=self.fetch_categories)
        thread.start()

    def fetch_categories(self):
        response = supabase.table('med_category').select('id, name').execute()
        if response.data:
            self.categories = {item['name']: item['id'] for item in response.data}
            Clock.schedule_once(self.populate_category_spinner, 0)

    def populate_category_spinner(self, dt):
        self.ids.category_spinner.values = list(self.categories.keys())

    def on_category_select(self, spinner, text):
        if text in self.categories:
            self.selected_ids['category_id'] = self.categories[text]
            self.fetch_medicines()
        else:
            print("Invalid category selected.")

    def fetch_medicines(self):
        category_id = self.selected_ids['category_id']
        response = supabase.table('med_medicines').select('id, name').eq('category_id', category_id).execute()
        if response.data:
            self.medicines = {item['name']: item['id'] for item in response.data}
            Clock.schedule_once(self.populate_medicine_spinner, 0)

    def populate_medicine_spinner(self, dt):
        self.ids.medicine_spinner.text = 'Select Medicine'
        self.ids.medicine_spinner.values = list(self.medicines.keys())
        self.ids.medicine_spinner.disabled = False

    def on_medicine_select(self, spinner, text):
        if text in self.medicines:
            self.selected_ids['medicine_id'] = self.medicines[text]
            self.fetch_dosages()
        else:
            print("Invalid medicine selected.")

    def fetch_dosages(self):
        medicine_id = self.selected_ids['medicine_id']
        response = supabase.table('med_dosage').select('id, name').eq('medicine_id', medicine_id).execute()
        if response.data:
            self.dosages = {item['name']: item['id'] for item in response.data}
            Clock.schedule_once(self.populate_dosage_spinner, 0)

    def populate_dosage_spinner(self, dt):
        self.ids.dosage_spinner.text = 'Select Dosage'
        self.ids.dosage_spinner.values = list(self.dosages.keys())
        self.ids.dosage_spinner.disabled = False

    def on_dosage_select(self, spinner, text):
        if text in self.dosages:
            self.selected_ids['dosage_id'] = self.dosages[text]
            self.fetch_forms()
        else:
            print("Invalid dosage selected.")

    def fetch_forms(self):
        dosage_id = self.selected_ids['dosage_id']
        response = supabase.table('med_form').select('id, name').eq('dosage_id', dosage_id).execute()
        if response.data:
            self.forms = {item['name']: item['id'] for item in response.data}
            Clock.schedule_once(self.populate_form_spinner, 0)

    def populate_form_spinner(self, dt):
        self.ids.form_spinner.text = 'Select Form'
        self.ids.form_spinner.values = list(self.forms.keys())
        self.ids.form_spinner.disabled = False

    def on_form_select(self, spinner, text):
        if text in self.forms:
            self.selected_ids['form_id'] = self.forms[text]
            self.fetch_brands()
        else:
            print("Invalid form selected.")

    def fetch_brands(self):
        form_id = self.selected_ids['form_id']
        response = supabase.table('med_brands').select('name').eq('formula_id', form_id).execute()
        if response.data:
            self.brands = [item['name'] for item in response.data]
            Clock.schedule_once(self.populate_brand_spinner, 0)

    def populate_brand_spinner(self, dt):
        self.ids.brand_spinner.text = 'Select Brand'
        self.ids.brand_spinner.values = self.brands
        self.ids.brand_spinner.disabled = False

class SearchArticlesScreen(Screen):
    def on_enter(self):
        self.load_articles()

    def load_articles(self):
        article_list = self.ids.article_list
        article_list.clear_widgets()

        articles = supabase.table('articles').select('*').execute()

        if articles.data:
            for article_data in articles.data:
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
        game_data = supabase.table('game_data').select('*').execute().data

        question = random.choice(game_data)

        self.image_source = question["img"]
        correct_answer = question["answer"]
        choices = [correct_answer, question["choice1"]]
        random.shuffle(choices)

        self.ids.img.source = self.image_source
        for i, choice in enumerate(choices):
            btn = self.ids[f"choice_{i+1}"]
            btn.text = choice
            btn.correct = (choice == correct_answer)
            btn.background_color = (0, 0, 0, 0)

    def check_answer(self, button):
        # Identify all choice buttons
        buttons = [self.ids.choice_1, self.ids.choice_2]

        # Check the selected button's correctness
        if button.correct:
            # Mark the correct button with green and show "CORRECT"
            button.text = "CORRECT"
            button.background_color = (0, 1, 0, 1)

            # Highlight the wrong button as red
            for btn in buttons:
                if btn != button:
                    btn.background_color = (1, 0, 0, 1)

            # Increase score, save, and load next question
            self.score += 1
            self.save_score()
            print(f"Score: {self.score}")
            Clock.schedule_once(lambda dt: self.load_question(), 1)
        else:
            # Mark the wrong button with red and show "WRONG"
            button.text = "WRONG"
            button.background_color = (1, 0, 0, 1)

            # Highlight the correct button as green
            for btn in buttons:
                if btn != button and btn.correct:
                    btn.background_color = (0, 1, 0, 1)

            # Delay loading the next question to show feedback
            Clock.schedule_once(lambda dt: self.load_question(), 1.0)

    def save_score(self):
        # Get the current authenticated user
        user_response = supabase.auth.get_user()
        
        if not user_response.user:
            print("User not authenticated")
            return

        user_id = user_response.user.id

        # Update the score in the Supabase users table (make sure 'uuid' is the unique key)
        response = supabase.table('users').update({'score': self.score}).eq('uuid', user_id).execute()

        # Check if the update was successful
        if response.data:
            print("Score updated successfully!")
        else:
            print("Error updating score:", response)

    def load_score(self):
        # Get the current authenticated user
        user_response = supabase.auth.get_user()
        
        if user_response.user:  # Check if a user is authenticated
            user_id = user_response.user.id
            
            # Fetch user's score from 'users' table
            response = supabase.table('users').select('score').eq('uuid', user_id).execute()
            
            if response.data and len(response.data) > 0:
                self.score = response.data[0]['score']
                self.ids.score_label.text = f"Your Score: {self.score}"
                print("Score loaded:", self.score)
            else:
                self.ids.score_label.text = "No score found"
                print("No score found or error:", response)

        else:
            print("User not authenticated")
            self.ids.score_label.text = "Please log in"

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
        # Get location (real GPS on mobile, simulated on PC)
        if platform in ('android', 'ios'):
            try:
                gps.configure(on_location=self.on_gps_location, on_status=self.on_gps_status)
                gps.start(minTime=1000, minDistance=0)
            except NotImplementedError:
                print("GPS not supported on this platform")
        else:
            # Simulated location for PC testing
            print("Simulating GPS on PC")
            self.user_lat = 14.8527
            self.user_lon = 120.8160
            self.load_map_data()

    def on_gps_location(self, **kwargs):
        # Get real GPS location
        self.user_lat = kwargs['lat']
        self.user_lon = kwargs['lon']
        print(f"User location: {self.user_lat}, {self.user_lon}")
        self.load_map_data()

    def on_gps_status(self, status):
        print("GPS status:", status)
        if status == 'provider-disabled':
            # Show a popup or notification
            self.show_location_off_alert()

    def load_map_data(self):
        # Fetch location data from Supabase
        location_data = supabase.table('map_loc').select('*').execute().data

        if not location_data:
            print("No location data found or error fetching data.")
            return

        nearby_markers = []
        for location in location_data:
            try:
                lat = float(location['lat'])
                lon = float(location['lon'])
                name = location.get('name', 'Unknown')

                # Calculate distance from user
                distance = self.calculate_distance(self.user_lat, self.user_lon, lat, lon)

                # Set distance threshold (e.g., 5 km)
                if distance <= 5:
                    nearby_markers.append((lat, lon, distance, name))

                # Add marker to the map
                Clock.schedule_once(lambda dt, lat=lat, lon=lon: self.add_marker(lat, lon))
            except (ValueError, KeyError) as e:
                print(f"Error processing location {location}: {e}")

        # Display nearby markers in the list
        self.display_nearby_markers(nearby_markers)

    def calculate_distance(self, lat1, lon1, lat2, lon2):
        # Radius of the Earth in km
        R = 6371.0

        # Convert coordinates from degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        # Calculate the differences
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        # Haversine formula
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        # Distance in kilometers
        distance = R * c
        return distance

    def add_marker(self, lat, lon):
        # Add marker to the map view
        map_view = self.ids.map_view
        marker_path = get_resource_path("logos/marker.png")

        # Create marker and add to map view
        marker = MapMarker(lat=lat, lon=lon, source=marker_path)
        map_view.add_marker(marker)
        print(f"Placing marker at: {lat}, {lon}")

    def show_location_off_alert(self):
        box = BoxLayout(orientation='vertical', spacing=10)
        box.add_widget(Label(text="Location is turned off.\nPlease enable it in your settings."))

        btn = Button(text="OK", size_hint_y=None, height='40dp')
        btn.bind(on_release=lambda x: popup.dismiss())
        box.add_widget(btn)

        popup = Popup(title="GPS Disabled", content=box, size_hint=(None, None), size=(300, 200))
        popup.open()

    def display_nearby_markers(self, markers):
        nearby_list = self.ids.nearby_list

        if not markers:
            nearby_list.data = [{'text': 'No nearby locations found.'}]
            return

        # Properly set the data for the RecycleView
        nearby_list.data = [
            {
                'text': f"{name}\nDistance: {distance:.2f} km",
                'lat': lat,
                'lon': lon
            }
            for lat, lon, distance, name in markers
        ]
        print(f"Nearby markers: {nearby_list.data}")

class ProfileScreen(Screen):
    score = NumericProperty(0)

    def on_enter(self):
        self.load_score()  # Load the score when the screen is entered

    def load_score(self):
        # Get the current authenticated user
        user_response = supabase.auth.get_user()
        
        if user_response.user:  # Check if a user is authenticated
            user_id = user_response.user.id
            
            # Fetch user's score from 'users' table
            response = supabase.table('users').select('score').eq('uuid', user_id).execute()
            
            if response.data and len(response.data) > 0:
                self.score = response.data[0]['score']
                self.ids.score_label.text = f"Your Score: {self.score}"
                print("Score loaded:", self.score)
            else:
                self.ids.score_label.text = "No score found"
                print("No score found or error:", response)

class MediEvaluateApp(App):
    def build(self):
        request_location_permission()
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
        self.padding = 10
        self.spacing = 5

        # Draw Rounded Rectangle
        with self.canvas.before:
            Color(0.247, 0.517, 0.631, 1)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[20])

        # Bind to size changes
        self.bind(pos=self.update_rect, size=self.update_rect)
        Window.bind(on_resize=self.update_height)  # Adjust height on resize

        self.headline_label = Label(
            text=headline,
            bold=True,
            font_size="16sp",
            size_hint_y=None,
            height=30,
            halign="left",
            valign="top",
            text_size=(self.width - 20, None),  # Adjust for padding
        )
        self.headline_label.bind(size=self.headline_label.setter('text_size'))
        self.add_widget(self.headline_label)

        self.description_label = Label(
            text=description,
            font_size="14sp",
            size_hint_y=None,
            halign="left",
            valign="top",
            text_size=(self.width - 20, None),  # Adjust for padding
        )
        self.description_label.bind(size=self.description_label.setter('text_size'))
        self.add_widget(self.description_label)

        # Read More Button
        link_button = Button(
            text="Read More",
            size_hint_y=None,
            height=35,
            background_color=(0, 0.5, 1, 1)
        )
        link_button.bind(on_release=lambda x: self.open_link(link))
        self.add_widget(link_button)

        # Set initial height
        Clock.schedule_once(lambda dt: self.update_height())

    def update_rect(self, *args):
        """Update the rounded rectangle."""
        self.rect.pos = self.pos
        self.rect.size = self.size

    def update_height(self, *args):
        """Dynamically adjust the height to fit content."""
        padding = self.padding[0] if isinstance(self.padding, (list, tuple)) else self.padding

        # Adjust total height calculation:
        total_height = padding * 2 + 35  # Button height + padding

        # Calculate heights of labels based on their content
        self.headline_label.height = self.headline_label.texture_size[1] + 10  # Add extra space for headline
        self.description_label.height = self.description_label.texture_size[1] + 10  # Add extra space for description

        total_height += self.headline_label.height + self.description_label.height + self.spacing * 2

        # Set a minimum height to avoid clipping
        min_height = 220  # Increase as needed
        self.height = max(total_height, min_height)

    def open_link(self, link):
        webbrowser.open(link)


if __name__ == "__main__":
    MediEvaluateApp().run()
