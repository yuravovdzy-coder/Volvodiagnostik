import os
import sys

# Спроба перехопити помилку ще до завантаження Kivy
try:
    from kivy.app import App
    from kivy.uix.label import Label
    from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
    from kivy.core.text import LabelBase
    from kivy.clock import Clock
    import requests
    import threading
except Exception as e:
    # Якщо вилітає тут - значить проблема в requirements (бібліотеках)
    print(f"CRITICAL IMPORT ERROR: {e}")

class ErrorScreen(Screen):
    def __init__(self, error_text, **kw):
        super().__init__(**kw)
        self.add_widget(Label(text=f"Критична помилка:\n{error_text}", halign='center'))

class VolvoApp(App):
    def build(self):
        try:
            # Спроба зареєструвати шрифти безпечно
            try:
                LabelBase.register(name='Arial', fn_regular='ArialRegular.ttf', fn_bold='ArialBold.ttf')
                self.font = 'Arial'
            except:
                self.font = 'Roboto'

            sm = ScreenManager(transition=FadeTransition())
            
            # Головний екран (мінімалістичний для тесту)
            main_screen = Screen(name='menu')
            lbl = Label(text="VOLVO DIAGNOSTIC\n(Працює)", font_name=self.font, font_size='24sp', halign='center')
            main_screen.add_widget(lbl)
            
            sm.add_widget(main_screen)
            return sm
        except Exception as e:
            return Label(text=f"Помилка інтерфейсу:\n{str(e)}")

if __name__ == '__main__':
    try:
        VolvoApp().run()
    except Exception as e:
        # Запис помилки у файл на телефоні, якщо все впало
        with open("crash_log.txt", "w") as f:
            f.write(str(e))
            
