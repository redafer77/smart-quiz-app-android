"""دعم عرض النص العربي في Kivy.

Kivy/SDL_ttf لا يقوم بالتشكيل الاتصالي (OpenType shaping) ولا بترتيب RTL،
لذلك نحوّل الحروف يدوياً إلى أشكالها السياقية من كتلة
Arabic Presentation Forms-B ثم نعكس ترتيب المقاطع العربية.

الوحدة مكتفية ذاتياً: لا تعتمد على arabic_reshaper أو python-bidi،
فقط على unicodedata من المكتبة القياسية.
"""

import os
import unicodedata

# ---------------------------------------------------------------- جداول الأشكال

_FORMS = {}          # حرف أساسي -> {"isolated","initial","medial","final"}
_LIGATURES = {}      # (لام, ألف) -> {"isolated","final"}

_SUFFIXES = (
    (" ISOLATED FORM", "isolated"),
    (" INITIAL FORM", "initial"),
    (" MEDIAL FORM", "medial"),
    (" FINAL FORM", "final"),
)

_LIG_BASES = {
    "ARABIC LIGATURE LAM WITH ALEF WITH MADDA ABOVE": ("\u0644", "\u0622"),
    "ARABIC LIGATURE LAM WITH ALEF WITH HAMZA ABOVE": ("\u0644", "\u0623"),
    "ARABIC LIGATURE LAM WITH ALEF WITH HAMZA BELOW": ("\u0644", "\u0625"),
    "ARABIC LIGATURE LAM WITH ALEF": ("\u0644", "\u0627"),
}


def _build_tables():
    by_name = {}
    for cp in range(0x0600, 0x0700):
        try:
            by_name[unicodedata.name(chr(cp))] = chr(cp)
        except ValueError:
            pass

    for cp in range(0xFE70, 0xFEFD):
        ch = chr(cp)
        try:
            name = unicodedata.name(ch)
        except ValueError:
            continue
        for suffix, key in _SUFFIXES:
            if not name.endswith(suffix):
                continue
            base_name = name[: -len(suffix)]
            if base_name in _LIG_BASES:
                _LIGATURES.setdefault(_LIG_BASES[base_name], {})[key] = ch
            elif base_name in by_name:
                _FORMS.setdefault(by_name[base_name], {})[key] = ch
            break


_build_tables()

# حروف شفافة (تشكيل/تطويل) لا تكسر الاتصال
_TRANSPARENT = set(
    [chr(c) for c in range(0x064B, 0x0660)]
    + [chr(c) for c in range(0x0610, 0x061B)]
    + [chr(c) for c in (0x0670, 0x06D6, 0x06DC, 0x06DF, 0x06E0, 0x06E2, 0x06E3, 0x06E8, 0x06EA, 0x06EB, 0x06EC, 0x06ED)]
)

_ARABIC_RANGES = ((0x0600, 0x06FF), (0x0750, 0x077F), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF))

_MIRROR = {"(": ")", ")": "(", "[": "]", "]": "[", "{": "}", "}": "{", "<": ">", ">": "<"}


def _is_arabic(ch):
    cp = ord(ch)
    return any(lo <= cp <= hi for lo, hi in _ARABIC_RANGES)


def _connects_after(ch):
    """هل يتصل هذا الحرف بما بعده؟"""
    return "initial" in _FORMS.get(ch, {})


def _connects_before(ch):
    """هل يقبل هذا الحرف الاتصال بما قبله؟"""
    return "final" in _FORMS.get(ch, {})


# ---------------------------------------------------------------- التشكيل

def reshape(text):
    """تحويل الحروف العربية إلى أشكالها السياقية."""
    if not text:
        return text

    chars = list(text)
    out = []
    i = 0
    n = len(chars)

    def prev_visible(idx):
        j = idx - 1
        while j >= 0 and chars[j] in _TRANSPARENT:
            j -= 1
        return chars[j] if j >= 0 else None

    def next_visible(idx):
        j = idx + 1
        while j < n and chars[j] in _TRANSPARENT:
            j += 1
        return chars[j] if j < n else None

    while i < n:
        ch = chars[i]

        if ch not in _FORMS:
            out.append(ch)
            i += 1
            continue

        # اللام + ألف => حرف واحد
        nxt = next_visible(i)
        if ch == "\u0644" and nxt is not None and (ch, nxt) in _LIGATURES:
            prev = prev_visible(i)
            joined_before = prev is not None and _connects_after(prev)
            lig = _LIGATURES[(ch, nxt)]
            out.append(lig.get("final" if joined_before else "isolated", ch + nxt))
            # تخطي اللام والألف وما بينهما من تشكيل
            j = i + 1
            while j < n and chars[j] in _TRANSPARENT:
                out.append(chars[j])
                j += 1
            i = j + 1
            continue

        prev = prev_visible(i)
        joined_before = prev is not None and _connects_after(prev) and _connects_before(ch)
        joined_after = nxt is not None and _connects_before(nxt) and _connects_after(ch)

        if joined_before and joined_after:
            key = "medial"
        elif joined_before:
            key = "final"
        elif joined_after:
            key = "initial"
        else:
            key = "isolated"

        forms = _FORMS[ch]
        out.append(forms.get(key) or forms.get("isolated") or ch)
        i += 1

    return "".join(out)


# ---------------------------------------------------------------- ترتيب RTL

_ET = set("%\u066a$\u00a3\u20ac\u00b0#")
_CS = set(",.:/\u00a0\u060c\u066b\u066c")  # فواصل مشتركة بين الأرقام
_ES = set("+-")


def _classify(ch):
    cp = ord(ch)
    if 0x0660 <= cp <= 0x0669 or 0x06F0 <= cp <= 0x06F9:
        return "EN"  # أرقام هندية: تُرتَّب من اليسار لليمين مثل الأوروبية
    if _is_arabic(ch):
        return "R"
    if ch.isdigit():
        return "EN"
    if ch.isalpha():
        return "L"
    if ch in _ET:
        return "ET"
    if ch in _CS:
        return "CS"
    if ch in _ES:
        return "ES"
    return "N"


def _bidi_line(line):
    """ترتيب بصري مبسّط لسطر اتجاه فقرته من اليمين لليسار (UBA مختصر)."""
    if not line:
        return line

    cls = [_classify(c) for c in line]
    n = len(cls)

    # W4: فاصل مفرد (. , : / + -) بين رقمين يصبح رقماً
    for i in range(1, n - 1):
        if cls[i] in ("CS", "ES") and cls[i - 1] == "EN" and cls[i + 1] == "EN":
            cls[i] = "EN"
    for i in range(n):
        if cls[i] in ("CS", "ES"):
            cls[i] = "N"

    # W5: سلسلة ET ملاصقة لـ EN تصبح EN
    i = 0
    while i < n:
        if cls[i] == "ET":
            j = i
            while j < n and cls[j] == "ET":
                j += 1
            before = cls[i - 1] if i > 0 else None
            after = cls[j] if j < n else None
            new = "EN" if (before == "EN" or after == "EN") else "N"
            for k in range(i, j):
                cls[k] = new
            i = j
        else:
            i += 1

    # N1/N2: المحايدات بين طرفين لاتينيين تصبح L، وإلا تأخذ اتجاه الفقرة (R).
    # الأرقام تُعامل كـ R عند حل المحايدات.
    def strong(c):
        return "L" if c == "L" else "R"

    i = 0
    while i < n:
        if cls[i] == "N":
            j = i
            while j < n and cls[j] == "N":
                j += 1
            before = strong(cls[i - 1]) if i > 0 else "R"
            after = strong(cls[j]) if j < n else "R"
            new = "L" if (before == "L" and after == "L") else "R"
            for k in range(i, j):
                cls[k] = new
            i = j
        else:
            i += 1

    # المستوى: R => 1 (يمين‑يسار)، L/EN => 2 (يسار‑يمين)
    segments = []
    for ch, c in zip(line, cls):
        rtl = c == "R"
        if segments and segments[-1][0] == rtl:
            segments[-1][1].append(ch)
        else:
            segments.append([rtl, [ch]])

    out = []
    for rtl, chs in reversed(segments):
        if rtl:
            out.append("".join(_MIRROR.get(c, c) for c in reversed(chs)))
        else:
            out.append("".join(chs))
    return "".join(out)


def ar(text):
    """جهّز نصاً عربياً للعرض في Kivy (تشكيل + RTL)."""
    if not text:
        return text
    text = str(text)
    if not any(_is_arabic(c) for c in text):
        return text
    return "\n".join(_bidi_line(reshape(line)) for line in text.split("\n"))


# ---------------------------------------------------------------- تسجيل الخط

FONT_NAME = "ArabicUI"
_FONT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "Amiri-Regular.ttf")


def register_font():
    """يسجّل الخط العربي كخط افتراضي لكيفي. يعيد اسم الخط أو None."""
    if not os.path.exists(_FONT_FILE):
        return None
    try:
        from kivy.core.text import LabelBase
    except Exception:
        return None

    LabelBase.register(name=FONT_NAME, fn_regular=_FONT_FILE)
    # اجعله الخط الافتراضي لكل الودجات
    try:
        LabelBase.register(name="Roboto", fn_regular=_FONT_FILE)
    except Exception:
        pass
    return FONT_NAME


if __name__ == "__main__":
    samples = [
        "مرحباً بك في تطبيق الاختبارات الذكي",
        "ما عاصمة المغرب؟",
        "أ) مراكش",
        "الإجابة: ب",
        "النتيجة: 8 من 10 (80%)",
        "لا إله إلا الله",
    ]
    for s in samples:
        print(s, "->", ar(s))
