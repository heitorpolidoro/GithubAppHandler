import inspect
import os
from collections import defaultdict
from functools import wraps
from typing import Any, Callable

from github import Github, GithubIntegration, Consts, GithubRetry
from github.Auth import Auth, AppUserAuth, AppAuth, Token
from github.Requester import Requester

from githubapp.events.event import Event


class SignatureError(Exception):
    """Exception when the method has a wrong signature"""

    def __init__(self, method: Callable[[Any], Any], signature):
        """
        Args:
        method (Callable): The method to be validated.
        signature: The signature of the method.
        """
        self.message = (
            f"Method {method.__qualname__}({signature}) signature error. "
            f"The method must accept only one argument of the Event type"
        )


def webhook_handler(event: type[Event]):
    """Decorator to register a method as a webhook handler.

    The method must accept only one argument of the Event type.

    Args:
        event: The event type to handle.

    Returns:
        A decorator that registers the method as a webhook handler.
    """

    def decorator(method):
        """Register the method as a handler for the event"""
        add_handler(event, method)
        return method

    return decorator


def add_handler(event: type[Event], method: Callable):
    """Add a handler for a specific event type.

    The handler must accept only one argument of the Event type.

    Args:
        event: The event type to handle.
        method: The handler method.
    """
    if subclasses := event.__subclasses__():
        for sub_event in subclasses:
            add_handler(sub_event, method)
    else:
        _validate_signature(method)
        handlers[event].append(method)


handlers = defaultdict(list)


def _get_auth(hook_installation_target_id=None, installation_id=None) -> Auth:
    """
    This method is used to get the authentication object for the GitHub API.
    It checks if the environment variables CLIENT_ID, CLIENT_SECRET, and TOKEN are set.
    If they are set, it uses the AppUserAuth object with the CLIENT_ID, CLIENT_SECRET, and TOKEN.
    Otherwise, it uses the AppAuth object with the private key.

    :return: The Auth to be used to authenticate in Github()
    """
    if os.environ.get("CLIENT_ID"):
        return AppUserAuth(
            client_id=os.environ.get("CLIENT_ID"),
            client_secret=os.environ.get("CLIENT_SECRET"),
            token=os.environ.get("TOKEN"),
        )
    if not (private_key := os.getenv("PRIVATE_KEY")):
        with open("private-key.pem", "rb") as key_file:  # pragma no cover
            private_key = key_file.read().decode()
    app_auth = AppAuth(hook_installation_target_id, private_key)
    token = GithubIntegration(auth=app_auth).get_access_token(installation_id).token
    return Token(token)


def handle(headers: dict[str, Any], body: dict[str, Any]):
    """Handle a webhook request.

    The request headers and body are passed to the appropriate handler methods.

    Args:
        headers: The request headers.
        body: The request body.
    """
    event_class = Event.get_event(headers, body)
    hook_installation_target_id = int(headers["X-Github-Hook-Installation-Target-Id"])
    installation_id = int(body["installation"]["id"])

    auth = _get_auth(hook_installation_target_id, installation_id)
    gh = Github(auth=auth)
    requester = Requester(
        auth=auth,
        base_url=Consts.DEFAULT_BASE_URL,
        timeout=Consts.DEFAULT_TIMEOUT,
        user_agent=Consts.DEFAULT_USER_AGENT,
        per_page=Consts.DEFAULT_PER_PAGE,
        verify=True,
        retry=GithubRetry(),
        pool_size=None,
    )

    for handler in handlers.get(event_class, []):
        handler(event_class(gh=gh, requester=requester, headers=headers, **body))


def root(name):
    """Decorator to register a default root handler.

    Args:
        name: The name of the App.

    Returns:
        A decorator that registers the method as the root handler.
    """

    def root_wrapper():
        """A wrapper function to return a default home screen for all Apps"""
        return f"<h1>{name} App up and running!</h1>"

    return wraps(root_wrapper)(root_wrapper)


def _validate_signature(method: Callable[[Any], Any]):
    """Validate the signature of a webhook handler method.

    The method must accept only one argument of the Event type.

    Args:
        method: The method to validate.

    Raises:
        SignatureError: If the method has a wrong signature.
    """
    parameters = inspect.signature(method).parameters
    if len(parameters) != 1:
        signature = ", ".join(parameters.keys())
        raise SignatureError(method, signature)


def handle_with_flask(
    app, use_default_index=True, webhook_endpoint="/", auth_callback_handler=None
) -> None:
    """
    This function registers the webhook_handler with a Flask application.

    Args:
        :param app: The Flask application to register the webhook_handler with.
        :param use_default_index: Whether to register the root handler with the Flask application. Default is False.
        :param webhook_endpoint: The endpoint to register the webhook_handler with. Default is "/".
        :param auth_callback_handler: The function to handle the auth_callback. Default is None.

    Returns:
        None

    Raises:
        TypeError: If the app parameter is not a Flask instance.
    """
    from flask import Flask, request

    if not isinstance(app, Flask):
        raise TypeError("app must be a Flask instance")

    if use_default_index:
        app.route("/", methods=["GET"])(lambda: root(app.name)())

    @app.route(webhook_endpoint, methods=["POST"])
    def webhook() -> str:
        """
        This route is the endpoint that receives the GitHub webhook call.
        It handles the headers and body of the request, and passes them to the webhook_handler for processing.
        """
        headers = dict(request.headers)
        body = request.json
        handle(headers, body)
        return "OK"

    if auth_callback_handler:
        # methods for:
        # - change the parameter to something like: use-user-oauth
        # - save the access_token @user_oauth_registration
        # - delete on installation.delete event @user_oauth_remove
        # - retrieve access_token @user_oauth_retrieve
        # use @, pass as parameters to this function ou as a class?
        @app.route("/auth-callback")
        def auth_callback():
            args = request.args
            code = args.get("code")
            installation_id = args.get("installation_id")
            access_token = (
                Github()
                .get_oauth_application(
                    os.getenv("CLIENT_ID"), os.getenv("CLIENT_SECRET")
                )
                .get_access_token(code)
            )

            auth_callback_handler(installation_id, access_token)
            return "OK"
