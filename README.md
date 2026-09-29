# 公链数据挖掘起步项目

这个项目采集公链的四类核心指标：

- 最大市值/FDV、流通市值、币种 24h 成交量: CoinPaprika
- TVL、网络费、DEX 交易量: DefiLlama
- 代币化美股/ETF 网络价值: RWA.xyz
- 衍生指标: `TVL/最大市值`、`网络费/最大市值`、`DEX交易量/TVL`、`币种换手率`
- 综合指标: `activity_score`，用于横向比较链上资本效率和交易活跃度

## 运行

```powershell
python main.py
```

指定公链：

```powershell
python main.py --chains ethereum,solana,bsc,base,arbitrum,polygon
```

## 输出

- `data/raw/`: 原始 API JSON，方便复核数据源
- `data/processed/chain_metrics.csv`: 结构化指标表
- `reports/chain_metrics_summary.md`: 简要排名报告

`chain_metrics.csv` 中的代币化美股/ETF字段：

- `tokenized_stock_value_usd`: 该链上的代币化股票/ETF总价值
- `tokenized_stock_asset_count`: 该链上的代币化股票/ETF资产数量
- `tokenized_stock_market_share`: 该链在代币化股票/ETF中的市占率
- `tokenized_stock_7d_change`: 该链代币化股票/ETF总价值的7日变化
- `tokenized_stock_to_tvl`: 代币化股票/ETF价值占该链TVL的比例

## 下一步可挖掘方向

- 横截面排名: 找出高 TVL、低估值、高费用或高交易活跃度的链
- 时间序列: 每天定时跑一次，观察指标变化率
- 异常检测: 识别 TVL 激增、费用激增、交易量异常放大
- 因子研究: 测试 `fees_24h_to_mcap`、`dex_volume_24h_to_tvl` 等指标对后续价格或生态热度的解释力
- 可视化: 用 Streamlit 或 Jupyter 做仪表盘

## 代币化美股/ETF

```powershell
python tokenized_stocks.py
```

输出：

- `data/processed/tokenized_stock_aggregates.csv`
- `data/processed/tokenized_stock_platforms.csv`
- `data/processed/tokenized_stock_networks.csv`
- `data/processed/tokenized_stock_assets_top25.csv`
- `reports/tokenized_stocks_tvl.md`

数据源是 RWA.xyz 的公开 Tokenized Stocks 页面。RWA.xyz 企业 API 需要 key，所以脚本使用页面内嵌快照；如果后续有 API key，可以改成完整分页数据采集。

## 静态网页

生成静态网页数据：

```powershell
python build_dashboard.py
```

本地预览：

```powershell
python serve_dashboard.py
```

然后打开：

```text
http://localhost:8765/
```

默认数据超过 24 小时会在访问时自动更新。也可以点击页面右上角“刷新数据”强制更新，或访问：

```text
http://localhost:8765/?refresh=1
```

调整过期时间：

```powershell
python serve_dashboard.py --max-age-hours 12
```

每天更新数据：

```powershell
.\update_dashboard.ps1
```

网页访问时只读取 `web/dashboard-data.js`，不会请求外部 API。空值会被处理为 `null`，页面展示为“暂无数据”，图表计算会自动跳过这些值。

## GitHub Pages 自动更新

项目已经包含 GitHub Actions 配置：

```text
.github/workflows/update-dashboard.yml
```

它会：

- 每天 UTC 22:15 自动运行一次
- 依次执行 `python main.py`、`python tokenized_stocks.py`、`python build_dashboard.py`
- 把新的 `data/processed/`、`reports/`、`web/dashboard-data.js` 提交回仓库
- 把 `web/` 目录部署到 GitHub Pages

首次部署步骤：

```powershell
git init
git add .
git commit -m "Initial dashboard"
git branch -M main
git remote add origin https://github.com/<你的用户名>/<仓库名>.git
git push -u origin main
```

然后到 GitHub 仓库：

1. 打开 `Settings -> Pages`
2. `Build and deployment` 选择 `GitHub Actions`
3. 打开 `Actions` 页签，手动运行一次 `Update dashboard data`

注意：GitHub Pages 是纯静态托管，访问者打开网页时不能直接写回仓库里的 JSON。自动更新由 GitHub Actions 定时完成；访问者只读取最新发布的静态数据。

这份脚本只是研究工具，不构成投资建议。
