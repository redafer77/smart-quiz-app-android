import re

_UNIT = re.compile(r"^([\d.]+)(sp|dp|px|pt|in|mm|cm)?$")


def _num(value):
    """يحاكي تحويل Kivy لقيم مثل '16sp' إلى بكسل."""
    if isinstance(value, str):
        m = _UNIT.match(value.strip())
        if m:
            return float(m.group(1))
    return value


class Widget:
    def __init__(self, **kw):
        self.children = []
        self.parent = None
        self.text = kw.pop("text", "")
        self.disabled = False
        self.width = 320.0
        self.height = 48.0
        self.font_size = _num(kw.pop("font_size", 16))
        self.font_name = kw.pop("font_name", None)
        for k, v in kw.items():
            setattr(self, k, _num(v) if k in ("height", "width") else v)

    @property
    def size(self):
        return (self.width, self.height)

    @size.setter
    def size(self, value):
        self.width, self.height = value

    def add_widget(self, w, *a, **k):
        self.children.insert(0, w)
        w.parent = self

    def remove_widget(self, w, *a, **k):
        if w in self.children:
            self.children.remove(w)

    def clear_widgets(self, *a, **k):
        self.children = []

    def bind(self, **kw):
        self._bound = kw

    def unbind(self, **kw):
        pass

    def fbind(self, *a, **k):
        pass

    def funbind(self, *a, **k):
        pass

    def setter(self, name):
        return lambda *a: None

    def getter(self, name):
        return lambda *a: None

    def dispatch(self, *a, **k):
        pass

    def open(self, *a, **k):
        self.opened = True

    def dismiss(self, *a, **k):
        self.opened = False
