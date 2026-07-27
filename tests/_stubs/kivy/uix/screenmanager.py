from kivy._stub import Widget as _W


class Screen(_W):
    def __init__(self, **kw):
        self.name = kw.pop("name", "")
        super().__init__(**kw)
    def on_pre_enter(self, *a): pass


class NoTransition:
    def __init__(self, **kw): pass


class ScreenManager(_W):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.screens = []
        self._current = None
    def add_widget(self, w, *a, **k):
        super().add_widget(w); self.screens.append(w)
        if self._current is None: self._current = w.name
    @property
    def current(self): return self._current
    @current.setter
    def current(self, name):
        self._current = name
        for s in self.screens:
            if s.name == name: s.on_pre_enter()
