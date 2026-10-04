from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
DEFILLAMA_PROTOCOLS_URL = "https://api.llama.fi/protocols"
DEFILLAMA_FEES_URL = "https://api.llama.fi/overview/fees?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true"


LENDING_GROUPS = [
    {
        "platform": "Aave",
        "token": "AAVE",
        "slugs": ["aave-v3", "aave-v4", "aave-v2", "aave-horizon-rwa"],
        "coinpaprika_id": "aave-new",
        "intro": "多链借贷龙头，覆盖 V2/V3/V4 与 RWA 借贷市场。",
    },
    {
        "platform": "Morpho",
        "token": "MORPHO",
        "slugs": ["morpho-blue"],
        "coinpaprika_id": "morpho-morpho",
        "intro": "以独立借贷市场和金库为核心的模块化借贷协议。",
    },
    {
        "platform": "Spark",
        "token": "SPK",
        "slugs": ["sparklend"],
        "coinpaprika_id": "spk-spark",
        "intro": "Spark 协议借贷产品，承接 DAI/USDS 体系内的链上信贷需求，平台代币为 SPK。",
    },
    {
        "platform": "World Liberty Financial",
        "token": "WLFI",
        "slugs": ["world-liberty-financial"],
        "coinpaprika_id": "wlfi-official-world-liberty-financial",
        "intro": "围绕 USD1 与链上美元流动性搭建的借贷与收益平台。",
    },
    {
        "platform": "Maple",
        "token": "SYRUP",
        "slugs": ["maple"],
        "coinpaprika_id": "syrup-syrup-token",
        "intro": "机构信贷和链上固定收益平台，面向加密和 RWA 借贷。",
    },
    {
        "platform": "Compound",
        "token": "COMP",
        "slugs": ["compound-v3", "compound-v2"],
        "coinpaprika_id": "comp-compoundd",
        "intro": "老牌货币市场协议，V3 聚焦隔离基础资产市场。",
    },
    {
        "platform": "Kamino Lend",
        "token": "KMNO",
        "slugs": ["kamino-lend"],
        "coinpaprika_id": "kmno-kamino",
        "intro": "Solana 生态借贷与流动性管理协议。",
    },
    {
        "platform": "Venus",
        "token": "XVS",
        "slugs": ["venus-core-pool"],
        "coinpaprika_id": "xvs-venus",
        "intro": "BNB Chain 起家的多链借贷市场。",
    },
    {
        "platform": "Jupiter Lend",
        "token": "JUP",
        "slugs": ["jupiter-lend"],
        "coinpaprika_id": "jup-jupiter-exchange-token",
        "intro": "Jupiter 生态的 Solana 借贷市场。",
    },
    {
        "platform": "Lista Lending",
        "token": "LISTA",
        "slugs": ["lista-lending"],
        "coinpaprika_id": "lista-lista-dao",
        "intro": "围绕 lisUSD 和 BNB 资产的借贷市场。",
    },
    {
        "platform": "Fluid Lending",
        "token": "FLUID",
        "slugs": ["fluid-lending"],
        "coinpaprika_id": "inst-instadapp",
        "intro": "原 Instadapp 生态的流动性与借贷基础设施。",
    },
    {
        "platform": "Dolomite",
        "token": "DOLO",
        "slugs": ["dolomite"],
        "coinpaprika_id": "dolo-dolomite",
        "intro": "支持保证金、借贷和多资产策略的 DeFi 货币市场。",
    },
    {
        "platform": "Euler",
        "token": "EUL",
        "slugs": ["euler-v2"],
        "coinpaprika_id": "eul-euler",
        "intro": "模块化借贷协议，V2 面向可组合借贷金库。",
    },
    {
        "platform": "Moonwell",
        "token": "WELL",
        "slugs": ["moonwell-lending"],
        "coinpaprika_id": "well-moonwell",
        "intro": "Base、Optimism、Moonbeam 等生态的借贷协议。",
    },
    {
        "platform": "BENQI",
        "token": "QI",
        "slugs": ["benqi-lending"],
        "coinpaprika_id": "qi-benqi",
        "intro": "Avalanche 生态代表性借贷市场。",
    },
    {
        "platform": "Gearbox",
        "token": "GEAR",
        "slugs": ["gearbox"],
        "coinpaprika_id": "gear-gearbox",
        "intro": "面向杠杆策略和信用账户的借贷协议。",
    },
    {
        "platform": "Silo",
        "token": "SILO",
        "slugs": ["silo-v2"],
        "coinpaprika_id": "silo-silo-finance",
        "intro": "隔离风险池设计的借贷协议。",
    },
    {
        "platform": "Radiant",
        "token": "RDNT",
        "slugs": ["radiant-v2"],
        "coinpaprika_id": "rdnt-radiant-capital",
        "intro": "多链货币市场，历史上强调跨链借贷流动性。",
    },
]


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


def number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def sum_numbers(values: list[Any]) -> float | None:
    usable = [number(value) for value in values]
    usable = [value for value in usable if value is not None]
    return sum(usable) if usable else None


def normalized_change(current: float | None, previous: float | None) -> float | None:
    if current is None or previous in (None, 0):
        return None
    return (current - previous) / previous


def protocol_name(protocol: dict[str, Any]) -> str:
    return protocol.get("displayName") or protocol.get("name") or ""


def extract_tvl_value(point: dict[str, Any]) -> float | None:
    if not point:
        return None
    total_liquidity = point.get("totalLiquidityUSD")
    if total_liquidity is not None:
        return number(total_liquidity)
    tvl = point.get("tvl")
    if tvl is not None:
        return number(tvl)
    return None


def closest_tvl(history: list[dict[str, Any]], target_timestamp: int) -> float | None:
    usable = [point for point in history if extract_tvl_value(point) is not None and point.get("date") is not None]
    if not usable:
        return None
    point = min(usable, key=lambda item: abs(int(item["date"]) - target_timestamp))
    return extract_tvl_value(point)


def load_protocol_detail(slug: str) -> dict[str, Any] | None:
    path = RAW_DIR / f"defillama_protocol_{slug}.json"
    try:
        return load_or_fetch_json(path, f"https://api.llama.fi/protocol/{quote(slug)}")
    except (HTTPError, URLError, TimeoutError):
        return None


def aggregate_tvl_history(slugs: list[str]) -> dict[str, float | None]:
    current_values = []
    previous_values = []
    now = int(datetime.now(timezone.utc).timestamp())
    target = int((datetime.now(timezone.utc) - timedelta(days=30)).timestamp())
    for slug in slugs:
        detail = load_protocol_detail(slug)
        if not detail:
            continue
        history = detail.get("tvl", [])
        current_values.append(closest_tvl(history, now))
        previous_values.append(closest_tvl(history, target))
    current = sum_numbers(current_values)
    previous = sum_numbers(previous_values)
    return {
        "tvl_current": current,
        "tvl_previous_30d": previous,
        "tvl_30d_change": normalized_change(current, previous),
    }


def group_protocols(protocols: list[dict[str, Any]], slugs: list[str]) -> list[dict[str, Any]]:
    slug_set = set(slugs)
    return [protocol for protocol in protocols if protocol.get("slug") in slug_set]


def aggregate_dimension(protocols: list[dict[str, Any]]) -> dict[str, float | None]:
    total_30d = sum_numbers([protocol.get("total30d") for protocol in protocols])
    previous_30d = sum_numbers([protocol.get("total60dto30d") for protocol in protocols])
    return {
        "total_30d": total_30d,
        "previous_30d": previous_30d,
        "change_30d": normalized_change(total_30d, previous_30d),
    }


def load_token_market_data(groups: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    output = {}
    for group in groups:
        coin_id = group.get("coinpaprika_id")
        token = group["token"]
        if not coin_id:
            continue
        path = RAW_DIR / f"coinpaprika_lending_token_{token.lower()}.json"
        try:
            ticker = load_or_fetch_json(path, f"https://api.coinpaprika.com/v1/tickers/{quote(coin_id)}")
        except (HTTPError, URLError, TimeoutError):
            continue
        quote_data = ticker.get("quotes", {}).get("USD", {})
        price = quote_data.get("price")
        max_supply = ticker.get("max_supply")
        total_supply = ticker.get("total_supply")
        fdv_supply = max_supply or total_supply
        output[token] = {
            "token_market_data_source": coin_id,
            "token_price_usd": price,
            "token_market_cap_usd": price * fdv_supply if price and fdv_supply else quote_data.get("market_cap"),
            "token_circulating_market_cap_usd": quote_data.get("market_cap"),
        }
    return output


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    protocols = load_or_fetch_json(RAW_DIR / "defillama_protocols.json", DEFILLAMA_PROTOCOLS_URL)
    fees_overview = load_or_fetch_json(RAW_DIR / "defillama_fees_overview.json", DEFILLAMA_FEES_URL)
    holders_overview = load_or_fetch_json(
        RAW_DIR / "defillama_holders_revenue_overview.json",
        f"{DEFILLAMA_FEES_URL}&dataType=dailyHoldersRevenue",
    )
    protocol_revenue_overview = load_or_fetch_json(
        RAW_DIR / "defillama_protocol_revenue_overview.json",
        f"{DEFILLAMA_FEES_URL}&dataType=dailyProtocolRevenue",
    )
    token_market_data = load_token_market_data(LENDING_GROUPS)

    rows = []
    for group in LENDING_GROUPS:
        matched_protocols = group_protocols(protocols, group["slugs"])
        matched_fees = group_protocols(fees_overview.get("protocols", []), group["slugs"])
        matched_holders = group_protocols(holders_overview.get("protocols", []), group["slugs"])
        matched_protocol_revenue = group_protocols(protocol_revenue_overview.get("protocols", []), group["slugs"])
        fees = aggregate_dimension(matched_fees)
        holders_revenue = aggregate_dimension(matched_holders)
        protocol_revenue = aggregate_dimension(matched_protocol_revenue)
        tvl_history = aggregate_tvl_history(group["slugs"])
        tvl = tvl_history["tvl_current"] or sum_numbers([protocol.get("tvl") for protocol in matched_protocols])
        chains = sorted({chain for protocol in matched_protocols for chain in protocol.get("chains", [])})
        market = token_market_data.get(group["token"], {})
        market_cap = market.get("token_market_cap_usd")
        fee_ps = market_cap / (fees["total_30d"] * 12) if market_cap and fees["total_30d"] else None
        protocol_revenue_ps = (
            market_cap / (protocol_revenue["total_30d"] * 12)
            if market_cap and protocol_revenue["total_30d"]
            else None
        )
        holders_revenue_pe = (
            market_cap / (holders_revenue["total_30d"] * 12)
            if market_cap and holders_revenue["total_30d"]
            else None
        )
        rows.append(
            {
                "platform": group["platform"],
                "token": group["token"],
                "intro": group["intro"],
                "chains": "; ".join(chains),
                "matched_protocols": "; ".join(protocol_name(protocol) for protocol in matched_protocols),
                "tvl_usd": tvl,
                "tvl_previous_30d_usd": tvl_history["tvl_previous_30d"],
                "tvl_30d_change": tvl_history["tvl_30d_change"],
                "token_market_cap_usd": market_cap,
                "token_circulating_market_cap_usd": market.get("token_circulating_market_cap_usd"),
                "token_price_usd": market.get("token_price_usd"),
                "token_market_data_source": market.get("token_market_data_source"),
                "market_cap_to_tvl": market_cap / tvl if market_cap and tvl else None,
                "fees_30d_usd": fees["total_30d"],
                "fees_previous_30d_usd": fees["previous_30d"],
                "fees_30d_change": fees["change_30d"],
                "protocol_revenue_30d_usd": protocol_revenue["total_30d"],
                "protocol_revenue_previous_30d_usd": protocol_revenue["previous_30d"],
                "protocol_revenue_30d_change": protocol_revenue["change_30d"],
                "holders_revenue_30d_usd": holders_revenue["total_30d"],
                "holders_revenue_previous_30d_usd": holders_revenue["previous_30d"],
                "holders_revenue_30d_change": holders_revenue["change_30d"],
                "holders_revenue_to_fees": (
                    holders_revenue["total_30d"] / fees["total_30d"]
                    if holders_revenue["total_30d"] is not None and fees["total_30d"]
                    else None
                ),
                "fee_ps": fee_ps,
                "protocol_revenue_ps": protocol_revenue_ps,
                "holders_revenue_pe": holders_revenue_pe,
                "data_status": "已匹配协议与代币" if matched_protocols and market else "部分数据缺失",
                "data_source": "DefiLlama protocols/fees/revenue/holders revenue; CoinPaprika",
            }
        )

    rows.sort(key=lambda row: row["tvl_usd"] or 0, reverse=True)
    output = PROCESSED_DIR / "lending_protocol_metrics.csv"
    with output.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {output}")


if __name__ == "__main__":
    main()
