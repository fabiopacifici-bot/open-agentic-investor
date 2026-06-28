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


def check_trailing_stop_loss(
    current_price: float,
    avg_price: float,
    thirty_day_high: float,
    trailing_pct: float = 0.10,
    hard_stop_pct: float = 0.15,
) -> tuple:
    """Check whether a trailing stop or hard stop-loss has been triggered.

    Two stop types are evaluated independently:
    - **Trailing stop**: triggered when ``current_price < thirty_day_high * (1 - trailing_pct)``.
    - **Hard stop**: triggered when ``current_price < avg_price * (1 - hard_stop_pct)``.

    When both are triggered the one representing the *larger* loss (lower price
    relative to the respective reference) is returned.

    Args:
        current_price:   Most recent price of the asset.
        avg_price:       Average (cost-basis) price held.
        thirty_day_high: Highest price recorded over the past 30 trading days.
        trailing_pct:    Drop from 30-day high that triggers the trailing stop (default 10%).
        hard_stop_pct:   Drop from avg_price that triggers the hard stop (default 15%).

    Returns:
        Tuple of ``(triggered: bool, reason: str, stop_type: str)``.
        - *triggered*: True if either stop fired.
        - *reason*: Human-readable explanation, e.g.
          "Trailing stop: price $85.00 is 15.0% below 30-day high $100.00".
        - *stop_type*: ``"trailing"``, ``"hard"``, or ``"none"``.
    """
    trailing_threshold = thirty_day_high * (1 - trailing_pct)
    hard_threshold = avg_price * (1 - hard_stop_pct)

    trailing_triggered = current_price < trailing_threshold
    hard_triggered = current_price < hard_threshold

    if not trailing_triggered and not hard_triggered:
        return False, "", "none"

    if trailing_triggered and not hard_triggered:
        drop_pct = (thirty_day_high - current_price) / thirty_day_high * 100
        reason = (
            f"Trailing stop: price ${current_price:.2f} is {drop_pct:.1f}% "
            f"below 30-day high ${thirty_day_high:.2f}"
        )
        return True, reason, "trailing"

    if hard_triggered and not trailing_triggered:
        drop_pct = (avg_price - current_price) / avg_price * 100
        reason = (
            f"Hard stop: price ${current_price:.2f} is {drop_pct:.1f}% "
            f"below avg price ${avg_price:.2f}"
        )
        return True, reason, "hard"

    # Both triggered — return the one representing the larger loss
    trailing_drop = (thirty_day_high - current_price) / thirty_day_high
    hard_drop = (avg_price - current_price) / avg_price

    if trailing_drop >= hard_drop:
        drop_pct = trailing_drop * 100
        reason = (
            f"Trailing stop: price ${current_price:.2f} is {drop_pct:.1f}% "
            f"below 30-day high ${thirty_day_high:.2f}"
        )
        return True, reason, "trailing"
    else:
        drop_pct = hard_drop * 100
        reason = (
            f"Hard stop: price ${current_price:.2f} is {drop_pct:.1f}% "
            f"below avg price ${avg_price:.2f}"
        )
        return True, reason, "hard"
