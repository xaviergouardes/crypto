import pytest
import numpy as np

from trading_bot.indicators.indicator_ema_cross_detector.ema_cross_calculator import IndicatorEmaCrossCalculator


# ---------------------------------------------------------------------------
# 1) Pas assez de données → aucun signal
# ---------------------------------------------------------------------------
def test_no_signal_with_insufficient_data():
    calc = IndicatorEmaCrossCalculator()
    assert calc.update(1.0, 1.1) is None


# ---------------------------------------------------------------------------
# 2) Pas de changement de signe → pas de cross
# ---------------------------------------------------------------------------
def test_no_cross_when_same_sign():
    calc = IndicatorEmaCrossCalculator()
    calc.update(1.2, 1.0)    # fast > slow
    assert calc.update(1.3, 1.1) is None  # même signe → aucun cross


# ---------------------------------------------------------------------------
# 3) Cross détecté mais rejeté par min_gap_pct (micro touch)
# ---------------------------------------------------------------------------
def test_cross_rejected_by_min_gap():
    calc = IndicatorEmaCrossCalculator(min_gap=0.01)

    calc.update(1.00, 1.01)     # prev_diff < 0
    result = calc.update(1.01005, 1.01)  # cross mais gap < 1%
    assert result is None


# ---------------------------------------------------------------------------
# 4) Cross détecté mais pente fast insuffisante
# ---------------------------------------------------------------------------
def test_cross_rejected_by_low_slope():
    calc = IndicatorEmaCrossCalculator(slope_threshold=0.1)

    calc.update(1.0, 1.1)
    calc.update(1.01, 1.1)
    calc.update(1.02, 1.1)
    calc.update(1.03, 1.1)

    # Cross mais slope ≈ 0.01 < 0.1
    result = calc.update(1.04, 1.03)
    assert result is None


# ---------------------------------------------------------------------------
# 5) Rejet si fast_slope et slow_slope incohérents
#    fast monte / slow descend ou inverse → aucun signal
# ---------------------------------------------------------------------------
def test_reject_cross_inconsistent_slopes():
    calc = IndicatorEmaCrossCalculator()

    # Incohérence : fast monte, slow descend
    values_fast = [1.0, 1.05, 1.1, 1.15, 1.2]
    values_slow = [1.2, 1.19, 1.18, 1.17, 1.16]

    for f, s in zip(values_fast[:-1], values_slow[:-1]):
        calc.update(f, s)

    # Le dernier point crée un cross mais les pentes sont incohérentes
    result = calc.update(values_fast[-1], values_slow[-1])
    assert result is None


# ---------------------------------------------------------------------------
# 6) Détection bullish validée
# ---------------------------------------------------------------------------
def test_bullish_cross():
    calc = IndicatorEmaCrossCalculator(min_gap=0.001)

    calc.update(1.00, 1.02)     # prev_diff < 0
    result = calc.update(1.06, 1.03)  # pente positive + diff > 0

    assert result == "bullish"


# ---------------------------------------------------------------------------
# 7) Détection bearish validée
# ---------------------------------------------------------------------------
def test_bearish_cross():
    calc = IndicatorEmaCrossCalculator(min_gap=0.001)

    # 1er update : fast > slow
    calc.update(1.05, 1.02)     # prev_diff > 0

    # 2e update : fast passe en dessous -> cross bearish attendu ici
    result = calc.update(1.01, 1.02)
    assert result == "bearish"


# ---------------------------------------------------------------------------
# 8) Test polyfit : pente trop faible malgré un cross
# ---------------------------------------------------------------------------
def test_polyfit_slope_low_rejects_cross():
    calc = IndicatorEmaCrossCalculator(slope_threshold=0.5)

    fast = [1.00, 1.01, 1.02, 1.03, 1.04]  # pente ≈ 0.01
    slow = [1.05, 1.04, 1.03, 1.02, 1.01]

    for f, s in zip(fast, slow):
        calc.update(f, s)

    # Cross mais pente trop faible (polyfit → slope ~0.01)
    result = calc.update(1.05, 1.00)
    assert result is None
