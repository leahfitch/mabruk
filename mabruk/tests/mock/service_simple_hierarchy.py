from mabruk.service import Handler

class SimpleHierarchyBar(Handler):
    
    def __init__(self):
        Handler.__init__(self)
        self.expose('echo')
        
        
    def echo(self, value):
        return value


class SimpleHierarchyFoo(Handler):
    
    def __init__(self):
        Handler.__init__(self)
        self.add_child('bar', SimpleHierarchyBar())


class SimpleHierarchyLeaf(Handler):
    
    def __init__(self):
        Handler.__init__(self)
        self.add_child('foo', SimpleHierarchyFoo())
        self.expose('echo')
        
        
    def echo(self, value):
        return value


class SimpleHierarchyRoot(Handler):
    
    def __init__(self):
        Handler.__init__(self)
        self.add_child('example', SimpleHierarchyLeaf())


handler = SimpleHierarchyRoot()