import threading
import requests
import random
import os
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.core.window import Window

# Налаштування Gemini 2.5 та API
API_KEY = "AIzaSyC7_ORLA_n8ap4guHX6uOOyBFu-eH_tAqI"
AI_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={API_KEY}"

# --- КЛАС ГРАФІЧНОЇ КНОПКИ (Кнопка-Малюнок) ---
class ImageButton(Button):
    def __init__(self, text, icon_path, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''  # Прибираємо стандартний фон кнопки
        self.background_color = (0, 0, 0, 0) # Робимо кнопку прозорою
        
        # Контейнер для малюнка та підпису
        self.container = BoxLayout(orientation='vertical', padding=10)
        
        # Саме зображення (основний вигляд кнопки)
        self.img = Image(
            source=icon_path if os.path.exists(icon_path) else 'logoVolvo.PNG',
            allow_stretch=True,
            keep_ratio=True
        )
        
        # Підпис під малюнком
        self.lbl = Label(
            text=text, 
            bold=True, 
            size_hint_y=0.2, 
            color=(1, 1, 1, 1),
            font_size='14sp'
        )
        
        self.container.add_widget(self.img)
        self.container.add_widget(self.lbl)
        self.add_widget(self.container)
        
        # Оновлення позиції при зміні розміру вікна
        self.bind(pos=self._update_ui, size=self._update_ui)

    def _update_ui(self, *args):
        self.container.pos = self.pos
        self.container.size = self.size

# --- ГОЛОВНА СТОРІНКА (6 КНОПОК-МАЛЮНКІВ) ---
class MenuScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        # Фон всього додатка
        self.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        
        # Сітка кнопок 2 стовпці x 3 рядки
        layout = GridLayout(cols=2, padding=30, spacing=30)
        
        # Конфігурація кнопок згідно з вашим запитом
        menu_items = [
            ("ПРИЛАДИ", "speedometer.png", 'dash'),
            ("P3Config", "p3_car.png", 'p3_finder'),
            ("ELM327", "check_engine.png", 'menu'),
            ("AI ПОМІЧНИК", "robot_head.png", 'ai'),
            ("СЕРВІС", "oil_service.png", 'service'),
            ("НАЛАШТУВАННЯ", "settings_gear.png", 'menu')
        ]
        
        for name, icon, screen_target in menu_items:
            btn = ImageButton(text=name, icon_path=icon)
            btn.bind(on_release=lambda x, s=screen_target: self.change_screen(s))
            layout.add_widget(btn)
            
        self.add_widget(layout)

    def change_screen(self, screen_name):
        self.manager.current = screen_name

# --- ТИМЧАСОВІ ЕКРАНИ ДЛЯ ТЕСТУ (ПРИЛАДИ, AI тощо) ---
# (Тут залишаються ваші класи DashScreen, AIScreen, EditableTextScreen з попереднього коду)

class VolvoApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(MenuScreen(name='menu'))
        # sm.add_widget(DashScreen(name='dash'))
        # sm.add_widget(AIScreen(name='ai'))
        # sm.add_widget(EditableTextScreen(filename='p3_data.txt', title='P3Config', name='p3_finder'))
        # sm.add_widget(EditableTextScreen(filename='service_data.txt', title='SERVICE LOG', name='service'))
        return sm

if __name__ == '__main__':
    VolvoApp().run()
    
