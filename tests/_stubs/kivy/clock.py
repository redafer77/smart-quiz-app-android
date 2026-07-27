class _Ev:
    def cancel(self): pass


class _Clock:
    def schedule_interval(self, cb, t): return _Ev()
    def schedule_once(self, cb, t=0): return _Ev()


Clock = _Clock()
