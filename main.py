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

# 🔑 КОНФІГУРАЦІЯ
API_KEY = "ВАШ_API_KEY"
# Оновлено до моделі 2.5 за вашим запитом
AI_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={API_KEY}"

# --- ФУНКЦІЯ ЧИТАННЯ ДАНИХ З ФАЙЛІВ ---
def get_txt_data(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    return "Файл даних не знайдено."

# --- ВКЛАДКА P3 (Дані з p3_data.txt) ---
class P3FinderScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        layout = BoxLayout(orientation='vertical', padding=20)
        
        self.label = Label(text="Завантаження P3 Data...", markup=True, halign='left', valign='top', size_hint_y=None)
        self.label.bind(texture_size=self.label.setter('size'))
        
        scroll = ScrollView()
        scroll.add_widget(self.label)
        layout.add_widget(scroll)
        
        layout.add_widget(Button(text="НАЗАД", size_hint_y=0.15, on_release=lambda x: setattr(self.manager, 'current', 'menu')))
        self.add_widget(layout)

    def on_enter(self):
        self.label.text = get_txt_data('p3_data.txt')

# --- ВКЛАДКА SERVICE (Дані з service_data.txt) ---
class ServiceScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        layout = BoxLayout(orientation='vertical', padding=20)
        
        self.label = Label(text="Завантаження Service Data...", markup=True, halign='left', valign='top', size_hint_y=None)
        self.label.bind(texture_size=self.label.setter('size'))
        
        scroll = ScrollView()
        scroll.add_widget(self.label)
        layout.add_widget(scroll)
        
        layout.add_widget(Button(text="НАЗАД", size_hint_y=0.15, on_release=lambda x: setattr(self.manager, 'current', 'menu')))
        self.add_widget(layout)

    def on_enter(self):
        self.label.text = get_txt_data('service_data.txt')

# --- ЕКРАН ПРИЛАДІВ ---
class DashScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.gauges_grid = GridLayout(spacing=15, size_hint_y=0.8)
        self.active_params = ["RPM", "Boost", "Coolant Temp", "Fuel Press", "Battery", "EVAP Press"]
        
        self.setup_gauges()
        layout.add_widget(self.gauges_grid)
        layout.add_widget(Button(text="НАЗАД", size_hint_y=0.15, on_release=lambda x: setattr(self.manager, 'current', 'menu')))
        self.add_widget(layout)

    def setup_gauges(self):
        self.gauges_grid.clear_widgets()
        self.gauges_grid.cols = 1 if len(self.active_params) <= 2 else 2
        self.value_labels = {}
        for p in self.active_params:
            box = BoxLayout(orientation='vertical')
            self.value_labels[p] = Label(text="--", font_size='40sp', bold=True, color=(0, 1, 0.5, 1))
            box.add_widget(Label(text=p, size_hint_y=0.3))
            box.add_widget(self.value_labels[p])
            self.gauges_grid.add_widget(box)

    def on_enter(self): Clock.schedule_interval(self.update_data, 1)
    def on_leave(self): Clock.unschedule(self.update_data)
    def update_data(self, dt):
        for p, lbl in self.value_labels.items(): lbl.text = str(random.randint(60, 160))

# --- РОБОЧИЙ ЕКРАН AI (Gemini 2.5) ---
class AIScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        self.log_label = Label(text="[b]VOLVO AI 2.5 ANALYZER[/b]", markup=True, size_hint_y=None, halign='center')
        self.log_label.bind(texture_size=self.log_label.setter('size'))
        scroll = ScrollView(size_hint=(1, 0.7)); scroll.add_widget(self.log_label); layout.add_widget(scroll)
        self.inp = TextInput(hint_text="P045500", size_hint_y=None, height=120, multiline=False, text="P045500")
        layout.add_widget(self.inp)
        btns = BoxLayout(size_hint_y=0.2, spacing=10)
        btns.add_widget(Button(text="АНАЛІЗ", bold=True, on_release=self.start_analysis))
        btns.add_widget(Button(text="НАЗАД", on_release=lambda x: setattr(self.manager, 'current', 'menu')))
        layout.add_widget(btns); self.add_widget(layout)

    def start_analysis(self, instance):
        code = self.inp.text.strip().upper()
        if not code: return
        self.log_label.text = f"[b]Аналіз Gemini 2.5: {code}...[/b]"
        threading.Thread(target=self.run_ai_request, args=(code,), daemon=True).start()

    def run_ai_request(self, code):
        try:
            payload = {"contents": [{"parts": [{"text": f"Ти технік Volvo P3. Поясни помилку {code} українською."}]}]}
            response = requests.post(AI_URL, json=payload, headers={"Content-Type": "application/json"}, timeout=20)
            answer = response.json()['candidates'][0]['content']['parts'][0]['text'] if response.status_code == 200 else f"❌ Помилка {response.status_code}"
            Clock.schedule_once(lambda dt: setattr(self.log_label, 'text', answer))
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self.log_label, 'text', f"❌ Збій: {str(e)}"))

# --- ГОЛОВНЕ МЕНЮ ---
class MenuScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        layout = GridLayout(cols=2, padding=25, spacing=15)
        items = [
            ("ПРИЛАДИ", "logoVolvo.PNG", 'dash'), ("AI ПОМІЧНИК", "logoVolvo.PNG", 'ai'),
            ("P3 FINDER", "logoVolvo.PNG", 'p3_finder'), ("СЕРВІС", "logoVolvo.PNG", 'service'),
            ("ELM327", "logoVolvo.PNG", 'menu'), ("НАЛАШТ.", "logoVolvo.PNG", 'menu')
        ]
        for txt, img, sc in items:
            btn = Button(text=txt, bold=True, background_color=(0.1, 0.1, 0.2, 0.8))
            btn.bind(on_release=lambda x, s=sc: setattr(self.manager, 'current', s))
            layout.add_widget(btn)
        self.add_widget(layout)

class VolvoApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(DashScreen(name='dash'))
        sm.add_widget(AIScreen(name='ai'))
        sm.add_widget(P3FinderScreen(name='p3_finder'))
        sm.add_widget(ServiceScreen(name='service'))
        return sm

if __name__ == '__main__': VolvoApp().run()
    
