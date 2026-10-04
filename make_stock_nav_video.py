from __future__ import annotations

import json
import math
import shutil
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

import imageio_ffmpeg
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont


BASE_DIR = Path(__file__).resolve().parent
OUT_DIR = BASE_DIR / "reports" / "videos"
FRAME_DIR = OUT_DIR / "mu_nav_frames"

TICKER = "MU"
COMPANY = "美光科技"
INITIAL_CASH_CNY = 1_000_000.0
USD_CNY_RATE = 6.7048
INITIAL_CASH = INITIAL_CASH_CNY / USD_CNY_RATE
YEARS = 10
FPS = 15
DURATION_SECONDS = 36
WIDTH, HEIGHT = 1080, 1920
ROLLING_WINDOW_DAYS = 730


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts/msyhbd.ttc" if bold else "msyh.ttc"),
        Path("C:/Windows/Fonts/simhei.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


FONT_H1 = font(72, True)
FONT_H2 = font(46, True)
FONT_BODY = font(34)
FONT_SMALL = font(26)
FONT_TINY = font(22)
FONT_NUMBER = font(58, True)


def request_json(url: str) -> dict:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 public-chain-data-mining/0.1",
        },
    )
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_yahoo_chart(ticker: str, start: datetime, end: datetime) -> pd.DataFrame:
    period1 = int(start.timestamp())
    period2 = int(end.timestamp())
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(ticker)}"
        f"?period1={period1}&period2={period2}&interval=1d&events=history&includeAdjustedClose=true"
    )
    payload = request_json(url)
    result = payload.get("chart", {}).get("result", [None])[0]
    if not result:
        raise RuntimeError(f"No chart data returned for {ticker}")
    timestamps = result.get("timestamp", [])
    adjclose = result.get("indicators", {}).get("adjclose", [{}])[0].get("adjclose", [])
    close = result.get("indicators", {}).get("quote", [{}])[0].get("close", [])
    rows = []
    for ts, adj, raw_close in zip(timestamps, adjclose, close):
        price = adj if adj is not None else raw_close
        if price is None:
            continue
        rows.append(
            {
                "date": datetime.fromtimestamp(ts, tz=timezone.utc).date(),
                "adj_close": float(price),
                "close": float(raw_close) if raw_close is not None else None,
            }
        )
    if not rows:
        raise RuntimeError(f"No usable prices returned for {ticker}")
    return pd.DataFrame(rows).drop_duplicates("date").sort_values("date").reset_index(drop=True)


def compute_backtest(prices: pd.DataFrame) -> pd.DataFrame:
    start_price = prices["adj_close"].iloc[0]
    shares = INITIAL_CASH / start_price
    prices = prices.copy()
    prices["shares"] = shares
    prices["portfolio_value"] = prices["adj_close"] * shares
    prices["nav"] = prices["portfolio_value"] / INITIAL_CASH
    prices["running_peak"] = prices["portfolio_value"].cummax()
    prices["drawdown"] = prices["portfolio_value"] / prices["running_peak"] - 1.0
    return prices


def money(value: float) -> str:
    if abs(value) >= 100_000_000:
        return f"{value / 100_000_000:.2f}亿元"
    if abs(value) >= 10_000:
        return f"{value / 10_000:.2f}万元"
    return f"{value:,.0f}元"


def usd_to_cny(value: float) -> float:
    return value * USD_CNY_RATE


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def nice_multiple(value: float) -> str:
    return f"{value:.1f}x"


def line_points(values: np.ndarray, x0: int, y0: int, w: int, h: int) -> list[tuple[int, int]]:
    lo = float(np.min(values))
    hi = float(np.max(values))
    if math.isclose(lo, hi):
        hi = lo + 1
    xs = np.linspace(x0, x0 + w, len(values))
    ys = y0 + h - ((values - lo) / (hi - lo)) * h
    return [(int(x), int(y)) for x, y in zip(xs, ys)]


def draw_card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], title: str, value: str, sub: str = "") -> None:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=28, fill=(19, 27, 43), outline=(55, 69, 95), width=2)
    draw.text((x1 + 28, y1 + 22), title, fill=(148, 163, 184), font=FONT_SMALL)
    draw.text((x1 + 28, y1 + 62), value, fill=(248, 250, 252), font=FONT_H2)
    if sub:
        draw.text((x1 + 28, y1 + 124), sub, fill=(93, 213, 184), font=FONT_TINY)


def draw_frame(backtest: pd.DataFrame, end_idx: int, final_stats: dict, frame_no: int, total_frames: int) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), (8, 12, 22))
    draw = ImageDraw.Draw(img)

    # Background grid.
    for y in range(260, 1510, 110):
        draw.line((70, y, WIDTH - 70, y), fill=(18, 28, 45), width=1)
    for x in range(90, WIDTH - 80, 120):
        draw.line((x, 260, x, 1510), fill=(14, 22, 36), width=1)

    current = backtest.iloc[end_idx]
    current_date = current["date"]
    window_start = current_date - timedelta(days=ROLLING_WINDOW_DAYS)
    shown = backtest[(backtest["date"] >= window_start) & (backtest.index <= end_idx)]
    if len(shown) < 8:
        shown = backtest.iloc[: end_idx + 1]
    history_to_date = backtest.iloc[: end_idx + 1]
    progress = frame_no / max(total_frames - 1, 1)

    draw.text((70, 72), f"十年前买入 {COMPANY}（{TICKER}）", fill=(248, 250, 252), font=FONT_H1)
    draw.text((72, 160), "复权收盘价净值回测 · 一次性买入并持有", fill=(148, 163, 184), font=FONT_BODY)
    draw.rounded_rectangle((72, 220, 388, 274), radius=24, fill=(22, 78, 99))
    draw.text((100, 232), f"本金 {money(INITIAL_CASH_CNY)}", fill=(236, 253, 245), font=FONT_SMALL)

    chart_box = (80, 350, WIDTH - 80, 1060)
    draw.rounded_rectangle(chart_box, radius=30, fill=(11, 18, 32), outline=(39, 53, 80), width=2)
    x0, y0, x2, y2 = chart_box
    chart_pad = 58
    pts = line_points(shown["nav"].to_numpy(), x0 + chart_pad, y0 + chart_pad, x2 - x0 - chart_pad * 2, y2 - y0 - chart_pad * 2)
    if len(pts) > 1:
        fill_poly = pts + [(pts[-1][0], y2 - chart_pad), (pts[0][0], y2 - chart_pad)]
        draw.polygon(fill_poly, fill=(10, 62, 75))
        draw.line(pts, fill=(94, 234, 212), width=6, joint="curve")
        draw.ellipse((pts[-1][0] - 10, pts[-1][1] - 10, pts[-1][0] + 10, pts[-1][1] + 10), fill=(250, 204, 21))
        label = f"{nice_multiple(float(current['nav']))}  {money(usd_to_cny(float(current['portfolio_value'])))}"
        label_x = min(pts[-1][0] + 18, x2 - chart_pad - 320)
        label_y = max(y0 + 92, min(pts[-1][1] - 28, y2 - chart_pad - 42))
        text_box = draw.textbbox((label_x, label_y), label, font=FONT_TINY)
        draw.rounded_rectangle(
            (text_box[0] - 12, text_box[1] - 8, text_box[2] + 12, text_box[3] + 8),
            radius=14,
            fill=(15, 23, 42),
            outline=(94, 234, 212),
            width=1,
        )
        draw.text((label_x, label_y), label, fill=(236, 253, 245), font=FONT_TINY)

    draw.text((x0 + 40, y0 + 26), "滚动净值窗口", fill=(226, 232, 240), font=FONT_H2)
    draw.text((x2 - 260, y0 + 34), str(current["date"]), fill=(148, 163, 184), font=FONT_SMALL)
    draw.text((x0 + 42, y2 - 54), str(shown["date"].iloc[0]), fill=(100, 116, 139), font=FONT_TINY)
    draw.text((x2 - 180, y2 - 54), str(shown["date"].iloc[-1]), fill=(100, 116, 139), font=FONT_TINY)

    draw.text((82, 1120), "当前回测结果", fill=(248, 250, 252), font=FONT_H2)
    draw_card(draw, (80, 1190, 505, 1370), "当前价值", money(usd_to_cny(float(current["portfolio_value"]))), f"净值 {nice_multiple(float(current['nav']))}")
    draw_card(draw, (575, 1190, 1000, 1370), "累计收益", pct(float(current["nav"] - 1)), f"持有 {len(history_to_date):,} 个交易日")

    draw_card(draw, (80, 1415, 505, 1595), "最终年化", pct(final_stats["cagr"] * progress), "随曲线推进显示")
    draw_card(draw, (575, 1415, 1000, 1595), "最大回撤", pct(float(history_to_date["drawdown"].min())), "历史峰值到低点")

    bar_x, bar_y, bar_w, bar_h = 80, 1675, 920, 22
    draw.rounded_rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), radius=12, fill=(30, 41, 59))
    draw.rounded_rectangle((bar_x, bar_y, bar_x + int(bar_w * progress), bar_y + bar_h), radius=12, fill=(94, 234, 212))

    final_text = (
        f"滚动窗口约 {ROLLING_WINDOW_DAYS // 365} 年；人民币本金，按 1 USD = {USD_CNY_RATE:.4f} CNY 折算。"
    )
    draw.text((80, 1730), final_text, fill=(148, 163, 184), font=FONT_SMALL)
    draw.text((80, 1780), "提示：历史回测不代表未来收益。", fill=(100, 116, 139), font=FONT_TINY)

    return img


def build_video() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if FRAME_DIR.exists():
        shutil.rmtree(FRAME_DIR)
    FRAME_DIR.mkdir(parents=True)

    end = datetime.now(timezone.utc) + timedelta(days=1)
    try:
        start = end.replace(year=end.year - YEARS)
    except ValueError:
        start = end.replace(year=end.year - YEARS, day=28)
    prices = fetch_yahoo_chart(TICKER, start, end)
    backtest = compute_backtest(prices)
    csv_path = OUT_DIR / f"{TICKER.lower()}_{YEARS}y_nav_backtest.csv"
    backtest.to_csv(csv_path, index=False, encoding="utf-8-sig")

    start_date = backtest["date"].iloc[0]
    end_date = backtest["date"].iloc[-1]
    final_value = float(backtest["portfolio_value"].iloc[-1])
    final_value_cny = usd_to_cny(final_value)
    total_return = final_value / INITIAL_CASH - 1
    days = (end_date - start_date).days
    cagr = (final_value / INITIAL_CASH) ** (365.25 / days) - 1
    max_drawdown = float(backtest["drawdown"].min())
    final_stats = {"cagr": cagr, "max_drawdown": max_drawdown}

    total_frames = FPS * DURATION_SECONDS
    curve_indices = np.linspace(5, len(backtest) - 1, total_frames).astype(int)
    for frame_no, idx in enumerate(curve_indices):
        frame = draw_frame(backtest, int(idx), final_stats, frame_no, total_frames)
        frame.save(FRAME_DIR / f"frame_{frame_no:04d}.png", optimize=True)

    cover = draw_frame(backtest, len(backtest) - 1, final_stats, total_frames - 1, total_frames)
    cover_path = OUT_DIR / f"{TICKER.lower()}_{YEARS}y_nav_rolling_cny_cover.png"
    cover.save(cover_path)

    mp4_path = OUT_DIR / f"{TICKER.lower()}_{YEARS}y_nav_rolling_cny_backtest.mp4"
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(FRAME_DIR / "frame_%04d.png"),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(mp4_path),
        ],
        check=True,
    )
    shutil.rmtree(FRAME_DIR)

    summary_path = OUT_DIR / f"{TICKER.lower()}_{YEARS}y_nav_rolling_cny_summary.json"
    summary = {
        "ticker": TICKER,
        "company": COMPANY,
        "initial_cash_cny": INITIAL_CASH_CNY,
        "initial_cash_usd": INITIAL_CASH,
        "usd_cny_rate": USD_CNY_RATE,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "start_adj_close": float(backtest["adj_close"].iloc[0]),
        "end_adj_close": float(backtest["adj_close"].iloc[-1]),
        "final_value_usd": final_value,
        "final_value_cny": final_value_cny,
        "total_return": total_return,
        "multiple": final_value / INITIAL_CASH,
        "cagr": cagr,
        "max_drawdown": max_drawdown,
        "video": str(mp4_path),
        "cover": str(cover_path),
        "csv": str(csv_path),
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    start_time = time.time()
    build_video()
    print(f"Done in {time.time() - start_time:.1f}s")
