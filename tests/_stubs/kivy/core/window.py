class _Win:
    clearcolor = (0, 0, 0, 1)
    size = (720, 1280)
    def bind(self, **kw): self._cb = kw
    def add_widget(self, *a, **k): pass
    def remove_widget(self, *a, **k): pass


Window = _Win()
