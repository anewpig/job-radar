"""共用的評估指標與統計工具。"""

from __future__ import annotations

from statistics import mean


def average(values: list[float]) -> float:
    """回傳平均值，空序列時回傳 0。"""
    return float(mean(values)) if values else 0.0


def p95(values: list[float]) -> float:
    """以簡單排序法估算 p95。"""
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, round((len(ordered) - 1) * 0.95)))
    return float(ordered[index])


def keyword_recall(text: str, expected_keywords: list[str]) -> float:
    """計算答案命中預期關鍵詞的比例。"""
    if not expected_keywords:
        return 1.0
    lowered = text.lower()
    hits = sum(1 for keyword in expected_keywords if keyword.lower() in lowered)
    return hits / len(expected_keywords)


def precision_recall_f1(actual: list[str], expected: list[str]) -> tuple[float, float, float]:
    """計算集合型欄位的 precision / recall / f1。"""
    actual_lower = {item.lower() for item in actual if str(item).strip()}
    expected_lower = {item.lower() for item in expected if str(item).strip()}
    if not actual_lower and not expected_lower:
        return 1.0, 1.0, 1.0
    hits = len(actual_lower & expected_lower)
    precision = hits / len(actual_lower) if actual_lower else 0.0
    recall = hits / len(expected_lower) if expected_lower else 1.0
    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)
    return precision, recall, f1


def set_recall(actual: list[str], expected: list[str]) -> float:
    """計算集合型欄位的召回率。"""
    return precision_recall_f1(actual, expected)[1]
