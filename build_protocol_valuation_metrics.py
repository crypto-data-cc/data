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
DEFILLAMA_PROTOCOLS_URL = "https://api.llama.fi/protocols"
DEFILLAMA_FEES_URL = "https://api.llama.fi/overview/fees?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true"


CATEGORY_DESCRIPTIONS = {
    "Dexs": "去中心化交易协议，提供链上兑换、做市和流动性服务",
    "DEX Aggregator": "DEX 聚合器，聚合多源流动性以优化交易路径和成交价格",
    "Lending": "链上借贷协议，提供资产存入、借出、抵押和利率市场服务",
    "Derivatives": "链上衍生品协议，提供永续、期权或杠杆交易服务",
    "Liquid Staking": "流动性质押协议，提供质押资产凭证和链上收益流动性",
    "Yield": "收益协议，围绕质押、流动性或策略仓位提升资产收益",
    "Yield Aggregator": "收益聚合器，自动聚合和优化多类 DeFi 收益策略",
    "Bridge": "跨链桥协议，提供资产跨链转移和链间流动性服务",
    "Cross Chain Bridge": "跨链桥协议，提供资产跨链转移和链间流动性服务",
    "Launchpad": "链上发行平台，提供项目启动、代币发行和流动性初始化服务",
    "Liquidity Manager": "流动性管理协议，帮助 LP 和做市方自动管理集中流动性头寸",
    "Liquidity Automation": "流动性自动化协议，围绕 AMM 头寸执行自动化调仓和费用优化",
    "Gamified Mining": "游戏化挖矿协议，通过链上竞赛或交互机制分配代币和收益",
    "Prediction Market": "预测市场协议，支持围绕事件、体育或数据结果进行链上交易",
    "Payments": "支付协议，提供链上支付、订阅、结算或资金分发基础设施",
    "Indexes": "指数协议，提供篮子资产、指数化投资或策略型代币产品",
    "NFT Marketplace": "NFT 市场协议，提供 NFT 发行、交易和市场流动性服务",
    "Physical TCG": "实物卡牌资产协议，将收藏卡牌等实物资产映射到链上交易场景",
    "RWA": "真实世界资产协议，将链下资产、收益或信用产品引入链上市场",
    "CDP": "抵押债仓协议，支持用户抵押资产并铸造或借出稳定资产",
    "Algo-Stables": "算法稳定币协议，围绕目标锚定资产设计供给和价格调节机制",
    "Staking Pool": "质押池协议，为用户提供质押聚合、验证节点或收益分配服务",
    "Oracle": "预言机协议，向链上应用提供价格、位置或其他外部数据服务",
    "DePIN": "DePIN 协议，通过代币激励协调现实世界或计算基础设施网络",
    "AI Agents": "AI Agent 协议，围绕链上智能代理、自动化执行或 AI 应用提供服务",
    "Developer Tools": "开发者工具协议，为链上应用提供计算、部署、监控或开发基础设施",
    "Services": "链上服务协议，面向项目方或用户提供安全、运营、数据等服务",
    "Interface": "链上交互入口，提供交易、聚合、工具或协议操作界面",
    "Foundation": "生态基金会或治理实体，负责协议发展、代币治理和生态激励",
    "Trading App": "链上交易应用，提供投资组合管理、订单执行或多市场交易入口",
    "SoFi": "社交金融协议，围绕内容、社区或社交关系构建链上金融场景",
    "Onchain Voting": "链上投票协议，提供治理、投票、分配或社区决策基础设施",
}


def chinese_category(category: str | None) -> str:
    if not category:
        return "链上协议"
    return CATEGORY_DESCRIPTIONS.get(category, f"{category} 赛道协议")


def chinese_intro(protocol: dict[str, Any]) -> str:
    name = protocol_name(protocol)
    category = protocol.get("category")
    description = chinese_category(category)
    separator = " " if description[:1].isascii() else ""
    chains = [chain for chain in (protocol.get("chains") or []) if chain]
    chain_text = ""
    if chains:
        shown = "、".join(chains[:3])
        chain_text = f"，主要覆盖 {shown}"
        if len(chains) > 3:
            chain_text += " 等网络"
    return f"{name} 是{separator}{description}{chain_text}。"


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
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalized_change(current: float | None, previous: float | None) -> float | None:
    if current is None or previous in (None, 0):
        return None
    return (current - previous) / previous


def protocol_name(protocol: dict[str, Any]) -> str:
    return protocol.get("displayName") or protocol.get("name") or ""


def by_slug(protocols: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {protocol.get("slug"): protocol for protocol in protocols if protocol.get("slug")}


def metric(source: dict[str, dict[str, Any]], slug: str) -> dict[str, float | None]:
    row = source.get(slug, {})
    total_30d = number(row.get("total30d"))
    previous_30d = number(row.get("total60dto30d"))
    return {
        "total_30d": total_30d,
        "previous_30d": previous_30d,
        "change_30d": normalized_change(total_30d, previous_30d),
    }


def annualized_multiple(market_cap: float | None, monthly_value: float | None) -> float | None:
    if market_cap is None or monthly_value is None or monthly_value <= 0:
        return None
    return market_cap / (monthly_value * 12)


def pe_basis(holders_pe: float | None, protocol_revenue_pe: float | None) -> tuple[float | None, str | None]:
    if holders_pe is not None and holders_pe > 0:
        return holders_pe, "持有人收入"
    if protocol_revenue_pe is not None and protocol_revenue_pe > 0:
        return protocol_revenue_pe, "协议收入"
    return None, None


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    protocols = load_or_fetch_json(RAW_DIR / "defillama_protocols.json", DEFILLAMA_PROTOCOLS_URL)
    fees = load_or_fetch_json(RAW_DIR / "defillama_fees_overview.json", DEFILLAMA_FEES_URL)
    protocol_revenue = load_or_fetch_json(
        RAW_DIR / "defillama_protocol_revenue_overview.json",
        f"{DEFILLAMA_FEES_URL}&dataType=dailyProtocolRevenue",
    )
    holders_revenue = load_or_fetch_json(
        RAW_DIR / "defillama_holders_revenue_overview.json",
        f"{DEFILLAMA_FEES_URL}&dataType=dailyHoldersRevenue",
    )

    fee_by_slug = by_slug(fees.get("protocols", []))
    protocol_revenue_by_slug = by_slug(protocol_revenue.get("protocols", []))
    holders_revenue_by_slug = by_slug(holders_revenue.get("protocols", []))

    rows = []
    for protocol in protocols:
        slug = protocol.get("slug")
        symbol = protocol.get("symbol")
        market_cap = number(protocol.get("mcap"))
        if not slug or not symbol or market_cap is None or market_cap <= 0:
            continue
        fees_metric = metric(fee_by_slug, slug)
        protocol_revenue_metric = metric(protocol_revenue_by_slug, slug)
        holders_revenue_metric = metric(holders_revenue_by_slug, slug)
        if not any(
            value is not None and value > 0
            for value in (
                fees_metric["total_30d"],
                protocol_revenue_metric["total_30d"],
                holders_revenue_metric["total_30d"],
            )
        ):
            continue

        fee_ps = annualized_multiple(market_cap, fees_metric["total_30d"])
        protocol_revenue_pe = annualized_multiple(market_cap, protocol_revenue_metric["total_30d"])
        holders_revenue_pe = annualized_multiple(market_cap, holders_revenue_metric["total_30d"])
        valuation_pe, valuation_pe_basis = pe_basis(holders_revenue_pe, protocol_revenue_pe)
        if valuation_pe is None:
            continue

        rows.append(
            {
                "protocol": protocol_name(protocol),
                "slug": slug,
                "token": symbol,
                "category": protocol.get("category"),
                "intro": protocol.get("description"),
                "intro_zh": chinese_intro(protocol),
                "chains": "; ".join(protocol.get("chains") or []),
                "tvl_usd": number(protocol.get("tvl")),
                "market_cap_usd": market_cap,
                "market_cap_to_tvl": (
                    market_cap / number(protocol.get("tvl"))
                    if number(protocol.get("tvl")) not in (None, 0)
                    else None
                ),
                "fees_30d_usd": fees_metric["total_30d"],
                "fees_previous_30d_usd": fees_metric["previous_30d"],
                "fees_30d_change": fees_metric["change_30d"],
                "protocol_revenue_30d_usd": protocol_revenue_metric["total_30d"],
                "protocol_revenue_previous_30d_usd": protocol_revenue_metric["previous_30d"],
                "protocol_revenue_30d_change": protocol_revenue_metric["change_30d"],
                "holders_revenue_30d_usd": holders_revenue_metric["total_30d"],
                "holders_revenue_previous_30d_usd": holders_revenue_metric["previous_30d"],
                "holders_revenue_30d_change": holders_revenue_metric["change_30d"],
                "fee_ps": fee_ps,
                "protocol_revenue_pe": protocol_revenue_pe,
                "holders_revenue_pe": holders_revenue_pe,
                "valuation_pe": valuation_pe,
                "valuation_pe_basis": valuation_pe_basis,
                "data_source": "DefiLlama protocols/fees/protocol revenue/holders revenue",
            }
        )

    rows.sort(key=lambda row: row["valuation_pe"])
    rows = rows[:100]
    output = PROCESSED_DIR / "protocol_valuation_top100.csv"
    with output.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {output}")


if __name__ == "__main__":
    main()
