from multiprocessing import Process, Pipe, log_to_stderr, get_logger
import logging
import errno
import socket
import signal
import os
import errno
from threading import Thread

async_socket = None
try:
    from eventlet.green import socket as async_socket
    from eventlet import coros
    
    class Waiter(object):
        
        def __init__(self, evt):
            self.evt = evt
            
        def join(self):
            self.evt.wait()
    
    def async_spawn(f, *args, **kwargs):
        return coros.execute(f, *args, **kwargs)
        
except ImportError:
    pass

log_to_stderr(logging.DEBUG)
log = get_logger()


def _create_bound_socket(sock_cls, addr):
    s = sock_cls(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(addr)
    s.listen(1)
    return s
    
    
def create_listener(addr):
    return _create_bound_socket(socket.socket, addr)
    
    
def create_async_listener(addr):
    return _create_bound_socket(async_socket.socket, addr)



def plat_specific_errors(*errnames):
    """Return error numbers for all errors in errnames on this platform.
    
    The 'errno' module contains different global constants depending on
    the specific platform (OS). This function will return the list of
    numeric values for a given list of potential names.
    """
    errno_names = dir(errno)
    nums = [getattr(errno, k) for k in errnames if k in errno_names]
    # de-dupe the list
    return dict.fromkeys(nums).keys()

socket_errors_to_ignore = plat_specific_errors(
    "EPIPE",
    "EBADF", "WSAEBADF",
    "ENOTSOCK", "WSAENOTSOCK",
    "ETIMEDOUT", "WSAETIMEDOUT",
    "ECONNREFUSED", "WSAECONNREFUSED",
    "ECONNRESET", "WSAECONNRESET",
    "ECONNABORTED", "WSAECONNABORTED",
    "ENETRESET", "WSAENETRESET",
    "EHOSTDOWN", "EHOSTUNREACH",
    )
socket_errors_to_ignore.append("timed out")


class Listener(object):
    """Listens for incoming connections and passes them to a handler"""
    
    
    def __init__(self, sock, handler):
        self.sock = sock
        self.handler = handler
        self.running = False
        self.waiter = None
        
        
    def start(self):
        """Start listening"""
        if async_socket and isinstance(self.sock, async_socket.socket):
            self.waiter = async_spawn(self.run)
        else:
            self.waiter = Thread(target=self.run)
            self.waiter.start()
        
        
    def run(self):
        self.running = True
        while self.running:
            conn, addr = self.sock.accept()
            self.handler(conn,addr)
    
    
    def stop(self):
        #thanks cherrpy
        
        if not self.running:
            return
            
        self.running = False
        
        # Touch our own socket to make accept() return immediately.
        try:
            host, port = self.sock.getsockname()[:2]
        except socket.error, x:
            if x.args[0] not in socket_errors_to_ignore:
                raise
        else:
            # Note that we're explicitly NOT using AI_PASSIVE,
            # here, because we want an actual IP to touch.
            # localhost won't work if we've bound to a public IP,
            # but it will if we bound to '0.0.0.0' (INADDR_ANY).
            for res in socket.getaddrinfo(host, port, socket.AF_UNSPEC,
                                          socket.SOCK_STREAM):
                af, socktype, proto, canonname, sa = res
                s = None
                try:
                    s = socket.socket(af, socktype, proto)
                    # See http://groups.google.com/group/cherrypy-users/
                    #        browse_frm/thread/bbfe5eb39c904fe0
                    s.settimeout(1.0)
                    s.connect((host, port))
                    s.close()
                except socket.error:
                    if s:
                        s.close()
                        
                        
    def join(self):
        self.waiter.join()



class Server(object):
    """Handles incoming connections and responds to messages from Manager"""
    
    
    def __init__(self, sock):
        self.listener = Listener(sock, self.serve_one)
        self.waiters = []
        
        
    def start(self, pipe):
        """Wait for messages from Manager and handle them"""
        while 1:
            msg, args = pipe.recv()
            
            log.debug('Got message: %s', msg)
            
            if msg == 'stop':
                self.stop()
                pipe.send(None)
            
            if msg == 'join':
                self.join()
                pipe.send(None)
                break
            
            if hasattr(self, 'handle_'+msg):
                handler = getattr(self, 'handle_'+msg)
                pipe.send(handler(*args))
    
    
    def stop(self):
        """Stop listening"""
        self.listener.stop()
        self.listener.join()
        
        
    def join(self):
        """Wait for any registered waiters, i.e. anything with a join() method"""
        for w in self.waiters:
            w.join()
    
    
    def add_waiter(self, w):
        self.waiters.append(w)
    
    
    def serve_one(self, conn, addr):
        """Handle a single connection"""
        raise NotImplementedError
    
    
    def setup(self):
        """Run server initialization, if any"""
    
    
    def handle_setup(self):
        self.setup()
    
    
    def handle_serve(self):
        self.listener.start()
        
        
        
class Manager(object):
    """Manages servers"""
    
    def __init__(self):
        self.servers = {}
        self.waiters = []
        signal.signal(signal.SIGTERM, self.handle_TERM)
        signal.signal(signal.SIGHUP, self.handle_HUP)
        log.info('Manager has PID %s', os.getpid())
    
    
    def add_server(self, name, cls, sock_or_addr, *args, **kwargs):
        """Add a named server description"""
        
        if isinstance(sock_or_addr, tuple):
            sock = create_listener(sock_or_addr)
        else:
            sock = sock_or_addr
        
        log.debug('Adding server: %s, %s, %s, %s, %s', name, cls, sock.getsockname(), args, kwargs)
        
        self.servers[name] = {
            'cls': cls,
            'args': (args, kwargs),
            'sock': sock,
            'pipe': None,
            'proc': None
        }
        
        
    def start(self, name):
        """Start the server identified by name"""
        server = self.servers[name]
        
        if server['proc'] and server['proc'].is_alive():
            log.info("%s already started.", name)
            return
        
        log.info("Starting %s.", name)
        
        s = server['cls'](server['sock'], *server['args'][0], **server['args'][1])
        server['pipe'] = Pipe()
        server['proc'] = Process(target=s.start, args=[server['pipe'][1]])
        server['proc'].start()
        
        server['pipe'][0].send(('setup', []))
        server['pipe'][0].recv()
        server['pipe'][0].send(('serve', []))
        server['pipe'][0].recv()
        
        self.waiters.append(server['proc'])
        
        
    def stop(self, name):
        """Stop the server identified by name"""
        server = self.servers[name]
        
        if not server['proc'] or not server['proc'].is_alive():
            log.info("%s is not running.", name)
            return
        
        log.info('Stopping %s.', name)
        
        server['pipe'][0].send(('stop', []))
        server['pipe'][0].recv()
        server['pipe'][0].send(('join', []))
        server['pipe'][0].recv()
        
        
    def restart(self, name):
        """Gracefully restart the server identified by name"""
        server = self.servers[name]
        
        if not server['proc'] or not server['proc'].is_alive():
            log.info("%s is not running.", name)
            self.start(name)
            return
        
        log.info('Restarting %s.', name)
        
        oldproc = server['proc']
        oldpipe = server['pipe']
        
        s = server['cls'](server['sock'], *server['args'][0], **server['args'][1])
        server['pipe'] = Pipe()
        server['proc'] = Process(target=s.start, args=[server['pipe'][1]])
        server['proc'].start()
        
        server['pipe'][0].send(('setup', []))
        server['pipe'][0].recv()
        
        oldpipe[0].send(('stop',[]))
        oldpipe[0].recv()
        
        server['pipe'][0].send(('serve', []))
        server['pipe'][0].recv()
        
        oldpipe[0].send(('join',[]))
        oldpipe[0].recv()
        
        self.waiters.append(server['proc'])
        
        
    def startall(self):
        """Start all registered servers and wait until they are complete"""
        for name in self.servers:
            self.start(name)
        self._wait()
        
        
    def restartall(self):
        """Gracefully restart all servers"""
        for name in self.servers:
            self.restart(name)
        self._wait()
        
        
    def shutdown(self):
        """Gracefully stop all servers and exit"""
        for name in self.servers:
            self.stop(name)
        
        
    def _wait(self):
        try:
            for w in self.waiters:
                w.join()
        except OSError, e:
            if e.errno != errno.EINTR:
                raise
        
        
    def handle_TERM(self, signo, frame):
        """Handle a TERM signal"""
        self.shutdown()
        
        
    def handle_HUP(self, signo, frame):
        """Handle a HUP signal"""
        self.restartall()
        