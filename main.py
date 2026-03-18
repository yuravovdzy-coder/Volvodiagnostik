from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
import os

class VolvoApp(App):
    def build(self):
        self.db = self.load_data()
        
        # Головний екран
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Заголовок
        self.layout.add_widget(Label(text="VOLVO SMART ASSISTANT", size_hint_y=0.1, font_size='20sp'))
        
        # Поле вводу
        self.input = TextInput(hint_text="Введіть P# або назву...", multiline=False, size_hint_y=0.1)
        self.layout.add_widget(self.input)
        
        # Кнопка пошуку
        btn_search = Button(text="ЗНАЙТИ", size_hint_y=0.1, background_color=(0.1, 0.5, 0.8, 1))
        btn_search.bind(on_press=self.search)
        self.layout.add_widget(btn_search)
        
        # Область результату зі скролом
        self.scroll = ScrollView(size_hint_y=0.6)
        self.result = Label(text="Результат з'явиться тут", text_size=(None, None), halign='left', valign='top')
        self.result.bind(size=lambda s, w: setattr(self.result, 'text_size', (s.width, None)))
        self.scroll.add_widget(self.result)
        self.layout.add_widget(self.scroll)
        
        return self.layout

    def load_data(self):
        database = {}
        path = os.path.join(os.path.dirname(__file__), 'p3_data.txt')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read().split('P#')
                for item in content:
                    if not item.strip(): continue
                    lines = item.strip().split('\n')
                    code = lines[0].split()[0]
                    desc = " ".join([l.strip() for l in lines[1:]])
                    database[code] = desc
        return database

    def search(self, instance):
        query = self.input.text.lower()
        found = False
        for code, desc in self.db.items():
            if query == code.lower() or query in desc.lower():
                self.result.text = f"P#{code}:\n\n{desc}"
                found = True
                break
        if not found:
            self.result.text = "❌ Нічого не знайдено"

if __name__ == "__main__":
    VolvoApp().run()
