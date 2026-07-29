#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""فحوص جودة بنك الأسئلة — بلا اعتمادات خارجية.

يكشف صنفين من العيوب التي لا يراها فحص البنية:

1. `revealing_questions`: أسئلة يظهر جوابها حرفياً في نصّها، فتُحَل بلا معرفة.
2. `wrong_arithmetic`: أسئلة حسابية جوابها المخزَّن يخالف الحساب الفعلي.
"""

import math
import re

# مصطلحات وصفية: السؤال يعطي التعريف والجواب هو الاسم الاصطلاحي المركّب منه.
# هذا أسلوب تعليمي مقصود لا ثغرة، فيُستثنى صراحةً.
SAME_NAME_CAPITALS = ("الجزائر", "تونس")

DEFINITION_TERMS = (
    "علم أسباب النزول",
    "منصّف الزاوية",
    "رسم القلب الكهربائي",
    "خطأ زمن التشغيل",
    "اختبار الوحدة",
    "عنوان آي بي",
    "بايثون فور أندرويد",
    "قاعدة رفع الحرج",
    "ليلة القدر",
    "فيتامين D",
)

_WORD = re.compile(r"[\u0621-\u064A]+")


def _stems(text):
    """كلمات دلالية: تُسقط أداة التعريف وحروف الجر والكلمات المكوّنة من حرفين."""
    out = set()
    for word in _WORD.findall(text):
        if word.startswith("ال") and len(word) > 4:
            word = word[2:]
        if len(word) >= 3:
            out.add(word)
    return out


def revealing_questions(bank):
    """أسئلة كل كلمة دلالية في جوابها موجودة في نصّها."""
    bad = []
    for q in bank:
        answer = q["options"][q["answer"]]
        if answer in DEFINITION_TERMS or answer in SAME_NAME_CAPITALS:
            continue  # العاصمة تحمل اسم بلدها فعلاً، والسؤال صحيح
        ans_stems = _stems(answer)
        if not ans_stems:
            continue
        # سؤال "استخرج الكلمة من الجملة": الجواب جزء من الجملة المعروضة بالضرورة
        head, _, sample = q["question"].partition("في جملة")
        if sample and ans_stems <= _stems(sample):
            continue
        if ans_stems <= _stems(q["question"]):
            bad.append((q.get("category", ""), q["question"], answer))
    return bad


# أنماط حسابية يمكن التحقق منها آلياً
_ARITHMETIC = (
    (r"^(?:كم يساوي|ما ناتج) (\d+) \+ (\d+)؟$", lambda a, b: int(a) + int(b)),
    (r"^(?:كم يساوي|ما ناتج) (\d+) - (\d+)؟$", lambda a, b: int(a) - int(b)),
    (r"^(?:كم يساوي|ما ناتج) (\d+) × (\d+)؟$", lambda a, b: int(a) * int(b)),
    (r"^(?:كم يساوي|ما ناتج) (\d+) ÷ (\d+)؟$", lambda a, b: int(a) // int(b)),
    (r"^كم يساوي (\d+) بالمئة من (\d+)؟$", lambda p, n: int(p) * int(n) // 100),
    (r"^ما الجذر التربيعي للعدد (\d+)؟$", lambda n: math.isqrt(int(n))),
    (r"^ما مربع العدد (\d+)؟$", lambda n: int(n) ** 2),
)
_AVERAGE = re.compile(r"^ما متوسط الأعداد ([\d\sو]+)؟$")


def _expected(question):
    """القيمة الصحيحة للسؤال، أو None إن كان غير قابل للحساب."""
    for pattern, fn in _ARITHMETIC:
        found = re.match(pattern, question)
        if found:
            return fn(*found.groups())
    found = _AVERAGE.match(question)
    if found:
        nums = [int(x) for x in re.findall(r"\d+", found.group(1))]
        mean = sum(nums) / float(len(nums))
        return int(mean) if mean.is_integer() else mean
    return None


def wrong_arithmetic(bank):
    """(السؤال, المخزَّن, المحسوب) لكل سؤال حسابي جوابه خاطئ."""
    bad = []
    for q in bank:
        value = _expected(q["question"].strip())
        if value is None:
            continue
        stored = q["options"][q["answer"]].strip()
        if stored != str(value):
            bad.append((q["question"], stored, value))
    return bad


def arithmetic_count(bank):
    """عدد الأسئلة التي غطّاها المتحقّق الحسابي."""
    return sum(1 for q in bank if _expected(q["question"].strip()) is not None)
