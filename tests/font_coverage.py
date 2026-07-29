# -*- coding: utf-8 -*-
"""قارئ خفيف لجدول cmap في ملفات TrueType.

الهدف: التحقق في الاختبارات من أن كل محرف تعرضه الواجهة له رسم فعلي في الخط،
حتى لا تظهر مربّعات فارغة على الجهاز. مكتوب بلا أي اعتماد خارجي.
"""

import struct


def _read_format4(buf, off):
    seg_x2 = struct.unpack_from(">H", buf, off + 6)[0]
    segs = seg_x2 // 2
    ends = struct.unpack_from(">%dH" % segs, buf, off + 14)
    starts = struct.unpack_from(">%dH" % segs, buf, off + 16 + seg_x2)
    deltas = struct.unpack_from(">%dh" % segs, buf, off + 16 + 2 * seg_x2)
    range_off_pos = off + 16 + 3 * seg_x2
    range_offsets = struct.unpack_from(">%dH" % segs, buf, range_off_pos)

    codes = set()
    for i in range(segs):
        if starts[i] > ends[i] or starts[i] == 0xFFFF:
            continue
        for code in range(starts[i], ends[i] + 1):
            if range_offsets[i] == 0:
                gid = (code + deltas[i]) & 0xFFFF
            else:
                pos = range_off_pos + 2 * i + range_offsets[i] + 2 * (code - starts[i])
                if pos + 2 > len(buf):
                    continue
                gid = struct.unpack_from(">H", buf, pos)[0]
                if gid:
                    gid = (gid + deltas[i]) & 0xFFFF
            if gid:
                codes.add(code)
    return codes


def _read_format12(buf, off):
    n_groups = struct.unpack_from(">I", buf, off + 12)[0]
    codes = set()
    pos = off + 16
    for _ in range(n_groups):
        start, end, gid = struct.unpack_from(">III", buf, pos)
        pos += 12
        if gid and end - start < 0x10000:
            codes.update(range(start, end + 1))
    return codes


def supported_codepoints(path):
    """مجموعة نقاط اليونيكود التي يرسمها الخط."""
    with open(path, "rb") as f:
        buf = f.read()

    num_tables = struct.unpack_from(">H", buf, 4)[0]
    cmap_off = None
    for i in range(num_tables):
        tag, _checksum, offset, _length = struct.unpack_from(">4sIII", buf, 12 + 16 * i)
        if tag == b"cmap":
            cmap_off = offset
            break
    if cmap_off is None:
        raise ValueError("لا يوجد جدول cmap في %s" % path)

    n_sub = struct.unpack_from(">H", buf, cmap_off + 2)[0]
    codes = set()
    for i in range(n_sub):
        _pid, _eid, sub_off = struct.unpack_from(">HHI", buf, cmap_off + 4 + 8 * i)
        table = cmap_off + sub_off
        fmt = struct.unpack_from(">H", buf, table)[0]
        if fmt == 4:
            codes |= _read_format4(buf, table)
        elif fmt == 12:
            codes |= _read_format12(buf, table)
    return codes


def missing_glyphs(path, text):
    """المحارف التي لا رسم لها في الخط (مع تجاهل الفراغات وفواصل الأسطر)."""
    supported = supported_codepoints(path)
    ignore = set("\n\r\t ")
    return sorted({c for c in text if c not in ignore and ord(c) not in supported})
