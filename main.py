import os
import random
import pyrebase
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
import webbrowser
import cloudinary
import cloudinary.uploader
import cloudinary.api

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

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
db = firebase.database()

class LoginScreen(Screen):
    def login(self):
        email = self.ids.email_input.text
        password = self.ids.password_input.text
        
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            user_id = user['localId']
            print("Login successful")
            self.manager.current = "main_screen"
        except Exception as e:
            print("Login Failed:", e)

    def go_to_signup(self):
        self.manager.current = "signup_screen"

class MainScreen(Screen):
    pass

class HomeScreen(Screen):
    pass

class SearchMedicineScreen(Screen):
    pass

class SignUpScreen(Screen):
    def sign_up(self):
        email = self.ids.email_input.text
        password = self.ids.password_input.text

        try:
            user = auth.create_user_with_email_and_password(email, password)
            self.ids.message_label.text = "Account created successfully!"
        except Exception as e:
            self.ids.message_label.text = f"Error: {str(e)}"

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

        self.image_source = question["img"]
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
        user = auth.current_user
        if user:
            user_id = user['localId']
            db.child("users").child(user_id).update({"score": self.score})
            print("Score saved!")

    def load_score(self):
        user = auth.current_user
        if user:
            user_id = user['localId']
            user_data = db.child("users").child(user_id).get().val()
            if user_data and "score" in user_data:
                self.score = user_data["score"]
                print("Score loaded:", self.score)

class MapScreen(Screen):
    def on_enter(self):
        map_view = self.ids.map_view
        location_ref = db.child("map_location")
        locations = location_ref.get().val()

        if locations:
            for location_key, location_data in locations.items():
                try:
                    lat = float(location_data['Latitude'])
                    lon = float(location_data['Longitude'])
                    marker = MapMarker(lat=lat, lon=lon)
                    map_view.add_marker(marker)
                except Exception as e:
                    print(f"Erorr processing location {location_key}: {e}")

class MediEvaluateApp(App):
    def build(self):
        Window.size = (360, 800)
        Builder.load_file("test.kv")
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name="login_screen"))
        sm.add_widget(SignUpScreen(name="signup_screen"))
        sm.add_widget(MainScreen(name="main_screen"))
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
