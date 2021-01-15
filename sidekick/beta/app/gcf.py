import json
import os
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Any, Tuple

from .cli import main as _main, parse_value
from .function_wrapper import wrap_function
from ...functions import signature
from ...proxy import import_later


# if TYPE_CHECKING or 1:
import flask
import functions_framework as runtime
from functions_framework import _http as server
import jsonrpc

# else:
#     jsonrpc = import_later("jsonrpc", pypi="sidekick[app.gcf]")
#     runtime = import_later("functions_framework", pypi="sidekick[app.gcf]")
#     server = import_later("functions_framework._http", pypi="sidekick[app.gcf]")
#     flask = import_later("flask", pypi="sidekick[app.gcf]")

DEFAULT_HANDLERS = {}
HTTP_METHODS = ("GET", "POST", "PATCH")
register_handler = lambda key: lambda fn: DEFAULT_HANDLERS.setdefault(key, fn)


def run(
    func: callable,
    signature_type="http",
    host="0.0.0.0",
    port=8080,
    debug=True,
    path=None,
    handlers=None,
    methods=HTTP_METHODS,
):
    """
    Run function in a "functions_framework" runtime. This emulates the GCF
    emulator locally.
    """

    methods = HTTP_METHODS if methods is None else methods
    handler_methods = bind_handlers(func, handlers, methods)

    def cloud_function(request: "flask.Request"):
        handler = get_handler(request, handler_methods)
        return handler(request, handler_methods)

    app = _create_app(cloud_function, signature_type=signature_type, path=path)
    server.create_server(app, debug).run(host, port)


def deploy(func: callable):
    """
    Deploy function to Google Cloud Platform.
    """


#
# Wrap function
#
def bind_handlers(func_or_mod, handlers, methods):
    """
    Receive a function and a mapping from {(mime, method): handler_factory}
    and return a populated mapping of handlers.
    """
    if handlers is None:
        handlers = DEFAULT_HANDLERS

    res = {k: mk_handler(func_or_mod) for k, mk_handler in handlers.items()}
    for k, v in list(res.items()):
        if isinstance(k, str):
            res.update({(k, m): v for m in methods if (k, m) not in res})

    if None in handlers:
        default_handler = handlers[None]
        for m in methods:
            res.setdefault((None, m), default_handler)

    return res


def get_handler(request: "flask.Request", handlers: Dict[Tuple[str, str], callable]):
    """
    Get handler from request.

    Handler is a function that receives a request and return a response.
    """
    method = request.method
    for mime in request.accept_mimetypes:
        try:
            fn = handlers[mime[0], method]
            print(mime[0], method)
            return fn
        except KeyError:
            pass
    try:
        return handlers[None, method]
    except KeyError:
        msg = f"Invalid method/mime: {request.method}, {request.accept_mimetypes}"
        return lambda *_: flask.Response(msg, 500)


@register_handler("application/json")
def jsonrpc_handler(func, info=True):
    dispatcher = jsonrpc_dispatcher(func, info)

    def handler(request, _):
        response = jsonrpc.JSONRPCResponseManager.handle(request.data, dispatcher)
        return flask.Response(response.json, mimetype="application/json")

    return handler


@register_handler(("application/json", "GET"))
def jsonrpc_handler_GET(func, info=True):
    dispatcher = jsonrpc_dispatcher(func, info)

    def handler(request: "flask.Request", _):
        params = dict(request.args)
        rpc_id = params.pop("json-rpc-id", 0)
        payload = {
            "jsonrpc": "2.0",
            "method": request.path.strip("/"),
            "params": {k: parse_value(v) for k, v in params.items()},
            "id": rpc_id,
        }
        request = jsonrpc.jsonrpc.JSONRPCRequest.from_data(payload)
        response = jsonrpc.JSONRPCResponseManager.handle_request(request, dispatcher)
        data = f"<h1>JSON response</h1><pre>{json.dumps(response.data, indent=2)}</pre>"
        return flask.Response(data, mimetype="text/html")

    return handler


@lru_cache(32)
def jsonrpc_dispatcher(func, info=True) -> "jsonrpc.Dispatcher":
    dispatcher = jsonrpc.Dispatcher()
    if callable(func):
        dispatcher[func.__name__] = wrap_function(func)
    else:
        raise NotImplementedError

    if info:
        info = lambda: {k: spec(fn) for k, fn in dispatcher.items()}
        dispatcher.setdefault("info", lru_cache(1)(info))

    return dispatcher


@register_handler("text/html")
def html_handler(func):
    """
    Generic handler that redirects to JSON.
    """

    def handler(request, handlers):
        fn = handlers["application/json", request.method]
        return fn(request, handlers)

    return handler


def arguments(request: "flask.Request", func) -> Dict[str, Any]:
    """
    Read arguments from request and return a mapping that will be passed to
    function.
    """
    return {k: parse_value(v) for k, v in request.values.items()}


def response(request: "flask.Request", result: Any) -> "flask.Response":
    """
    Compute flask Response for the given value.
    """
    return flask.make_response(str(result))


@lru_cache(64)
def spec(func):
    """
    A JSON-like element with function specification.
    """
    # TODO: convert to valid RPC-JSON.
    sig = signature(func)
    return {
        "name": func.__name__,
        "args": dict(zip(sig.argnames(), map(repr_type, sig.args()))),
    }


@lru_cache(64)
def repr_type(t):
    """
    Convert type to string representation.
    """
    return str(t)


#
# This was copied and adapted from functions_framework
#
def _create_app(function, signature_type=None, path=None):
    path = Path(path or os.getcwd())
    template_folder = str(path / "templates")

    # Set the environment variable if it wasn't already
    os.environ["FUNCTION_SIGNATURE_TYPE"] = signature_type
    os.environ["TARGET"] = target = function.__name__
    os.environ["SOURCE"] = "<string>"

    app = flask.Flask(target, template_folder=template_folder)
    app.config["MAX_CONTENT_LENGTH"] = runtime.MAX_CONTENT_LENGTH

    # Mount the function at the root. Support GCF's default path behavior
    # Modify the url_map and view_functions directly here instead of using
    # add_url_rule in order to create endpoints that route all methods
    import werkzeug

    if signature_type == "http":
        app.url_map.add(
            werkzeug.routing.Rule("/", defaults={"path": ""}, endpoint="run")
        )
        app.url_map.add(werkzeug.routing.Rule("/robots.txt", endpoint="error"))
        app.url_map.add(werkzeug.routing.Rule("/favicon.ico", endpoint="error"))
        app.url_map.add(werkzeug.routing.Rule("/<path:path>", endpoint="run"))
        app.view_functions["run"] = runtime._http_view_func_wrapper(
            function, flask.request
        )
        app.view_functions["error"] = lambda: flask.abort(404, description="Not Found")
        app.after_request(runtime.read_request)
    elif signature_type == "event" or signature_type == "cloudevent":
        app.url_map.add(
            werkzeug.routing.Rule(
                "/", defaults={"path": ""}, endpoint=signature_type, methods=["POST"]
            )
        )
        app.url_map.add(
            werkzeug.routing.Rule(
                "/<path:path>", endpoint=signature_type, methods=["POST"]
            )
        )

        # Add a dummy endpoint for GET /
        app.url_map.add(werkzeug.routing.Rule("/", endpoint="get", methods=["GET"]))
        app.view_functions["get"] = lambda: ""

        # Add the view functions
        app.view_functions["event"] = runtime._event_view_func_wrapper(
            function, flask.request
        )
        app.view_functions["cloudevent"] = runtime._cloudevent_view_func_wrapper(
            function, flask.request
        )
    else:
        raise runtime.FunctionsFrameworkException(
            "Invalid signature type: {signature_type}".format(
                signature_type=signature_type
            )
        )

    return app


if __name__ == "__main__":
    _main(run)
