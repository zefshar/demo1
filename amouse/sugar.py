class Sugar(object):
    """Client proxy
    """

    def __init__(self, a_mouse, value):
        self.a_mouse = a_mouse
        self.contained = value

    def __getitem__(self, item):
        result = self.contained[item]
        if isinstance(result, type(self.contained)):
            result = Sugar(result)
        return result

    def __getattr__(self, item):
        result = getattr(self.contained, item)
        if item == 'get':
            return self.a_mouse._authorized_get_request(self.contained, result)
        return result

    def __repr__(self):
        return repr(self.contained)
