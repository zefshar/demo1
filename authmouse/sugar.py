class Sugar(object):

    def __init__(self, mouse, value):
        self.mouse = mouse
        self.contained = value

    def __getitem__(self, item):
        result = self.contained[item]
        if isinstance(result, type(self.contained)):
            result = Sugar(result)
        return result

    def __getattr__(self, item):
        result = getattr(self.contained, item)
        #if callable(result):
        #    result = Sugar(result)
        return result

    def __repr__(self):
        return repr(self.contained)
