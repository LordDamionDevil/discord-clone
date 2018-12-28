# size units
KILOBYTES = 1024

# time units
MINUTES = 60
HOURS = 60 * MINUTES


class Color:
    """Custom color class"""
    def __init__(self, val: int):
        self.blue = val & 255
        self.green = (val >> 8) & 255
        self.red = (val >> 16) & 255

    @property
    def value(self):
        """Give the actual RGB integer encoding this color."""
        return int('%02x%02x%02x' % (self.red, self.green, self.blue), 16)

    def __int__(self):
        return self.value


def timestamp_(dt):
    return f'{dt.isoformat()}+00:00' if dt else None
