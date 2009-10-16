from ..core import Server, Manager
from threading import Thread
import time
import os
import sys
import socket


class FoobarHandler(Thread):
    
    def __init__(self, conn, server):
        super(FoobarHandler, self).__init__()
        self.conn = conn
        self.server = server
        
        
    def run(self):
        for i in range(0,20):
            try:
                self.conn.send('%s: %s(%s)\n' % (os.getpid(), self.server.value, i))
            except Exception, e:
                break
            time.sleep(1)
        try:
            self.conn.close()
        except Exception, e:
            pass



class FoobarServer(Server):
    
    
    def __init__(self, *args, **kwargs):
        super(FoobarServer, self).__init__(*args, **kwargs)
        self.value = None
    
    
    def setup(self):
        import foobar
        self.value = foobar.VALUE
    
    
    def serve_one(self, conn, addr):
        h = FoobarHandler(conn, self)
        h.start()
        self.waiters.append(h)
        
        
        
if __name__ == "__main__":
    addr = ('127.0.0.1', 1983)
    f = open('foobar.py','w')
    f.write('VALUE="foo"')
    f.close()
    m = Manager()
    m.add_server('foobar', FoobarServer, addr)
    m.start('foobar')
    time.sleep(5)
    f = open('foobar.py','w')
    f.write('VALUE="bar"')
    f.close()
    m.restart('foobar')
    time.sleep(5)
    m.shutdown()