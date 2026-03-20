import kivy
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.uix.carousel import Carousel
from kivy.clock import Clock
import threading
import requests
import os

# --- КОНФІГУРАЦІЯ ---
API_KEY = "AIzaSyARna8YDsY4tQd8Cv0QAsWTUJvRDTZlUWE"
AI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

# Перевірка та створення файлів, щоб не було вильотів
for f_name in ['p3_data.txt', 'service_data.txt']:
    if not os.path.exists(f_name):
        with open(f_name, 'w', encoding='utf-8') as f:
            f.write(f"Дані для {f_name} завантажуються...")

# База 30 приладів (PID)
PIDS_DATA = {
    f"P#{i:03d} Parameter": {"unit": "val"} for i in range(1, 31)
}

class MainMenu(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = FloatLayout()
        root.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        
        grid = GridLayout(cols=2, spacing=15, padding=25, size_hint=(0.9, 0.75), pos_hint={'center_x': 0.5, 'center_y': 0.45})
        
        # Кнопки з іконками
        menu_items = [
            ("📊\nПРИЛАДИ", "dash"), ("🤖\nAI ПОМІЧНИК", "ai"), 
            ("🔍\nP3 FINDER", "p3"), ("🔧\nСЕРВІС", "svc"),
            ("📡\nELM327", "status"), ("⚙️\nНАЛАШТ.", "settings")
        ]
        
        for text, sn in menu_items:
            btn = Button(text=text, background_color=(0, 0, 0, 0.8), background_normal='', bold=True, halign='center')
            btn.bind(on_release=lambda x, n=sn: setattr(self.manager, 'current', n))
            grid.add_widget(btn)
        
        root.add_widget(grid)
        self.add_widget(root)

class DashScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        root = FloatLayout()
        
        # Кнопка шестерня (Налаштування приладів)
        settings_btn = Button(text="⚙️", size_hint=(None, None), size=(60, 60), pos_hint={'right': 0.98, 'top': 0.98}, background_color=(0,0,0,0.5))
        settings_btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'dash_settings'))
        
        self.display = Label(text="Оберіть прилади в ⚙️", font_size='20sp', pos_hint={'center_x': 0.5, 'center_y': 0.5})
        
        back = Button(text="НАЗАД", size_hint=(0.3, 0.1), pos_hint={'x': 0.02, 'y': 0.02})
        back.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
        
        root.add_widget(self.display)
        root.add_widget(settings_btn)
        root.add_widget(back)
        self.add_widget(root)

class DashSettingsScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        layout.add_widget(Label(text="Оберіть прилади (до 30)", size_hint_y=0.1))
        
        scroll = ScrollView()
        grid = GridLayout(cols=1, spacing=5, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))
        
        for pid_name in PIDS_DATA.keys():
            btn = ToggleButton(text=pid_name, size_hint_y=None, height=50, background_normal='', background_color=(0.2, 0.2, 0.2, 1))
            grid.add_widget(btn)
            
        scroll.add_widget(grid)
        layout.add_widget(scroll)
        
        apply_btn = Button(text="ЗАСТОСУВАТИ", size_hint_y=0.15, background_color=(0, 0.5, 0, 1))
        apply_btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'dash'))
        layout.add_widget(apply_btn)
        self.add_widget(layout)

class AIScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        self.log = Label(text="AI чекає...", size_hint_y=None, halign='left', valign='top', text_size=(400, None))
        self.log.bind(texture_size=self.log.setter('size'))
        scroll = ScrollView(); scroll.add_widget(self.log); layout.add_widget(scroll)
        
        self.input = TextInput(hint_text="Код помилки...", size_hint_y=None, height=80, multiline=False)
        layout.add_widget(self.input)
        
        btns = BoxLayout(size_hint_y=0.15, spacing=10)
        go = Button(text="АНАЛІЗ", background_color=(0.5, 0, 0.7, 1))
        go.bind(on_release=self.ask)
        back = Button(text="НАЗАД")
        back.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
        btns.add_widget(go); btns.add_widget(back); layout.add_widget(btns)
        self.add_widget(layout)

    def ask(self, instance):
        q = self.input.text.strip()
        if q:
            self.log.text += f"\nВи: {q}\nАналізую..."
            self.input.text = ""
            threading.Thread(target=self.fetch, args=(q,), daemon=True).start()

    def fetch(self, q):
        try:
            headers = {'Content-Type': 'application/json'}
            data = {"contents": [{"parts": [{"text": f"Volvo P3 expert: explain DTC {q} in Ukrainian shortly."}]}]}
            r = requests.post(AI_URL, headers=headers, json=data, timeout=10)
            res = r.json()['candidates'][0]['content']['parts'][0]['text']
            Clock.schedule_once(lambda dt: setattr(self.log, 'text', self.log.text + f"\nAI: {res}"))
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self.log, 'text', self.log.text + f"\nПомилка: {str(e)}"))

class P3FinderScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        l = BoxLayout(orientation='vertical', padding=20)
        self.inp = TextInput(hint_text="Пошук в p3_data...", size_hint_y=None, height=80)
        self.res = Label(text="Результати...", size_hint_y=None, halign='left', text_size=(400, None))
        self.res.bind(texture_size=self.res.setter('size'))
        scroll = ScrollView(); scroll.add_widget(self.res)
        l.add_widget(self.inp); l.add_widget(scroll)
        btn = Button(text="ЗНАЙТИ", size_hint_y=0.15); btn.bind(on_release=self.find)
        back = Button(text="НАЗАД", size_hint_y=0.1); back.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
        l.add_widget(btn); l.add_widget(back); self.add_widget(l)

    def find(self, instance):
        q = self.inp.text.lower()
        try:
            with open('p3_data.txt', 'r', encoding='utf-8') as f:
                lines = f.read().split('P#')
                out = ["P#"+i.strip() for i in lines if q in i.lower()]
                self.res.text = "\n\n".join(out[:10]) if out else "Не знайдено."
        except: self.res.text = "Файл відсутній."

class ServiceScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        l = BoxLayout(orientation='vertical', padding=20)
        self.info = Label(text="Дані сервісу...", halign='left', text_size=(400, None))
        scroll = ScrollView(); scroll.add_widget(self.info); l.add_widget(scroll)
        btn = Button(text="ЗЧИТАТИ", size_hint_y=0.15); btn.bind(on_release=self.load)
        back = Button(text="НАЗАД", size_hint_y=0.1); back.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
        l.add_widget(btn); l.add_widget(back); self.add_widget(l)

    def load(self, instance):
        try:
            with open('service_data.txt', 'r', encoding='utf-8') as f: self.info.text = f.read()
        except: self.info.text = "Файл не знайдено."

class VolvoApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(MainMenu(name='menu'))
        sm.add_widget(AIScreen(name='ai'))
        sm.add_widget(DashScreen(name='dash'))
        sm.add_widget(DashSettingsScreen(name='dash_settings'))
        sm.add_widget(P3FinderScreen(name='p3'))
        sm.add_widget(ServiceScreen(name='svc'))
        # Заглушки
        for n in ['status', 'settings']:
            scr = Screen(name=n)
            scr.add_widget(Label(text="В РОБОТІ"))
            sm.add_widget(scr)
        return sm

if __name__ == '__main__':
    VolvoApp().run()
            
