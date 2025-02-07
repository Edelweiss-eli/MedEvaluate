import folium
import os
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy_garden.mapview import MapView, MapMarker

class HomeScreen(Screen):
    pass

class SearchMedicineScreen(Screen):
    pass

class SearchArticlesScreen(Screen):
    pass

class WeGamingScreen(Screen):
    pass

class MapScreen(Screen):
    def on_enter(self):
        map_view = self.ids.map_view
        marker = MapMarker(lat=14.8527, lon=120.8160)

        map_view.add_marker(marker)

class TestApp(App):
    def build(self):
        Window.size = (360, 800)
        return Builder.load_file("test.kv")

if __name__ == '__main__':
    TestApp().run()