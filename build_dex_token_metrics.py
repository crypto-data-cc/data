from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
DEFILLAMA_FEES_URL = "https://api.llama.fi/overview/fees?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true"


TOKEN_GROUPS = [
    {"token": "ZRX", "match": ["0x"]},
    {"token": "AERO", "match": ["Aerodrome", "Aero Lite"]},
    {"token": "GMGN", "match": ["GMGN"]},
    {"token": "UNI", "match": ["Uniswap"]},
    {"token": "CRV", "match": ["Curve"]},
    {"token": "1INCH", "match": ["1inch"]},
    {"token": "ORCA", "match": ["Orca"]},
    {"token": "RAY", "match": ["Raydium"]},
    {"token": "CAKE", "match": ["PancakeSwap"]},
    {"token": "GRAIL", "match": ["Camelot"]},
    {"token": "QUICK", "match": ["Quickswap"]},
    {"token": "VELO", "match": ["Velodrome"]},
    {"token": "JOE", "match": ["Joe "]},
    {"token": "SUN", "match": ["SUNSwap"]},
]

TOKEN_MARKET_IDS = {
    "ZRX": "zrx-0x",
    "AERO": "aero-aerodrome-finance",
    "UNI": "uni-uniswap",
    "CRV": "crv-curve-dao-token",
    "1INCH": "1inch-1inch",
    "ORCA": "orca-orca",
    "RAY": "ray-raydium",
    "CAKE": "cake-pancakeswap",
    "GRAIL": "grail-camelot-token",
    "QUICK": "quick-quickswap",
    "VELO": "velo-velodrome-finance",
    "JOE": "joe-lfj",
    "SUN": "sun-sun",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def request_json(url: str) -> Any:
    req = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "public-chain-data-mining/0.1 (+local research)",
        },
    )
    with urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def load_or_fetch_json(path: Path, url: str) -> Any:
    try:
        payload = request_json(url)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload
    except (HTTPError, URLError, TimeoutError):
        if path.exists():
            return load_json(path)
        raise


def protocol_name(protocol: dict[str, Any]) -> str:
    return protocol.get("displayName") or protocol.get("name") or ""


def matches_group(protocol: dict[str, Any], patterns: list[str]) -> bool:
    name = protocol_name(protocol)
    slug = str(protocol.get("slug") or "")
    haystack = f"{name} {slug}".lower()
    return any(pattern.lower() in haystack for pattern in patterns)


def normalized_change(current: float | None, previous: float | None) -> float | None:
    if current is None or previous in (None, 0):
        return None
    return (current - previous) / previous


def number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def load_token_market_data() -> dict[str, dict[str, Any]]:
    output = {}
    for token, coin_id in TOKEN_MARKET_IDS.items():
        path = RAW_DIR / f"coinpaprika_token_{token.lower()}.json"
        try:
            if path.exists():
                ticker = load_json(path)
            else:
                ticker = request_json(f"https://api.coinpaprika.com/v1/tickers/{coin_id}")
                path.write_text(json.dumps(ticker, ensure_ascii=False, indent=2), encoding="utf-8")
        except (HTTPError, URLError, RuntimeError):
            continue
        quote = ticker.get("quotes", {}).get("USD", {})
        price = quote.get("price")
        max_supply = ticker.get("max_supply")
        total_supply = ticker.get("total_supply")
        fdv_supply = max_supply or total_supply
        output[token] = {
            "coinpaprika_id": coin_id,
            "token_price_usd": price,
            "token_market_cap_usd": price * fdv_supply if price and fdv_supply else quote.get("market_cap"),
            "token_circulating_market_cap_usd": quote.get("market_cap"),
        }
    return output


def group_protocols(
    protocols: list[dict[str, Any]],
    patterns: list[str],
    category: str | None = None,
) -> list[dict[str, Any]]:
    rows = [protocol for protocol in protocols if matches_group(protocol, patterns)]
    if category is not None:
        rows = [protocol for protocol in rows if protocol.get("category") == category]
    return rows


def aggregate_protocols(protocols: list[dict[str, Any]]) -> dict[str, float | None]:
    total_30d = sum(number(protocol.get("total30d")) or 0 for protocol in protocols)
    previous_30d = sum(number(protocol.get("total60dto30d")) or 0 for protocol in protocols)
    return {
        "total_30d": total_30d if protocols else None,
        "previous_30d": previous_30d if previous_30d else None,
        "change_30d": normalized_change(total_30d, previous_30d),
    }


def component_rows(token: str, protocols: list[dict[str, Any]], metric: str) -> list[dict[str, Any]]:
    rows = []
    for protocol in protocols:
        total_30d = number(protocol.get("total30d"))
        previous_30d = number(protocol.get("total60dto30d"))
        rows.append(
            {
                "token": token,
                "metric": metric,
                "protocol": protocol_name(protocol),
                "slug": protocol.get("slug"),
                "total_30d_usd": total_30d,
                "previous_30d_usd": previous_30d,
                "change_30d": normalized_change(total_30d, previous_30d),
            }
        )
    return rows


def main() -> None:
    dex_overview = load_json(RAW_DIR / "defillama_dex_volume_overview.json")
    fees_overview = load_or_fetch_json(RAW_DIR / "defillama_fees_overview.json", DEFILLAMA_FEES_URL)
    holders_overview = load_or_fetch_json(
        RAW_DIR / "defillama_holders_revenue_overview.json",
        f"{DEFILLAMA_FEES_URL}&dataType=dailyHoldersRevenue",
    )
    protocol_revenue_overview = load_or_fetch_json(
        RAW_DIR / "defillama_protocol_revenue_overview.json",
        f"{DEFILLAMA_FEES_URL}&dataType=dailyProtocolRevenue",
    )
    dex_protocols = dex_overview.get("protocols", [])
    fee_protocols = fees_overview.get("protocols", [])
    holder_protocols = holders_overview.get("protocols", [])
    protocol_revenue_protocols = protocol_revenue_overview.get("protocols", [])
    token_market_data = load_token_market_data()

    rows = []
    components = []
    for group in TOKEN_GROUPS:
        token = group["token"]
        dex_matches = group_protocols(dex_protocols, group["match"])
        fee_matches = group_protocols(fee_protocols, group["match"], category="Dexs")
        holder_matches = group_protocols(holder_protocols, group["match"], category="Dexs")
        protocol_revenue_matches = group_protocols(protocol_revenue_protocols, group["match"], category="Dexs")
        volume = aggregate_protocols(dex_matches)
        fees = aggregate_protocols(fee_matches)
        holders_revenue = aggregate_protocols(holder_matches)
        protocol_revenue = aggregate_protocols(protocol_revenue_matches)
        token_market = token_market_data.get(token, {})
        token_market_cap = token_market.get("token_market_cap_usd")
        fee_pe = (
            token_market_cap / (fees["total_30d"] * 12)
            if token_market_cap is not None and fees["total_30d"] not in (None, 0)
            else None
        )
        holders_revenue_pe = (
            token_market_cap / (holders_revenue["total_30d"] * 12)
            if token_market_cap is not None and holders_revenue["total_30d"] not in (None, 0)
            else None
        )
        holders_revenue_to_fees = (
            holders_revenue["total_30d"] / fees["total_30d"]
            if holders_revenue["total_30d"] is not None and fees["total_30d"] not in (None, 0)
            else None
        )

        rows.append(
            {
                "token": token,
                "matched_protocol_count_volume": len(dex_matches),
                "matched_protocol_count_fees": len(fee_matches),
                "matched_protocol_count_holders_revenue": len(holder_matches),
                "matched_volume_protocols": "; ".join(protocol_name(p) for p in dex_matches),
                "matched_fee_protocols": "; ".join(protocol_name(p) for p in fee_matches),
                "matched_holders_revenue_protocols": "; ".join(protocol_name(p) for p in holder_matches),
                "token_market_cap_usd": token_market_cap,
                "token_circulating_market_cap_usd": token_market.get("token_circulating_market_cap_usd"),
                "token_price_usd": token_market.get("token_price_usd"),
                "token_market_data_source": token_market.get("coinpaprika_id"),
                "volume_30d_usd": volume["total_30d"],
                "volume_previous_30d_usd": volume["previous_30d"],
                "volume_30d_change": volume["change_30d"],
                "fees_30d_usd": fees["total_30d"],
                "fees_previous_30d_usd": fees["previous_30d"],
                "fees_30d_change": fees["change_30d"],
                "fee_pe": fee_pe,
                "protocol_revenue_30d_usd": protocol_revenue["total_30d"],
                "protocol_revenue_previous_30d_usd": protocol_revenue["previous_30d"],
                "protocol_revenue_30d_change": protocol_revenue["change_30d"],
                "holders_revenue_30d_usd": holders_revenue["total_30d"],
                "holders_revenue_previous_30d_usd": holders_revenue["previous_30d"],
                "holders_revenue_30d_change": holders_revenue["change_30d"],
                "holders_revenue_to_fees": holders_revenue_to_fees,
                "holders_revenue_pe": holders_revenue_pe,
                "burn_30d": holders_revenue["total_30d"],
                "burn_data_status": "以 DefiLlama Holders Revenue 作为回购/销毁/持有人收入代理，具体机制以协议说明为准",
                "data_source": "DefiLlama dimensions; DefiLlama holders revenue; CoinPaprika",
            }
        )
        components.extend(component_rows(token, dex_matches, "volume"))
        components.extend(component_rows(token, fee_matches, "fees"))
        components.extend(component_rows(token, holder_matches, "holders_revenue"))

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output = PROCESSED_DIR / "dex_token_metrics.csv"
    with output.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    component_output = PROCESSED_DIR / "dex_token_component_metrics.csv"
    with component_output.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(components[0].keys()))
        writer.writeheader()
        writer.writerows(components)

    print(f"Wrote {len(rows)} rows to {output}")
    print(f"Wrote {len(components)} component rows to {component_output}")


if __name__ == "__main__":
    main()
