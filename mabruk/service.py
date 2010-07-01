class MethodNotFound(Exception):
    """Raised when a handler method is not found"""


class Handler:
    """Abstract base class for a service handler
    
    Service handlers expose methods to clients via Service instance.
    """
    
    def __init__(self):
        self.children = {}
        self.methods = {}
        
    def expose(self, method_name):
        """Expose a method through a service"""
        self.methods[method_name] = getattr(self, method_name)
        
    def add_child(self, name, handler):
        """Add a child handler"""
        self.children[name] = handler
        
    def walk_children(self, path=''):
        """Iterate over all child handlers"""
        
        for name, h in self.children.items():
            p = '.'.join([path, name])
            yield h, p
            
            for ch,cp in h.walk_children(p):
                yield ch, cp
        
    def call(self, method_name, *args, **kwargs):
        if not isinstance(method_name, basestring):
            raise ValueError, "<%s> is not a valid method name" % (method_name)
        
        parts = method_name.split('.')
        method = parts.pop()
        handler = self
        
        try:
            for p in parts:
                handler = handler.children[p]
            method = handler.methods[method]
        except KeyError:
            raise MethodNotFound, method_name
        
        return method(*args, **kwargs)


class Service:
    """A provider of some functionality."""
    
    def __init__(self, module):
        if not hasattr(module, 'handler'):
            raise ValueError, "Service module has no handler"
        
        if not isinstance(module.handler, Handler):
            raise TypeError, "Expected an instance of Handler, got %s" % \
                                                (type(module.handler))
        
        for h, path in module.handler.walk_children():
            if not isinstance(h, Handler):
                raise TypeError, "Expected an instance of Handler, got %s at %s" % \
                                                (type(h), path)
        
        self.handler = module.handler
        
    def call(self, method, *args, **kwargs):
        return self.handler.call(method, *args, **kwargs)