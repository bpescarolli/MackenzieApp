import os
from kaki.app import App
from kivy.uix.screenmanager import ScreenManager
from kivymd.app import MDApp

from telas.telaPrincipal.telaPrincipal import TelaPrincipal
from telas.telaUSB.telaUSB import TelaUSB
from telas.telaBLE.telaBLE import TelaBLE
from telas.telaNFC.telaNFC import TelaNFC


class LiveApp(MDApp, App):
    DEBUG = 1

    KV_FILES = {
        os.path.join(os.getcwd(), "telas/screenmanager.kv"),
        os.path.join(os.getcwd(), "telas/telaPrincipal/telaPrincipal.kv"),
        os.path.join(os.getcwd(), "telas/telaUSB/telaUSB.kv"),
        os.path.join(os.getcwd(), "telas/telaBLE/telaBLE.kv"),
        os.path.join(os.getcwd(), "telas/telaNFC/telaNFC.kv"),
        os.path.join(os.getcwd(), "telas/telaNFC/telaNFC.kv"),
    }

    CLASSES = {
        "MainScreenManager": "telas.screenmanager",
        "TelaPrincipal": "telas.telaPrincipal.telaPrincipal",
        "TelaUSB": "telas.telaUSB.telaUSB",
        "TelaBLE": "telas.telaBLE.telaBLE",
        "TelaNFC": "telas.telaNFC.telaNFC",
    }

    AUTORELOADER_PATHS = [
        (".", {"recursive": True}),
    ]

    def build_app(self):
        app = MDApp.get_running_app()
        app.sm = ScreenManager()
        app.theme_cls.material_style = "Light"
        app.sm.add_widget(TelaPrincipal())
        app.sm.add_widget(TelaUSB())
        app.sm.add_widget(TelaBLE())
        app.sm.add_widget(TelaNFC())
        return app.sm

if __name__ == "__main__":
    LiveApp().run()
