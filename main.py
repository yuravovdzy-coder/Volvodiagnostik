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
from kivy.clock import Clock
from kivy.core.window import Window
import threading
import requests
import os

# --- НАЛАШТУВАННЯ КЛАВІАТУРИ ---
# Це піднімає екран, коли з'являється клавіатура
Window.softinput_mode = 'below_target'

API_KEY = "AIzaSyARna8YDsY4tQd8Cv0QAsWTUJvRDTZlUWE"
AI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

PIDS_LIST = [f"P#{i:03d} Parameter" for i in range(1, 31)]

class MainMenu(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = FloatLayout()
        root.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        grid = GridLayout(cols=2, spacing=15, padding=25, size_hint=(0.9, 0.75), pos_hint={'center_x': 0.5, 'center_y': 0.45})
        items = [("📊\nПРИЛАДИ", "dash"), ("🤖\nAI ПОМІЧНИК", "ai"), ("🔍\nP3 FINDER", "p3"), ("🔧\nСЕРВІС", "svc"), ("📡\nELM327", "status"), ("⚙️\nНАЛАШТ.", "settings")]
        for text, sn in items:
            btn = Button(text=text, background_color=(0, 0, 0, 0.8), background_normal='', bold=True, halign='center', font_size='18sp')
            btn.bind(on_release=lambda x, n=sn: setattr(self.manager, 'current', n))
            grid.add_widget(btn)
        root.add_widget(grid)
        self.add_widget(root)

class DashScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        self.layout = FloatLayout()
        self.data_grid = GridLayout(cols=2, spacing=10, padding=20, size_hint=(1, 0.7), pos_hint={'top': 0.9})
        self.layout.add_widget(self.data_grid)
        set_btn = Button(text="⚙️", size_hint=(None, None), size=(80, 80), pos_hint={'right': 0.98, 'top': 0.98}, background_color=(0,0,0,0.5))
        set_btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'dash_settings'))
        back = Button(text="НАЗАД", size_hint=(0.3, 0.08), pos_hint={'x': 0.05, 'y': 0.05})
        back.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
        self.layout.add_widget(set_btn); self.layout.add_widget(back)
        self.add_widget(self.layout)

    def on_pre_enter(self):
        self.data_grid.clear_widgets()
        selected = App.get_running_app().selected_pids
        if not selected:
            self.data_grid.add_widget(Label(text="Оберіть прилади в ⚙️", font_size='18sp'))
        else:
            for p in selected:
                box = BoxLayout(orientation='vertical')
                box.add_widget(Label(text=p, font_size='12sp', color=(0.7,0.7,0.7,1)))
                box.add_widget(Label(text="--", font_size='22sp', bold=True))
                self.data_grid.add_widget(box)

class DashSettingsScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=20, spacing=10)
        l.add_widget(Label(text="СПИСОК ПРИЛАДІВ", size_hint_y=0.1, bold=True))
        scroll = ScrollView(); grid = GridLayout(cols=1, spacing=5, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))
        for pid in PIDS_LIST:
            btn = ToggleButton(text=pid, size_hint_y=None, height=60, background_normal='', background_color=(0.15, 0.15, 0.15, 1))
            btn.bind(on_release=self.update_selection); grid.add_widget(btn)
        scroll.add_widget(grid); l.add_widget(scroll)
        done = Button(text="ЗБЕРЕГТИ", size_hint_y=0.15, background_color=(0, 0.5, 0, 1))
        done.bind(on_release=lambda x: setattr(self.manager, 'current', 'dash'))
        l.add_widget(done); self.add_widget(l)

    def update_selection(self, instance):
        app = App.get_running_app()
        if instance.state == 'down':
            if instance.text not in app.selected_pids: app.selected_pids.append(instance.text)
        else:
            if instance.text in app.selected_pids: app.selected_pids.remove(instance.text)

class AIScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        l = BoxLayout(orientation='vertical', padding=20, spacing=10)
        self.log = Label(text="AI чекає запит...", size_hint_y=None, halign='left', valign='top', text_size=(Window.width*0.8, None))
        self.log.bind(texture_size=self.log.setter('size'))
        scroll = ScrollView(); scroll.add_widget(self.log); l.add_widget(scroll)
        self.inp = TextInput(hint_text="Код помилки...", size_hint_y=None, height=100, multiline=False)
        l.add_widget(self.inp)
        btns = BoxLayout(size_hint_y=0.15, spacing=10)
        go = Button(text="АНАЛІЗ", background_color=(0.4, 0.1, 0.6, 1)); go.bind(on_release=self.start_ai)
        back = Button(text="НАЗАД"); back.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
        btns.add_widget(go); btns.add_widget(back); l.add_widget(btns); self.add_widget(l)

    def start_ai(self, instance):
        q = self.inp.text.strip()
        if q:
            self.log.text += f"\n\nВи: {q}\nАналізую..."
            self.inp.text = ""; threading.Thread(target=self.get_ai, args=(q,), daemon=True).start()

    def get_ai(self, q):
        try:
            r = requests.post(AI_URL, json={"contents": [{"parts": [{"text": f"Поясни помилку Volvo {q} українською."}]}]}, timeout=10)
            ans = r.json()['candidates'][0]['content']['parts'][0]['text']
            Clock.schedule_once(lambda dt: self.update_log(ans))
        except Exception as e:
            Clock.schedule_once(lambda dt: self.update_log(f"Помилка: {str(e)}"))

    def update_log(self, text): self.log.text += f"\nAI: {text}"

class P3FinderScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        l = BoxLayout(orientation='vertical', padding=20, spacing=10)
        self.res = Label(text="Введіть назву для пошуку", size_hint_y=None, halign='left', text_size=(Window.width*0.8, None))
        self.res.bind(texture_size=self.res.setter('size'))
        scroll = ScrollView(); scroll.add_widget(self.res); l.add_widget(scroll)
        self.inp = TextInput(hint_text="Що шукаємо?", size_hint_y=None, height=100, multiline=False)
        self.inp.bind(on_text_validate=self.do_find)
        l.add_widget(self.inp)
        btns = BoxLayout(size_hint_y=0.15, spacing=10)
        btn = Button(text="ПОШУК", background_color=(0, 0.5, 0.3, 1)); btn.bind(on_release=self.do_find)
        back = Button(text="НАЗАД"); back.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
        btns.add_widget(btn); btns.add_widget(back); l.add_widget(btns); self.add_widget(l)

    def do_find(self, instance):
        q = self.inp.text.lower().strip()
        if not q: return
        try:
            with open('p3_data.txt', 'r', encoding='utf-8') as f:
                parts = f.read().split('P#')
                res = ["P#"+i.strip() for i in parts if q in i.lower()]
                self.res.text = "\n\n---\n\n".join(res) if res else "Нічого не знайдено."
        except: self.res.text = "Файл p3_data.txt відсутній."

class ServiceScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        l = BoxLayout(orientation='vertical', padding=20, spacing=10)
        self.info = Label(text="Завантаження...", size_hint_y=None, halign='left', text_size=(Window.width*0.8, None))
        self.info.bind(texture_size=self.info.setter('size'))
        scroll = ScrollView(); scroll.add_widget(self.info); l.add_widget(scroll)
        back = Button(text="НАЗАД", size_hint_y=0.15); back.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
        l.add_widget(back); self.add_widget(l)

    def on_pre_enter(self):
        try:
            with open('service_data.txt', 'r', encoding='utf-8') as f: self.info.text = f.read()
        except: self.info.text = "Сервісна книжка порожня або файл не знайдено."

class VolvoApp(App):
    selected_pids = []
    def build(self):
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(MainMenu(name='menu'))
        sm.add_widget(AIScreen(name='ai'))
        sm.add_widget(DashScreen(name='dash'))
        sm.add_widget(DashSettingsScreen(name='dash_settings'))
        sm.add_widget(P3FinderScreen(name='p3'))
        sm.add_widget(ServiceScreen(name='svc'))
        for n in ['status', 'settings']: sm.add_widget(Screen(name=n))
        return sm

if __name__ == '__main__':
    VolvoApp().run()
    
