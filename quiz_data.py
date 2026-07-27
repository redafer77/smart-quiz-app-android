"""تخزين بنك الأسئلة والإعدادات وسجل النتائج."""

import json
import os
import random
import time

BANK_FILE = "questions.json"
LEGACY_FILE = "questions.txt"
SETTINGS_FILE = "settings.json"
HISTORY_FILE = "history.json"

LETTERS = ["أ", "ب", "ج", "د", "هـ", "و"]

DEFAULT_SETTINGS = {
    "minutes": 10,
    "shuffle_questions": True,
    "shuffle_options": False,
    "instant_feedback": True,
    "question_limit": 0,  # 0 = كل الأسئلة
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
        if text and len(options) >= 2:
            clean.append({"question": text, "options": options, "answer": min(max(answer, 0), len(options) - 1)})
    return clean


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
    return data


def save_settings(data):
    _write_json(SETTINGS_FILE, data)


# ------------------------------------------------------------------ السجل

def load_history():
    data = _read_json(HISTORY_FILE, [])
    return data if isinstance(data, list) else []


def add_history(score, total, seconds):
    entry = {
        "date": time.strftime("%Y-%m-%d %H:%M"),
        "score": score,
        "total": total,
        "seconds": int(seconds),
    }
    history = load_history()
    history.insert(0, entry)
    _write_json(HISTORY_FILE, history[:50])
    return entry


def clear_history():
    _write_json(HISTORY_FILE, [])


# ------------------------------------------------------------------ الاختبار

def build_quiz(bank, settings):
    """يجهّز قائمة أسئلة الاختبار حسب الإعدادات."""
    items = [dict(q, options=list(q["options"])) for q in bank]
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
