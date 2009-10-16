from ..servers.wsgi import WSGIServer
from ..core import Manager


def app(environ, start_response):
    start_response('200 OK', [('Content-Type','text/plain')])
    return ["Always look on the bright side of life."]


manager = Manager()
manager.add_server('wsgi-example', WSGIServer, ('127.0.0.1', 8585), app)
manager.startall()


if __name__ == "__main__":
    pass