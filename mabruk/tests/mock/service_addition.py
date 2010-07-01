from mabruk.service import Handler


class AdditionHandler(Handler):
    
    def __init__(self):
        Handler.__init__(self)
        self.expose('add')
    
    def add(self, a, b):
        return a + b


handler = AdditionHandler()