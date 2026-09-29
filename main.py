from __future__ import annotations

import argparse
import csv
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from tokenized_stocks import (
    SOURCE_URL as TOKENIZED_STOCKS_SOURCE_URL,
    extract_next_data,
    league_rows,
    request_text,
)


BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
REPORT_DIR = BASE_DIR / "reports"

DEFAULT_CHAINS = [
    "ethereum",
    "solana",
    "bsc",
    "base",
    "arbitrum",
    "polygon",
    "optimism",
    "avalanche",
    "tron",
    "bitcoin",
    "robinhood",
    "arc",
]

CHAIN_CONFIG: dict[str, dict[str, str]] = {
    "ethereum": {"llama_name": "Ethereum", "breakdown_key": "ethereum", "coinpaprika_id": "eth-ethereum", "rwa_network": "Ethereum"},
    "solana": {"llama_name": "Solana", "breakdown_key": "solana", "coinpaprika_id": "sol-solana", "rwa_network": "Solana"},
    "bsc": {"llama_name": "BSC", "breakdown_key": "bsc", "coinpaprika_id": "bnb-binance-coin", "rwa_network": "BNB Chain"},
    "base": {"llama_name": "Base", "breakdown_key": "base", "coinpaprika_id": "", "rwa_network": "Base"},
    "arbitrum": {"llama_name": "Arbitrum", "breakdown_key": "arbitrum", "coinpaprika_id": "arb-arbitrum", "rwa_network": "Arbitrum"},
    "polygon": {"llama_name": "Polygon", "breakdown_key": "polygon", "coinpaprika_id": "pol-polygon-ecosystem-token", "rwa_network": "Polygon"},
    "optimism": {"llama_name": "OP Mainnet", "breakdown_key": "optimism", "coinpaprika_id": "op-optimism", "rwa_network": "Optimism"},
    "avalanche": {"llama_name": "Avalanche", "breakdown_key": "avax", "coinpaprika_id": "avax-avalanche", "rwa_network": "Avalanche C-Chain"},
    "tron": {"llama_name": "Tron", "breakdown_key": "tron", "coinpaprika_id": "trx-tron", "rwa_network": "Tron"},
    "bitcoin": {"llama_name": "Bitcoin", "breakdown_key": "bitcoin", "coinpaprika_id": "btc-bitcoin", "rwa_network": "Bitcoin"},
    "robinhood": {"llama_name": "Robinhood Chain", "breakdown_key": "robinhood", "coinpaprika_id": "", "rwa_network": "Robinhood"},
    "arc": {"llama_name": "Arc", "breakdown_key": "arc", "coinpaprika_id": "", "rwa_network": "Arc"},
}


def request_json(url: str, timeout: int = 30) -> Any:
    req = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "public-chain-data-mining/0.1 (+local research)",
        },
    )
    try:
        with urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:300]
        raise RuntimeError(f"HTTP {exc.code} for {url}: {body}") from exc
    except URLError as exc:
        raise RuntimeError(f"Network error for {url}: {exc}") from exc


def save_raw(name: str, payload: Any) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def fetch_llama_chains() -> list[dict[str, Any]]:
    return request_json("https://api.llama.fi/v2/chains")


def fetch_llama_overview(kind: str, data_type: str) -> dict[str, Any]:
    query = urlencode({"excludeTotalDataChartBreakdown": "true", "dataType": data_type})
    return request_json(f"https://api.llama.fi/overview/{kind}?{query}")


def fetch_llama_chain_fees(chain_key: str) -> dict[str, Any]:
    query = urlencode({"excludeTotalDataChartBreakdown": "true", "dataType": "dailyFees"})
    return request_json(f"https://api.llama.fi/overview/fees/{chain_key}?{query}")


def fetch_coinpaprika_ticker(coin_id: str) -> dict[str, Any] | None:
    if not coin_id:
        return None
    return request_json(f"https://api.coinpaprika.com/v1/tickers/{coin_id}")


def fetch_tokenized_stock_networks() -> dict[str, dict[str, Any]]:
    page = request_text(TOKENIZED_STOCKS_SOURCE_URL)
    data = extract_next_data(page)
    save_raw("rwa_xyz_stocks_next_data.json", data)
    page_props = data["props"]["pageProps"]
    networks = league_rows(page_props, "distributed", "networks")
    return {row["name"]: row for row in networks}


def sum_protocol_breakdown(
    protocols: list[dict[str, Any]], breakdown_field: str, chain_key: str
) -> float:
    total = 0.0
    for protocol in protocols:
        breakdown = protocol.get(breakdown_field) or {}
        chain_breakdown = breakdown.get(chain_key, {})
        if isinstance(chain_breakdown, dict):
            total += sum(float(value or 0) for value in chain_breakdown.values())
    return total


def get_chain_fee_window(
    fees: dict[str, Any], chain_key: str, breakdown_field: str
) -> float:
    return sum_protocol_breakdown(fees.get("protocols", []), breakdown_field, chain_key)


def safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator


def zscore(values: list[float | None], value: float | None) -> float:
    clean = [v for v in values if v is not None and math.isfinite(v)]
    if value is None or len(clean) < 2:
        return 0.0
    mean = sum(clean) / len(clean)
    variance = sum((v - mean) ** 2 for v in clean) / (len(clean) - 1)
    stdev = math.sqrt(variance)
    if stdev == 0:
        return 0.0
    return (value - mean) / stdev


def build_rows(chains: list[str]) -> list[dict[str, Any]]:
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")

    llama_chains = fetch_llama_chains()
    fees = fetch_llama_overview("fees", "dailyFees")
    dex_volume = fetch_llama_overview("dexs", "dailyVolume")
    tokenized_stock_by_network = fetch_tokenized_stock_networks()

    save_raw("defillama_chains.json", llama_chains)
    save_raw("defillama_fees_overview.json", fees)
    save_raw("defillama_dex_volume_overview.json", dex_volume)

    tvl_by_name = {item.get("name"): item for item in llama_chains}
    rows: list[dict[str, Any]] = []

    for chain in chains:
        config = CHAIN_CONFIG.get(chain)
        if not config:
            raise ValueError(f"Unsupported chain: {chain}. Add it to CHAIN_CONFIG first.")

        ticker = fetch_coinpaprika_ticker(config["coinpaprika_id"])
        if ticker:
            time.sleep(0.25)
            save_raw(f"coinpaprika_{chain}.json", ticker)

        quotes = (ticker or {}).get("quotes", {}).get("USD", {})
        chain_tvl = tvl_by_name.get(config["llama_name"], {})
        tvl = float(chain_tvl.get("tvl") or 0)
        circulating_market_cap = quotes.get("market_cap")
        price = quotes.get("price")
        max_supply = (ticker or {}).get("max_supply")
        total_supply = (ticker or {}).get("total_supply")
        fdv_supply = max_supply or total_supply
        token_fdv = price * fdv_supply if price and fdv_supply else None
        market_cap = token_fdv or circulating_market_cap
        token_volume_24h = quotes.get("volume_24h")
        fees_24h = sum_protocol_breakdown(
            fees.get("protocols", []), "breakdown24h", config["breakdown_key"]
        )
        try:
            chain_fees = fetch_llama_chain_fees(config["breakdown_key"])
            save_raw(f"defillama_fees_{chain}.json", chain_fees)
            fees_30d = chain_fees.get("total30d")
            fees_previous_30d = chain_fees.get("total60dto30d")
        except RuntimeError:
            fees_30d = get_chain_fee_window(fees, config["breakdown_key"], "breakdown30d")
            fees_previous_30d = None
        dex_volume_24h = sum_protocol_breakdown(
            dex_volume.get("protocols", []), "breakdown24h", config["breakdown_key"]
        )
        rwa_network_name = config.get("rwa_network")
        tokenized_stock_network = tokenized_stock_by_network.get(rwa_network_name or "", {})
        tokenized_stock_value = tokenized_stock_network.get("total_value_usd")

        rows.append(
            {
                "snapshot_utc": ts,
                "chain": chain,
                "llama_name": config["llama_name"],
                "native_token": chain_tvl.get("tokenSymbol") or (ticker or {}).get("symbol"),
                "market_cap_usd": market_cap,
                "token_circulating_market_cap_usd": circulating_market_cap,
                "token_volume_24h_usd": token_volume_24h,
                "tvl_usd": tvl,
                "network_fees_24h_usd": fees_24h,
                "network_fees_30d_usd": fees_30d,
                "network_fees_previous_30d_usd": fees_previous_30d,
                "network_fees_30d_change": safe_ratio(
                    (fees_30d or 0) - (fees_previous_30d or 0), fees_previous_30d
                ),
                "dex_volume_24h_usd": dex_volume_24h,
                "tokenized_stock_value_usd": tokenized_stock_value,
                "tokenized_stock_asset_count": tokenized_stock_network.get("asset_count"),
                "tokenized_stock_market_share": tokenized_stock_network.get("market_share"),
                "tokenized_stock_7d_change": tokenized_stock_network.get("value_7d_change"),
                "tokenized_stock_30d_change": tokenized_stock_network.get("value_30d_change"),
                "tokenized_stock_network": rwa_network_name,
                "tvl_to_mcap": safe_ratio(tvl, market_cap),
                "fees_24h_to_mcap": safe_ratio(fees_24h, market_cap),
                "fees_30d_to_mcap": safe_ratio(fees_30d, market_cap),
                "dex_volume_24h_to_tvl": safe_ratio(dex_volume_24h, tvl),
                "tokenized_stock_to_tvl": safe_ratio(tokenized_stock_value, tvl),
                "token_turnover_24h": safe_ratio(token_volume_24h, market_cap),
                "market_data_source": "CoinPaprika" if ticker else "missing",
                "onchain_data_source": "DefiLlama; RWA.xyz",
            }
        )

    score_columns = [
        "tvl_to_mcap",
        "fees_24h_to_mcap",
        "dex_volume_24h_to_tvl",
        "token_turnover_24h",
    ]
    for row in rows:
        row["activity_score"] = sum(
            zscore([r[column] for r in rows], row[column]) for column in score_columns
        )

    rows.sort(key=lambda row: row["activity_score"], reverse=True)
    return rows


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def money(value: Any) -> str:
    if value is None:
        return "NA"
    value = float(value)
    if abs(value) >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"${value / 1_000:.2f}K"
    return f"${value:.2f}"


def pct(value: Any) -> str:
    if value is None:
        return "NA"
    return f"{float(value) * 100:.2f}%"


def write_report(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 公链数据挖掘摘要",
        "",
        f"- 生成时间 UTC: {rows[0]['snapshot_utc']}",
        "- 数据源: DefiLlama(TVL/Fees/DEX Volume), CoinPaprika(市值/币种成交量), RWA.xyz(代币化美股/ETF)",
        "- 注意: activity_score 是标准化后的相对活跃度分数，不是投资建议。",
        "",
        "| 排名 | 公链 | 市值 | TVL | 代币化美股 | 30天网络费环比 | 24h DEX量 | TVL/市值 | DEX量/TVL | 分数 |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(rows, start=1):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    row["llama_name"],
                    money(row["market_cap_usd"]),
                    money(row["tvl_usd"]),
                    money(row["tokenized_stock_value_usd"]),
                    pct(row["network_fees_30d_change"]),
                    money(row["dex_volume_24h_usd"]),
                    pct(row["tvl_to_mcap"]),
                    pct(row["dex_volume_24h_to_tvl"]),
                    f"{row['activity_score']:.2f}",
                ]
            )
            + " |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_fee_report(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 公链交易手续费月度对比",
        "",
        f"- 生成时间 UTC: {rows[0]['snapshot_utc']}",
        "- 最近30天: DefiLlama `total30d`",
        "- 上一30天: DefiLlama `total60dto30d`，即 60天前至30天前窗口",
        "",
        "| 排名 | 公链 | 最近30天手续费 | 上一30天手续费 | 环比变化 | 24h手续费 |",
        "|---:|---|---:|---:|---:|---:|",
    ]
    fee_rows = sorted(
        rows,
        key=lambda row: float(row["network_fees_30d_usd"] or 0),
        reverse=True,
    )
    for index, row in enumerate(fee_rows, start=1):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    row["llama_name"],
                    money(row["network_fees_30d_usd"]),
                    money(row["network_fees_previous_30d_usd"]),
                    pct(row["network_fees_30d_change"]),
                    money(row["network_fees_24h_usd"]),
                ]
            )
            + " |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect and rank public-chain market/on-chain metrics."
    )
    parser.add_argument(
        "--chains",
        default=",".join(DEFAULT_CHAINS),
        help="Comma-separated chain keys. Supported: " + ", ".join(CHAIN_CONFIG),
    )
    parser.add_argument(
        "--csv",
        default=str(PROCESSED_DIR / "chain_metrics.csv"),
        help="Output CSV path.",
    )
    parser.add_argument(
        "--report",
        default=str(REPORT_DIR / "chain_metrics_summary.md"),
        help="Output Markdown report path.",
    )
    parser.add_argument(
        "--fee-report",
        default=str(REPORT_DIR / "chain_fee_monthly_comparison.md"),
        help="Output monthly fee comparison report path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    chains = [item.strip().lower() for item in args.chains.split(",") if item.strip()]
    rows = build_rows(chains)
    write_csv(rows, Path(args.csv))
    write_report(rows, Path(args.report))
    write_fee_report(rows, Path(args.fee_report))
    print(f"Wrote {len(rows)} rows to {args.csv}")
    print(f"Wrote report to {args.report}")
    print(f"Wrote fee report to {args.fee_report}")


if __name__ == "__main__":
    main()
