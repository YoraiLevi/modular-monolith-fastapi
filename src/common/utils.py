from fastapi import FastAPI
from fastapi.routing import Mount


def get_mounted_apps(app: FastAPI):
    return [(route.path, route.app) for route in app.router.routes if isinstance(route, Mount)]
