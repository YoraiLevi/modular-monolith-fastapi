#! /usr/bin/env python3
from fastapi.routing import Mount
from fastapi import FastAPI
import json
from common.importer import import_from_string
from fastapi.openapi.utils import get_openapi
import sys


def merge_dicts(a: dict, b: dict, path=[], resolve_conflicts="Ignore"):
    """https://stackoverflow.com/a/7205107/12603110
    resolve_conflicts: "Ignore" | "Replace" | "Raise"
    """
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge_dicts(a[key], b[key], path + [str(key)])
            elif a[key] != b[key]:
                print(f"Conflict at {key}: {a[key]=}, {b[key]=}", file=sys.stderr)
                if resolve_conflicts == "Ignore":
                    pass
                elif resolve_conflicts == "Replace":
                    a[key] = b[key]
                else:
                    raise Exception("Conflict at " + ".".join(path + [str(key)]))
        else:
            a[key] = b[key]
    return a


def get_mounted_apps(app: FastAPI):
    return [(route.path, route.app) for route in app.router.routes if isinstance(route, Mount)]


def main(openapi_version, title, version, app, get_mounted_apps):
    operationIds = set()
    open_api = get_openapi(
        openapi_version=openapi_version, title=title, version=version, routes=app.routes
    )
    for path in open_api["paths"].values():
        for method in path.values():
            operationIds.add(method["operationId"])
    for path_prefix, subapp in get_mounted_apps(app):
        sub_openapi = get_openapi(
            openapi_version=openapi_version, title=title, version=version, routes=subapp.routes
        )
        sub_openapi["paths"] = {
            f"{path_prefix}{path}": details for path, details in sub_openapi["paths"].items()
        }
        operation_prefix = path_prefix.replace("/", "_")
        if not operation_prefix.endswith("_"):
            operation_prefix += "_"
        if operation_prefix.startswith("_"):
            operation_prefix = operation_prefix[1:]
        for path in sub_openapi["paths"].values():
            for method in path.values():
                if method["operationId"] in operationIds:
                    if method["operationId"].startswith("root_"):
                        new_operation_id = f"{method['operationId']}".replace(
                            "root_", operation_prefix, 1
                        )
                    else:
                        new_operation_id = f"{operation_prefix}{method['operationId']}"
                    print(
                        f"Duplicate operationId: {method['operationId']}, New operationId: {new_operation_id}",
                        file=sys.stderr,
                    )
                    method["operationId"] = new_operation_id
                operationIds.add(method["operationId"])
        open_api = merge_dicts(open_api, sub_openapi)
    print(json.dumps(open_api))


if __name__ == "__main__":
    # make these into commant line arguments
    openapi_version = "3.1.0"
    title = "FastAPI"
    version = "0.1.0"
    app = import_from_string("app.main:app")
    main(openapi_version, title, version, app, get_mounted_apps)
