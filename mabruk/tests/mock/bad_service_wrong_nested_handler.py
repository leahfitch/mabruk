from mabruk.service import Handler

class WrongNestedHandler(Handler):
    
    def __init__(self):
        Handler.__init__(self)
        self.add_child('foo', 23)
        
handler = WrongNestedHandler()