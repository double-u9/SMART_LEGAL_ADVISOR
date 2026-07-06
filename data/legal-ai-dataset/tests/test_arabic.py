from legal_ai_dataset.arabic import arabic_ratio, normalize_arabic_surface, normalize_for_search


def test_surface_normalization_preserves_text_and_removes_noise() -> None:
    text = "اﻟﻤﺎدةــ ١\n\n\n   اختبار"
    cleaned = normalize_arabic_surface(text)
    assert "المادة" in cleaned
    assert "ــ" not in cleaned
    assert "\n\n\n" not in cleaned


def test_search_normalization_unifies_common_arabic_forms() -> None:
    text = "إلتزام وآثار الدعوى رقم ١٢"
    normalized = normalize_for_search(text)
    assert "التزام" in normalized
    assert "12" in normalized


def test_arabic_ratio_detects_arabic_text() -> None:
    assert arabic_ratio("المادة 1 من القانون") > 0.5

