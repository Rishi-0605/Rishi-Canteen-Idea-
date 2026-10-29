"""Technical analyst: indicators from daily OHLCV.

SMA, EMA, RSI (Wilder), MACD, swing-pivot support/resistance, 52-week range,
average traded value, annualised volatility, max drawdown, beta vs benchmark.
Every indicator needs a minimum number of bars and returns None below it.
These are descriptive statistics of past prices, not forecasts.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

TRADING_DAYS = 252


def sma(xs: list, n: int) -> list:
    out = [None] * len(xs)
    if n <= 0:
        raise ValueError("window must be positive")
    s = 0.0
    for i, x in enumerate(xs):
        s += x
        if i >= n:
            s -= xs[i - n]
        if i >= n - 1:
            out[i] = s / n
    return out


def ema(xs: list, n: int) -> list:
    """EMA seeded with the SMA of the first n values (alpha = 2/(n+1))."""
    out = [None] * len(xs)
    if len(xs) < n:
        return out
    k = 2.0 / (n + 1)
    prev = sum(xs[:n]) / n
    out[n - 1] = prev
    for i in range(n, len(xs)):
        prev = xs[i] * k + prev * (1 - k)
        out[i] = prev
    return out


def rsi(closes: list, n: int = 14) -> list:
    """Wilder's RSI: first average = simple mean of n changes, then smoothed."""
    out = [None] * len(closes)
    if len(closes) <= n:
        return out
    gains = losses = 0.0
    for i in range(1, n + 1):
        ch = closes[i] - closes[i - 1]
        gains += max(ch, 0)
        losses += max(-ch, 0)
    ag, al = gains / n, losses / n
    out[n] = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
    for i in range(n + 1, len(closes)):
        ch = closes[i] - closes[i - 1]
        ag = (ag * (n - 1) + max(ch, 0)) / n
        al = (al * (n - 1) + max(-ch, 0)) / n
        out[i] = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
    return out


def macd(closes: list, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
    ef, es = ema(closes, fast), ema(closes, slow)
    line = [(a - b) if a is not None and b is not None else None for a, b in zip(ef, es)]
    valid = [x for x in line if x is not None]
    sig_vals = ema(valid, signal)
    sig = [None] * (len(line) - len(valid)) + sig_vals
    hist = [(a - b) if a is not None and b is not None else None for a, b in zip(line, sig)]
    return line, sig, hist


def pivots(highs: list, lows: list, w: int = 5) -> tuple:
    """Swing highs/lows: a bar whose high (low) is the max (min) of the w bars each side."""
    ph, pl = [], []
    for i in range(w, len(highs) - w):
        if highs[i] == max(highs[i - w:i + w + 1]):
            ph.append((i, highs[i]))
        if lows[i] == min(lows[i - w:i + w + 1]):
            pl.append((i, lows[i]))
    return ph, pl


def cluster_levels(points: list, tol: float = 0.02) -> list:
    """Group nearby pivot prices; return [(level, touches)] strongest first."""
    levels = []
    for _, p in sorted(points, key=lambda t: t[1]):
        if levels and abs(p / levels[-1][0] - 1) <= tol:
            lvl, n = levels[-1]
            levels[-1] = ((lvl * n + p) / (n + 1), n + 1)
        else:
            levels.append((p, 1))
    return sorted(levels, key=lambda t: (-t[1], t[0]))


def max_drawdown(closes: list) -> Optional[float]:
    if len(closes) < 2:
        return None
    peak, mdd = closes[0], 0.0
    for c in closes:
        peak = max(peak, c)
        mdd = min(mdd, c / peak - 1)
    return mdd


def log_returns(closes: list) -> list:
    return [math.log(b / a) for a, b in zip(closes, closes[1:]) if a > 0 and b > 0]


def volatility(closes: list) -> Optional[float]:
    r = log_returns(closes)
    if len(r) < 20:
        return None
    m = sum(r) / len(r)
    var = sum((x - m) ** 2 for x in r) / (len(r) - 1)
    return math.sqrt(var) * math.sqrt(TRADING_DAYS)


def aligned_returns(a_bars: list, b_bars: list) -> tuple:
    """Daily simple returns on dates both series traded."""
    bmap = {b.date: b.close for b in b_bars}
    common = [x for x in a_bars if x.date in bmap]
    ra, rb = [], []
    for p, q in zip(common, common[1:]):
        ra.append(q.close / p.close - 1)
        rb.append(bmap[q.date] / bmap[p.date] - 1)
    return ra, rb


def beta(stock_bars: list, bench_bars: list, min_obs: int = 60) -> Optional[float]:
    ra, rb = aligned_returns(stock_bars, bench_bars)
    if len(ra) < min_obs:
        return None
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb)) / (len(ra) - 1)
    var = sum((y - mb) ** 2 for y in rb) / (len(rb) - 1)
    return cov / var if var > 0 else None


def correlation(a_bars: list, b_bars: list, min_obs: int = 60) -> Optional[float]:
    ra, rb = aligned_returns(a_bars, b_bars)
    if len(ra) < min_obs:
        return None
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    sa = math.sqrt(sum((x - ma) ** 2 for x in ra))
    sb = math.sqrt(sum((y - mb) ** 2 for y in rb))
    if sa == 0 or sb == 0:
        return None
    return sum((x - ma) * (y - mb) for x, y in zip(ra, rb)) / (sa * sb)


@dataclass
class TechnicalAnalysis:
    as_of: Optional[str]
    bars: int
    last_close: Optional[float]
    values: dict = field(default_factory=dict)  # name -> float|None
    support: list = field(default_factory=list)
    resistance: list = field(default_factory=list)
    signals: list = field(default_factory=list)  # descriptive observations
    insufficient: list = field(default_factory=list)
    source_id: Optional[str] = None


def analyse(series, bench=None, sma_windows=(20, 50, 200), rsi_period=14, macd_p=(12, 26, 9),
            pivot_window=5, min_bars=30) -> TechnicalAnalysis:
    if not series or not series.bars:
        return TechnicalAnalysis(None, 0, None, insufficient=["no price data"])
    bars = series.bars
    c = [b.close for b in bars]
    ta = TechnicalAnalysis(bars[-1].date.isoformat(), len(bars), c[-1], source_id=series.source.id)
    if len(bars) < min_bars:
        ta.insufficient.append("only %d bars (need %d)" % (len(bars), min_bars))
        return ta
    v = ta.values
    for w in sma_windows:
        s = sma(c, w)
        v["sma_%d" % w] = s[-1]
        if s[-1] is None:
            ta.insufficient.append("SMA%d needs %d bars" % (w, w))
    v["ema_20"] = ema(c, 20)[-1]
    r = rsi(c, rsi_period)
    v["rsi_%d" % rsi_period] = r[-1]
    line, sig, hist = macd(c, *macd_p)
    v["macd"], v["macd_signal"], v["macd_hist"] = line[-1], sig[-1], hist[-1]
    window = bars[-TRADING_DAYS:]
    v["high_52w"] = max(b.high for b in window)
    v["low_52w"] = min(b.low for b in window)
    v["pct_from_52w_high"] = (c[-1] / v["high_52w"] - 1) * 100
    tv = [b.close * b.volume for b in bars[-20:]]
    v["avg_traded_value_20d_cr"] = sum(tv) / len(tv) / 1e7 if tv else None
    v["avg_volume_20d"] = sum(b.volume for b in bars[-20:]) / min(20, len(bars))
    v["volume_ratio_5d_vs_20d"] = ((sum(b.volume for b in bars[-5:]) / 5) / v["avg_volume_20d"]
                                   if v["avg_volume_20d"] else None)
    v["volatility_ann"] = volatility(c[-TRADING_DAYS:])
    v["max_drawdown_1y"] = max_drawdown(c[-TRADING_DAYS:])
    v["return_1m"] = (c[-1] / c[-22] - 1) * 100 if len(c) > 22 else None
    v["return_6m"] = (c[-1] / c[-127] - 1) * 100 if len(c) > 127 else None
    v["return_1y"] = (c[-1] / c[-253] - 1) * 100 if len(c) > 253 else None
    v["beta_1y"] = beta(bars[-TRADING_DAYS - 1:], bench.bars) if bench and bench.bars else None
    # support / resistance from swing pivots in the last year
    hs, ls = [b.high for b in window], [b.low for b in window]
    ph, pl = pivots(hs, ls, pivot_window)
    levels = cluster_levels(ph + pl)
    last = c[-1]
    ta.support = sorted([(round(l, 2), n) for l, n in levels if l < last], key=lambda t: -t[0])[:3]
    ta.resistance = sorted([(round(l, 2), n) for l, n in levels if l > last], key=lambda t: t[0])[:3]
    # descriptive observations
    s50, s200 = v.get("sma_50"), v.get("sma_200")
    if s200 is not None:
        ta.signals.append("price %s 200-day average (%.2f)" % ("above" if last > s200 else "below", s200))
        if s50 is not None:
            ta.signals.append("50-day average %s 200-day average" % ("above" if s50 > s200 else "below"))
    rv = v.get("rsi_%d" % rsi_period)
    if rv is not None:
        zone = "overbought zone (>70)" if rv > 70 else "oversold zone (<30)" if rv < 30 else "neutral range"
        ta.signals.append("RSI %.1f: %s" % (rv, zone))
    if v["macd_hist"] is not None:
        ta.signals.append("MACD %s its signal line" % ("above" if v["macd_hist"] > 0 else "below"))
    return ta
