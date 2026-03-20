import requests
from kivy.app import App
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView

# ВСТАВТЕ ВАШ КЛЮЧ ТУТ
API_KEY = "AIzaSyCSZYfcXUtjZdGnk-NfDLwSERlFEDZrbVc"
AI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"


class MainInterface(TabbedPanel):
    def __init__(self, **kwargs):
        super(MainInterface, self).__init__(**kwargs)
        self.do_default_tab = False
        self.tab_pos = 'bottom_mid'

        # ВКЛАДКА 1: DASHBOARD
        self.tab1 = TabbedPanelItem(text='DASHBOARD')
        self.tab1.add_widget(Label(text="Volvo XC60 2017 (B4204T9)\nДані з ThinkDiag 2 з'являться тут...", halign='center'))
        self.add_widget(self.tab1)

        # ВКЛАДКА 2: AI DIAGNOSTIC
        self.tab2 = TabbedPanelItem(text='AI DIAG')
        layout2 = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        self.error_input = TextInput(text='P045500', multiline=False, size_hint_y=None, height=100, font_size='20sp')
        layout2.add_widget(self.error_input)

        self.btn = Button(text="АНАЛІЗУВАТИ ШІ", background_color=(0.1, 0.5, 0.1, 1), size_hint_y=None, height=120)
        self.btn.bind(on_press=self.get_ai_help)
        layout2.add_widget(self.btn)

        self.scroll = ScrollView()
        self.ai_label = Label(text="Введіть код помилки...", text_size=(400, None), halign='left', valign='top')
        self.ai_label.bind(size=lambda s, v: setattr(self.ai_label, 'text_size', (s.width, None)))
        self.scroll.add_widget(self.ai_label)
        layout2.add_widget(self.scroll)

        self.tab2.add_widget(layout2)
        self.add_widget(self.tab2)

    def get_ai_help(self, instance):
        err = self.error_input.text.strip()
        self.ai_label.text = "Зв'язок з сервером..."
        prompt = f"Ти фахівець Volvo. Машина XC60 2017, T6 B4204T9 з Polestar. Помилка: {err}. Поясни причини та що перевірити українською."
        
        try:
            res = requests.post(AI_URL, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=10)
            if res.status_code == 200:
                self.ai_label.text = res.json()['candidates'][0]['content']['parts'][0]['text']
            else:
                self.ai_label.text = f"Помилка API ({res.status_code}). Перевірте ключ."
        except Exception as e:
            self.ai_label.text = f"Помилка мережі: {str(e)}"

class VolvoDiagApp(App):
    def build(self):
        return MainInterface()

if __name__ == "__main__":
    VolvoDiagApp().run()
    
