import requests
from kivy.app import App
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.properties import StringProperty
from kivy.utils import get_color_from_hex

# --- НАЛАШТУВАННЯ API ---
# ВСТАВТЕ ВАШ КЛЮЧ
API_KEY = "AIzaSyARna8YDsY4tQd8Cv0QAsWTUJvRDTZlUWE"

# ОНОВЛЕНИЙ URL (Версія v1 замість v1beta)
AI_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key=" + API_KEY


# --- КОНСТАНТИ ELM327 ---
CMD_ATZ = "ATZ"
CMD_RPM = "010C"
CMD_TEMP = "0105"
CMD_EVAP = "0132"

class DashboardTab(FloatLayout):
    status_text = StringProperty("СТАТУС: ВІДКЛЮЧЕНО")
    rpm_text = StringProperty("0\nRPM")
    temp_text = StringProperty("0°C\nCOOLANT")
    evap_text = StringProperty("0 Pa\nEVAP")

    def __init__(self, **kwargs):
        super(DashboardTab, self).__init__(**kwargs)
        
        # 1. ФОН (Переконайтеся, що файл background.png є в папці проекту на GitHub)
        try:
            self.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        except:
            pass # Якщо файлу немає, просто пропустимо

        # 2. ОВЕРЛЕЙ З ДАНИМИ
        content_layout = BoxLayout(orientation='vertical', padding=[40, 20, 40, 20], spacing=10)
        
        status_label = Label(text=self.status_text, size_hint_y=0.1, font_size='16sp', color=(1, 1, 1, 0.7))
        self.bind(status_text=status_label.setter('text'))
        content_layout.add_widget(status_label)

        data_layout = BoxLayout(orientation='vertical', spacing=10, size_hint_y=0.7)
        
        rpm_label = Label(text=self.rpm_text, font_size='60sp', bold=True, halign='center')
        self.bind(rpm_text=rpm_label.setter('text'))
        data_layout.add_widget(rpm_label)
        
        temp_label = Label(text=self.temp_text, font_size='24sp', halign='center')
        self.bind(temp_text=temp_label.setter('text'))
        data_layout.add_widget(temp_label)
        
        evap_label = Label(text=self.evap_text, font_size='24sp', halign='center', color=get_color_from_hex('#3399FF'))
        self.bind(evap_text=evap_label.setter('text'))
        data_layout.add_widget(evap_label)
        
        content_layout.add_widget(data_layout)

        # Кнопки
        button_layout = BoxLayout(size_hint_y=0.2, spacing=15)
        connect_btn = Button(text="ПІДКЛЮЧИТИСЯ", background_color=get_color_from_hex('#004488'), background_normal='')
        connect_btn.bind(on_release=self.on_connect)
        button_layout.add_widget(connect_btn)
        
        atz_btn = Button(text="ATZ", background_color=get_color_from_hex('#333333'), background_normal='', size_hint_x=0.3)
        atz_btn.bind(on_release=self.on_atz)
        button_layout.add_widget(atz_btn)
        
        content_layout.add_widget(button_layout)
        self.add_widget(content_layout)
        self.is_connected = False

    def on_connect(self, instance):
        self.status_text = "СТАТУС: ПІДКЛЮЧЕННЯ (MOCK)..."
        Clock.schedule_once(self.mock_connect_success, 1.5)

    def mock_connect_success(self, dt):
        self.is_connected = True
        self.status_text = "СТАТУС: ПІДКЛЮЧЕНО (ELM327)"
        Clock.schedule_interval(self.update_data, 1)

    def on_atz(self, instance):
        if self.is_connected:
            self.status_text = "СТАТУС: ATZ ВІДПРАВЛЕНО"
            Clock.schedule_once(lambda dt: setattr(self, 'status_text', "СТАТУС: ПІДКЛЮЧЕНО (ELM327)"), 1)

    def update_data(self, dt):
        import random
        self.rpm_text = f"{random.randint(750, 850)}\nRPM"
        self.temp_text = f"{random.randint(90, 95)}°C\nCOOLANT"
        self.evap_text = f"{random.randint(200, 210)} Pa\nEVAP"

class MainInterface(TabbedPanel):
    def __init__(self, **kwargs):
        super(MainInterface, self).__init__(**kwargs)
        self.do_default_tab = False
        self.tab_pos = 'bottom_mid'

        # ВКЛАДКА 1: DASHBOARD (Ваш новий дизайн)
        self.tab1 = TabbedPanelItem(text='DASHBOARD')
        self.tab1.add_widget(DashboardTab())
        self.add_widget(self.tab1)

        # ВКЛАДКА 2: AI DIAGNOSTIC
        self.tab2 = TabbedPanelItem(text='AI DIAG')
        layout2 = BoxLayout(orientation='vertical', padding=20, spacing=15)
        self.error_input = TextInput(text='P045500', multiline=False, size_hint_y=None, height=100, font_size='20sp')
        layout2.add_widget(self.error_input)
        self.btn = Button(text="АНАЛІЗУВАТИ ШІ", background_color=get_color_from_hex('#115511'), size_hint_y=None, height=120)
        self.btn.bind(on_press=self.get_ai_help)
        layout2.add_widget(self.btn)
        self.scroll = ScrollView()
        self.ai_label = Label(text="Очікування...", text_size=(400, None), halign='left', valign='top')
        self.ai_label.bind(size=lambda s, v: setattr(self.ai_label, 'text_size', (s.width, None)))
        self.scroll.add_widget(self.ai_label)
        layout2.add_widget(self.scroll)
        self.tab2.add_widget(layout2)
        self.add_widget(self.tab2)

    def get_ai_help(self, instance):
        err = self.error_input.text.strip()
        self.ai_label.text = "Зв'язок з сервером Gemini..."
        prompt = f"Ти фахівець Volvo. Машина XC60 2017, T6 B4204T9. Помилка: {err}. Поясни причини українською."
        try:
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            res = requests.post(AI_URL, json=payload, headers={'Content-Type': 'application/json'}, timeout=15)
            if res.status_code == 200:
                self.ai_label.text = res.json()['candidates'][0]['content']['parts'][0]['text']
            else:
                self.ai_label.text = f"Помилка {res.status_code}: {res.text}"
        except Exception as e:
            self.ai_label.text = f"Помилка мережі: {str(e)}"

class VolvoDiagApp(App):
    def build(self):
        return MainInterface()

if __name__ == "__main__":
    VolvoDiagApp().run()
                
