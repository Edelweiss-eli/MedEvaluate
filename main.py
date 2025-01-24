from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle


# Declare both screens
class SearchMedicineScreen(Screen):
    pass

class SearchArticlesScreen(Screen):
    pass

class WeGamingScreen(Screen):
    pass

class TestApp(App):

    def build(self):
        Window.size = (360, 800)
        return

if __name__ == '__main__':
    TestApp().run()