# app core modules
from modules.app.settings import Settings

class Crypt:
    def __init__( self, context ) -> None:
        self.context = context;
        self.settings : Settings = context.settings