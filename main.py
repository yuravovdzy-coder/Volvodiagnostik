import kivy
import sys
import traceback

# --- ФУНКЦІЯ ЗАПИСУ ПОМИЛОК ---
# Якщо додаток впаде, ми знайдемо причину в файлі error_log.txt
def log_error(error_text):
    with open("error_log.txt", "a", encoding='utf-8') as f:
        f.write(error_text + "\n")

try:
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
except Exception as e:
    log_error(f"Import Error: {traceback.format_exc()}")
    raise e

# Реєстрація шрифтів
try:
    LabelBase.register(name='Arial', 
                       fn_regular='ArialRegular.ttf',
                       fn_bold='ArialBold.ttf')
    MY_FONT = 'Arial'
except:
    MY_FONT = 'Roboto'

Window.softinput_mode = 'adjustPan'

# API Конфігурація
API_KEY = "AIzaSyARna8YDsY4tQd8Cv0QAsWTUJvRDTZlUWE"
AI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

# --- ГРАФІЧНИЙ ВІДЖЕТ ---
class GraphWidget(BoxLayout):
    def __init__(self, name, graph_type="line", **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.name = name
        self.graph_type = graph_type
        self.values = [0] * 30
        self.header = Label(text=name, font_name=MY_FONT, bold=True, size_hint_y=0.2)
        self.canvas_area = BoxLayout()
        self.add_widget(self.header)
        self.add_widget(self.canvas_area)
        Clock.schedule_interval(self.update_data, 0.5)

    def update_data(self, dt):
        self.values.append(random.randint(15, 85))
        self.values.pop(0)
        self.draw()

    def draw(self):
        self.canvas_area.canvas.clear()
        with self.canvas_area.canvas:
            Color(0.1, 0.1, 0.1, 0.6)
            Rectangle(pos=self.canvas_area.pos, size=self.canvas_area.size)
            Color(0, 0.7, 0.9, 1)
            w, h = self.canvas_area.size
            x, y = self.canvas_area.pos
            if self.graph_type == "line":
                pts = []
                step = w / len(self.values)
                for i, v in enumerate(self.values):
                    pts.extend([x + i * step, y + (v / 100 * h)])
                if len(pts) >= 4: Line(points=pts, width=1.5)
            elif self.graph_type == "bar":
                Rectangle(pos=(x + w*0.35, y), size=(w*0.3, (self.values[-1]/100)*h))

# --- ЕКРАНИ ---
class MainMenu(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = FloatLayout()
        if os.path.exists('background.png'):
            root.add_widget(Image(source='background.png', allow_stretch=True, keep_ratio=False))
        
        grid = GridLayout(cols=2, spacing=15, padding=25, size_hint=(0.9, 0.7), pos_hint={'center_x': 0.5, 'center_y': 0.45})
        btns = [("📊\nПРИЛАДИ", "dash"), ("🤖\nAI ПОМІЧНИК", "ai"), 
                ("🔍\nP3 FINDER", "p3"), ("🔧\nСЕРВІС", "svc"),
                ("📡\nELM327", "status"), ("⚙️\nНАЛАШТ.", "settings")]
        
        for txt, sn in btns:
            b = Button(text=txt, background_color=(0,0,0,0.85), font_name=MY_FONT, bold=True, halign='center')
            b.bind(on_release=lambda x, n=sn: setattr(self.manager, 'current', n))
            grid.add_widget(b)
        root.add_widget(grid)
        self.add_widget(root)

class DashScreen(Screen):
    def on_pre_enter(self):
        self.container.clear_widgets()
        pids = App.get_running_app().selected_pids
        if not pids:
            self.container.add_widget(Label(text="Оберіть параметри в ⚙️", font_name=MY_FONT))
        for n, t in pids.items():
            self.container.add_widget(GraphWidget(name=n, graph_type=t, size_hint_y=None, height=220))

    def __init__(self, **kw):
        super().__init__(**kw)
        root = FloatLayout()
        scroll = ScrollView(size_hint=(1, 0.85), pos_hint={'top': 0.9})
        self.container = GridLayout(cols=1, spacing=10, size_hint_y=None, padding=20)
        self.container.bind(minimum_height=self.container.setter('height'))
        scroll.add_widget(self.container)
        
        btn_s = Button(text="⚙️", size_hint=(None, None), size=(80,80), pos_hint={'right':1, 'top':1})
        btn_s.bind(on_release=lambda x: setattr(self.manager, 'current', 'dash_settings'))
        back = Button(text="НАЗАД", size_hint=(0.3, 0.08), pos_hint={'x':0.05, 'y':0.02})
        back.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
        
        root.add_widget(scroll); root.add_widget(btn_s); root.add_widget(back)
        self.add_widget(root)

class DashSettingsScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=20)
        scroll = ScrollView()
        grid = GridLayout(cols=1, spacing=10, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))
        for i in range(1, 16):
            pn = f"Sensor {i:02d}"
            row = BoxLayout(size_hint_y=None, height=70)
            row.add_widget(Label(text=pn, font_name=MY_FONT))
            for t in ["line", "bar"]:
                btn = ToggleButton(text=t, group=pn, font_name=MY_FONT)
                btn.bind(on_release=lambda x, p=pn, g=t: self.save(p, g))
                row.add_widget(btn)
            grid.add_widget(row)
        scroll.add_widget(grid); l.add_widget(scroll)
        ok = Button(text="ЗБЕРЕГТИ", size_hint_y=0.15); ok.bind(on_release=lambda x: setattr(self.manager, 'current', 'dash'))
        l.add_widget(ok); self.add_widget(l)
    def save(self, p, g): App.get_running_app().selected_pids[p] = g

class AIScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        l = BoxLayout(orientation='vertical', padding=20, spacing=10)
        self.log = Label(text="AI Online. Введіть код...", font_name=MY_FONT, markup=True, size_hint_y=None, halign='left')
        self.log.bind(texture_size=self.log.setter('size'))
        scroll = ScrollView(); scroll.add_widget(self.log); l.add_widget(scroll)
        self.inp = TextInput(hint_text="PXXXX", size_hint_y=None, height=100, multiline=False)
        l.add_widget(self.inp)
        btns = BoxLayout(size_hint_y=0.15, spacing=10)
        go = Button(text="АНАЛІЗ", bold=True); go.bind(on_release=self.start_ai)
        back = Button(text="НАЗАД"); back.bind(on_release=lambda x: setattr(self.manager, 'current', 'menu'))
        btns.add_widget(go); btns.add_widget(back); l.add_widget(btns); self.add_widget(l)

    def start_ai(self, instance):
        q = self.inp.text.strip()
        if q:
            self.log.text += f"\n\n[b]Ви:[/b] {q}\n[i]Запит до сервісу...[/i]"
            self.inp.text = ""; threading.Thread(target=self.get_ai, args=(q,), daemon=True).start()

    def get_ai(self, q):
        try:
            r = requests.post(AI_URL, json={"contents":[{"parts":[{"text":f"Explain Volvo DTC {q} in Ukrainian."}]}]}, timeout=10)
            txt = r.json()['candidates'][0]['content']['parts'][0]['text']
            Clock.schedule_once(lambda dt: self.done(txt))
        except Exception as e:
            Clock.schedule_once(lambda dt: self.done("[color=ff0000]Відсутнє з'єднання з інтернетом[/color]"))

    def done(self, txt):
        self.log.text = self.log.text.replace("[i]Запит до сервісу...[/i]", "")
        self.log.text += f"\n[b]AI:[/b] {txt}"

class VolvoApp(App):
    selected_pids = {}
    def build(self):
        try:
            sm = ScreenManager(transition=FadeTransition())
            sm.add_widget(MainMenu(name='menu'))
            sm.add_widget(DashScreen(name='dash'))
            sm.add_widget(DashSettingsScreen(name='dash_settings'))
            sm.add_widget(AIScreen(name='ai'))
            # Заглушки
            for n in ['p3', 'svc', 'status', 'settings']: sm.add_widget(Screen(name=n))
            return sm
        except Exception as e:
            log_error(f"Build Error: {traceback.format_exc()}")
            return Label(text="Критична помилка. Перевірте error_log.txt")

if __name__ == '__main__':
    try:
        VolvoApp().run()
    except Exception as e:
        log_error(f"Run Error: {traceback.format_exc()}")
                  
