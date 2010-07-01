from mabruk.service import Handler


class SimpleHierarchyLeaf(Handler):
    
    def __init__(self):
        Handler.__init__(self)
        self.expose('echo')
        
        
    def echo(self, value):
        return value


class SimpleHierarchyRoot(Handler):
    
    def __init__(self):
        Handler.__init__(self)
        self.add_child('example', SimpleHierarchyLeaf())


handler = SimpleHierarchyRoot()