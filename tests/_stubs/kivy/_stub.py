class Widget:
    def __init__(self, **kw):
        self.children = []
        self.parent = None
        self.text = kw.pop("text", "")
        self.size = (100, 100)
        self.disabled = False
        for k, v in kw.items():
            setattr(self, k, v)
    def add_widget(self, w, *a, **k):
        self.children.insert(0, w); w.parent = self
    def remove_widget(self, w, *a, **k):
        if w in self.children: self.children.remove(w)
    def clear_widgets(self, *a, **k): self.children = []
    def bind(self, **kw): self._bound = kw
    def unbind(self, **kw): pass
    def fbind(self, *a, **k): pass
    def funbind(self, *a, **k): pass
    def setter(self, name): return lambda *a: None
    def getter(self, name): return lambda *a: None
    def dispatch(self, *a, **k): pass
    def open(self, *a, **k): self.opened = True
    def dismiss(self, *a, **k): self.opened = False
