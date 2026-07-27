#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""اختبارات المشروع.

تعمل بدون تثبيت Kivy: مجلد ``tests/_stubs`` يوفّر بدائل خفيفة لودجات Kivy
حتى يمكن اختبار منطق التطبيق كاملاً في بيئة CI بلا شاشة ولا OpenGL.
"""

import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "_stubs"))
sys.path.insert(0, ROOT)

# عزل مجلد التخزين حتى لا تلمس الاختبارات بيانات المستخدم
TMP_HOME = tempfile.mkdtemp(prefix="smartquiz-tests-")
os.environ["HOME"] = TMP_HOME

FAILURES = []


def check(name, condition, detail=""):
    if condition:
        print("  ok   %s" % name)
    else:
        print("  FAIL %s %s" % (name, detail))
        FAILURES.append(name)


def section(title):
    print("\n== %s" % title)


# ---------------------------------------------------------------- دعم العربية

def test_arabic():
    section("دعم العربية")
    from arabic_support import ar, reshape

    cases = [
        ("ما عاصمة المغرب؟", "؟ﺏﺮﻐﻤﻟﺍ ﺔﻤﺻﺎﻋ ﺎﻣ"),
        ("الإجابة: ب", "ﺏ :ﺔﺑﺎﺟﻹﺍ"),
        ("السؤال 1 / 12", "12 / 1 ﻝﺍﺆﺴﻟﺍ"),
        ("وقت متبق 09:45", "09:45 ﻖﺒﺘﻣ ﺖﻗﻭ"),
        ("النتيجة: 8 من 10 (80%)", "(80%) 10 ﻦﻣ 8 :ﺔﺠﻴﺘﻨﻟﺍ"),
        ("اختبار Kivy على Android", "Android ﻰﻠﻋ Kivy ﺭﺎﺒﺘﺧﺍ"),
    ]
    for src, expected in cases:
        check("تحويل: %s" % src, ar(src) == expected, "-> %r" % ar(src))

    check("لام‑ألف تُدمج", "\ufefb" in reshape("لا") or "\ufefc" in reshape("لا"))
    check("النص اللاتيني لا يتغيّر", ar("Hello World 123") == "Hello World 123")
    check("النص الفارغ آمن", ar("") == "" and ar(None) is None)
    check("أسطر متعددة", ar("سطر\nسطر") == ar("سطر") + "\n" + ar("سطر"))
    check("لا حروف أساسية متبقية",
          all(not (0x0620 <= ord(c) <= 0x064A) for c in ar("تطبيق الاختبارات")))


# ---------------------------------------------------------------- بنك الأسئلة

def test_data():
    section("بنك الأسئلة والإعدادات")
    import quiz_data as data

    text = data.to_text_bank(data.SAMPLE_BANK)
    check("تصدير/استيراد الصيغة النصية", data.parse_text_bank(text) == data.SAMPLE_BANK)

    legacy = "سؤال: س1\nأ) خ1\nب) خ2\nالإجابة: ب\n\nسؤال: س2\nأ) ن1\nب) ن2\nج) ن3\nالإجابة: ج"
    parsed = data.parse_text_bank(legacy)
    check("قراءة الصيغة القديمة", len(parsed) == 2 and parsed[1]["answer"] == 2, parsed)

    check("تجاهل السؤال الناقص", data.parse_text_bank("سؤال: بلا خيارات") == [])

    bank = data.load_bank()
    check("بذرة الأسئلة الأولية", len(bank) >= 10)

    settings = dict(data.DEFAULT_SETTINGS, question_limit=4, shuffle_questions=True)
    quiz = data.build_quiz(bank, settings)
    check("حد عدد الأسئلة", len(quiz) == 4)

    shuffled = dict(data.DEFAULT_SETTINGS, shuffle_options=True, shuffle_questions=False)
    quiz2 = data.build_quiz(bank, shuffled)
    check("خلط الخيارات يحافظ على الإجابة",
          all(q["options"][q["answer"]] == b["options"][b["answer"]]
              for q, b in zip(quiz2, bank)))
    check("خلط الخيارات لا يغيّر البنك الأصلي",
          bank[0]["options"] == data.load_bank()[0]["options"])


# ---------------------------------------------------------------- منطق التطبيق

def test_app():
    section("منطق التطبيق")
    import main
    import quiz_data as data

    app = main.SmartQuizApp()
    app.build()
    check("كل الشاشات موجودة",
          sorted(app.screens) == ["edit", "history", "home", "manage", "quiz",
                                  "result", "settings"], sorted(app.screens))

    # إضافة سؤال
    app.go_edit(None)
    editor = app.screens["edit"]
    editor.q_field.value = "سؤال اختباري؟"
    editor.opt_fields[0].value = "أول"
    editor.opt_fields[1].value = "ثانٍ"
    editor.pick_answer(1)
    before = len(app.bank)
    editor.save()
    check("حفظ سؤال جديد", len(app.bank) == before + 1)
    added = app.bank[-1]
    check("الإجابة الصحيحة مرتبطة بالنص", added["options"][added["answer"]] == "ثانٍ")

    # خيار فارغ في المنتصف
    app.go_edit(None)
    editor.q_field.value = "س"
    for i, v in enumerate(["A", "B", "", "D"]):
        editor.opt_fields[i].value = v
    editor.pick_answer(3)
    editor.save()
    q = app.bank[-1]
    check("تجاهل الخيارات الفارغة", q["options"] == ["A", "B", "D"])
    check("مؤشر الإجابة يُصحَّح", q["options"][q["answer"]] == "D")

    # رفض المدخلات الناقصة
    count = len(app.bank)
    app.go_edit(None)
    editor.q_field.value = ""
    editor.save()
    check("رفض سؤال بلا نص", len(app.bank) == count)
    app.go_edit(None)
    editor.q_field.value = "س"
    editor.opt_fields[0].value = "وحيد"
    editor.save()
    check("رفض سؤال بخيار واحد", len(app.bank) == count)

    # حذف
    app.screens["manage"].refresh()
    app.bank.pop()
    app.bank.pop()
    app.save_bank()

    # اختبار كامل بإجابات صحيحة
    app.settings.update(question_limit=3, instant_feedback=True,
                        shuffle_questions=False, shuffle_options=False)
    app.start_quiz()
    check("عدد أسئلة الاختبار يحترم الحد", len(app.questions) == 3)
    for i in range(3):
        app.choose(app.questions[i]["answer"])
        app.choose((app.questions[i]["answer"] + 1) % 2)  # يجب تجاهلها بعد التصحيح
        if i < 2:
            app.move(1)
    app.finish_quiz()
    entry = data.load_history()[0]
    check("النتيجة الكاملة", entry["score"] == 3 and entry["total"] == 3, entry)
    check("الانتقال لشاشة النتيجة", app.sm.current == "result")

    # تعديل الإجابة مسموح عند إيقاف التصحيح الفوري
    app.settings["instant_feedback"] = False
    app.start_quiz()
    first = app.questions[0]
    app.choose((first["answer"] + 1) % len(first["options"]))
    app.move(1)
    app.move(-1)
    app.choose(first["answer"])
    check("تغيير الإجابة بدون تصحيح فوري", app.answers[0] == first["answer"])
    check("زر السابق لا يتجاوز البداية", (app.move(-1), app.index)[1] == 0)

    # انتهاء الوقت
    app.start_quiz()
    app.remaining = 1
    app.tick(1)
    check("إنهاء تلقائي عند انتهاء الوقت", app.sm.current == "result")

    # الإعدادات
    settings_screen = app.screens["settings"]
    settings_screen.on_pre_enter()
    for _ in range(60):
        settings_screen.bump("minutes", -5, 1, 180)
    check("الحد الأدنى للمدة", app.settings["minutes"] == 1)
    for _ in range(300):
        settings_screen.bump("question_limit", 5, 0, 500)
    check("الحد الأعلى لعدد الأسئلة", app.settings["question_limit"] == 500)
    settings_screen.reset()
    check("استعادة الافتراضي", app.settings == data.DEFAULT_SETTINGS)

    # السجل وزر الرجوع
    app.screens["history"].refresh()
    app.screens["history"].wipe()
    check("مسح السجل", data.load_history() == [])
    app.go("settings")
    check("زر الرجوع يعود للرئيسية", app.on_key(None, 27) and app.sm.current == "home")
    check("زر الرجوع يخرج من الرئيسية", app.on_key(None, 27) is False)

    # بنك فارغ
    app.bank = []
    app.save_bank()
    app.start_quiz()
    check("لا يبدأ اختبار بلا أسئلة", app.sm.current == "manage")


def main_():
    try:
        test_arabic()
        test_data()
        test_app()
    finally:
        shutil.rmtree(TMP_HOME, ignore_errors=True)
    print("\n" + ("=" * 40))
    if FAILURES:
        print("فشل %d اختبار: %s" % (len(FAILURES), ", ".join(FAILURES)))
        return 1
    print("نجحت كل الاختبارات")
    return 0


if __name__ == "__main__":
    sys.exit(main_())
