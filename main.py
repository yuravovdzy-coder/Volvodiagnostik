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

# --- КОНФІГУРАЦІЯ AI (Твій ключ) ---
API_KEY = "AIzaSyARna8YDsY4tQd8Cv0QAsWTUJvRDTZlUWE"
# Покращений URL для більш стабільних запитів
AI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

# --- БАЗА ПАРАМЕТРІВ OBD2 (30 PID) ---
PIDS = {
    "RPM": {"pid": "010C", "formula": lambda d: (int(d[0],16)*256+int(d[1],16))/4, "unit": "RPM", "group": "Engine"},
    "SPEED": {"pid": "010D", "formula": lambda d: int(d[0],16), "unit": "km/h", "group": "Engine"},
    "COOLANT_T": {"pid": "0105", "formula": lambda d: int(d[0],16)-40, "unit": "°C", "group": "Engine"},
    "ENGINE_LOAD": {"pid": "0104", "formula": lambda d: int(d[0],16)*100/255, "unit": "%", "group": "Engine"},
    
    "BOOST": {"pid": "010B", "formula": lambda d: int(d[0],16)-101, "unit": "kPa", "group": "Turbo"}, # Мінус атм. тиск
    "INTAKE_T": {"pid": "010F", "formula": lambda d: int(d[0],16)-40, "unit": "°C", "group": "Turbo"},
    "MAF": {"pid": "0110", "formula": lambda d: (int(d[0],16)*256+int(d[1],16))/100, "unit": "g/s", "group": "Turbo"},
    
    "EVAP_P": {"pid": "0132", "formula": lambda d: ((int(d[0],16)*256)+int(d[1],16))/4, "unit": "Pa", "group": "EVAP"}, # Твій пріоритет!
    "PURGE_C": {"pid": "012E", "formula": lambda d: int(d[0],16)*100/255, "unit": "%", "group": "EVAP"},
    
    "FUEL_P": {"pid": "0123", "formula": lambda d: (int(d[0],16)*256+int(d[1],16))*10, "unit": "kPa", "group": "Fuel"},
    "FUEL_L": {"pid": "012F", "formula": lambda d: int(d[0],16)*100/255, "unit": "%", "group": "Fuel"},
    "STFT1": {"pid": "0106", "formula": lambda d: (int(d[0],16)-128)*100/128, "unit": "%", "group": "Fuel"},
    
    "VOLTAGE": {"pid": "0142", "formula": lambda d: (int(d[0],16)*256+int(d[1],16))/1000, "unit": "V", "group": "Elec"},
    "OIL_T": {"pid": "015C", "formula": lambda d: int(d[0],16)-40, "unit": "°C", "group": "Engine"},
    # ...Можна розширити до 30 PID за цим шаблоном, додаючи їх у конфігуратор
}

# --- 1. ГОЛОВНЕ МЕНЮ ---
class MainMenu(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = FloatLayout()
        root.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        
        # Сітка з графічними іконками (Unicode)
        menu_grid = GridLayout(cols=2, spacing=25, padding=40, size_hint=(0.9, 0.75), pos_hint={'center_x': 0.5, 'center_y': 0.45})
        
        buttons = [
            ("📊\nПРИЛАДИ\nOBD2", "dash", "#003366"),
            ("📡\nСТАТУС\nELM327", "status_bt", "#222222"),
            ("🤖\nAI\nASSISTANT", "ai_chat", "#5E2D79"),
            ("🛠️\nCONFIG\nP3TOOL", "p3tool", "#006644"),
            ("🔧\nСЕРВІС", "service", "#880000"),
            ("⚙️\nНАЛАШТ.", "settings", "#444444")
        ]
        
        for text, sn, color in buttons:
            btn = Button(text=text, background_color=get_color_from_hex(color), halign='center', bold=True, background_normal='')
            btn.bind(on_release=lambda x, sn=sn: setattr(self.manager, 'current', sn))
            menu_grid.add_widget(btn)
            
        root.add_widget(menu_grid)
        root.add_widget(Label(text="VOLVO P3 SMARTSCAN + AI", pos_hint={'top': 0.96}, font_size='22sp', bold=True))
        self.add_widget(root)

# --- 2. ЕКРАН AI (ВИПРАВЛЕНИЙ) ---
class AIScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        layout.add_widget(Label(text="GEMINI AI ASSISTANT", size_hint_y=0.1, bold=True))
        
        self.scroll = ScrollView(size_hint_y=0.7)
        self.chat_log = Label(text="Volvo AI готовий. Запитай про помилку (P0455 Volvo)...\n", size_hint_y=None, halign='left', valign='top', text_size=(400, None))
        self.chat_log.bind(texture_size=self.chat_log.setter('size'))
        self.scroll.add_widget(self.chat_log)
        layout.add_widget(scroll)
        
        self.input = TextInput(hint_text="Код помилки...", size_hint_y=None, height=100, multiline=False)
        layout.add_widget(self.input)
        
        btn_layout = BoxLayout(size_hint_y=0.15, spacing=10)
        send_btn = Button(text="АНАЛІЗУВАТИ", background_color=get_color_from_hex("#5E2D79"))
        send_btn.bind(on_release=self.ask_ai); back_btn = Button(text="НАЗАД")
        back_btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
        btn_layout.add_widget(send_btn); btn_layout.add_widget(back_btn)
        layout.add_widget(btn_layout)
        self.add_widget(layout)

    def ask_ai(self, instance):
        query = self.input.text
        if not query: return
        self.chat_log.text += f"\nВи: {query}\nAI аналізує систему Volvo...\n"
        self.input.text = ""
        threading.Thread(target=self.get_ai_response, args=(query,), daemon=True).start()

    def get_ai_response(self, query):
        prompt = f"Ти діагност Volvo. Коротко поясни причини помилки {query} для платформи P3 українською."
        # Виправлений формат запиту для підвищення стабільності
        headers = {'Content-Type': 'application/json'}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            r = requests.post(AI_URL, headers=headers, json=payload, timeout=12)
            data = r.json()
            if 'candidates' in data:
                ans = data['candidates'][0]['content']['parts'][0]['text']
            else:
                ans = f"Помилка API Google: {data.get('error', {}).get('message', 'Перевірте формат запиту')}"
            Clock.schedule_once(lambda dt: setattr(self.chat_log, 'text', self.chat_log.text + f"\nAI: {ans}\n"))
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self.chat_log, 'text', self.chat_log.text + f"\nAI: Помилка зв'язку (Мережа): {str(e)}\n"))

# --- 3. ПАНЕЛЬ ПРИЛАДІВ ТА НАЛАШТУВАННЯ PIDS ---
class DashboardItem(BoxLayout):
    """Віджет одного показника"""
    def __init__(self, name, unit, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.add_widget(Label(text=name, font_size='16sp', color=(1,1,1,0.7)))
        self.value_label = Label(text="--", font_size='50sp', bold=True)
        self.add_widget(self.value_label)
        self.add_widget(Label(text=unit, font_size='14sp', color=(1,1,1,0.5)))

class DashScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = FloatLayout()
        root.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        
        # Кнопка Налаштувань (Шестерня)
        set_btn = Button(text="⚙️", size_hint=(None, None), size=(60, 60), pos_hint={'right':0.98, 'top':0.98}, background_color=(0,0,0,0.2))
        set_btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'settings_pids'))
        root.add_widget(set_btn)
        
        self.carousel = Carousel(direction='right')
        root.add_widget(self.carousel)
        self.add_widget(root)

        self.current_items = {} # Посилання на лейбли

    def update_dashboards(self, config):
        self.carousel.clear_widgets()
        self.current_items = {}
        for page in config:
            grid = GridLayout(cols=2 if len(page) > 1 else 1, spacing=20, padding=40)
            for pid_key in page:
                pid_info = PIDS[pid_key]
                item = DashboardItem(pid_key, pid_info["unit"])
                grid.add_widget(item)
                self.current_items[pid_key] = item.value_label # Зберігаємо для оновлення
            self.carousel.add_widget(grid)

class SettingsPidsScreen(Screen):
    """Меню вибору 30 приладів (Конфігуратор)"""
    def __init__(self, **kw):
        super().__init__(**kw)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=15)
        layout.add_widget(Label(text="КОНФІГУРАТОР ПРИЛАДІВ", font_size='22sp', size_hint_y=0.1, bold=True))
        
        scroll = ScrollView()
        self.grid = GridLayout(cols=2, spacing=10, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        
        self.btns = {}
        for name in PIDS.keys():
            b = ToggleButton(text=name, size_hint_y=None, height=60, background_down=[0,0.5,1,1])
            self.btns[name] = b
            self.grid.add_widget(b)
        
        scroll.add_widget(self.grid)
        layout.add_widget(scroll)
        
        save_btn = Button(text="ЗАСТОСУВАТИ", size_hint_y=0.15, background_color=(0,0.6,0,1))
        save_btn.bind(on_release=self.apply_config)
        layout.add_widget(save_btn)
        self.add_widget(layout)

    def apply_config(self, instance):
        # Отримуємо вибрані PID
        selected = [name for name, btn in self.btns.items() if btn.state == 'down']
        # Розбиваємо на сторінки по 6 штук
        new_config = [selected[i:i + 6] for i in range(0, len(selected), 6)]
        
        self.manager.get_screen('dash').update_dashboards(new_config)
        self.manager.current = 'dash'

# --- 4. ПУСТІ ЕКРАНИ ---
class PlaceholderScreen(Screen):
    def __init__(self, title, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=50)
        l.add_widget(Label(text=title, font_size='20sp'))
        b = Button(text="НАЗАД", size_hint_y=0.2); b.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
        l.add_widget(b); self.add_widget(l)

# --- МЕНЕДЖЕР ПРОГРАМИ ---
class VolvoApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(MainMenu(name='menu'))
        sm.add_widget(AIScreen(name='ai_chat'))
        self.dash = DashScreen(name='dash')
        sm.add_widget(self.dash)
        sm.add_widget(SettingsPidsScreen(name='settings_pids'))
        sm.add_widget(PlaceholderScreen("P3TOOL CONFIG (В РОБОТІ)", name='p3tool'))
        sm.add_widget(PlaceholderScreen("СЕРВІСНА ІНФОРМАЦІЯ", name='service'))
        sm.add_widget(PlaceholderScreen("СТАТУС BLUETOOTH", name='status_bt'))
        sm.add_widget(PlaceholderScreen("НАЛАШТУВАННЯ ДОДАТКА", name='settings'))
        
        # Початкова конфігурація для дашборду
        self.dash.update_dashboards([["RPM", "COOLANT_T", "EVAP_P", "BOOST"]])
        
        return sm

if __name__ == '__main__':
    VolvoApp().run()
    
