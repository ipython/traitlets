#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
"""A simple example of using Application subcommands, for docs"""
from __future__ import annotations

from traitlets.config import Application


class SubApp1(Application):
    pass


class SubApp2(Application):
    @classmethod
    def get_subapp_instance(cls, app: Application) -> Application:
        app.clear_instance()  # since Application is singleton, need to clear main app
        return cls.instance(parent=app)  # type: ignore[no-any-return]


class MainApp(Application):
    subcommands = {
        "subapp1": (SubApp1, "First subapp"),
        "subapp2": (SubApp2.get_subapp_instance, "Second subapp"),
    }


if __name__ == "__main__":
    MainApp.launch_instance()
