from __future__ import annotations

import unicodedata

_MULTI_MATCH: dict[str, str] = {
    'ا': 'اأآإى',
    'أ': 'أإءؤئ',
    'إ': 'أإءؤئ',
    'ء': 'ءأإؤئ',
    'ت': 'تة',
    'ة': 'ةته',
    'ه': 'هة',
    'ى': 'ىاي',
    'ي': 'يى',
}


def _is_arabic(ch: str) -> bool:
    cp = ord(ch)
    ranges = (
        (0x0600, 0x06FF),
        (0x0750, 0x077F),
        (0x08A0, 0x08FF),
        (0xFB50, 0xFDFF),
        (0xFE70, 0xFEFF),
    )
    return any(a <= cp <= b for a, b in ranges)


def _is_mark(ch: str) -> bool:
    return unicodedata.combining(ch) != 0


def _sanitize(text: str) -> str:
    out: list[str] = []
    for ch in text or '':
        if ch == ' ':
            out.append(ch)
            continue
        cat = unicodedata.category(ch)[0]
        if cat in {'L', 'N', 'M'}:
            out.append(ch)
    return ''.join(out).strip()


def _expand(ch: str) -> str:
    mapped = _MULTI_MATCH.get(ch)
    return f'[{mapped}]' if mapped else ch


def _gaps(s: str) -> str:
    return '.*?'.join(part for part in s.split(' ') if part)


def build_plain(query: str) -> str:
    s = _sanitize(query)
    expanded = ''.join(_expand(ch) for ch in s)
    return _gaps(expanded)


def build_ignore(query: str) -> str:
    s = _sanitize(query)
    out: list[str] = []
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if ch == ' ':
            out.append('.*?')
            i += 1
            continue
        if _is_mark(ch):
            i += 1
            continue
        token = _expand(ch)
        if _is_arabic(ch):
            out.append(f'(?:{token}[\\p{{M}}\\x{{0640}}]*)')
            j = i + 1
            while j < n and _is_mark(s[j]):
                j += 1
            i = j
        else:
            out.append(token)
            i += 1
    return ''.join(out)


def build_require(query: str) -> str:
    s = _sanitize(query)
    out: list[str] = []
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if ch == ' ':
            out.append('.*?')
            i += 1
            continue
        if _is_mark(ch):
            i += 1
            continue
        token = _expand(ch)
        if not _is_arabic(ch):
            out.append(token)
            i += 1
            continue
        j = i + 1
        has = False
        while j < n and _is_mark(s[j]):
            has = True
            j += 1
        out.append(f'(?:{token}[\\p{{M}}]+)' if has else token)
        i = j
    return ''.join(out)


def build_pattern(mode: str | None, query: str) -> tuple[str, bool]:
    m = (mode or '').strip().lower()
    if m == 'regex':
        return query, False
    if m == 'ignore':
        return build_ignore(query), True
    if m == 'require':
        return build_require(query), True
    # smart/default
    return build_plain(query), False


__all__ = [
    'build_pattern',
    'build_plain',
    'build_ignore',
    'build_require',
]
