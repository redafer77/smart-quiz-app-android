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


def test_wrap():
    section("التفاف الأسطر")
    from arabic_support import ar, wrap

    # قياس تقريبي: عرض ثابت لكل حرف
    measure = lambda t: len(t) * 10.0
    text = "من هو العالم المسلم الذي وضع أسس علم الجبر وكتب كتاب الجبر والمقابلة في بغداد؟"
    lines = wrap(text, 200, measure).split("\n")

    check("انقسم إلى عدة أسطر", len(lines) > 1, len(lines))
    check("كل سطر ضمن العرض", all(measure(l) <= 200 for l in lines[:-1]))

    # الترتيب المنطقي محفوظ: أول كلمة منطقية في أول سطر
    first_word = ar("من")
    check("أول سطر يبدأ ببداية الجملة", first_word in lines[0], lines[0])
    last_word = ar("بغداد؟")
    check("آخر سطر يحوي نهاية الجملة", last_word in lines[-1], lines[-1])

    check("الأسطر الأصلية محفوظة", len(wrap("سطر أول\nسطر ثانٍ", 10000, measure).split("\n")) == 2)
    long_word = "كلمةطويلةجداااااااا"
    check("كلمة أطول من السطر لا تُفقد", wrap(long_word, 20, measure) == ar(long_word))
    check("عرض غير صالح يتراجع لـ ar()", wrap("مرحبا", 0, measure) == ar("مرحبا"))
    check("نص فارغ آمن", wrap("", 100, measure) == "")


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

    # الدمج والاستيراد
    merged, added = data.merge_bank(list(bank), data.default_bank())
    check("الدمج يتجاهل المكرر", added == 0 and len(merged) == len(bank))
    merged, added = data.merge_bank([], [{"question": "س", "options": ["أ", "ب"], "answer": 1},
                                         {"question": "س", "options": ["ج", "د"], "answer": 0}])
    check("الدمج يزيل التكرار داخل الدفعة", added == 1 and len(merged) == 1)

    path = os.path.join(data.storage_dir(), "questions_import.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("سؤال: سؤال مستورد؟\nأ) لا\nب) نعم\nالإجابة: ب\n")
    check("اكتشاف ملف الاستيراد", path in data.import_candidates())
    imported = data.import_from_file(path)
    check("قراءة ملف الاستيراد",
          len(imported) == 1 and imported[0]["options"][imported[0]["answer"]] == "نعم", imported)
    os.remove(path)

    check("مسارات التصدير غير فارغة", len(data.export_targets()) >= 1)
    check("shared_dir لا يفشل على سطح المكتب", data.shared_dir() is None)


# ---------------------------------------------------------------- منطق التطبيق

def test_categories():
    section("الفئات والمستويات")
    import quiz_data as data

    bank = data.default_bank()
    cats = data.available_categories(bank)
    check("البنك المضمَّن كبير", len(bank) >= 500, len(bank))
    check("عدة فئات", len(cats) >= 5, [c[0] for c in cats])
    check("مجموع الفئات = حجم البنك", sum(c[2] for c in cats) == len(bank))
    check("كل سؤال له فئة ومستوى",
          all(q["category"] in data.CATEGORY_TITLES and 1 <= q["level"] <= 4 for q in bank))
    check("لا أسئلة مكرّرة", len({q["question"] for q in bank}) == len(bank))
    check("مؤشر الإجابة داخل النطاق",
          all(0 <= q["answer"] < len(q["options"]) for q in bank))
    check("أربعة خيارات مختلفة لكل سؤال",
          all(len(set(q["options"])) == len(q["options"]) >= 2 for q in bank))

    spread = {}
    for q in bank:
        spread[q["answer"]] = spread.get(q["answer"], 0) + 1
    widest = max(spread.values()) - min(spread.values())
    check("مواضع الإجابة الصحيحة متوازنة", widest <= len(bank) * 0.05, spread)
    check("كل المواضع الأربعة مستعملة", len(spread) == 4, sorted(spread))

    key = cats[0][0]
    subset = data.filter_bank(bank, key)
    check("الترشيح بالفئة", subset and all(q["category"] == key for q in subset))
    subset2 = data.filter_bank(bank, key, 3)
    check("الترشيح بالفئة والمستوى",
          subset2 and all(q["category"] == key and q["level"] == 3 for q in subset2))
    check("مستويات الفئة", len(data.available_levels(bank, key)) >= 1)

    quiz = data.build_quiz(bank, dict(data.DEFAULT_SETTINGS, category=key, level=2,
                                      question_limit=7))
    check("بناء اختبار مُرشَّح",
          len(quiz) == 7 and all(q["category"] == key and q["level"] == 2 for q in quiz))

    empty = data.build_quiz(bank, dict(data.DEFAULT_SETTINGS, category="no-such-category"))
    check("فئة بلا أسئلة تُعيد قائمة فارغة", empty == [])

    custom = data._normalize([{"question": "س", "options": ["أ", "ب"], "answer": 0}])
    check("السؤال بلا فئة يصير «أسئلتي»", custom[0]["category"] == data.CUSTOM_CATEGORY)
    check("المستوى الافتراضي 1", custom[0]["level"] == 1)


def test_bank_quality():
    section("جودة بنك الأسئلة")
    import json
    import bank_quality as bq

    with open(os.path.join(ROOT, "data", "questions.json"), encoding="utf-8") as fh:
        bank = json.load(fh)

    leaks = bq.revealing_questions(bank)
    check("لا سؤال يفضح جوابه في نصّه", not leaks,
          leaks[:3] if leaks else None)

    wrong = bq.wrong_arithmetic(bank)
    check("كل جواب حسابي يطابق الحساب الفعلي", not wrong,
          wrong[:3] if wrong else None)
    covered = bq.arithmetic_count(bank)
    check("المتحقّق الحسابي يغطي أسئلة فعلية", covered >= 40, covered)

    # الكاشف نفسه يجب أن يعمل: سؤال مفضوح مصنوع يدوياً
    trap = [{"question": "ما اسم مدينة القاهرة الكبرى؟",
             "options": ["القاهرة", "دمشق", "بغداد", "تونس"], "answer": 0}]
    check("الكاشف يمسك سؤالاً مفضوحاً", len(bq.revealing_questions(trap)) == 1)
    bad_math = [{"question": "كم يساوي 2 + 2؟",
                 "options": ["5", "4", "3", "6"], "answer": 0}]
    check("الكاشف يمسك حساباً خاطئاً", len(bq.wrong_arithmetic(bad_math)) == 1)
    good_math = [{"question": "كم يساوي 2 + 2؟",
                  "options": ["5", "4", "3", "6"], "answer": 1}]
    check("الكاشف لا يشكو من حساب صحيح", not bq.wrong_arithmetic(good_math))


def test_review():
    section("مراجعة الأخطاء وإحصاءات الفئات")
    import quiz_data as data

    data.clear_review()
    qs = [
        {"question": "س1", "options": ["أ", "ب"], "answer": 0, "category": "math", "level": 1},
        {"question": "س2", "options": ["أ", "ب"], "answer": 1, "category": "math", "level": 1},
        {"question": "س3", "options": ["أ", "ب"], "answer": 0, "category": "islam", "level": 1},
    ]
    added, removed = data.record_mistakes(qs, {0: 1, 1: 1, 2: 0})
    check("الخاطئ يُحفظ فقط", (added, removed) == (1, 0), (added, removed))
    check("محتوى قائمة المراجعة",
          [q["question"] for q in data.load_review()] == ["س1"])

    added, removed = data.record_mistakes(qs, {0: 1, 1: 0, 2: 1})
    check("الخاطئ الجديد يُضاف", added == 2, added)
    check("لا تكرار في القائمة",
          len({q["question"] for q in data.load_review()}) == len(data.load_review()))

    data.record_mistakes(qs, {0: 0, 1: 1, 2: 0})
    check("المتقَن يُحذف", data.load_review() == [], data.load_review())

    data.record_mistakes(qs, {})
    check("عدم الإجابة يُعد خطأ", len(data.load_review()) == 3)
    check("سؤال المراجعة يحتفظ بخياراته",
          all(len(q["options"]) == 2 for q in data.load_review()))
    data.clear_review()
    check("مسح المراجعة", data.load_review() == [])

    hist = [
        {"category": "math", "score": 2, "total": 10},
        {"category": "math", "score": 8, "total": 10},
        {"category": "islam", "score": 9, "total": 10},
        {"category": "islam", "score": 0, "total": 0},
    ]
    rows = data.category_stats(hist)
    check("تجميع الفئات", len(rows) == 2, rows)
    check("الأضعف أولاً", rows[0][0] == "math" and rows[0][4] == 50, rows)
    check("تجاهل المحاولات الفارغة", rows[1][3] == 10, rows)
    check("سجل فارغ", data.category_stats([]) == [])


def test_font_coverage():
    """كل محرف يعرضه التطبيق يجب أن يكون له رسم في الخط، وإلا ظهر مربّعاً فارغاً."""
    section("تغطية الخط")
    import ast

    from arabic_support import _FONT_FILE, ar
    from font_coverage import missing_glyphs, supported_codepoints
    import quiz_data as data

    check("ملف الخط موجود", os.path.exists(_FONT_FILE))
    codes = supported_codepoints(_FONT_FILE)
    check("الخط يحوي رسوماً كثيرة", len(codes) > 1000, len(codes))
    check("الخط يغطي الأشكال السياقية",
          sum(1 for c in range(0xFE70, 0xFEFD) if c in codes) > 130)

    pieces = []
    for q in data.default_bank():
        pieces.append(q["question"])
        pieces.extend(q["options"])
    for name in ("main.py", "quiz_data.py"):
        tree = ast.parse(open(os.path.join(ROOT, name), encoding="utf-8").read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                pieces.append(node.value)
    pieces.extend(title for _key, title in data.CATEGORY_TITLES.items())
    pieces.extend(title for _lvl, title in data.LEVELS)

    blob = "".join(pieces) + "".join(ar(p) for p in pieces)
    missing = missing_glyphs(_FONT_FILE, blob)
    check("لا محارف بلا رسم في الواجهة وبنك الأسئلة",
          not missing, [(c, hex(ord(c))) for c in missing[:12]])


def test_app():
    section("منطق التطبيق")
    import main
    import quiz_data as data

    app = main.SmartQuizApp()
    app.build()
    check("كل الشاشات موجودة",
          sorted(app.screens) == ["edit", "history", "home", "manage", "pick",
                                  "quiz", "result", "settings"], sorted(app.screens))

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
    check("السؤال الجديد في فئة «أسئلتي»", added["category"] == data.CUSTOM_CATEGORY)

    # تبديل الفئة والمستوى في المحرّر
    app.go_edit(len(app.bank) - 1)
    editor.cycle_category()
    editor.pick_level(3)
    picked = editor.category
    editor.save()
    check("تبديل فئة السؤال", app.bank[-1]["category"] == picked and picked != data.CUSTOM_CATEGORY)
    check("تبديل مستوى السؤال", app.bank[-1]["level"] == 3)
    app.go_edit(len(app.bank) - 1)
    check("المحرّر يحمّل فئة السؤال", editor.category == picked and editor.level == 3)

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

    # استيراد واستعادة الافتراضي
    manage = app.screens["manage"]
    kept = len(app.bank)
    app.bank = []
    app.save_bank()
    manage.restore_defaults()
    check("زر الاستعادة يعرض تأكيداً فقط", len(app.bank) == 0)
    app.bank, added = data.merge_bank(app.bank, data.default_bank())
    app.save_bank()
    check("استعادة الأسئلة الافتراضية", len(app.bank) == added >= 10)
    manage.export_text()
    manage.import_text()
    manage.refresh()

    # حذف
    app.screens["manage"].refresh()
    app.bank.pop()
    app.bank.pop()
    app.save_bank()

    # شاشة اختيار الفئة والمستوى
    pick = app.screens["pick"]
    app.bank = data.default_bank()
    app.save_bank()
    pick.on_pre_enter()
    first_cat = data.available_categories(app.bank)[0][0]
    pick._pick_category(first_cat)
    check("اختيار الفئة يُحفظ", app.settings["category"] == first_cat)
    pick._pick_level(2)
    pick._pick_limit(5)
    app.start_quiz()
    check("الاختبار يحترم الفئة والمستوى",
          len(app.questions) == 5
          and all(q["category"] == first_cat and q["level"] == 2 for q in app.questions))
    app.finish_quiz()
    check("السجل يحفظ الفئة", data.load_history()[0]["category"] == first_cat)
    app.settings["category"] = "no-such-category"
    app.start_quiz()
    check("فئة فارغة تُعيد لشاشة الاختيار", app.sm.current == "pick")
    app.settings.update(category="", level=0)
    app.save_settings()

    # ترشيح وتصفّح شاشة الإدارة
    manage = app.screens["manage"]
    manage.filter_category = ""
    manage.page = 0
    manage.refresh()
    check("الصفحة الأولى محدودة الحجم", len(manage.list_box.children) <= manage.page_size)
    manage.turn(1)
    check("الانتقال للصفحة التالية", manage.page == 1)
    manage.cycle_filter()
    check("تبديل الفئة يعيد للصفحة الأولى", manage.page == 0)
    manage.filter_category = ""
    manage.refresh()

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

    # وضع المراجعة
    data.clear_review()
    app.settings.update(question_limit=4, instant_feedback=True,
                        shuffle_questions=False, shuffle_options=False,
                        category="", level=0)
    app.start_quiz()
    for i, q in enumerate(app.questions):          # كلها خاطئة عمداً
        app.choose((q["answer"] + 1) % len(q["options"]))
        if i < len(app.questions) - 1:
            app.move(1)
    app.finish_quiz()
    pool = data.load_review()
    check("الأخطاء تدخل قائمة المراجعة", len(pool) == 4, len(pool))

    hist_before = len(data.load_history())
    app.start_review()
    check("وضع المراجعة يعمل", app.review_mode and app.sm.current == "quiz")
    check("أسئلة المراجعة من القائمة",
          {q["question"] for q in app.questions} == {q["question"] for q in pool})
    for i, q in enumerate(app.questions):          # كلها صحيحة الآن
        app.choose(q["answer"])
        if i < len(app.questions) - 1:
            app.move(1)
    app.finish_quiz()
    check("المراجعة تفرّغ القائمة عند الإتقان", data.load_review() == [],
          data.load_review())
    check("المراجعة لا تُسجَّل في سجل النتائج",
          len(data.load_history()) == hist_before, len(data.load_history()))
    check("زر الإعادة يعرف أنه مراجعة", app.screens["result"]._was_review)

    app.review_mode = False
    app.start_review()
    check("مراجعة فارغة لا تبدأ اختباراً", app.sm.current == "result")

    # عرض إحصاءات الفئات
    hs = app.screens["history"]
    hs.on_pre_enter()
    hs.toggle_view()
    check("تبديل عرض أداء الفئات", hs.show_stats)
    hs.refresh()
    hs.toggle_view()
    check("العودة لعرض المحاولات", not hs.show_stats)

    # بنك فارغ
    app.bank = []
    app.save_bank()
    app.start_quiz()
    check("لا يبدأ اختبار بلا أسئلة", app.sm.current == "manage")


def main_():
    try:
        test_arabic()
        test_wrap()
        test_data()
        test_categories()
        test_bank_quality()
        test_review()
        test_font_coverage()
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
