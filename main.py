import threading
import requests
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.core.window import Window

# Android keyboard fix
Window.softinput_mode = 'pan'

# 🔑 ВСТАВ СЮДИ СВІЙ API КЛЮЧ
API_KEY = "AIzaSyC7_ORLA_n8ap4guHX6uOOyBFu-eH_tAqI"

# 🔥 АКТУАЛЬНА МОДЕЛЬ
AI_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={API_KEY}"


class AIScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)

        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        self.log_label = Label(
            text="[b]VOLVO AI ANALYZER[/b]\nВведіть код помилки",
            markup=True,
            size_hint_y=None,
            halign='center',
            font_size='18sp'
        )
        self.log_label.bind(texture_size=self.log_label.setter('size'))

        scroll = ScrollView(size_hint=(1, 0.7))
        scroll.add_widget(self.log_label)
        layout.add_widget(scroll)

        self.inp = TextInput(
            hint_text="P045500",
            size_hint_y=None,
            height=120,
            multiline=False,
            font_size='22sp',
            text="P045500"
        )
        layout.add_widget(self.inp)

        btn_layout = BoxLayout(size_hint_y=0.2, spacing=10)

        btn_analyze = Button(
            text="АНАЛІЗ",
            bold=True,
            background_color=(0.1, 0.5, 0.8, 1)
        )
        btn_analyze.bind(on_release=self.start_analysis)

        btn_back = Button(
            text="НАЗАД",
            on_release=lambda x: setattr(self.manager, 'current', 'menu')
        )

        btn_layout.add_widget(btn_analyze)
        btn_layout.add_widget(btn_back)
        layout.add_widget(btn_layout)

        self.add_widget(layout)

    def start_analysis(self, instance):
        code = self.inp.text.strip().upper()

        if not code:
            self.log_label.text = "Введи код помилки"
            return

        self.log_label.text = f"[b]Аналіз коду {code}...[/b]"

        threading.Thread(
            target=self.run_ai_request,
            args=(code,),
            daemon=True
        ).start()

    def run_ai_request(self, code):
        try:
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": f"""
Ти автоелектрик Volvo P3.

Код: {code}

Дай відповідь українською:
1. Що означає помилка
2. Основні причини
3. Як перевірити мультиметром
4. Як виправити

Коротко і по ділу.
"""
                            }
                        ]
                    }
                ]
            }

            response = requests.post(
                AI_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=20
            )

            if response.status_code == 200:
                res_data = response.json()

                try:
                    answer = res_data['candidates'][0]['content']['parts'][0]['text']
                except:
                    answer = str(res_data)

                self.update_ui(answer)

            else:
                self.update_ui(
                    f"❌ Помилка {response.status_code}\n{response.text[:200]}"
                )

        except Exception as e:
            self.update_ui(f"❌ Збій:\n{str(e)}")

    def update_ui(self, text):
        Clock.schedule_once(
            lambda dt: setattr(self.log_label, 'text', text)
        )


class VolvoApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition())

        menu = Screen(name='menu')

        layout = BoxLayout(
            orientation='vertical',
            padding=50,
            spacing=20
        )

        layout.add_widget(Label(
            text="VOLVO TOOLS",
            font_size='30sp',
            bold=True
        ))

        btn = Button(
            text="AI ДІАГНОСТИКА",
            size_hint_y=0.4,
            on_release=lambda x: setattr(sm, 'current', 'ai')
        )

        layout.add_widget(btn)
        menu.add_widget(layout)

        sm.add_widget(menu)
        sm.add_widget(AIScreen(name='ai'))

        return sm


if __name__ == '__main__':
    VolvoApp().run()
