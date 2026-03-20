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
from kivy.utils import get_color_from_hex
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
        # Твій фон з GitHub (background.png)
        root.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        
        grid = GridLayout(cols=2, spacing=15, padding=30, size_hint=(0.9, 0.75), pos_hint={'center_x': 0.5, 'center_y': 0.45})
        
        # Меню з іконками
        menu_items = [
            ("📊\nПРИЛАДИ", "dash"), 
            ("🤖\nAI ПОМІЧНИК", "ai"), 
            ("🔍\nP3 FINDER", "p3"), 
            ("🔧\nСЕРВІС", "svc"),
            ("📡\nELM327", "status"),
            ("⚙️\nНАЛАШТ.", "settings")
        ]
        
        for text, sn in menu_items:
            btn = Button(
                text=text, 
                background_color=(0, 0, 0, 0.6), 
                background_normal='', 
                bold=True,
                halign='center',
                font_size='18sp'
            )
            btn.bind(on_release=lambda x, n=sn: setattr(self.manager, 'current', n))
            grid.add_widget(btn)
        
        root.add_widget(grid)
        root.add_widget(Label(text="VOLVO P3 SMARTSCAN", pos_hint={'top': 0.96}, font_size='22sp', bold=True))
        self.add_widget(root)

class P3FinderScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        layout.add_widget(Label(text="🔍 ПОШУК КОНФІГУРАЦІЇ P3", size_hint_y=0.1, bold=True))
        
        # Поле для введення запиту
        self.search_input = TextInput(
            hint_text="Що хочете знайти? (напр. 'Mirror' або 'Двері')", 
            size_hint_y=None, 
            height=100, 
            multiline=False,
            font_size='18sp'
        )
        self.search_input.bind(on_text_validate=self.search_config)
        layout.add_widget(self.search_input)
        
        # Вікно результатів
        self.result_view = Label(
            text="Введіть назву функції або номер P#...", 
            size_hint_y=None, 
            halign='left', 
            valign='top', 
            text_size=(400, None),
            color=(0.9, 0.9, 0.9, 1)
        )
        self.result_view.bind(texture_size=self.result_view.setter('size'))
        scroll = ScrollView(size_hint_y=0.6)
        scroll.add_widget(self.result_view)
        layout.add_widget(scroll)
        
        # Кнопки
        btns = BoxLayout(size_hint_y=0.15, spacing=10)
        find_btn = Button(text="ЗНАЙТИ 🔎", background_color=(0, 0.4, 0.2, 1), background_normal='')
        find_btn.bind(on_release=self.search_config)
        
        back_btn = Button(text="НАЗАД")
        back_btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
        
        btns.add_widget(find_btn); btns.add_widget(back_btn)
        layout.add_widget(btns)
        self.add_widget(layout)

    def search_config(self, instance):
        query = self.search_input.text.lower().strip()
        if not query: return
        
        results = []
        try:
            # [span_0](start_span)Читання твого файлу p3_data.txt[span_0](end_span)
            with open('p3_data.txt', 'r', encoding='utf-8') as f:
                content = f.read()
                # [span_1](start_span)[span_2](start_span)[span_3](start_span)Розбиваємо на блоки по P#[span_1](end_span)[span_2](end_span)[span_3](end_span)
                items = content.split('P#')
                for item in items:
                    if query in item.lower():
                        results.append("P#" + item.strip())
            
            if results:
                self.result_view.text = f"Знайдено ({len(results)}):\n\n" + "\n\n---\n\n".join(results)
            else:
                self.result_view.text = f"За запитом '{query}' нічого не знайдено.\nСпробуйте інше слово."
        except Exception as e:
            self.result_view.text = f"Помилка зчитування файлу: {str(e)}"

class AIScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        self.log = Label(text="AI чекає на код помилки...", size_hint_y=None, halign='left', valign='top', text_size=(400, None))
        self.log.bind(texture_size=self.log.setter('size'))
        scroll = ScrollView(size_hint_y=0.7); scroll.add_widget(self.log); layout.add_widget(scroll)
        self.input = TextInput(hint_text="Код (напр. P0455)...", size_hint_y=None, height=100, multiline=False)
        layout.add_widget(self.input)
        btns = BoxLayout(size_hint_y=0.15, spacing=10)
        analyze = Button(text="АНАЛІЗ 🤖", background_color=(0.4, 0.1, 0.6, 1), background_normal='')
        analyze.bind(on_release=self.ask)
        back = Button(text="НАЗАД")
        back.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
        btns.add_widget(analyze); btns.add_widget(back); layout.add_widget(btns)
        self.add_widget(layout)

    def ask(self, instance):
        q = self.input.text.strip()
        if not q: return
        self.log.text += f"\n\nВи: {q}\nAI аналізує..."; self.input.text = ""
        threading.Thread(target=self.fetch_ai, args=(q,), daemon=True).start()

    def fetch_ai(self, q):
        prompt = f"Ти фахівець Volvo. Поясни причини коду {q} для Volvo P3 (XC60/S60/V60). Відповідай коротко українською."
        try:
            r = requests.post(AI_URL, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=15)
            ans = r.json()['candidates'][0]['content']['parts'][0]['text']
            Clock.schedule_once(lambda dt: setattr(self.log, 'text', self.log.text + f"\nAI: {ans}"))
        except: Clock.schedule_once(lambda dt: setattr(self.log, 'text', self.log.text + "\nПомилка мережі."))

class VolvoApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(MainMenu(name='menu'))
        sm.add_widget(AIScreen(name='ai'))
        sm.add_widget(P3FinderScreen(name='p3'))
        # Заглушки
        for n in ['dash', 'svc', 'status', 'settings']:
            sm.add_widget(Screen(name=n))
        return sm

if __name__ == '__main__':
    VolvoApp().run()
    
