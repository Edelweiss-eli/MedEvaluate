import folium
import os
import pandas as pd
import random
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy_garden.mapview import MapView, MapMarker
from kivy.properties import StringProperty, NumericProperty
from kivy.clock import Clock

class HomeScreen(Screen):
    pass

class SearchMedicineScreen(Screen):
    pass

class SearchArticlesScreen(Screen):
    pass

class WeGamingScreen(Screen):
    image_source = StringProperty("")
    score = NumericProperty(0)

    def on_enter(self):
        self.load_question()

    def load_question(self):
        df = pd.read_excel("game_data.xlsx")
        question = df.sample(1).iloc[0]

        self.image_source = question["image_path"]
        correct_answer = question["correct_answer"]
        choices = [correct_answer, question["option_1"], question["option_2"], question["option_3"]]
        random.shuffle(choices)

        self.ids.img.source = self.image_source
        for i, choice in enumerate(choices):
            btn = self.ids[f"choice_{i+1}"]
            btn.text = choice
            btn.correct = (choice == correct_answer)
            btn.background_color = (1, 1, 1, 1)

    def check_answer(self, button):
        if button.correct:
            button.background_color = (0, 1, 0, 1)
            self.score += 1
            print(f"Score: {self.score}")
            Clock.schedule_once(lambda dt: self.load_question(), 0.5)
        else:
            button.background_color = (1, 0, 0, 1)
            Clock.schedule_once(lambda dt: self.load_question(), 1.0)

class MapScreen(Screen):
    def on_enter(self):
        map_view = self.ids.map_view
        df = pd.read_excel('locData.xlsx', sheet_name='Sheet1')

        for index, row in df.iterrows():
            try:
                lat = float(row['Latitude'])
                lon = float(row['Longitude'])
                marker = MapMarker(lat=lat, lon=lon)
                map_view.add_marker(marker)
            except Exception as e:
                print(f"Error processing row {index}: {e}")


class TestApp(App):
    def build(self):
        Window.size = (360, 800)
        return Builder.load_file("test.kv")

if __name__ == '__main__':
    TestApp().run()