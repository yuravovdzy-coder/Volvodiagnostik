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
from kivy.utils import get_color_from_hex
import threading
import requests
import json
import time

# --- КОНФІГУРАЦІЯ AI ---
API_KEY = "AIzaSyARna8YDsY4tQd8Cv0QAsWTUJvRDTZlUWE"
AI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

# --- БАЗА ПАРАМЕТРІВ OBD2 (30 PID) ---
PIDS = {
    "RPM": {"pid": "010C", "unit": "RPM", "formula": lambda d: (int(d[0],16)*256 + int(d[1],16))/4},
    "SPEED": {"pid": "010D", "unit": "km/h", "formula": lambda d: int(d[0],16)},
    "COOLANT": {"pid": "0105", "unit": "°C", "formula": lambda d: int(d[0],16)-40},
    "EVAP_PRESS": {"pid": "0132", "unit": "Pa", "formula": lambda d: ((int(d[0],16)*256)+int(d[1],16))/4},
    "BOOST": {"pid": "010B", "unit": "kPa", "formula": lambda d: int(d[0],16) - 101},
    "VOLTAGE": {"pid": "0142", "unit": "V", "formula": lambda d: (int(d[0],16)*256 + int(d[1],16))/1000},
    "OIL_TEMP": {"pid": "015C", "unit": "°C", "formula": lambda d: int(d[0],16)-40},
    "LOAD": {"pid": "0104", "unit": "%", "formula": lambda d: int(d[0],16)*100/255},
}

# --- 1. ГОЛОВНЕ МЕНЮ ---
class MainMenu(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = FloatLayout()
        root.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        
        menu_grid = GridLayout(cols=2, spacing=20, padding=30, size_hint=(0.9, 0.75), pos_hint={'center_x': 0.5, 'center_y': 0.45})
        
        btns = [
            ("ПРИЛАДИ\nOBD2", "dash"), ("СТАТУС\nELM327", "status"),
            ("AI\nASSISTANT", "ai"), ("CONFIG\nP3TOOL", "p3tool"),
            ("СЕРВІС", "service"), ("НАЛАШТУВАННЯ", "settings")
        ]
        
        for text, sn in btns:
            b = Button(text=text, background_color=(0,0,0,0.4), halign='center', bold=True, background_normal='')
            b.bind(on_release=lambda x, name=sn: setattr(self.manager, 'current', name))
            menu_grid.add_widget(b)
            
        root.add_widget(menu_grid)
        root.add_widget(Label(text="VOLVO P3 SMARTSCAN", pos_hint={'top': 0.95}, font_size='22sp', bold=True))
        self.add_widget(root)

# --- 2. ЕКРАН AI ---
class AIScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        self.chat_log = Label(text="Запитай про помилку (P0455...)\n", size_hint_y=None, halign='left', valign='top')
        self.chat_log.bind(texture_size=self.chat_log.setter('size'))
        scroll = ScrollView(size_hint_y=0.7)
        scroll.add_widget(self.chat_log)
        layout.add_widget(scroll)
        
        self.input = TextInput(hint_text="Код помилки...", size_hint_y=None, height=100, multiline=False)
        layout.add_widget(self.input)
        
        btns = BoxLayout(size_hint_y=0.15, spacing=10)
        ask_btn = Button(text="АНАЛІЗ", background_color=(0.4, 0.2, 0.5, 1))
        ask_btn.bind(on_release=self.ask)
        back_btn = Button(text="НАЗАД")
        back_btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
        btns.add_widget(ask_btn); btns.add_widget(back_btn)
        layout.add_widget(btns)
        self.add_widget(layout)

    def ask(self, instance):
        q = self.input.text
        if not q: return
        self.chat_log.text += f"\nВи: {q}\nAI думає..."
        self.input.text = ""
        threading.Thread(target=self.get_ai, args=(q,)).start()

    def get_ai(self, q):
        try:
            p = f"Ти діагност Volvo. Поясни помилку {q} коротко."
            r = requests.post(AI_URL, json={"contents": [{"parts": [{"text": p}]}]}, timeout=10)
            ans = r.json()['candidates'][0]['content']['parts'][0]['text']
            Clock.schedule_once(lambda dt: setattr(self.chat_log, 'text', self.chat_log.text + f"\nAI: {ans}\n"))
        except: Clock.schedule_once(lambda dt: setattr(self.chat_log, 'text', self.chat_log.text + "\nПомилка зв'язку."))

# --- 3. ЕКРАН ПРИЛАДІВ ---
class DashScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        self.carousel = Carousel(direction='right')
        self.add_widget(self.carousel)
        
        back = Button(text="< МЕНЮ", size_hint=(0.2, 0.08), pos_hint={'x':0, 'top':1})
        back.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
        self.add_widget(back)
        
        self.items = {}

    def build_pages(self, config):
        self.carousel.clear_widgets()
        for page in config:
            grid = GridLayout(cols=2 if len(page)>1 else 1, padding=40, spacing=20)
            for name in page:
                box = BoxLayout(orientation='vertical')
                box.add_widget(Label(text=name, font_size='14sp'))
                val = Label(text="--", font_size='45sp', bold=True)
                box.add_widget(val); box.add_widget(Label(text=PIDS[name]['unit']))
                grid.add_widget(box)
                self.items[name] = val
            self.carousel.add_widget(grid)

# --- МЕНЕДЖЕР ТА BLUETOOTH ---
class VolvoApp(App):
    def build(self):
        self.sm = ScreenManager(transition=FadeTransition())
        self.dash = DashScreen(name='dash')
        self.sm.add_widget(MainMenu(name='menu'))
        self.sm.add_widget(AIScreen(name='ai'))
        self.sm.add_widget(self.dash)
        # Додаємо пусті екрани для інших розділів
        for n in ['status', 'p3tool', 'service', 'settings']:
            self.sm.add_widget(Screen(name=n))
            
        self.dash.build_pages([["RPM", "COOLANT"], ["EVAP_PRESS", "BOOST"]])
        
        Clock.schedule_once(self.start_bt, 1)
        return self.sm

    def start_bt(self, dt):
        threading.Thread(target=self.bt_logic, daemon=True).start()

    def bt_logic(self):
        try:
            from jnius import autoclass
            BA = autoclass('android.bluetooth.BluetoothAdapter')
            paired = BA.getDefaultAdapter().getBondedDevices().toArray()
            target = next((d for d in paired if "OBD" in d.getName().upper()), None)
            if target:
                sock = target.createRfcommSocketToServiceRecord(autoclass('java.util.UUID').fromString("00001101-0000-1000-8000-00805F9B34FB"))
                sock.connect()
                self.out, self.inp = sock.getOutputStream(), sock.getInputStream()
                while True:
                    for name in self.dash.items.keys():
                        self.out.write((PIDS[name]['pid'] + "\r").encode())
                        time.sleep(0.2)
                        res = ""
                        while self.inp.available() > 0: res += chr(self.inp.read())
                        if "41" in res:
                            d = res.split()[2:]
                            v = PIDS[name]['formula'](d)
                            Clock.schedule_once(lambda dt, n=name, val=v: setattr(self.dash.items[n], 'text', f"{val:.0f}"))
                    time.sleep(0.1)
        except: pass

if __name__ == '__main__':
    VolvoApp().run()
        
