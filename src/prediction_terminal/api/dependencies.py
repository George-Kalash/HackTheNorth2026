from fastapi import Request

from prediction_terminal.bootstrap import Container


def container(request: Request) -> Container:
    return request.app.state.container
