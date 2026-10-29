"""Technical indicators against known values."""

import datetime as dt
import math
import unittest

from helpers import src

from fortune_research.analysis import technical as T
from fortune_research.models import PriceBar, PriceSeries


def series(closes, start=dt.date(2025, 1, 1)):
    bars = [PriceBar(start + dt.timedelta(days=i), c, c * 1.01, c * 0.99, c, 1000) for i, c in enumerate(closes)]
    return PriceSeries(bars, src("px"), adjusted=True)


class Indicators(unittest.TestCase):
    def test_sma(self):
        self.assertEqual(T.sma([1, 2, 3, 4, 5], 3), [None, None, 2.0, 3.0, 4.0])

    def test_ema_seeded_with_sma(self):
        e = T.ema([1, 2, 3, 4, 5], 3)
        self.assertEqual(e[:2], [None, None])
        self.assertAlmostEqual(e[2], 2.0)
        self.assertAlmostEqual(e[3], 4 * 0.5 + 2.0 * 0.5)
        self.assertAlmostEqual(e[4], 5 * 0.5 + 3.0 * 0.5)

    def test_rsi_extremes_and_wilder_value(self):
        self.assertEqual(T.rsi(list(range(1, 30)), 14)[-1], 100.0)
        self.assertEqual(T.rsi(list(range(30, 1, -1)), 14)[-1], 0.0)
        # textbook check: alternating +1/-1 gives RSI around 50
        alt = [10 + (i % 2) for i in range(60)]
        self.assertAlmostEqual(T.rsi(alt, 14)[-1], 50, delta=4)
        # hand calc for n=2: changes +1, +1, -1 -> ag=1, al=0 -> 100; then ag=(1*1+0)/2=0.5, al=(0+1)/2=0.5 -> 50
        self.assertEqual(T.rsi([1, 2, 3, 2], 2), [None, None, 100.0, 50.0])

    def test_macd_constant_series_is_zero(self):
        line, sig, hist = T.macd([100.0] * 60)
        self.assertAlmostEqual(line[-1], 0)
        self.assertAlmostEqual(sig[-1], 0)
        self.assertAlmostEqual(hist[-1], 0)
        self.assertIsNone(line[24])
        self.assertIsNotNone(line[25])

    def test_drawdown_and_volatility(self):
        self.assertAlmostEqual(T.max_drawdown([100, 120, 90, 130, 117]), 90 / 120 - 1)
        self.assertIsNone(T.volatility([100] * 10))
        r = [100 * math.exp(0.01 * ((-1) ** i)) for i in range(100)]
        self.assertGreater(T.volatility(r), 0.2)

    def test_beta_and_correlation(self):
        base = [100.0]
        for i in range(150):
            base.append(base[-1] * (1 + 0.01 * math.sin(i)))
        a = series(base)
        double = [100.0]
        for x, y in zip(base, base[1:]):
            double.append(double[-1] * (1 + 2 * (y / x - 1)))
        self.assertAlmostEqual(T.beta(series(double).bars, a.bars), 2.0, places=6)
        self.assertAlmostEqual(T.correlation(series(double).bars, a.bars), 1.0, places=6)
        self.assertIsNone(T.beta(a.bars[:30], a.bars[:30]))  # too few observations

    def test_pivots_and_levels(self):
        highs = [1, 2, 5, 2, 1, 2, 3, 2, 1]
        lows = [h - 0.5 for h in highs]
        ph, pl = T.pivots(highs, lows, 2)
        self.assertEqual(ph, [(2, 5), (6, 3)])  # index 6 is the max of its 2-bar window too
        self.assertIn((4, 0.5), pl)
        self.assertEqual(T.cluster_levels([(0, 100), (1, 101), (2, 150)], 0.02), [(100.5, 2), (150, 1)])


class Analyse(unittest.TestCase):
    def test_insufficient_history(self):
        ta = T.analyse(series([100 + i for i in range(10)]))
        self.assertEqual(ta.values, {})
        self.assertTrue(ta.insufficient)
        self.assertEqual(T.analyse(None).insufficient, ["no price data"])

    def test_full_run(self):
        closes = [100 + 10 * math.sin(i / 10) + i * 0.1 for i in range(260)]
        ta = T.analyse(series(closes))
        self.assertAlmostEqual(ta.values["sma_20"], sum(closes[-20:]) / 20)
        self.assertIsNotNone(ta.values["sma_200"])
        self.assertTrue(all(lv < closes[-1] for lv, _ in ta.support))
        self.assertTrue(all(lv > closes[-1] for lv, _ in ta.resistance))
        self.assertAlmostEqual(ta.values["avg_traded_value_20d_cr"], sum(c * 1000 for c in closes[-20:]) / 20 / 1e7)


if __name__ == "__main__":
    unittest.main()
