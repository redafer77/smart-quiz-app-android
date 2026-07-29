#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""يبني data/questions.json من ملفات المصدر في data/source ويتحقق من صحّتها.

صيغة السطر في ملفات المصدر:

    مستوى|السؤال؟|خيار1|خيار2|خيار3|خيار4|رقم الإجابة (1-4)

- المستوى من 1 إلى 4 (سهل ← صعب).
- الأسطر الفارغة والأسطر التي تبدأ بـ # تُتجاهل.
- اسم الملف (بدون الامتداق) هو معرّف الفئة، ويجب أن يكون معروفاً في CATEGORIES.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SOURCE_DIR = os.path.join(ROOT, "data", "source")
OUTPUT = os.path.join(ROOT, "data", "questions.json")

# ترتيب الفئات يحدّد ترتيب المراحل في التطبيق
CATEGORIES = [
    ("general", "معلومات عامة"),
    ("geography", "جغرافيا"),
    ("history", "تاريخ"),
    ("science", "علوم"),
    ("math", "رياضيات"),
    ("islam", "إسلاميات"),
    ("arabic", "لغة عربية"),
    ("tech", "تقنية"),
    ("sports", "رياضة"),
    ("culture", "أدب وفنون"),
]

LEVEL_NAMES = {1: "مبتدئ", 2: "متوسط", 3: "متقدّم", 4: "خبير"}


def fail(message):
    print("خطأ: %s" % message)
    sys.exit(1)


def parse_file(path, category):
    questions = []
    with open(path, "r", encoding="utf-8") as handle:
        for lineno, raw in enumerate(handle, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("|")]
            where = "%s:%d" % (os.path.basename(path), lineno)
            if len(parts) != 7:
                fail("%s: عدد الحقول %d وليس 7" % (where, len(parts)))
            level_text, question = parts[0], parts[1]
            options, answer_text = parts[2:6], parts[6]
            if not level_text.isdigit() or not 1 <= int(level_text) <= 4:
                fail("%s: مستوى غير صالح %r" % (where, level_text))
            if not answer_text.isdigit() or not 1 <= int(answer_text) <= 4:
                fail("%s: رقم إجابة غير صالح %r" % (where, answer_text))
            if not question.endswith("؟") and not question.endswith(":"):
                fail("%s: السؤال يجب أن ينتهي بعلامة استفهام" % where)
            if any(not o for o in options):
                fail("%s: يوجد خيار فارغ" % where)
            if len(set(options)) != 4:
                fail("%s: خيارات مكرّرة %r" % (where, options))
            questions.append({
                "question": question,
                "options": options,
                "answer": int(answer_text) - 1,
                "category": category,
                "level": int(level_text),
            })
    return questions


# خيارات لا يصحّ نقلها عن آخر القائمة
_ANCHORED = ("كل ما سبق", "جميع ما سبق", "كل ما ذُكر", "لا شيء مما سبق", "لا شيء مما ذُكر")


def balance_answers(questions):
    """يوزّع موضع الإجابة الصحيحة بالتساوي على الخيارات الأربعة.

    كُتبت ملفات المصدر بوضع الإجابة في موضع شبه ثابت، ما يجعل الاختبار قابلاً
    للتخمين بلا قراءة. نزيح الخيارات إزاحة دائرية (تحافظ على ترتيبها النسبي)
    حتى تستقر الإجابة في الموضع المستهدف. العملية حتمية فتبقى النتيجة قابلة
    لإعادة الإنتاج بالضبط.
    """
    moved = 0
    for index, item in enumerate(questions):
        options = item["options"]
        size = len(options)
        if any(any(mark in opt for mark in _ANCHORED) for opt in options):
            continue
        target = index % size
        shift = (target - item["answer"]) % size
        if not shift:
            continue
        item["options"] = options[-shift:] + options[:-shift]
        item["answer"] = target
        moved += 1
    return moved


# الحد الأقصى لنسبة إصابة استراتيجية «اختر الأطول»؛ الصدفة 25%
BIAS_LIMIT = 0.34


def length_bias(bank, ratio=1.3):
    """نسبة الأسئلة التي يكون فيها الخيار الأطول بوضوح هو الصحيح.

    الخيار الأطول بوضوح = أطول من ثانيه بنسبة `ratio` على الأقل، فذلك ما تراه
    العين. إن اقتربت النسبة من 25% لم يُفد طول الخيار في التخمين.
    """
    hits = total = 0
    for item in bank:
        lengths = [len(opt) for opt in item["options"]]
        longest = max(lengths)
        if lengths.count(longest) > 1 or longest < ratio * sorted(lengths)[-2]:
            continue
        total += 1
        if lengths[item["answer"]] == longest:
            hits += 1
    return hits, total


def check_length_bias(bank):
    """يمنع عودة الانحياز: إجابة صحيحة أطول من مشتّتاتها تكشف نفسها."""
    hits, total = length_bias(bank)
    if not total:
        return
    rate = hits / float(total)
    print("انحياز الطول: الأطول بوضوح صحيح في %d من %d سؤال (%.0f%%، الصدفة 25%%)"
          % (hits, total, rate * 100))
    if rate > BIAS_LIMIT:
        fail("الخيار الأطول يكشف الإجابة في %.0f%% من الأسئلة (الحد %.0f%%). "
             "أطِل المشتّتات في الأسئلة المنحازة." % (rate * 100, BIAS_LIMIT * 100))


def main():
    if not os.path.isdir(SOURCE_DIR):
        fail("مجلد المصدر غير موجود: %s" % SOURCE_DIR)

    bank = []
    seen = {}
    report = []
    missing = []
    for category, title in CATEGORIES:
        path = os.path.join(SOURCE_DIR, category + ".txt")
        if not os.path.exists(path):
            missing.append(title)
            continue
        items = parse_file(path, category)
        for item in items:
            key = item["question"]
            if key in seen:
                fail("سؤال مكرّر بين %s و %s: %s" % (seen[key], category, key))
            seen[key] = category
        counts = {}
        for item in items:
            counts[item["level"]] = counts.get(item["level"], 0) + 1
        items.sort(key=lambda q: q["level"])
        balance_answers(items)
        bank.extend(items)
        report.append((title, len(items), counts))

    with open(OUTPUT, "w", encoding="utf-8") as handle:
        json.dump(bank, handle, ensure_ascii=False, indent=0, separators=(",", ":"))

    print("الفئة                عدد   توزيع المستويات")
    for title, total, counts in report:
        spread = " ".join("م%d:%d" % (lvl, counts.get(lvl, 0)) for lvl in (1, 2, 3, 4))
        print("%-18s %5d   %s" % (title, total, spread))
    print("-" * 46)
    print("المجموع: %d سؤال في %s" % (len(bank), os.path.relpath(OUTPUT, ROOT)))
    size = os.path.getsize(OUTPUT) / 1024.0
    print("حجم الملف: %.1f كيلوبايت" % size)
    spread = {}
    for item in bank:
        spread[item["answer"]] = spread.get(item["answer"], 0) + 1
    print("توزيع موضع الإجابة: %s"
          % "  ".join("خيار %d: %d" % (k + 1, spread.get(k, 0)) for k in range(4)))
    if missing:
        print("فئات بلا ملف مصدر (تُتجاهل): %s" % "، ".join(missing))
    if not bank:
        fail("لم يُبنَ أي سؤال")
    check_length_bias(bank)


if __name__ == "__main__":
    main()
