class LabelBase:
    @staticmethod
    def register(**kw):
        pass


class Label:
    """بديل خفيف لـ CoreLabel: يقدّر عرض النص تقديراً خطياً."""

    def __init__(self, font_size=16, font_name=None, **kw):
        self.font_size = float(font_size)
        self.font_name = font_name

    def get_extents(self, text):
        return (len(text) * self.font_size * 0.5, self.font_size * 1.2)
