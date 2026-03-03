"""Tests for scripts/signals.py — RSI, SMA, and volume-spike helpers."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts.signals import calculate_rsi, calculate_sma, detect_volume_spike


# ---------------------------------------------------------------------------
# SMA tests
# ---------------------------------------------------------------------------

def test_sma_basic():
    """SMA of [1..20] over period 20 should equal 10.5."""
    prices = list(range(1, 21))
    assert calculate_sma(prices, period=20) == 10.5


def test_sma_period_shorter_than_list():
    """SMA uses only the last *period* prices."""
    prices = [100, 200, 300, 400, 500]
    result = calculate_sma(prices, period=3)
    assert abs(result - 400.0) < 1e-9, f"Expected 400.0, got {result}"


def test_sma_insufficient_data():
    """Returns None when fewer prices than period."""
    assert calculate_sma([10, 20], period=5) is None


# ---------------------------------------------------------------------------
# RSI tests
# ---------------------------------------------------------------------------

def test_rsi_overbought():
    """Steadily rising prices should produce RSI > 70."""
    prices = [float(i) for i in range(1, 32)]  # 31 values, all gains
    rsi = calculate_rsi(prices, period=14)
    assert rsi is not None
    assert rsi > 70, f"Expected RSI > 70 for rising series, got {rsi}"


def test_rsi_oversold():
    """Steadily falling prices should produce RSI < 30."""
    prices = [float(i) for i in range(31, 0, -1)]  # 31 values, all losses
    rsi = calculate_rsi(prices, period=14)
    assert rsi is not None
    assert rsi < 30, f"Expected RSI < 30 for falling series, got {rsi}"


def test_rsi_insufficient_data():
    """Returns None when fewer than period+1 prices are provided."""
    assert calculate_rsi([10, 20, 30], period=14) is None


def test_rsi_known_value():
    """Validate RSI against a hand-calculated reference.

    Using 15 prices where first 14 diffs are all gains of 1 → avg_gain=1, avg_loss=0 → RSI=100.
    """
    prices = [float(i) for i in range(1, 16)]  # [1..15], 14 periods, all gains
    rsi = calculate_rsi(prices, period=14)
    assert rsi == 100.0, f"Expected 100.0, got {rsi}"


# ---------------------------------------------------------------------------
# Volume spike tests
# ---------------------------------------------------------------------------

def test_volume_spike_detected():
    prior = [100, 100, 100, 100]
    latest = [100, 100, 100, 100, 200]  # 200 > 1.5 * 100
    assert detect_volume_spike(latest, threshold=1.5) is True


def test_volume_spike_not_detected():
    volumes = [100, 100, 100, 100, 120]  # 120 < 1.5 * 100
    assert detect_volume_spike(volumes, threshold=1.5) is False


def test_volume_spike_insufficient_data():
    assert detect_volume_spike([500], threshold=1.5) is False
