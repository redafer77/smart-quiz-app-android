"""تخزين بنك الأسئلة والإعدادات وسجل النتائج."""

import json
import os
import random
import time

BANK_FILE = "questions.json"
LEGACY_FILE = "questions.txt"
SETTINGS_FILE = "settings.json"
HISTORY_FILE = "history.json"
REVIEW_FILE = "review.json"

LETTERS = ["أ", "ب", "ج", "د", "هـ", "و"]

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
CATEGORY_TITLES = dict(CATEGORIES)
CUSTOM_CATEGORY = "custom"
CATEGORY_TITLES[CUSTOM_CATEGORY] = "أسئلتي"

LEVELS = [(1, "مبتدئ"), (2, "متوسط"), (3, "متقدّم"), (4, "خبير")]
LEVEL_TITLES = dict(LEVELS)

DEFAULT_SETTINGS = {
    "minutes": 10,
    "shuffle_questions": True,
    "shuffle_options": False,
    "instant_feedback": True,
    "question_limit": 10,   # 0 = كل الأسئلة
    "category": "",         # "" = كل الفئات
    "level": 0,             # 0 = كل المستويات
}

SAMPLE_BANK = [
    {"question": "ما عاصمة المغرب؟", "options": ["مراكش", "الرباط", "الدار البيضاء", "فاس"], "answer": 1},
    {"question": "كم عدد أيام السنة الميلادية الكبيسة؟", "options": ["364", "365", "366", "367"], "answer": 2},
    {"question": "ما أكبر محيط في العالم؟", "options": ["الأطلسي", "الهندي", "الهادئ", "المتجمد"], "answer": 2},
    {"question": "من كتب رواية «الأيام»؟", "options": ["نجيب محفوظ", "طه حسين", "توفيق الحكيم", "جبران خليل جبران"], "answer": 1},
    {"question": "ما الرمز الكيميائي للذهب؟", "options": ["Ag", "Au", "Fe", "Gd"], "answer": 1},
    {"question": "كم عدد أضلاع الشكل السداسي؟", "options": ["4", "5", "6", "8"], "answer": 2},
    {"question": "في أي قارة تقع مصر؟", "options": ["آسيا", "أوروبا", "أفريقيا", "أستراليا"], "answer": 2},
    {"question": "ما أسرع حيوان بري؟", "options": ["الأسد", "الفهد الصياد", "الحصان", "الغزال"], "answer": 1},
    {"question": "ما لغة برمجة تطبيق كيفي (Kivy)؟", "options": ["Java", "Python", "C#", "Swift"], "answer": 1},
    {"question": "كم عدد الكواكب في المجموعة الشمسية؟", "options": ["7", "8", "9", "10"], "answer": 1},
]


# ------------------------------------------------------------------ المسارات

def storage_dir():
    """مجلد تخزين خاص بالتطبيق يعمل على أندرويد وعلى سطح المكتب."""
    try:
        from android.storage import app_storage_path  # type: ignore
        base = app_storage_path()
    except Exception:
        base = os.path.join(os.path.expanduser("~"), ".smartquiz")
    try:
        os.makedirs(base, exist_ok=True)
    except Exception:
        base = os.getcwd()
    return base


def shared_dir():
    """مجلد التطبيق الظاهر لمدير الملفات على أندرويد (بلا أذونات).

    ‎/sdcard/Android/data/<package>/files — يستعمله المستخدم لوضع ملف
    الاستيراد أو لأخذ ملف التصدير. يعيد None على سطح المكتب.
    """
    try:
        from jnius import autoclass  # type: ignore
        activity = autoclass("org.kivy.android.PythonActivity").mActivity
        directory = activity.getExternalFilesDir(None)
        if directory is not None:
            return directory.getAbsolutePath()
    except Exception:
        pass
    return None


def _path(name):
    return os.path.join(storage_dir(), name)


def _read_json(name, default):
    try:
        with open(_path(name), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _write_json(name, data):
    tmp = _path(name) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, _path(name))


# ------------------------------------------------------------ الصيغة النصية

def parse_text_bank(text):
    """يحوّل الصيغة النصية القديمة إلى قائمة أسئلة."""
    questions = []
    for block in text.replace("\r\n", "\n").strip().split("\n\n"):
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        q, options, answer_letter = "", [], ""
        for line in lines:
            if line.startswith("سؤال:"):
                q = line[len("سؤال:"):].strip()
            elif line.startswith("الإجابة:"):
                answer_letter = line[len("الإجابة:"):].strip()
            else:
                for letter in LETTERS:
                    if line.startswith(letter + ")"):
                        options.append(line[len(letter) + 1:].strip())
                        break
        if not q or len(options) < 2:
            continue
        idx = 0
        letter = answer_letter.replace(")", "").strip()
        if letter in LETTERS:
            idx = LETTERS.index(letter)
        elif letter.isdigit():
            idx = max(0, int(letter) - 1)
        else:
            for i, opt in enumerate(options):
                if opt == letter:
                    idx = i
                    break
        questions.append({"question": q, "options": options, "answer": min(idx, len(options) - 1)})
    return questions


def to_text_bank(questions):
    out = []
    for q in questions:
        block = ["سؤال: " + q["question"]]
        for i, opt in enumerate(q["options"]):
            block.append("%s) %s" % (LETTERS[i], opt))
        block.append("الإجابة: " + LETTERS[q["answer"]])
        out.append("\n".join(block))
    return "\n\n".join(out) + "\n"


# ------------------------------------------------------------------ بنك الأسئلة

def _normalize(items):
    clean = []
    for q in items or []:
        try:
            text = str(q["question"]).strip()
            options = [str(o).strip() for o in q["options"] if str(o).strip()]
            answer = int(q.get("answer", 0))
        except Exception:
            continue
        if not text or len(options) < 2:
            continue
        category = str(q.get("category") or CUSTOM_CATEGORY)
        if category not in CATEGORY_TITLES:
            category = CUSTOM_CATEGORY
        try:
            level = int(q.get("level", 1))
        except Exception:
            level = 1
        clean.append({
            "question": text,
            "options": options,
            "answer": min(max(answer, 0), len(options) - 1),
            "category": category,
            "level": min(max(level, 1), 4),
        })
    return clean


def available_categories(bank):
    """الفئات الموجودة فعلاً في البنك مع عدد أسئلة كل منها، بترتيب ثابت."""
    counts = {}
    for q in bank:
        counts[q["category"]] = counts.get(q["category"], 0) + 1
    order = [key for key, _ in CATEGORIES] + [CUSTOM_CATEGORY]
    return [(key, CATEGORY_TITLES[key], counts[key]) for key in order if key in counts]


def available_levels(bank, category=""):
    counts = {}
    for q in bank:
        if category and q["category"] != category:
            continue
        counts[q["level"]] = counts.get(q["level"], 0) + 1
    return [(lvl, LEVEL_TITLES[lvl], counts[lvl]) for lvl, _ in LEVELS if lvl in counts]


def filter_bank(bank, category="", level=0):
    return [q for q in bank
            if (not category or q["category"] == category)
            and (not level or q["level"] == level)]


def load_bank():
    """يحمّل بنك الأسئلة، مع ترحيل الملف النصي القديم وبذرة أسئلة أولية."""
    if os.path.exists(_path(BANK_FILE)):
        return _normalize(_read_json(BANK_FILE, []))

    legacy = _path(LEGACY_FILE)
    if os.path.exists(legacy):
        try:
            with open(legacy, "r", encoding="utf-8") as f:
                migrated = _normalize(parse_text_bank(f.read()))
            if migrated:
                save_bank(migrated)
                return migrated
        except Exception:
            pass

    bundled = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", BANK_FILE)
    if os.path.exists(bundled):
        try:
            with open(bundled, "r", encoding="utf-8") as f:
                seed = _normalize(json.load(f))
            if seed:
                save_bank(seed)
                return seed
        except Exception:
            pass

    save_bank(SAMPLE_BANK)
    return list(SAMPLE_BANK)


def save_bank(questions):
    _write_json(BANK_FILE, questions)


def default_bank():
    """بنك الأسئلة المضمَّن مع التطبيق."""
    bundled = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", BANK_FILE)
    try:
        with open(bundled, "r", encoding="utf-8") as f:
            seed = _normalize(json.load(f))
        if seed:
            return seed
    except Exception:
        pass
    return [dict(q, options=list(q["options"])) for q in SAMPLE_BANK]


def merge_bank(bank, new_questions):
    """يضيف الأسئلة غير المكرّرة ويعيد (البنك الجديد، عدد المضاف)."""
    seen = {q["question"].strip() for q in bank}
    added = 0
    for q in _normalize(new_questions):
        if q["question"].strip() in seen:
            continue
        bank.append(q)
        seen.add(q["question"].strip())
        added += 1
    return bank, added


IMPORT_NAMES = ("questions_import.txt", "questions.txt", "questions_export.txt")


def import_candidates():
    """مسارات ملفات نصية يمكن الاستيراد منها."""
    found = []
    for base in (shared_dir(), storage_dir(), os.getcwd()):
        if not base:
            continue
        for name in IMPORT_NAMES:
            path = os.path.join(base, name)
            if os.path.exists(path) and path not in found:
                found.append(path)
    return found


def import_from_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return parse_text_bank(f.read())


def export_targets():
    """أماكن كتابة ملف التصدير: مساحة التطبيق + المجلد الظاهر إن وُجد."""
    targets = [os.path.join(storage_dir(), "questions_export.txt")]
    shared = shared_dir()
    if shared:
        targets.append(os.path.join(shared, "questions_export.txt"))
    return targets


# ------------------------------------------------------------------ الإعدادات

def load_settings():
    data = dict(DEFAULT_SETTINGS)
    stored = _read_json(SETTINGS_FILE, {})
    if isinstance(stored, dict):
        for key in DEFAULT_SETTINGS:
            if key in stored:
                data[key] = stored[key]
    data["minutes"] = max(1, min(int(data["minutes"] or 1), 180))
    data["question_limit"] = max(0, int(data["question_limit"] or 0))
    if data["category"] not in CATEGORY_TITLES:
        data["category"] = ""
    try:
        data["level"] = int(data["level"])
    except Exception:
        data["level"] = 0
    if data["level"] not in LEVEL_TITLES:
        data["level"] = 0
    return data


def save_settings(data):
    _write_json(SETTINGS_FILE, data)


# ------------------------------------------------------------------ السجل

def load_history():
    data = _read_json(HISTORY_FILE, [])
    return data if isinstance(data, list) else []


def add_history(score, total, seconds, category="", level=0):
    entry = {
        "date": time.strftime("%Y-%m-%d %H:%M"),
        "score": score,
        "total": total,
        "seconds": int(seconds),
        "category": category,
        "level": level,
    }
    history = load_history()
    history.insert(0, entry)
    _write_json(HISTORY_FILE, history[:50])
    return entry


def clear_history():
    _write_json(HISTORY_FILE, [])


def category_stats(history=None):
    """أداء المستخدم في كل فئة: (المفتاح، العنوان، الصحيح، الإجمالي، النسبة).

    مرتّبة من الأضعف إلى الأقوى ليظهر ما يحتاج مراجعة أولاً.
    """
    totals = {}
    for entry in history if history is not None else load_history():
        key = entry.get("category") or ""
        score, total = int(entry.get("score", 0)), int(entry.get("total", 0))
        if total <= 0:
            continue
        got, had = totals.get(key, (0, 0))
        totals[key] = (got + score, had + total)

    rows = []
    for key, (got, had) in totals.items():
        title = CATEGORY_TITLES.get(key, "كل الفئات" if not key else key)
        rows.append((key, title, got, had, round(got * 100.0 / had)))
    rows.sort(key=lambda r: (r[4], -r[3]))
    return rows


# ------------------------------------------------------------- مراجعة الأخطاء

def load_review():
    """الأسئلة التي أخطأ فيها المستخدم ولم يتقنها بعد."""
    items = _read_json(REVIEW_FILE, [])
    return _normalize(items) if isinstance(items, list) else []


def _question_key(question):
    return question.get("question", "").strip()


def record_mistakes(questions, answers):
    """يضيف الأسئلة الخاطئة إلى قائمة المراجعة ويحذف ما أُتقن.

    يعيد (عدد المضاف، عدد المحذوف).
    """
    review = load_review()
    index = {_question_key(q): i for i, q in enumerate(review)}
    added = removed = 0

    for position, question in enumerate(questions):
        key = _question_key(question)
        if not key:
            continue
        correct = answers.get(position) == question["answer"]
        if correct:
            if key in index:
                review[index[key]] = None
                del index[key]
                removed += 1
        elif key not in index:
            entry = dict(question, options=list(question["options"]))
            index[key] = len(review)
            review.append(entry)
            added += 1

    review = [q for q in review if q]
    _write_json(REVIEW_FILE, review)
    return added, removed


def clear_review():
    _write_json(REVIEW_FILE, [])


# ------------------------------------------------------------------ الاختبار

def build_quiz(bank, settings):
    """يجهّز قائمة أسئلة الاختبار حسب الإعدادات."""
    pool = filter_bank(bank, settings.get("category", ""), settings.get("level", 0))
    items = [dict(q, options=list(q["options"])) for q in pool]
    if settings.get("shuffle_questions"):
        random.shuffle(items)
    limit = settings.get("question_limit") or 0
    if limit:
        items = items[:limit]
    if settings.get("shuffle_options"):
        for q in items:
            correct = q["options"][q["answer"]]
            random.shuffle(q["options"])
            q["answer"] = q["options"].index(correct)
    return items
