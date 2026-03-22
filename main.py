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

Window.softinput_mode = 'pan'

# 🔑 КОНФІГУРАЦІЯ (Gemini 2.5)
API_KEY = "AIzaSyC7_ORLA_n8ap4guHX6uOOyBFu-eH_tAqI"
AI_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={API_KEY}"

# Безпечне читання файлів
def load_data(filename, default_text="Нотатки порожні"):
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return f.read()
    except Exception as e:
        print(f"Помилка читання {filename}: {e}")
    return default_text

# --- ЕКРАН РЕДАГУВАННЯ (P3Config та Service) ---
class EditableScreen(Screen):
    def __init__(self, filename, title, **kw):
        super().__init__(**kw)
        self.filename = filename
        # Перевірка фону
        bg_source = 'background.png' if os.path.exists('background.png') else ''
        if bg_source:
            self.add_widget(Image(source=bg_source, allow_stretch=True, keep_ratio=False))
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        layout.add_widget(Label(text=f"[b]{title}[/b]", markup=True, size_hint_y=0.1, font_size='20sp'))
        
        self.editor = TextInput(multiline=True, background_color=(0, 0, 0, 0.5), foreground_color=(1, 1, 1, 1))
        layout.add_widget(self.editor)
        
        btns = BoxLayout(size_hint_y=0.15, spacing=10)
        btn_save = Button(text="ЗБЕРЕГТИ", bold=True, background_color=(0, 0.6, 0, 1))
        btn_save.bind(on_release=self.save_data)
        btn_back = Button(text="НАЗАД", on_release=self.go_back)
        
        btns.add_widget(btn_save); btns.add_widget(btn_back)
        layout.add_widget(btns); self.add_widget(layout)

    def on_enter(self):
        self.editor.text = load_data(self.filename)

    def save_data(self, instance):
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                f.write(self.editor.text)
            self.manager.current = 'menu'
        except Exception as e:
            print(f"Не вдалося зберегти: {e}")

    def go_back(self, x):
        self.manager.current = 'menu'

# --- ПАНЕЛЬ ПРИЛАДІВ ---
class DashScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        if os.path.exists('background.png'):
            self.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        
        layout = BoxLayout(orientation='vertical', padding=10)
        self.grid = GridLayout(cols=2, spacing=15, size_hint_y=0.8)
        self.labels = {}
        for p in ["RPM", "Boost", "Temp", "Volt"]:
            l = Label(text="--", font_size='30sp', bold=True)
            self.labels[p] = l
            box = BoxLayout(orientation='vertical')
            box.add_widget(Label(text=p, size_hint_y=0.3))
            box.add_widget(l)
            self.grid.add_widget(box)
        
        layout.add_widget(self.grid)
        layout.add_widget(Button(text="НАЗАД", size_hint_y=0.2, on_release=lambda x: setattr(self.manager, 'current', 'menu')))
        self.add_widget(layout)

    def on_enter(self): Clock.schedule_interval(self.update_vals, 1)
    def on_leave(self): Clock.unschedule(self.update_vals)
    def update_vals(self, dt):
        for l in self.labels.values(): l.text = str(random.randint(60, 120))

# --- ГОЛОВНЕ МЕНЮ ---
class MenuScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        if os.path.exists('background.png'):
            self.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        
        layout = GridLayout(cols=2, padding=20, spacing=20)
        # ВАЖЛИВО: Назви екранів ('dash', 'p3', 'ai' тощо) мають точно збігатися з тими, що в VolvoApp
        items = [
            ("ПРИЛАДИ", 'dash'), ("P3Config", 'p3'),
            ("AI ПОМІЧНИК", 'ai'), ("СЕРВІС", 'service'),
            ("ELM327", 'menu'), ("НАЛАШТ.", 'menu')
        ]
        for txt, target in items:
            btn = Button(text=txt, bold=True, background_color=(0.1, 0.2, 0.3, 0.8))
            btn.bind(on_release=lambda x, t=target: self.change_sc(t))
            layout.add_widget(btn)
        self.add_widget(layout)

    def change_sc(self, target):
        if target in self.manager.screen_names:
            self.manager.current = target

class VolvoApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition())
        # Реєструємо всі екрани з унікальними іменами
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(DashScreen(name='dash'))
        sm.add_widget(EditableScreen(filename='p3_data.txt', title='P3 Config Data', name='p3'))
        sm.add_widget(EditableScreen(filename='service_data.txt', title='Service Log', name='service'))
        # AIScreen потрібно додати сюди, якщо він у вас є в коді
        return sm

if __name__ == '__main__':
    VolvoApp().run()
