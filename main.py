# -*- coding: utf-8 -*-
"""تطبيق الاختبارات الذكي — واجهة Kivy عربية كاملة."""

import os
import time

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import NoTransition, Screen, ScreenManager
from kivy.uix.switch import Switch
from kivy.uix.textinput import TextInput

import quiz_data as data
from arabic_support import ar, register_font

FONT = register_font()

BG = (0.09, 0.11, 0.16, 1)
CARD = (0.15, 0.18, 0.25, 1)
PRIMARY = (0.13, 0.55, 0.85, 1)
SUCCESS = (0.16, 0.65, 0.40, 1)
DANGER = (0.80, 0.25, 0.25, 1)
WARN = (0.90, 0.60, 0.15, 1)
MUTED = (0.35, 0.38, 0.46, 1)
TEXT = (0.93, 0.95, 0.98, 1)

Window.clearcolor = BG


def _font_kwargs(**kw):
    if FONT:
        kw["font_name"] = FONT
    return kw


class L(Label):
    """عنوان عربي جاهز للعرض."""

    def __init__(self, text="", size="16sp", color=TEXT, **kw):
        kw.setdefault("halign", "right")
        kw.setdefault("valign", "middle")
        kw.setdefault("markup", False)
        super().__init__(text=ar(text), font_size=size, color=color, **_font_kwargs(**kw))
        self.bind(size=self._sync)

    def _sync(self, *_):
        self.text_size = self.size

    def set(self, text):
        self.text = ar(text)


class B(Button):
    """زر عربي."""

    def __init__(self, text="", bg=PRIMARY, size="17sp", **kw):
        kw.setdefault("size_hint_y", None)
        kw.setdefault("height", dp(52))
        super().__init__(
            text=ar(text), background_normal="", background_color=bg,
            font_size=size, color=TEXT, **_font_kwargs(**kw)
        )
        self._bg = bg

    def set(self, text):
        self.text = ar(text)

    def tint(self, bg):
        self._bg = bg
        self.background_color = bg


class Field(BoxLayout):
    """حقل إدخال مع معاينة عربية مشكّلة (Kivy لا يشكّل أثناء الكتابة)."""

    def __init__(self, hint="", multiline=False, **kw):
        super().__init__(orientation="vertical", size_hint_y=None,
                         height=dp(76 if multiline else 68), spacing=dp(2), **kw)
        self.input = TextInput(
            hint_text=ar(hint), multiline=multiline, size_hint_y=None,
            height=dp(46), font_size="16sp", halign="right",
            background_color=(1, 1, 1, 1), foreground_color=(0.05, 0.05, 0.08, 1),
            **_font_kwargs()
        )
        self.preview = Label(
            text="", font_size="14sp", color=(0.6, 0.7, 0.85, 1), halign="right",
            valign="middle", size_hint_y=None, height=dp(20), **_font_kwargs()
        )
        self.preview.bind(size=lambda *a: setattr(self.preview, "text_size", self.preview.size))
        self.input.bind(text=self._on_text)
        self.add_widget(self.input)
        self.add_widget(self.preview)

    def _on_text(self, _w, value):
        self.preview.text = ar(value.strip())

    @property
    def value(self):
        return self.input.text.strip()

    @value.setter
    def value(self, v):
        self.input.text = v or ""


def toast(message, title="تنبيه"):
    box = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
    box.add_widget(L(message, size="17sp"))
    btn = B("حسناً", bg=PRIMARY)
    box.add_widget(btn)
    popup = Popup(title=ar(title), content=box, size_hint=(0.88, None), height=dp(220),
                  title_align="right", separator_color=PRIMARY,
                  title_font=FONT or "Roboto", title_size="17sp")
    btn.bind(on_press=popup.dismiss)
    popup.open()
    return popup


def confirm(message, on_yes, title="تأكيد"):
    box = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
    box.add_widget(L(message, size="17sp"))
    row = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(10))
    yes, no = B("نعم", bg=DANGER), B("إلغاء", bg=MUTED)
    row.add_widget(yes)
    row.add_widget(no)
    box.add_widget(row)
    popup = Popup(title=ar(title), content=box, size_hint=(0.88, None), height=dp(230),
                  title_align="right", separator_color=DANGER,
                  title_font=FONT or "Roboto", title_size="17sp")
    no.bind(on_press=popup.dismiss)

    def _yes(*_):
        popup.dismiss()
        on_yes()

    yes.bind(on_press=_yes)
    popup.open()


def scroller(container):
    sv = ScrollView(size_hint=(1, 1), bar_width=dp(4))
    sv.add_widget(container)
    return sv


def column(spacing=8):
    box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(spacing), padding=(0, dp(4)))
    box.bind(minimum_height=box.setter("height"))
    return box


class Base(Screen):
    """شاشة بترويسة موحّدة."""

    def __init__(self, app, title, back_to=None, **kw):
        super().__init__(**kw)
        self.app = app
        self.root_box = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
        header = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        self.title_label = L(title, size="21sp", color=(0.55, 0.78, 1, 1))
        if back_to:
            back = B("رجوع", bg=MUTED, size="15sp", size_hint_x=None, width=dp(90), height=dp(42))
            back.bind(on_press=lambda *_: self.app.go(back_to))
            header.add_widget(back)
        header.add_widget(self.title_label)
        self.root_box.add_widget(header)
        self.body = BoxLayout(orientation="vertical", spacing=dp(10))
        self.root_box.add_widget(self.body)
        self.add_widget(self.root_box)


# --------------------------------------------------------------- الشاشة الرئيسية

class HomeScreen(Base):
    def __init__(self, app, **kw):
        super().__init__(app, "تطبيق الاختبارات الذكي", name="home", **kw)

        self.summary = L("", size="16sp", color=(0.65, 0.72, 0.85, 1),
                         size_hint_y=None, height=dp(56))
        self.body.add_widget(self.summary)

        menu = column(10)
        entries = [
            ("بدء اختبار جديد", SUCCESS, lambda *_: self.app.start_quiz()),
            ("إدارة الأسئلة", PRIMARY, lambda *_: self.app.go("manage")),
            ("إضافة سؤال", WARN, lambda *_: self.app.go("edit")),
            ("الإعدادات", MUTED, lambda *_: self.app.go("settings")),
            ("سجل النتائج", (0.45, 0.30, 0.70, 1), lambda *_: self.app.go("history")),
        ]
        for text, color, cb in entries:
            btn = B(text, bg=color, size="18sp", height=dp(56))
            btn.bind(on_press=cb)
            menu.add_widget(btn)
        self.body.add_widget(scroller(menu))

    def on_pre_enter(self, *_):
        count = len(self.app.bank)
        history = data.load_history()
        best = max((h["score"] / max(h["total"], 1) for h in history), default=0)
        line = "عدد الأسئلة المخزّنة: %d" % count
        if history:
            line += "\nأفضل نتيجة: %d%%   |   عدد المحاولات: %d" % (round(best * 100), len(history))
        self.summary.set(line)


# --------------------------------------------------------------- إدارة الأسئلة

class ManageScreen(Base):
    def __init__(self, app, **kw):
        super().__init__(app, "إدارة الأسئلة", back_to="home", name="manage", **kw)
        self.list_box = column(8)
        self.body.add_widget(scroller(self.list_box))

        row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        add = B("إضافة سؤال", bg=SUCCESS, size="16sp", height=dp(50))
        add.bind(on_press=lambda *_: self.app.go("edit"))
        exp = B("تصدير نصي", bg=PRIMARY, size="16sp", height=dp(50))
        exp.bind(on_press=self.export_text)
        clear = B("حذف الكل", bg=DANGER, size="16sp", height=dp(50))
        clear.bind(on_press=self.clear_all)
        for w in (add, exp, clear):
            row.add_widget(w)
        self.body.add_widget(row)

    def on_pre_enter(self, *_):
        self.refresh()

    def refresh(self):
        self.list_box.clear_widgets()
        if not self.app.bank:
            self.list_box.add_widget(L("لا توجد أسئلة بعد. أضف سؤالك الأول.",
                                       size="16sp", size_hint_y=None, height=dp(60)))
            return
        for index, q in enumerate(self.app.bank):
            card = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(4),
                             padding=(dp(8), dp(6)))
            label = L("%d. %s" % (index + 1, q["question"]), size="16sp",
                      size_hint_y=None, height=dp(44))
            correct = L("الإجابة: %s) %s" % (data.LETTERS[q["answer"]], q["options"][q["answer"]]),
                        size="14sp", color=(0.45, 0.85, 0.6, 1), size_hint_y=None, height=dp(26))
            actions = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
            edit = B("تعديل", bg=PRIMARY, size="14sp", height=dp(40))
            edit.bind(on_press=lambda _w, i=index: self.app.go_edit(i))
            remove = B("حذف", bg=DANGER, size="14sp", height=dp(40))
            remove.bind(on_press=lambda _w, i=index: self.delete(i))
            actions.add_widget(edit)
            actions.add_widget(remove)
            actions.add_widget(BoxLayout())
            for w in (label, correct, actions):
                card.add_widget(w)
            card.height = dp(118)
            self.list_box.add_widget(card)

    def delete(self, index):
        def _do():
            del self.app.bank[index]
            self.app.save_bank()
            self.refresh()

        confirm("هل تريد حذف هذا السؤال؟", _do, "حذف سؤال")

    def clear_all(self, *_):
        def _do():
            self.app.bank = []
            self.app.save_bank()
            self.refresh()

        confirm("سيتم حذف كل الأسئلة نهائياً. متابعة؟", _do, "حذف الكل")

    def export_text(self, *_):
        if not self.app.bank:
            toast("لا توجد أسئلة للتصدير.")
            return
        path = os.path.join(data.storage_dir(), "questions_export.txt")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(data.to_text_bank(self.app.bank))
            toast("تم التصدير إلى:\n%s" % path, "تم")
        except Exception as exc:
            toast("تعذّر التصدير: %s" % exc, "خطأ")


# ------------------------------------------------------------ إضافة/تعديل سؤال

class EditScreen(Base):
    def __init__(self, app, **kw):
        super().__init__(app, "إضافة سؤال", back_to="manage", name="edit", **kw)
        self.index = None

        form = column(6)
        self.q_field = Field("نص السؤال", multiline=True)
        form.add_widget(self.q_field)
        self.opt_fields = []
        for i in range(4):
            hint = "الخيار %s%s" % (data.LETTERS[i], "" if i < 2 else " (اختياري)")
            field = Field(hint)
            self.opt_fields.append(field)
            form.add_widget(field)

        form.add_widget(L("اختر الإجابة الصحيحة:", size="16sp", size_hint_y=None, height=dp(32)))
        self.answer_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        self.answer_buttons = []
        for i in range(4):
            btn = B(data.LETTERS[i], bg=MUTED, size="17sp", height=dp(48))
            btn.bind(on_press=lambda _w, i=i: self.pick_answer(i))
            self.answer_buttons.append(btn)
            self.answer_row.add_widget(btn)
        form.add_widget(self.answer_row)
        self.answer = 0

        save = B("حفظ السؤال", bg=SUCCESS, size="18sp", height=dp(54))
        save.bind(on_press=self.save)
        form.add_widget(save)
        self.body.add_widget(scroller(form))

    def load(self, index=None):
        self.index = index
        if index is None:
            self.title_label.set("إضافة سؤال")
            self.q_field.value = ""
            for field in self.opt_fields:
                field.value = ""
            self.pick_answer(0)
            return
        q = self.app.bank[index]
        self.title_label.set("تعديل السؤال %d" % (index + 1))
        self.q_field.value = q["question"]
        for i, field in enumerate(self.opt_fields):
            field.value = q["options"][i] if i < len(q["options"]) else ""
        self.pick_answer(q["answer"])

    def pick_answer(self, index):
        self.answer = index
        for i, btn in enumerate(self.answer_buttons):
            btn.tint(SUCCESS if i == index else MUTED)

    def save(self, *_):
        question = self.q_field.value
        options = [f.value for f in self.opt_fields]
        filled = [o for o in options if o]
        if not question:
            toast("اكتب نص السؤال أولاً.")
            return
        if len(filled) < 2:
            toast("أدخل خيارين على الأقل.")
            return
        if not options[self.answer]:
            toast("الخيار المحدد كإجابة صحيحة فارغ.")
            return
        correct_text = options[self.answer]
        entry = {"question": question, "options": filled, "answer": filled.index(correct_text)}
        if self.index is None:
            self.app.bank.append(entry)
        else:
            self.app.bank[self.index] = entry
        self.app.save_bank()
        toast("تم الحفظ بنجاح.", "تم")
        self.app.go("manage")


# ------------------------------------------------------------------- الاختبار

class QuizScreen(Base):
    def __init__(self, app, **kw):
        super().__init__(app, "الاختبار", name="quiz", **kw)

        top = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(8))
        self.timer_label = L("00:00", size="18sp", color=(1, 0.8, 0.4, 1), halign="left")
        self.progress_label = L("", size="16sp")
        top.add_widget(self.timer_label)
        top.add_widget(self.progress_label)
        self.body.add_widget(top)

        self.progress = ProgressBar(max=1, value=0, size_hint_y=None, height=dp(6))
        self.body.add_widget(self.progress)

        self.question_label = L("", size="20sp", size_hint_y=None, height=dp(96))
        self.body.add_widget(self.question_label)

        self.options_box = column(8)
        self.body.add_widget(scroller(self.options_box))

        self.feedback = L("", size="16sp", size_hint_y=None, height=dp(28), halign="center")
        self.body.add_widget(self.feedback)

        nav = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8))
        self.prev_btn = B("السابق", bg=MUTED, size="16sp")
        self.prev_btn.bind(on_press=lambda *_: self.app.move(-1))
        self.next_btn = B("التالي", bg=PRIMARY, size="16sp")
        self.next_btn.bind(on_press=lambda *_: self.app.move(1))
        quit_btn = B("إنهاء", bg=DANGER, size="16sp")
        quit_btn.bind(on_press=lambda *_: confirm("إنهاء الاختبار الآن وعرض النتيجة؟",
                                                  self.app.finish_quiz, "إنهاء"))
        for w in (self.prev_btn, self.next_btn, quit_btn):
            nav.add_widget(w)
        self.body.add_widget(nav)
        self.option_buttons = []

    def render(self, index, question, chosen, revealed, total):
        self.progress.max = total
        self.progress.value = index + 1
        self.progress_label.set("السؤال %d من %d" % (index + 1, total))
        self.question_label.set(question["question"])
        self.options_box.clear_widgets()
        self.option_buttons = []
        for i, opt in enumerate(question["options"]):
            btn = B("%s) %s" % (data.LETTERS[i], opt), bg=(0.22, 0.26, 0.34, 1),
                    size="16sp", height=dp(50))
            btn.bind(on_press=lambda _w, i=i: self.app.choose(i))
            self.option_buttons.append(btn)
            self.options_box.add_widget(btn)
        self.paint(question, chosen, revealed)
        self.prev_btn.disabled = index == 0
        self.next_btn.set("إنهاء وعرض النتيجة" if index == total - 1 else "التالي")

    def paint(self, question, chosen, revealed):
        for i, btn in enumerate(self.option_buttons):
            if revealed:
                if i == question["answer"]:
                    btn.tint(SUCCESS)
                elif i == chosen:
                    btn.tint(DANGER)
                else:
                    btn.tint((0.22, 0.26, 0.34, 1))
            else:
                btn.tint(PRIMARY if i == chosen else (0.22, 0.26, 0.34, 1))
        if revealed and chosen is not None:
            ok = chosen == question["answer"]
            self.feedback.set("إجابة صحيحة" if ok else
                              "إجابة خاطئة — الصواب: %s" % question["options"][question["answer"]])
            self.feedback.color = SUCCESS if ok else DANGER
        else:
            self.feedback.set("")

    def set_time(self, seconds):
        minutes, secs = divmod(max(int(seconds), 0), 60)
        self.timer_label.set("%02d:%02d" % (minutes, secs))
        self.timer_label.color = DANGER if seconds <= 30 else (1, 0.8, 0.4, 1)


# -------------------------------------------------------------------- النتيجة

class ResultScreen(Base):
    def __init__(self, app, **kw):
        super().__init__(app, "النتيجة", back_to="home", name="result", **kw)
        self.headline = L("", size="22sp", halign="center", size_hint_y=None, height=dp(110))
        self.body.add_widget(self.headline)
        self.review_box = column(8)
        self.body.add_widget(scroller(self.review_box))
        row = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8))
        retry = B("إعادة الاختبار", bg=SUCCESS, size="16sp")
        retry.bind(on_press=lambda *_: self.app.start_quiz())
        home = B("القائمة الرئيسية", bg=MUTED, size="16sp")
        home.bind(on_press=lambda *_: self.app.go("home"))
        row.add_widget(retry)
        row.add_widget(home)
        self.body.add_widget(row)

    def show(self, questions, answers, score, elapsed):
        total = max(len(questions), 1)
        pct = round(score * 100.0 / total)
        grade = "ممتاز" if pct >= 85 else "جيد جداً" if pct >= 70 else "جيد" if pct >= 50 else "يحتاج مراجعة"
        minutes, secs = divmod(int(elapsed), 60)
        self.headline.set("نتيجتك: %d من %d\nالنسبة: %d%%   —   %s\nالزمن المستغرق: %02d:%02d"
                          % (score, total, pct, grade, minutes, secs))
        self.headline.color = SUCCESS if pct >= 50 else DANGER

        self.review_box.clear_widgets()
        wrong = [(i, q) for i, q in enumerate(questions) if answers.get(i) != q["answer"]]
        if not wrong:
            self.review_box.add_widget(L("أحسنت! كل الإجابات صحيحة.", size="17sp",
                                         color=SUCCESS, size_hint_y=None, height=dp(50)))
            return
        self.review_box.add_widget(L("مراجعة الأخطاء (%d):" % len(wrong), size="17sp",
                                     color=WARN, size_hint_y=None, height=dp(36)))
        for i, q in wrong:
            chosen = answers.get(i)
            card = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(104),
                             spacing=dp(2), padding=(dp(8), dp(4)))
            card.add_widget(L("%d. %s" % (i + 1, q["question"]), size="15sp",
                              size_hint_y=None, height=dp(40)))
            card.add_widget(L("إجابتك: %s" % (q["options"][chosen] if chosen is not None else "بدون إجابة"),
                              size="14sp", color=DANGER, size_hint_y=None, height=dp(26)))
            card.add_widget(L("الصواب: %s" % q["options"][q["answer"]], size="14sp",
                              color=SUCCESS, size_hint_y=None, height=dp(26)))
            self.review_box.add_widget(card)


# ------------------------------------------------------------------ الإعدادات

class SettingsScreen(Base):
    def __init__(self, app, **kw):
        super().__init__(app, "الإعدادات", back_to="home", name="settings", **kw)
        form = column(10)

        self.minutes_label = L("", size="17sp", size_hint_y=None, height=dp(36))
        form.add_widget(self.minutes_label)
        minutes_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        for delta, text, color in ((-5, "- 5", DANGER), (-1, "- 1", MUTED),
                                   (1, "+ 1", MUTED), (5, "+ 5", SUCCESS)):
            btn = B(text, bg=color, size="16sp", height=dp(50))
            btn.bind(on_press=lambda _w, d=delta: self.bump("minutes", d, 1, 180))
            minutes_row.add_widget(btn)
        form.add_widget(minutes_row)

        self.limit_label = L("", size="17sp", size_hint_y=None, height=dp(36))
        form.add_widget(self.limit_label)
        limit_row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        for delta, text, color in ((-5, "- 5", DANGER), (-1, "- 1", MUTED),
                                   (1, "+ 1", MUTED), (5, "+ 5", SUCCESS)):
            btn = B(text, bg=color, size="16sp", height=dp(50))
            btn.bind(on_press=lambda _w, d=delta: self.bump("question_limit", d, 0, 500))
            limit_row.add_widget(btn)
        form.add_widget(limit_row)

        self.switches = {}
        for key, text in (("shuffle_questions", "ترتيب عشوائي للأسئلة"),
                          ("shuffle_options", "ترتيب عشوائي للخيارات"),
                          ("instant_feedback", "إظهار التصحيح فور الاختيار")):
            row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
            switch = Switch(active=True, size_hint_x=None, width=dp(90))
            switch.bind(active=lambda _w, v, k=key: self.toggle(k, v))
            row.add_widget(switch)
            row.add_widget(L(text, size="16sp"))
            self.switches[key] = switch
            form.add_widget(row)

        reset = B("استعادة الإعدادات الافتراضية", bg=WARN, size="16sp", height=dp(52))
        reset.bind(on_press=self.reset)
        form.add_widget(reset)
        self.body.add_widget(scroller(form))

    def on_pre_enter(self, *_):
        self.refresh()

    def refresh(self):
        settings = self.app.settings
        self.minutes_label.set("مدة الاختبار: %d دقيقة" % settings["minutes"])
        limit = settings["question_limit"]
        self.limit_label.set("عدد الأسئلة في الاختبار: %s"
                             % ("كل الأسئلة" if not limit else str(limit)))
        for key, switch in self.switches.items():
            switch.active = bool(settings[key])

    def bump(self, key, delta, low, high):
        self.app.settings[key] = max(low, min(self.app.settings[key] + delta, high))
        self.app.save_settings()
        self.refresh()

    def toggle(self, key, value):
        self.app.settings[key] = bool(value)
        self.app.save_settings()

    def reset(self, *_):
        self.app.settings = dict(data.DEFAULT_SETTINGS)
        self.app.save_settings()
        self.refresh()


# --------------------------------------------------------------------- السجل

class HistoryScreen(Base):
    def __init__(self, app, **kw):
        super().__init__(app, "سجل النتائج", back_to="home", name="history", **kw)
        self.list_box = column(6)
        self.body.add_widget(scroller(self.list_box))
        clear = B("مسح السجل", bg=DANGER, size="16sp", height=dp(50))
        clear.bind(on_press=lambda *_: confirm("مسح كل سجل النتائج؟", self.wipe, "مسح"))
        self.body.add_widget(clear)

    def on_pre_enter(self, *_):
        self.refresh()

    def refresh(self):
        self.list_box.clear_widgets()
        history = data.load_history()
        if not history:
            self.list_box.add_widget(L("لا توجد محاولات سابقة.", size="16sp",
                                       size_hint_y=None, height=dp(50)))
            return
        for item in history:
            pct = round(item["score"] * 100.0 / max(item["total"], 1))
            minutes, secs = divmod(int(item["seconds"]), 60)
            row = L("%s   |   %d/%d   |   %d%%   |   %02d:%02d"
                    % (item["date"], item["score"], item["total"], pct, minutes, secs),
                    size="15sp", size_hint_y=None, height=dp(38),
                    color=SUCCESS if pct >= 50 else DANGER)
            self.list_box.add_widget(row)

    def wipe(self):
        data.clear_history()
        self.refresh()


# ------------------------------------------------------------------- التطبيق

class SmartQuizApp(App):
    def build(self):
        self.title = "تطبيق الاختبارات الذكي"
        self.bank = data.load_bank()
        self.settings = data.load_settings()

        self.questions = []
        self.answers = {}
        self.revealed = set()
        self.index = 0
        self.remaining = 0
        self.started_at = 0
        self.timer_event = None

        self.sm = ScreenManager(transition=NoTransition())
        self.screens = {}
        for cls in (HomeScreen, ManageScreen, EditScreen, QuizScreen, ResultScreen,
                    SettingsScreen, HistoryScreen):
            screen = cls(self)
            self.screens[screen.name] = screen
            self.sm.add_widget(screen)

        Window.bind(on_keyboard=self.on_key)
        return self.sm

    # ------------------------------------------------------------- التنقل
    def go(self, name):
        if name != "quiz":
            self.stop_timer()
        self.sm.current = name

    def go_edit(self, index=None):
        self.screens["edit"].load(index)
        self.go("edit")

    def on_key(self, _window, key, *_args):
        if key != 27:  # زر الرجوع في أندرويد
            return False
        current = self.sm.current
        if current == "home":
            return False
        if current == "quiz":
            confirm("إنهاء الاختبار الآن وعرض النتيجة؟", self.finish_quiz, "إنهاء")
        elif current in ("edit", "manage"):
            self.go("manage" if current == "edit" else "home")
        else:
            self.go("home")
        return True

    # ------------------------------------------------------------- البيانات
    def save_bank(self):
        data.save_bank(self.bank)

    def save_settings(self):
        data.save_settings(self.settings)

    # ------------------------------------------------------------- الاختبار
    def start_quiz(self):
        if not self.bank:
            toast("لا توجد أسئلة. أضف أسئلة أولاً من «إدارة الأسئلة».")
            self.go("manage")
            return
        self.questions = data.build_quiz(self.bank, self.settings)
        self.answers = {}
        self.revealed = set()
        self.index = 0
        self.remaining = self.settings["minutes"] * 60
        self.started_at = time.time()
        self.render()
        self.go("quiz")
        self.start_timer()

    def render(self):
        self.screens["quiz"].render(
            self.index, self.questions[self.index],
            self.answers.get(self.index), self.index in self.revealed,
            len(self.questions),
        )
        self.screens["quiz"].set_time(self.remaining)

    def choose(self, option_index):
        if self.index in self.revealed:
            return
        self.answers[self.index] = option_index
        if self.settings["instant_feedback"]:
            self.revealed.add(self.index)
        self.screens["quiz"].paint(self.questions[self.index], option_index,
                                   self.index in self.revealed)

    def move(self, step):
        new_index = self.index + step
        if new_index < 0:
            return
        if new_index >= len(self.questions):
            self.finish_quiz()
            return
        self.index = new_index
        self.render()

    def start_timer(self):
        self.stop_timer()
        self.timer_event = Clock.schedule_interval(self.tick, 1)

    def stop_timer(self):
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None

    def tick(self, _dt):
        self.remaining -= 1
        self.screens["quiz"].set_time(self.remaining)
        if self.remaining <= 0:
            self.stop_timer()
            toast("انتهى الوقت المخصص للاختبار.", "الوقت")
            self.finish_quiz()

    def finish_quiz(self):
        self.stop_timer()
        score = sum(1 for i, q in enumerate(self.questions)
                    if self.answers.get(i) == q["answer"])
        elapsed = time.time() - self.started_at
        if self.questions:
            data.add_history(score, len(self.questions), elapsed)
        self.screens["result"].show(self.questions, self.answers, score, elapsed)
        self.go("result")

    def on_pause(self):
        return True


if __name__ == "__main__":
    SmartQuizApp().run()
