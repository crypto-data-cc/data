from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
STABLECOINS_URL = "https://stablecoins.llama.fi/stablecoins?includePrices=true"


def request_json(url: str) -> Any:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "public-chain-data-mining/0.1 (+local research)",
        },
    )
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def load_or_fetch_json(path: Path, url: str) -> Any:
    try:
        payload = request_json(url)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload
    except (HTTPError, URLError, TimeoutError):
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        raise


def pegged_usd(value: dict[str, Any] | None) -> float | None:
    if not value:
        return None
    amount = value.get("peggedUSD")
    return float(amount) if amount is not None else None


def normalized_change(current: float | None, previous: float | None) -> float | None:
    if current is None or previous in (None, 0):
        return None
    return (current - previous) / previous


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    payload = load_or_fetch_json(RAW_DIR / "defillama_stablecoins.json", STABLECOINS_URL)
    rows = []
    for asset in payload.get("peggedAssets", []):
        current = pegged_usd(asset.get("circulating"))
        previous = pegged_usd(asset.get("circulatingPrevMonth"))
        if current is None:
            continue
        rows.append(
            {
                "snapshot_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "stablecoin": asset.get("name"),
                "symbol": asset.get("symbol"),
                "peg_type": asset.get("pegType"),
                "peg_mechanism": asset.get("pegMechanism"),
                "market_cap_usd": current,
                "market_cap_previous_30d_usd": previous,
                "market_cap_30d_abs_change_usd": current - previous if previous is not None else None,
                "market_cap_30d_change": normalized_change(current, previous),
                "price_usd": asset.get("price"),
                "chains_count": len(asset.get("chainCirculating", {}) or {}),
                "data_source": "DefiLlama stablecoins",
            }
        )

    rows.sort(key=lambda row: row["market_cap_usd"] or 0, reverse=True)
    output = PROCESSED_DIR / "stablecoin_metrics.csv"
    with output.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {output}")


if __name__ == "__main__":
    main()
