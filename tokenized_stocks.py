from __future__ import annotations

import csv
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
REPORT_DIR = BASE_DIR / "reports"
SOURCE_URL = "https://app.rwa-xyz.com/stocks"


def request_text(url: str) -> str:
    req = Request(
        url,
        headers={
            "Accept": "text/html",
            "User-Agent": "public-chain-data-mining/0.1 (+local research)",
        },
    )
    with urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8")


def extract_next_data(page_html: str) -> dict[str, Any]:
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        page_html,
        flags=re.DOTALL,
    )
    if not match:
        raise RuntimeError("Could not find __NEXT_DATA__ in RWA.xyz page.")
    return json.loads(html.unescape(match.group(1)))


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


def metric_value(value: Any) -> Any:
    if isinstance(value, dict):
        return value.get("val")
    return value


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def league_rows(page_props: dict[str, Any], tab: str, group: str) -> list[dict[str, Any]]:
    tabs = page_props["leagueTableTabs"]
    rows = tabs[tab][0]["data"]["rows"]
    for item in tabs[tab]:
        if item["key"] == group:
            rows = item["data"]["rows"]
            break
    distributed_value = next(
        (
            item["value"]
            for item in page_props.get("aggregates", [])
            if item.get("label") == "Distributed Value"
        ),
        None,
    )
    distributed_change = next(
        (
            item.get("percentChange", {}).get("value")
            for item in page_props.get("aggregates", [])
            if item.get("label") == "Distributed Value"
        ),
        None,
    )
    distributed_value_30d_ago = (
        distributed_value / (1 + distributed_change)
        if distributed_value is not None and distributed_change not in (None, -1)
        else None
    )

    return [
        {
            "rank": row["rowIndex"] + 1,
            "name": row["group"]["name"],
            "asset_count": row.get("asset_count"),
            "total_value_usd": row.get("value"),
            "value_7d_change": row.get("value_7d_change"),
            "value_30d_ago": (
                distributed_value_30d_ago * row.get("market_share_pct_30d_ago")
                if distributed_value_30d_ago is not None
                and row.get("market_share_pct_30d_ago") is not None
                else None
            ),
            "value_30d_change": (
                row.get("value")
                / (distributed_value_30d_ago * row.get("market_share_pct_30d_ago"))
                - 1
                if distributed_value_30d_ago is not None
                and row.get("market_share_pct_30d_ago") not in (None, 0)
                else None
            ),
            "market_share": row.get("market_share_pct"),
            "market_share_30d_change": row.get("market_share_pct_30d_change"),
        }
        for row in rows
    ]


def asset_rows(page_props: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for index, asset in enumerate(page_props["listQueryResponse"]["results"], start=1):
        total_value = next(
            (
                metric_value(asset.get(field))
                for field in [
                    "circulating_market_value_dollar",
                    "total_asset_value_dollar",
                    "bridged_token_value_dollar",
                    "market_value_dollar",
                    "market_cap_dollar",
                ]
                if metric_value(asset.get(field)) is not None
            ),
            None,
        )
        rows.append(
            {
                "rank": index,
                "name": asset["name"],
                "ticker": asset.get("ticker"),
                "asset_class": asset.get("asset_class_name"),
                "total_value_usd": total_value,
                "one_month_return": asset.get("trailing_1_month_return_percent"),
                "one_year_return": asset.get("trailing_1_year_return_percent"),
                "tokenization_types": ", ".join(asset.get("tokenization_types") or []),
                "platforms": ", ".join(
                    sorted({token.get("platform_name") for token in asset.get("tokens", []) if token.get("platform_name")})
                ),
                "networks": ", ".join(asset.get("network_names") or []),
            }
        )
    return rows


def aggregate_rows(page_props: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "metric": item["label"],
            "value": item["value"],
            "percent_change": item.get("percentChange", {}).get("value"),
            "interval": item.get("percentChange", {}).get("interval"),
        }
        for item in page_props["aggregates"]
    ]


def write_report(
    aggregates: list[dict[str, Any]],
    platforms: list[dict[str, Any]],
    networks: list[dict[str, Any]],
    assets: list[dict[str, Any]],
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    lines = [
        "# 代币化美股/ETF 锁仓价值快照",
        "",
        f"- 生成时间 UTC: {generated_at}",
        f"- 数据源: RWA.xyz Tokenized Stocks ({SOURCE_URL})",
        "- 口径: RWA.xyz 的 Total Value。Distributed 指面向链上分发/持有的代币化股票；Represented 指链上记录/表示层。",
        "- 注意: RWA.xyz 企业 API 需要 key；本脚本使用公开页面内嵌快照。",
        "",
        "## 总览",
        "",
        "| 指标 | 数值 | 变化区间 | 变化 |",
        "|---|---:|---:|---:|",
    ]
    for row in aggregates:
        value = money(row["value"]) if "Value" in row["metric"] or "Volume" in row["metric"] else f"{row['value']:,}"
        lines.append(
            f"| {row['metric']} | {value} | {row['interval'] or 'NA'} | {pct(row['percent_change'])} |"
        )

    lines.extend(
        [
            "",
            "## 平台排行",
            "",
            "| 排名 | 平台 | 资产数 | 总价值 | 7日变化 | 市占率 |",
            "|---:|---|---:|---:|---:|---:|",
        ]
    )
    for row in platforms[:10]:
        lines.append(
            f"| {row['rank']} | {row['name']} | {row['asset_count']} | {money(row['total_value_usd'])} | {pct(row['value_7d_change'])} | {pct(row['market_share'])} |"
        )

    lines.extend(
        [
            "",
            "## 网络排行",
            "",
            "| 排名 | 网络 | 资产数 | 总价值 | 7日变化 | 市占率 |",
            "|---:|---|---:|---:|---:|---:|",
        ]
    )
    for row in networks[:10]:
        lines.append(
            f"| {row['rank']} | {row['name']} | {row['asset_count']} | {money(row['total_value_usd'])} | {pct(row['value_7d_change'])} | {pct(row['market_share'])} |"
        )

    lines.extend(
        [
            "",
            "## 首页资产排行",
            "",
            "| 排名 | 资产 | Ticker | 总价值 | 1月收益 | 平台 | 网络 |",
            "|---:|---|---|---:|---:|---|---|",
        ]
    )
    for row in assets[:15]:
        lines.append(
            f"| {row['rank']} | {row['name']} | {row['ticker']} | {money(row['total_value_usd'])} | {pct((row['one_month_return'] or 0) / 100 if row['one_month_return'] is not None else None)} | {row['platforms']} | {row['networks']} |"
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    page = request_text(SOURCE_URL)
    data = extract_next_data(page)
    page_props = data["props"]["pageProps"]

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    (RAW_DIR / "rwa_xyz_stocks_next_data.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    aggregates = aggregate_rows(page_props)
    platforms = league_rows(page_props, "distributed", "platforms")
    networks = league_rows(page_props, "distributed", "networks")
    assets = asset_rows(page_props)

    write_csv(aggregates, PROCESSED_DIR / "tokenized_stock_aggregates.csv")
    write_csv(platforms, PROCESSED_DIR / "tokenized_stock_platforms.csv")
    write_csv(networks, PROCESSED_DIR / "tokenized_stock_networks.csv")
    write_csv(assets, PROCESSED_DIR / "tokenized_stock_assets_top25.csv")
    write_report(
        aggregates,
        platforms,
        networks,
        assets,
        REPORT_DIR / "tokenized_stocks_tvl.md",
    )

    print("Wrote tokenized stock RWA reports and CSV files.")


if __name__ == "__main__":
    main()
