"""
signals.py — Technical indicator helpers for BUY/SELL signal generation.
All functions are pure Python (stdlib only).
"""


def calculate_rsi(prices: list, period: int = 14) -> float:
    """Calculate Wilder's RSI for the given price series.

    Args:
        prices: List of closing prices (oldest → newest).
        period: RSI look-back period (default 14).

    Returns:
        RSI value as a float in [0, 100], or None if insufficient data.
    """
    if len(prices) < period + 1:
        return None

    gains = []
    losses = []
    for i in range(1, period + 1):
        change = prices[i] - prices[i - 1]
        gains.append(change if change > 0 else 0.0)
        losses.append(-change if change < 0 else 0.0)

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    # Wilder's smoothing for remaining data points
    for i in range(period + 1, len(prices)):
        change = prices[i] - prices[i - 1]
        gain = change if change > 0 else 0.0
        loss = -change if change < 0 else 0.0
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def calculate_sma(prices: list, period: int = 20) -> float:
    """Calculate Simple Moving Average over the last *period* prices.

    Args:
        prices: List of prices (oldest → newest).
        period: Number of periods to average (default 20).

    Returns:
        SMA value as a float, or None if insufficient data.
    """
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period


def detect_volume_spike(volumes: list, threshold: float = 1.5) -> bool:
    """Detect whether the latest volume is a spike relative to the average.

    Args:
        volumes: List of volume values (oldest → newest); must have ≥ 2 entries.
        threshold: Multiplier above which latest volume is considered a spike (default 1.5).

    Returns:
        True if latest volume > threshold * average of all prior volumes, else False.
    """
    if len(volumes) < 2:
        return False
    prior = volumes[:-1]
    avg = sum(prior) / len(prior)
    if avg == 0:
        return False
    return volumes[-1] > threshold * avg
