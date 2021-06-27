import logging

class BasicTask:

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.args = args;
        self.kwargs = kwargs;
        self.logger = logging.getLogger(str(self.__class__))

    def execute(self):
        """
        Do something valuable
        """
        pass