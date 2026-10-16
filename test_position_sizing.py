import math

def calc_qty(capital, risk_pct, entry, stop):
    if entry <= stop or stop <= 0:
        return 0
    risk_budget = capital * risk_pct / 100
    return max(0, min(math.floor(risk_budget / (entry-stop)), math.floor(capital / entry)))

def test_default_example():
    qty = calc_qty(50000, 1, 1450, 1410)
    assert qty == 12
    assert qty * (1450-1410) <= 500
    assert qty * 1450 <= 50000

def test_zero_or_invalid_risk():
    assert calc_qty(50000, 1, 1400, 1400) == 0
    assert calc_qty(50000, 1, 1400, 1450) == 0
