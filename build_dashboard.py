from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
WEB_DIR = BASE_DIR / "web"


NUMBER_FIELDS = {
    "market_cap_usd",
    "token_circulating_market_cap_usd",
    "token_volume_24h_usd",
    "tvl_usd",
    "network_fees_24h_usd",
    "network_fees_30d_usd",
    "network_fees_previous_30d_usd",
    "network_fees_30d_change",
    "dex_volume_24h_usd",
    "tokenized_stock_value_usd",
    "tokenized_stock_asset_count",
    "tokenized_stock_market_share",
    "tokenized_stock_7d_change",
    "tokenized_stock_30d_change",
    "tokenized_stock_to_tvl",
    "tvl_to_mcap",
    "fees_24h_to_mcap",
    "fees_30d_to_mcap",
    "dex_volume_24h_to_tvl",
    "token_turnover_24h",
    "activity_score",
    "matched_protocol_count_volume",
    "matched_protocol_count_fees",
    "matched_protocol_count_holders_revenue",
    "token_market_cap_usd",
    "token_circulating_market_cap_usd",
    "token_price_usd",
    "volume_30d_usd",
    "volume_previous_30d_usd",
    "volume_30d_change",
    "fees_30d_usd",
    "fees_previous_30d_usd",
    "fees_30d_change",
    "fee_pe",
    "protocol_revenue_30d_usd",
    "protocol_revenue_previous_30d_usd",
    "protocol_revenue_30d_change",
    "holders_revenue_30d_usd",
    "holders_revenue_previous_30d_usd",
    "holders_revenue_30d_change",
    "holders_revenue_to_fees",
    "holders_revenue_pe",
    "burn_30d",
}

MISSING_VALUE_NOTES = {
    ("base", "market_cap_usd"): "Base 是 L2 网络，没有独立原生代币市值。",
    ("tron", "tokenized_stock_value_usd"): "RWA.xyz 当前未匹配到 Tron 的代币化美股/ETF数据。",
    ("bitcoin", "tokenized_stock_value_usd"): "RWA.xyz 当前未匹配到 Bitcoin 的代币化美股/ETF数据。",
}


def clean_value(key: str, value: str) -> Any:
    if value == "":
        return None
    if key in NUMBER_FIELDS:
        try:
            return float(value)
        except ValueError:
            return None
    return value


def read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return [
            {key: clean_value(key, value) for key, value in row.items()}
            for row in csv.DictReader(file)
        ]


def main() -> None:
    WEB_DIR.mkdir(parents=True, exist_ok=True)
    chains = read_csv(PROCESSED_DIR / "chain_metrics.csv")
    for row in chains:
        market_cap = row.get("market_cap_usd")
        monthly_fees = row.get("network_fees_30d_usd")
        row["fee_pe"] = (
            market_cap / (monthly_fees * 12)
            if isinstance(market_cap, float) and isinstance(monthly_fees, float) and monthly_fees > 0
            else None
        )
        notes = {}
        for (chain, field), note in MISSING_VALUE_NOTES.items():
            if row.get("chain") == chain and row.get(field) is None:
                notes[field] = note
        row["missing_notes"] = notes
    stock_networks = read_csv(PROCESSED_DIR / "tokenized_stock_networks.csv")
    stock_platforms = read_csv(PROCESSED_DIR / "tokenized_stock_platforms.csv")
    stock_aggregates = read_csv(PROCESSED_DIR / "tokenized_stock_aggregates.csv")
    dex_tokens_path = PROCESSED_DIR / "dex_token_metrics.csv"
    dex_token_components_path = PROCESSED_DIR / "dex_token_component_metrics.csv"
    dex_tokens = read_csv(dex_tokens_path) if dex_tokens_path.exists() else []
    dex_token_components = read_csv(dex_token_components_path) if dex_token_components_path.exists() else []

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sources": ["DefiLlama", "CoinPaprika", "RWA.xyz"],
        "chains": chains,
        "tokenized_stock_networks": stock_networks,
        "tokenized_stock_platforms": stock_platforms,
        "tokenized_stock_aggregates": stock_aggregates,
        "dex_tokens": dex_tokens,
        "dex_token_components": dex_token_components,
        "notes": {
            "nulls": "缺失或不适用的数据用 null 表示，页面显示为“暂无数据”。",
            "update": "运行 python main.py 后再运行 python build_dashboard.py，即可刷新静态网页数据。",
        },
    }
    data = json.dumps(payload, ensure_ascii=False, indent=2)
    (WEB_DIR / "dashboard-data.js").write_text(
        "window.DASHBOARD_DATA = " + data + ";\n",
        encoding="utf-8",
    )
    print(f"Wrote {WEB_DIR / 'dashboard-data.js'}")


if __name__ == "__main__":
    main()
