"""Run the production HTTP WSGI server."""

from gunicorn.app.base import BaseApplication

from .app import create_app
from .config import load_settings


def main():
    settings = load_settings()

    class Server(BaseApplication):
        def load_config(self):
            self.cfg.set("bind", f"{settings.HOST}:{settings.PORT}")
            self.cfg.set("workers", 1)
            self.cfg.set("threads", int(settings.LIMITS.WORKERS))
            self.cfg.set("timeout", 30)
            self.cfg.set("accesslog", None)

        def load(self):
            return create_app(settings)

    Server().run()
