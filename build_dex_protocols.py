from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

DEX_OVERVIEW_PATH = RAW_DIR / "defillama_dex_volume_overview.json"
PROTOCOLS_PATH = RAW_DIR / "defillama_protocols.json"
OUTPUT_PATH = PROCESSED_DIR / "chain_dex_protocols.csv"

CHAIN_MAP = {
    "ethereum": "Ethereum",
    "solana": "Solana",
    "bsc": "BSC",
    "base": "Base",
    "arbitrum": "Arbitrum",
    "polygon": "Polygon",
    "optimism": "OP Mainnet",
    "avax": "Avalanche",
    "tron": "Tron",
    "bitcoin": "Bitcoin",
    "robinhood": "Robinhood Chain",
    "arc": "Arc",
}

TOKEN_OVERRIDES = {
    "0x": "ZRX",
    "1inch Aqua": "1INCH",
    "Aerodrome Slipstream": "AERO",
    "Aerodrome V1": "AERO",
    "Balancer V1": "BAL",
    "Balancer V2": "BAL",
    "Balancer V3": "BAL",
    "Camelot V3": "GRAIL",
    "Curve DEX": "CRV",
    "Fluid DEX": "FLUID",
    "GMGN": "GMGN",
    "Meteora DLMM": "MET",
    "Orca DEX": "ORCA",
    "PancakeSwap AMM": "CAKE",
    "PancakeSwap AMM V3": "CAKE",
    "PancakeSwap Infinity": "CAKE",
    "Pendle V2": "PENDLE",
    "Polymarket International": "POLY",
    "PumpSwap": "PUMP",
    "Raydium AMM": "RAY",
    "SUNSwap V1": "SUN",
    "SUNSwap V2": "SUN",
    "SUNSwap V3": "SUN",
    "SushiSwap": "SUSHI",
    "SushiSwap V3": "SUSHI",
    "Uniswap V2": "UNI",
    "Uniswap V3": "UNI",
    "Uniswap V4": "UNI",
    "Velodrome V2": "VELO",
    "Velodrome V3": "VELO",
    "WOOFi Swap": "WOO",
}


def request_json(url: str) -> Any:
    req = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "public-chain-data-mining/0.1 (+local research)",
        },
    )
    with urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def load_protocols() -> list[dict[str, Any]]:
    if PROTOCOLS_PATH.exists():
        return json.loads(PROTOCOLS_PATH.read_text(encoding="utf-8"))
    protocols = request_json("https://api.llama.fi/protocols")
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROTOCOLS_PATH.write_text(
        json.dumps(protocols, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return protocols


def clean_symbol(symbol: Any) -> str | None:
    if not symbol:
        return None
    text = str(symbol).strip()
    if not text or text == "-":
        return None
    return text.upper()


def build_symbol_indexes(protocols: list[dict[str, Any]]) -> dict[str, str]:
    index: dict[str, str] = {}
    for protocol in protocols:
        symbol = clean_symbol(protocol.get("symbol"))
        if not symbol:
            continue
        for key in [
            protocol.get("slug"),
            protocol.get("name"),
            protocol.get("displayName"),
        ]:
            if key:
                index[str(key).lower()] = symbol
    return index


def find_token_symbol(protocol: dict[str, Any], index: dict[str, str]) -> str | None:
    name = protocol.get("displayName") or protocol.get("name")
    if name in TOKEN_OVERRIDES:
        return TOKEN_OVERRIDES[name]
    for key in [
        protocol.get("slug"),
        protocol.get("name"),
        protocol.get("displayName"),
        protocol.get("module"),
    ]:
        if key and str(key).lower() in index:
            return index[str(key).lower()]
    for linked in protocol.get("linkedProtocols") or []:
        if str(linked).lower() in index:
            return index[str(linked).lower()]
        if linked in TOKEN_OVERRIDES:
            return TOKEN_OVERRIDES[linked]
    return None


def main() -> None:
    dex = json.loads(DEX_OVERVIEW_PATH.read_text(encoding="utf-8"))
    protocols = load_protocols()
    symbol_index = build_symbol_indexes(protocols)

    rows = []
    for protocol in dex.get("protocols", []):
        name = protocol.get("displayName") or protocol.get("name")
        token_symbol = find_token_symbol(protocol, symbol_index)
        for chain_key, chain_name in CHAIN_MAP.items():
            breakdown_24h = (protocol.get("breakdown24h") or {}).get(chain_key, {})
            breakdown_30d = (protocol.get("breakdown30d") or {}).get(chain_key, {})
            volume_24h = (
                sum(float(value or 0) for value in breakdown_24h.values())
                if isinstance(breakdown_24h, dict)
                else 0
            )
            volume_30d = (
                sum(float(value or 0) for value in breakdown_30d.values())
                if isinstance(breakdown_30d, dict)
                else 0
            )
            if volume_24h or volume_30d:
                rows.append(
                    {
                        "chain_key": chain_key,
                        "chain": chain_name,
                        "dex": name,
                        "token_symbol": token_symbol,
                        "slug": protocol.get("slug"),
                        "category": protocol.get("category"),
                        "volume_24h_usd": volume_24h,
                        "volume_30d_usd": volume_30d,
                        "protocol_total_24h_usd": protocol.get("total24h"),
                        "protocol_total_30d_usd": protocol.get("total30d"),
                        "protocol_change_1d_pct": protocol.get("change_1d"),
                        "protocol_change_7d_pct": protocol.get("change_7d"),
                        "protocol_change_1m_pct": protocol.get("change_1m"),
                    }
                )

    rows.sort(key=lambda row: (row["chain"], -row["volume_24h_usd"], -row["volume_30d_usd"]))
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
