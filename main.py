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
from kivy.graphics import Color, Line, Rectangle
from kivy.core.window import Window
from kivy.core.text import LabelBase
import threading
import requests
import random
import os

# --- 1. РЕЄСТРАЦІЯ ШРИФТІВ ---
try:
    LabelBase.register(name='Arial', 
                       fn_regular='ArialRegular.ttf',
                       fn_bold='ArialBold.ttf',
                       fn_italic='ArialItalic.ttf')
    MY_FONT = 'Arial'
except:
    MY_FONT = 'Roboto'

# Підняття екрану при відкритті клавіатури
Window.softinput_mode = 'adjustPan'

# API Конфігурація AI
API_KEY = "AIzaSyARna8YDsY4tQd8Cv0QAsWTUJvRDTZlUWE"
AI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

# --- ГРАФІЧНИЙ ВІДЖЕТ ---
class GraphWidget(BoxLayout):
    def __init__(self, name, graph_type="line", **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.name = name
        self.graph_type = graph_type
        self.values = [0] * 40
        self.header = Label(text=f"{name}", font_name=MY_FONT, bold=True, size_hint_y=0.2)
        self.canvas_area = BoxLayout()
        self.add_widget(self.header)
        self.add_widget(self.canvas_area)
        Clock.schedule_interval(self.update_data, 0.5)

    def update_data(self, dt):
        self.values.append(random.randint(10, 90))
        self.values.pop(0)
        self.draw()

    def draw(self):
        self.canvas_area.canvas.clear()
        with self.canvas_area.canvas:
            Color(0.1, 0.1, 0.1, 0.5)
            Rectangle(pos=self.canvas_area.pos, size=self.canvas_area.size)
            Color(0, 0.8, 1, 1) # Блакитний графік
            w, h = self.canvas_area.size
            x, y = self.canvas_area.pos
            
            if self.graph_type == "line":
                points = []
                step = w / len(self.values)
                for i, v in enumerate(self.values):
                    points.extend([x + i * step, y + (v / 100 * h)])
                if len(points) >= 4:
                    Line(points=points, width=1.2)
            elif self.graph_type == "bar":
                v = self.values[-1]
                Rectangle(pos=(x + w*0.3, y), size=(w*0.4, (v/100)*h))
            elif self.graph_type == "gauge":
                v = self.values[-1]
                Line(circle=(x + w/2, y + h/2, min(w,h)*0.3, 0, (v/100)*360), width=2)

# --- ЕКРАНИ ---
class MainMenu(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = FloatLayout()
        root.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        grid = GridLayout(cols=2, spacing=15, padding=25, size_hint=(0.9, 0.75), pos_hint={'center_x': 0.5, 'center_y': 0.45})
        
        items = [("📊\nПРИЛАДИ", "dash"), ("🤖\nAI ПОМІЧНИК", "ai"), 
                 ("🔍\nP3 FINDER", "p3"), ("🔧\nСЕРВІС", "svc"),
                 ("📡\nELM327", "status"), ("⚙️\nНАЛАШТ.", "settings")]
        
        for text, sn in items:
            btn = Button(text=text, background_color=(0, 0, 0, 0.8), background_normal='', 
                         bold=True, halign='center', font_size='20sp', font_name=MY_FONT)
            btn.bind(on_release=lambda x, n=sn: setattr(self.manager, 'current', n))
            grid.add_widget(btn)
        root.add_widget(grid)
        self.add_widget(root)

class DashScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        root = FloatLayout()
        scroll = ScrollView(size_hint=(1, 0.85), pos_hint={'top': 0.9})
        self.container = GridLayout(cols=1, spacing=15, size_hint_y=None, padding=20)
        self.container.bind(minimum_height=self.container.setter('height'))
        scroll.add_widget(self.container)
        
        btn_set = Button(text="⚙️", font_name=MY_FONT, size_hint=(None, None), size=(70,70), pos_hint={'right':1, 'top':1})
        btn_set.bind(on_release=lambda x: setattr(self.manager, 'current', 'dash_settings'))
        
        back = Button(text="НАЗАД", font_name=MY_FONT, size_hint=(0.3, 0.07), pos_hint={'x':0.05, 'y':0.02})
        back.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
        
        root.add_widget(scroll); root.add_widget(btn_set); root.add_widget(back)
        self.add_widget(root)

    def on_pre_enter(self):
        self.container.clear_widgets()
        app = App.get_running_app()
        if not app.selected_pids:
            self.container.add_widget(Label(text="Оберіть прилади в налаштуваннях ⚙️", font_name=MY_FONT))
        for name, gtype in app.selected_pids.items():
            self.container.add_widget(GraphWidget(name=name, graph_type=gtype, size_hint_y=None, height=250))

class DashSettingsScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=20, spacing=10)
        l.add_widget(Label(text="НАЛАШТУВАННЯ ПАРАМЕТРІВ", font_name=MY_FONT, bold=True, size_hint_y=0.1))
        
        scroll = ScrollView()
        grid = GridLayout(cols=1, spacing=10, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))
        
        for i in range(1, 31):
            p_name = f"P#{i:03d} Parameter"
            row = BoxLayout(size_hint_y=None, height=80, spacing=5)
            row.add_widget(Label(text=p_name, font_name=MY_FONT, size_hint_x=0.4, font_size='12sp'))
            for t in ["line", "bar", "gauge"]:
                btn = ToggleButton(text=t, group=p_name, size_hint_x=0.2, font_name=MY_FONT)
                btn.bind(on_release=lambda x, p=p_name, g=t: self.save(p, g))
                row.add_widget(btn)
            grid.add_widget(row)
            
        scroll.add_widget(grid); l.add_widget(scroll)
        btn_ok = Button(text="ГОТОВО", font_name=MY_FONT, size_hint_y=0.12, background_color=(0,0.5,0,1))
        btn_ok.bind(on_release=lambda x: setattr(self.manager, 'current', 'dash'))
        l.add_widget(btn_ok); self.add_widget(l)

    def save(self, p, g):
        App.get_running_app().selected_pids[p] = g

class AIScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        l = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        self.log = Label(text="Вольво AI готовий до роботи...", font_name=MY_FONT, markup=True,
                         size_hint_y=None, halign='left', valign='top', text_size=(Window.width*0.85, None))
        self.log.bind(texture_size=self.log.setter('size'))
        
        scroll = ScrollView(); scroll.add_widget(self.log); l.add_widget(scroll)
        self.inp = TextInput(hint_text="Введіть код помилки...", font_name=MY_FONT, size_hint_y=None, height=110, multiline=False)
        l.add_widget(self.inp)
        
        btns = BoxLayout(size_hint_y=0.15, spacing=10)
        go = Button(text="АНАЛІЗ", font_name=MY_FONT, bold=True, background_color=(0.4,0.1,0.6,1))
        go.bind(on_release=self.start_ai)
        back = Button(text="НАЗАД", font_name=MY_FONT); back.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
        btns.add_widget(go); btns.add_widget(back); l.add_widget(btns); self.add_widget(l)

    def start_ai(self, instance):
        q = self.inp.text.strip()
        if q:
            self.log.text += f"\n\n[b]Ви:[/b] {q}\n[i]Шукаю рішення...[/i]"
            self.inp.text = ""
            threading.Thread(target=self.get_response, args=(q,), daemon=True).start()

    def get_response(self, q):
        try:
            r = requests.post(AI_URL, json={"contents":[{"parts":[{"text":f"Explain Volvo DTC {q} in Ukrainian."}]}]}, timeout=7)
            ans = r.json()['candidates'][0]['content']['parts'][0]['text']
            Clock.schedule_once(lambda dt: self.update_ui(ans))
        except requests.exceptions.ConnectionError:
            Clock.schedule_once(lambda dt: self.update_ui("[color=ff3333]Відсутнє з'єднання з інтернетом[/color]"))
        except:
            Clock.schedule_once(lambda dt: self.update_ui("Помилка запиту."))

    def update_ui(self, txt):
        self.log.text = self.log.text.replace("[i]Шукаю рішення...[/i]", "")
        self.log.text += f"\n[b]AI:[/b] {txt}"

class ServiceScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        l = BoxLayout(orientation='vertical', padding=20)
        self.info = Label(text="", font_name=MY_FONT, size_hint_y=None, halign='left', text_size=(Window.width*0.8, None))
        self.info.bind(texture_size=self.info.setter('size'))
        scroll = ScrollView(); scroll.add_widget(self.info); l.add_widget(scroll)
        back = Button(text="НАЗАД", font_name=MY_FONT, size_hint_y=0.15)
        back.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
        l.add_widget(back); self.add_widget(l)

    def on_pre_enter(self):
        try:
            with open('service_data.txt', 'r', encoding='utf-8') as f:
                self.info.text = f.read()
        except:
            self.info.text = "Дані сервісу відсутні."

class P3FinderScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        l = BoxLayout(orientation='vertical', padding=20, spacing=10)
        self.res = Label(text="Результати пошуку...", font_name=MY_FONT, size_hint_y=None, halign='left', text_size=(Window.width*0.8, None))
        self.res.bind(texture_size=self.res.setter('size'))
        scroll = ScrollView(); scroll.add_widget(self.res); l.add_widget(scroll)
        self.inp = TextInput(hint_text="Назва параметра...", font_name=MY_FONT, size_hint_y=None, height=100)
        l.add_widget(self.inp)
        btns = BoxLayout(size_hint_y=0.15, spacing=10)
        b1 = Button(text="ШУКАТИ", font_name=MY_FONT, background_color=(0,0.4,0.3,1))
        b1.bind(on_release=self.find)
        b2 = Button(text="НАЗАД", font_name=MY_FONT)
        b2.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
        btns.add_widget(b1); btns.add_widget(b2); l.add_widget(btns); self.add_widget(l)

    def find(self, instance):
        q = self.inp.text.lower().strip()
        try:
            with open('p3_data.txt', 'r', encoding='utf-8') as f:
                parts = f.read().split('P#')
                out = ["P#"+i.strip() for i in parts if q in i.lower()]
                self.res.text = "\n\n---\n\n".join(out) if out else "Не знайдено."
        except:
            self.res.text = "Файл p3_data.txt не знайдено."

class StatusScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=20)
        l.add_widget(Label(text="ELM327 Статус: Не підключено", font_name=MY_FONT))
        back = Button(text="НАЗАД", size_hint_y=0.1)
        back.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
        l.add_widget(back)
        self.add_widget(l)

class SettingsScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=20)
        l.add_widget(Label(text="Налаштування додатка", font_name=MY_FONT))
        back = Button(text="НАЗАД", size_hint_y=0.1)
        back.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
        l.add_widget(back)
        self.add_widget(l)

class VolvoApp(App):
    selected_pids = {}
    def build(self):
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(MainMenu(name='menu'))
        sm.add_widget(DashScreen(name='dash'))
        sm.add_widget(DashSettingsScreen(name='dash_settings'))
        sm.add_widget(AIScreen(name='ai'))
        sm.add_widget(ServiceScreen(name='svc'))
        sm.add_widget(P3FinderScreen(name='p3'))
        sm.add_widget(StatusScreen(name='status'))
        sm.add_widget(SettingsScreen(name='settings'))
        return sm

if __name__ == '__main__':
    VolvoApp().run()
