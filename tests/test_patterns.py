from core.patterns import build_pattern, build_plain, build_ignore, build_require


def test_build_pattern_smart_no_pcre():
    pat, pcre = build_pattern('smart', 'العربية')
    assert pcre is False
    assert '\\p{M}' not in pat
    assert pat.startswith('[اأآإى]ل')


def test_build_pattern_ignore_pcre_and_marks():
    pat, pcre = build_pattern('ignore', 'العربية')
    assert pcre is True
    assert '\\p{M}' in pat


def test_build_pattern_require_marks_when_typed():
    pat, pcre = build_pattern('require', 'العَر')
    assert pcre is True
    assert '[\\p{M}]+' in pat


def test_build_pattern_require_no_marks_when_not_typed():
    pat, pcre = build_pattern('require', 'العربية')
    assert pcre is True
    assert '\\p{M}' not in pat


def test_build_pattern_regex_passthrough():
    q = 'a.*b'
    pat, pcre = build_pattern('regex', q)
    assert pat == q
    assert pcre is False


def test_build_plain_gaps():
    assert build_plain('abc def') == 'abc.*?def'


def test_build_ignore_contains_optional_marks():
    assert '\\p{M}' in build_ignore('العربية')


def test_build_require_contains_plus_only_if_typed():
    assert '[\\p{M}]+' in build_require('العَر')
    assert '\\p{M}' not in build_require('العربية')
