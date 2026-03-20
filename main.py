import kivy
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
import threading
import requests
import json

# Конфігурація AI
API_KEY = "AIzaSyARna8YDsY4tQd8Cv0QAsWTUJvRDTZlUWE"
AI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

class MainMenu(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = FloatLayout()
        root.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        grid = GridLayout(cols=2, spacing=15, padding=30, size_hint=(0.9, 0.75), pos_hint={'center_x': 0.5, 'center_y': 0.45})
        items = [
            ("📊\nПРИЛАДИ", "dash"), ("🤖\nAI ПОМІЧНИК", "ai"), 
            ("🔍\nP3 FINDER", "p3"), ("🔧\nСЕРВІС", "svc"),
            ("📡\nELM327", "status"), ("⚙️\nНАЛАШТ.", "settings")
        ]
        for text, sn in items:
            btn = Button(text=text, background_color=(0, 0, 0, 0.8), background_normal='', bold=True, halign='center')
            btn.bind(on_release=lambda x, n=sn: setattr(self.manager, 'current', n))
            grid.add_widget(btn)
        root.add_widget(grid)
        self.add_widget(root)

class AIScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        self.log = Label(text="AI чекає на код помилки...", size_hint_y=None, halign='left', valign='top', text_size=(400, None))
        self.log.bind(texture_size=self.log.setter('size'))
        scroll = ScrollView(size_hint_y=0.7); scroll.add_widget(self.log); layout.add_widget(scroll)
        self.input = TextInput(hint_text="Код (напр. P0455)...", background_color=(0.1, 0.1, 0.1, 1), foreground_color=(1,1,1,1), size_hint_y=None, height=100, multiline=False)
        layout.add_widget(self.input)
        btns = BoxLayout(size_hint_y=0.15, spacing=10)
        analyze = Button(text="АНАЛІЗ", background_color=(0.4, 0.1, 0.6, 1), background_normal='')
        analyze.bind(on_release=self.ask)
        back = Button(text="НАЗАД")
        back.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
        btns.add_widget(analyze); btns.add_widget(back); layout.add_widget(btns)
        self.add_widget(layout)

    def ask(self, instance):
        q = self.input.text.strip()
        if not q: return
        self.log.text += f"\n\nВи: {q}\nAI аналізує..."
        self.input.text = ""
        threading.Thread(target=self.fetch_ai, args=(q,), daemon=True).start()

    def fetch_ai(self, q):
        try:
            # Використовуємо правильний формат запиту для Gemini 1.5 Flash
            headers = {'Content-Type': 'application/json'}
            payload = {"contents": [{"parts": [{"text": f"Ти експерт Volvo. Коротко поясни причини помилки {q} для Volvo P3 українською."}]}]}
            r = requests.post(AI_URL, headers=headers, json=payload, timeout=15)
            res = r.json()
            if 'candidates' in res:
                ans = res['candidates'][0]['content']['parts'][0]['text']
            else:
                ans = "Помилка API. Перевірте ключ або формат запиту."
            Clock.schedule_once(lambda dt: setattr(self.log, 'text', self.log.text + f"\nAI: {ans}"))
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self.log, 'text', self.log.text + f"\nПомилка: {str(e)}"))

class P3FinderScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        self.search = TextInput(hint_text="Пошук (напр. 'Engine')...", background_color=(0.1, 0.1, 0.1, 1), foreground_color=(1,1,1,1), size_hint_y=None, height=100)
        self.results = Label(text="Дані p3_data.txt", size_hint_y=None, halign='left', valign='top', text_size=(400, None))
        self.results.bind(texture_size=self.results.setter('size'))
        scroll = ScrollView(); scroll.add_widget(self.results)
        layout.add_widget(self.search); layout.add_widget(scroll)
        btns = BoxLayout(size_hint_y=0.2, spacing=10)
        fbtn = Button(text="ЗНАЙТИ", background_color=(0, 0.4, 0.2, 1)); fbtn.bind(on_release=self.do_search)
        bbtn = Button(text="НАЗАД"); bbtn.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
        btns.add_widget(fbtn); btns.add_widget(bbtn); layout.add_widget(btns); self.add_widget(layout)

    def do_search(self, instance):
        query = self.search.text.lower().strip()
        try:
            with open('p3_data.txt', 'r', encoding='utf-8') as f:
                content = f.read().split('P#')
                res = ["P#" + i.strip() for i in content if query in i.lower()]
                self.results.text = "\n\n---\n\n".join(res) if res else "Нічого не знайдено."
        except: self.results.text = "Файл p3_data.txt не знайдено."

class ServiceScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        layout.add_widget(Label(text="🔧 СЕРВІСНА ІНФОРМАЦІЯ", bold=True, size_hint_y=0.1))
        self.info = Label(text="Натисніть 'ОНОВИТИ'", size_hint_y=None, halign='left', valign='top', text_size=(400, None))
        self.info.bind(texture_size=self.info.setter('size'))
        scroll = ScrollView(); scroll.add_widget(self.info); layout.add_widget(scroll)
        btns = BoxLayout(size_hint_y=0.2, spacing=10)
        ubtn = Button(text="ОНОВИТИ", background_color=(0.2, 0.4, 0.6, 1)); ubtn.bind(on_release=self.load_service)
        bbtn = Button(text="НАЗАД"); bbtn.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
        btns.add_widget(ubtn); btns.add_widget(bbtn); layout.add_widget(btns); self.add_widget(layout)

    def load_service(self, instance):
        try:
            with open('service_data.txt', 'r', encoding='utf-8') as f:
                self.info.text = f.read()
        except: self.info.text = "Файл service_data.txt не знайдено."

class ElmStatusScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        l = BoxLayout(orientation='vertical', padding=40)
        l.add_widget(Label(text="📡 СТАТУС ELM327", bold=True))
        l.add_widget(Label(text="Статус: Очікування підключення...\nПротокол: AUTO\nНапруга: -- V"))
        btn = Button(text="НАЗАД", size_hint_y=0.2); btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
        l.add_widget(btn); self.add_widget(l)

class DashScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        l = BoxLayout(orientation='vertical', padding=40)
        l.add_widget(Label(text="📊 ПАНЕЛЬ ПРИЛАДІВ", bold=True))
        l.add_widget(Label(text="RPM: 0\nTemp: 0°C\nBoost: 0.0 bar", font_size='20sp'))
        btn = Button(text="НАЗАД", size_hint_y=0.2); btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
        l.add_widget(btn); self.add_widget(l)

class VolvoApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(MainMenu(name='menu'))
        sm.add_widget(AIScreen(name='ai'))
        sm.add_widget(P3FinderScreen(name='p3'))
        sm.add_widget(ServiceScreen(name='svc'))
        sm.add_widget(ElmStatusScreen(name='status'))
        sm.add_widget(DashScreen(name='dash'))
        sm.add_widget(Screen(name='settings'))
        return sm

if __name__ == '__main__':
    VolvoApp().run()
