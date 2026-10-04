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


PERPS_GROUPS = [
    {
        "platform": "Hyperliquid",
        "token": "HYPE",
        "slugs": ["hyperliquid-hlp"],
        "coinpaprika_id": "hype-hyperliquid",
        "intro": "高性能链上永续合约交易生态，HLP 承担做市和流动性收益角色。",
    },
    {
        "platform": "Jupiter Perps",
        "token": "JUP",
        "slugs": ["jupiter-perpetual-exchange"],
        "coinpaprika_id": "jup-jupiter-exchange-token",
        "intro": "Solana 生态核心永续合约产品，依托 Jupiter 交易入口和流动性网络。",
    },
    {
        "platform": "GMX",
        "token": "GMX",
        "slugs": ["gmx-v2-perps", "gmx-v1-perps", "gmx-solana"],
        "coinpaprika_id": "gmx-gmx",
        "intro": "老牌链上永续平台，覆盖 Arbitrum、Avalanche 等多链市场。",
    },
    {
        "platform": "dYdX",
        "token": "DYDX",
        "slugs": ["dydx-v4", "dydx-v3"],
        "coinpaprika_id": "dydx-dydx-chain",
        "intro": "订单簿型去中心化永续交易所，已迁移到独立 dYdX Chain。",
    },
    {
        "platform": "Lighter",
        "token": "LIT",
        "slugs": ["lighter-robinhood-perps"],
        "coinpaprika_id": "lit-lighter",
        "intro": "Robinhood Chain 上的链上永续合约平台，当前 TVL 体量处于新兴平台前列。",
    },
    {
        "platform": "Aster Perps",
        "token": "ASTER",
        "slugs": ["aster-perps"],
        "coinpaprika_id": "aster-aster",
        "intro": "面向永续合约和现货交易的衍生品平台，Perps 手续费数据已收录但 TVL 口径暂缺。",
    },
    {
        "platform": "Derive",
        "token": "DRV",
        "slugs": ["derive-v2"],
        "coinpaprika_id": "drv-derive",
        "intro": "面向期权与永续等衍生品的链上交易协议。",
    },
    {
        "platform": "Aevo Perps",
        "token": "AEVO",
        "slugs": ["aevo-perps"],
        "coinpaprika_id": "aevo-aevo",
        "intro": "衍生品 L2 交易平台，覆盖永续与期权场景。",
    },
    {
        "platform": "Gains Network",
        "token": "GNS",
        "slugs": ["gains-network"],
        "coinpaprika_id": "gns-gains-network",
        "intro": "gTrade 背后的多链合成杠杆交易协议。",
    },
    {
        "platform": "MUX Perps",
        "token": "MCB",
        "slugs": ["mux-perps"],
        "coinpaprika_id": "mcb-mcdex",
        "intro": "多链永续聚合与流动性协议，面向杠杆交易场景。",
    },
    {
        "platform": "Synthetix Perps",
        "token": "SNX",
        "slugs": ["synthetix-v4"],
        "coinpaprika_id": "snx-synthetix-network-token",
        "intro": "合成资产与衍生品基础设施，支持链上永续市场。",
    },
    {
        "platform": "Perpetual Protocol",
        "token": "PERP",
        "slugs": ["perpetual-protocol"],
        "coinpaprika_id": "perp-perpetual-protocol",
        "intro": "早期链上永续协议，主要部署在 Ethereum / Optimism 生态。",
    },
    {
        "platform": "SynFutures",
        "token": "F",
        "slugs": ["synfutures-v3"],
        "coinpaprika_id": "f-synfutures",
        "intro": "支持任意资产合约市场的链上衍生品协议。",
    },
    {
        "platform": "Bluefin Pro",
        "token": "BLUE",
        "slugs": ["bluefin-pro"],
        "coinpaprika_id": "blue-bluefin",
        "intro": "Sui 生态订单簿衍生品交易平台。",
    },
    {
        "platform": "ApeX Pro",
        "token": "APEX",
        "slugs": ["apex-pro"],
        "coinpaprika_id": "apex-apex-token",
        "intro": "多链订单簿永续交易平台。",
    },
    {
        "platform": "KiloEx",
        "token": "KILO",
        "slugs": ["kiloex"],
        "coinpaprika_id": "kilo-kiloex",
        "intro": "部署在 BSC、Base、opBNB 等网络的多链永续协议。",
    },
    {
        "platform": "Drift",
        "token": "DRIFT",
        "slugs": ["drift-trade"],
        "coinpaprika_id": "drift-drift-protocol",
        "intro": "Solana 生态衍生品与保证金交易协议。",
    },
    {
        "platform": "Parcl",
        "token": "PRCL",
        "slugs": ["parcl-v3"],
        "coinpaprika_id": "prcl-parcl",
        "intro": "围绕房地产指数等资产构建的 Solana 衍生品协议。",
    },
    {
        "platform": "Fulcrom",
        "token": "FUL",
        "slugs": ["fulcrom-perps"],
        "coinpaprika_id": "ful-fulcrom",
        "intro": "Cronos 生态永续交易协议。",
    },
    {
        "platform": "Adrena",
        "token": "ADX",
        "slugs": ["adrena-protocol"],
        "coinpaprika_id": "adx-adrena",
        "intro": "Solana 生态永续合约交易协议。",
    },
    {
        "platform": "Contango",
        "token": "TANGO",
        "slugs": ["contango-v2", "contango-v1"],
        "coinpaprika_id": "tango-contango",
        "intro": "多链到期合约和利率衍生品协议。",
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


def normalized_change(current: float | None, previous: float | None) -> float | None:
    if current is None or previous in (None, 0):
        return None
    return (current - previous) / previous


def protocol_name(protocol: dict[str, Any]) -> str:
    return protocol.get("displayName") or protocol.get("name") or ""


def load_token_market_data(groups: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    output = {}
    for group in groups:
        coin_id = group.get("coinpaprika_id")
        token = group["token"]
        if not coin_id:
            continue
        path = RAW_DIR / f"coinpaprika_perps_token_{token.lower()}.json"
        try:
            if path.exists():
                ticker = json.loads(path.read_text(encoding="utf-8"))
            else:
                ticker = request_json(f"https://api.coinpaprika.com/v1/tickers/{quote(coin_id)}")
                path.write_text(json.dumps(ticker, ensure_ascii=False, indent=2), encoding="utf-8")
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


def group_protocols(protocols: list[dict[str, Any]], slugs: list[str]) -> list[dict[str, Any]]:
    slug_set = set(slugs)
    return [protocol for protocol in protocols if protocol.get("slug") in slug_set]


def fee_protocols_by_slug(protocols: list[dict[str, Any]], slugs: list[str]) -> list[dict[str, Any]]:
    slug_set = set(slugs)
    return [protocol for protocol in protocols if protocol.get("slug") in slug_set or protocol.get("parentProtocol") in slug_set]


def load_protocol_detail(slug: str) -> dict[str, Any] | None:
    path = RAW_DIR / f"defillama_protocol_{slug}.json"
    try:
        return load_or_fetch_json(path, f"https://api.llama.fi/protocol/{quote(slug)}")
    except (HTTPError, URLError, TimeoutError):
        return None


def aggregate_tvl_history(slugs: list[str]) -> dict[str, float | None]:
    current_values = []
    previous_values = []
    target = int((datetime.now(timezone.utc) - timedelta(days=30)).timestamp())
    for slug in slugs:
        detail = load_protocol_detail(slug)
        if not detail:
            continue
        history = detail.get("tvl", [])
        current_values.append(closest_tvl(history, int(datetime.now(timezone.utc).timestamp())))
        previous_values.append(closest_tvl(history, target))
    current = sum_numbers(current_values)
    previous = sum_numbers(previous_values)
    return {
        "tvl_current": current,
        "tvl_previous_30d": previous,
        "tvl_30d_change": normalized_change(current, previous),
    }


def aggregate_dimension(protocols: list[dict[str, Any]]) -> dict[str, float | None]:
    total_30d = sum_numbers([protocol.get("total30d") for protocol in protocols])
    previous_30d = sum_numbers([protocol.get("total60dto30d") for protocol in protocols])
    return {
        "total_30d": total_30d,
        "previous_30d": previous_30d,
        "change_30d": normalized_change(total_30d, previous_30d),
    }


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    protocols = load_or_fetch_json(RAW_DIR / "defillama_protocols.json", DEFILLAMA_PROTOCOLS_URL)
    fees_overview = load_or_fetch_json(RAW_DIR / "defillama_fees_overview.json", DEFILLAMA_FEES_URL)
    holders_overview = load_or_fetch_json(
        RAW_DIR / "defillama_holders_revenue_overview.json",
        f"{DEFILLAMA_FEES_URL}&dataType=dailyHoldersRevenue",
    )
    token_market_data = load_token_market_data(PERPS_GROUPS)

    rows = []
    for group in PERPS_GROUPS:
        matched_protocols = group_protocols(protocols, group["slugs"])
        matched_fees = fee_protocols_by_slug(fees_overview.get("protocols", []), group["slugs"])
        matched_holders = fee_protocols_by_slug(holders_overview.get("protocols", []), group["slugs"])
        fees = aggregate_dimension(matched_fees)
        holders_revenue = aggregate_dimension(matched_holders)
        tvl_history = aggregate_tvl_history(group["slugs"])
        tvl = tvl_history["tvl_current"] or sum_numbers([protocol.get("tvl") for protocol in matched_protocols])
        chains = sorted({chain for protocol in matched_protocols for chain in protocol.get("chains", [])})
        market = token_market_data.get(group["token"], {})
        market_cap = market.get("token_market_cap_usd")
        fee_ps = market_cap / (fees["total_30d"] * 12) if market_cap and fees["total_30d"] else None
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
                "holders_revenue_30d_usd": holders_revenue["total_30d"],
                "holders_revenue_previous_30d_usd": holders_revenue["previous_30d"],
                "holders_revenue_30d_change": holders_revenue["change_30d"],
                "holders_revenue_to_fees": (
                    holders_revenue["total_30d"] / fees["total_30d"]
                    if holders_revenue["total_30d"] is not None and fees["total_30d"]
                    else None
                ),
                "fee_ps": fee_ps,
                "holders_revenue_pe": holders_revenue_pe,
                "data_status": "已匹配协议与代币" if matched_protocols and market else "部分数据缺失",
                "data_source": "DefiLlama protocols/fees/holders revenue; CoinPaprika",
            }
        )

    rows.sort(key=lambda row: row["tvl_usd"] or 0, reverse=True)
    output = PROCESSED_DIR / "perps_platform_metrics.csv"
    with output.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {output}")


if __name__ == "__main__":
    main()
