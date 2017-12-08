from datetime import tzinfo, timedelta


class Zone(tzinfo):
    def __init__(self, offset, is_dst, name):
        self.offset = offset
        self.is_dst = is_dst
        self.name = name

    def utcoffset(self, dt):
        return timedelta(hours=self.offset) + self.dst(dt)

    def dst(self, dt):
        return timedelta(hours=1) if self.is_dst else timedelta(0)

    def tzname(self, dt):
        return self.name
