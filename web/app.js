(function () {
  const data = window.DASHBOARD_DATA || {};
  const chains = Array.isArray(data.chains) ? data.chains : [];
  const dexTokens = Array.isArray(data.dex_tokens) ? data.dex_tokens : [];
  const perpsPlatforms = Array.isArray(data.perps_platforms) ? data.perps_platforms : [];
  const stablecoins = Array.isArray(data.stablecoins) ? data.stablecoins : [];
  const lendingProtocols = Array.isArray(data.lending_protocols) ? data.lending_protocols : [];
  const protocolValuations = Array.isArray(data.protocol_valuations) ? data.protocol_valuations : [];

  const sortBy = document.getElementById("sortBy");
  const filterMode = document.getElementById("filterMode");
  let currentLang = localStorage.getItem("dashboard_lang") || "zh";
  let currentView = "chains";
  const tableSort = {
    key: "market_cap_usd",
    direction: "desc",
  };
  const dexSort = {
    key: "holders_revenue_pe",
    direction: "asc",
  };
  const perpsSort = {
    key: "tvl_usd",
    direction: "desc",
  };
  const stablecoinSort = {
    key: "market_cap_usd",
    direction: "desc",
  };
  const lendingSort = {
    key: "tvl_usd",
    direction: "desc",
  };
  const valuationSort = {
    key: "valuation_pe",
    direction: "asc",
  };

  const i18n = {
    zh: {
      title: "公链数据挖掘 Dashboard",
      staticData: "静态数据",
      reload: "重新载入",
      loading: "载入中...",
      langButton: "English",
      updated: "更新",
      noUpdatedAt: "暂无更新时间",
      sort: "排序",
      filter: "过滤",
      sortTokenizedStocks: "代币化美股价值",
      sortTvl: "TVL",
      sortFeeGrowth: "30天手续费环比",
      sortDexVolume: "24h DEX量",
      filterAll: "全部公链",
      filterStock: "有代币化美股",
      filterMissing: "缺少代币化美股",
      stockByChain: "代币化美股按公链分布",
      stockByChainMeta: "RWA.xyz 总价值 / 30天增幅",
      feePe: "手续费 P/S",
      feePeMeta: "最大市值 / 近30天手续费年化",
      chain: "公链",
      maxMarketCap: "最大市值",
      fees30d: "30天手续费",
      fullMetrics: "完整公链指标",
      tokenizedStocks: "代币化美股",
      stocksToTvl: "美股/TVL",
      feeGrowth30d: "30天手续费环比",
      dexVolume24h: "24h DEX量",
      dexToTvl: "DEX量/TVL",
      institutionLabel: "Research Access",
      footerTitle: "更多链上投研数据与交易入口",
      footerText: "BN 开户享 30% 返佣；也欢迎添加币安广场好友交流数据看法。",
      rebateLink: "BN 开户享 30% 返佣",
      binanceSquare: "币安广场 ID",
      totalTvl: "总 TVL",
      totalTokenizedStocks: "代币化美股总值",
      coveredChains: "覆盖公链",
      feeGrowth: "30天手续费环比",
      totalDexVolume: "24h DEX总量",
      missing: "暂无数据",
      notApplicable: "不适用",
      rows: "条",
      chainData: "公链数据",
      dexData: "DEX 数据",
      perpsData: "永续合约",
      stablecoinData: "稳定币",
      lendingData: "借贷",
      valuationData: "协议估值",
      dexTokenMetrics: "DEX 代币指标",
      dexTokenMeta: "按代币聚合协议族，同时展示手续费 P/S 与持有人收入 PE",
      perpsIntroTitle: "链上永续合约平台简介",
      perpsIntroText: "链上永续合约平台提供去中心化杠杆交易。本页先展示可稳定自动更新的公开字段，包括协议 TVL、代币市值、手续费、持有人收入以及费用向代币价值捕获的传导效率。",
      perpsFocus1: "流动性基础",
      perpsFocus2: "估值约束",
      perpsFocus3: "价值捕获",
      perpsPlatformMetrics: "链上永续合约平台指标",
      perpsPlatformMeta: "已发币平台，按协议版本聚合；缺失数据不参与估值排序",
      platform: "平台",
      intro: "简介",
      mainChains: "主要链",
      marketCapToTvl: "市值/TVL",
      tvl30dChange: "TVL 30天环比",
      feePsShort: "手续费 P/S",
      stablecoinIntroTitle: "稳定币市值月度变化",
      stablecoinIntroText: "稳定币市值反映链上美元流动性规模。本页展示当前稳定币流通市值、30天前市值、绝对增减额和月环比。",
      stablecoinFocus1: "当前规模",
      stablecoinFocus2: "绝对变化",
      stablecoinFocus3: "增长速度",
      stablecoinMetrics: "稳定币市值指标",
      stablecoinMeta: "按当前流通市值排序，展示 30 天绝对增量和环比增速",
      stablecoin: "稳定币",
      currentMarketCap: "当前市值",
      previous30dMarketCap: "30天前市值",
      marketCapAbsChange: "30天绝对增减",
      marketCap30dChange: "30天环比",
      pegMechanism: "抵押机制",
      chainsCount: "覆盖链数",
      lendingIntroTitle: "链上借贷协议估值",
      lendingIntroText: "借贷协议的核心观察点是可借贷资产规模、利差和费用向代币持有人的传导。本页按已发币借贷协议聚合 TVL、手续费、协议收入、持有人收入，并计算 P/S 与 PE。",
      lendingFocus1: "资金规模",
      lendingFocus2: "收入效率",
      lendingFocus3: "价值捕获",
      lendingProtocolMetrics: "借贷协议指标",
      lendingProtocolMeta: "已发币借贷协议，按协议版本聚合；P/S 使用 30 天收入年化口径",
      protocolRevenue30d: "30天协议收入",
      protocolRevenuePs: "协议收入 P/S",
      valuationIntroTitle: "发币协议 PE Top 100",
      valuationIntroText: "本页筛选已发币且可匹配市值与收入数据的协议，按 PE 从低到高排序。优先使用持有人收入 PE；若持有人收入缺失，则使用协议收入 PE 补位并标出口径。",
      valuationFocus1: "筛选范围",
      valuationFocus2: "排序指标",
      valuationFocus3: "展示数量",
      valuationMetrics: "协议估值 Top 100",
      valuationMeta: "市值来自 DefiLlama 协议页；收入来自 DefiLlama Fees/Revenue/Holders Revenue",
      protocol: "协议",
      category: "分类",
      protocolRevenuePe: "协议收入 PE",
      valuationPe: "排序 PE",
      peBasis: "PE 口径",
      token: "代币",
      volume30d: "30天交易量",
      volume30dChange: "交易量环比",
      holdersRevenue30d: "30天回购/持有人收入",
      buybackRatio: "回购比例",
      feePeShort: "手续费 P/S",
      holdersPe: "持有人收入 PE",
    },
    en: {
      title: "Public Chain Data Mining Dashboard",
      staticData: "Static data",
      reload: "Reload",
      loading: "Loading...",
      langButton: "中文",
      updated: "Updated",
      noUpdatedAt: "No update time",
      sort: "Sort",
      filter: "Filter",
      sortTokenizedStocks: "Tokenized stock value",
      sortTvl: "TVL",
      sortFeeGrowth: "30D fee growth",
      sortDexVolume: "24h DEX volume",
      filterAll: "All chains",
      filterStock: "With tokenized stocks",
      filterMissing: "Missing tokenized stocks",
      stockByChain: "Tokenized Stocks by Chain",
      stockByChainMeta: "RWA.xyz Total Value / 30D Growth",
      feePe: "Fee P/S",
      feePeMeta: "FDV / annualized 30D fees",
      chain: "Chain",
      maxMarketCap: "FDV",
      fees30d: "30D Fees",
      fullMetrics: "Full Chain Metrics",
      tokenizedStocks: "Tokenized Stocks",
      stocksToTvl: "Stocks/TVL",
      feeGrowth30d: "30D Fee Growth",
      dexVolume24h: "24h DEX Volume",
      dexToTvl: "DEX/TVL",
      institutionLabel: "Research Access",
      footerTitle: "More On-chain Research and Trading Access",
      footerText: "Open a BN account for 30% commission rebate; add my Binance Square ID for market discussion.",
      rebateLink: "BN 30% Rebate",
      binanceSquare: "Binance Square ID",
      totalTvl: "Total TVL",
      totalTokenizedStocks: "Total Tokenized Stocks",
      coveredChains: "Covered Chains",
      feeGrowth: "30D Fee Growth",
      totalDexVolume: "24h DEX Volume",
      missing: "No data",
      notApplicable: "N/A",
      rows: "rows",
      chainData: "Chain Data",
      dexData: "DEX Data",
      perpsData: "Perps",
      stablecoinData: "Stablecoins",
      lendingData: "Lending",
      valuationData: "Valuation",
      dexTokenMetrics: "DEX Token Metrics",
      dexTokenMeta: "Aggregated by protocol token; fee P/S and holder-revenue P/E are shown side by side",
      perpsIntroTitle: "On-chain Perpetuals Overview",
      perpsIntroText: "On-chain perpetual platforms provide decentralized leveraged trading. This page first shows public fields that can update reliably: protocol TVL, token valuation, fees, holder revenue, and fee-to-token value capture.",
      perpsFocus1: "Liquidity Base",
      perpsFocus2: "Valuation Anchor",
      perpsFocus3: "Value Capture",
      perpsPlatformMetrics: "On-chain Perpetual Platform Metrics",
      perpsPlatformMeta: "Tokenized platforms aggregated across protocol versions; missing values are excluded from valuation sorting",
      platform: "Platform",
      intro: "Intro",
      mainChains: "Main Chains",
      marketCapToTvl: "MCap/TVL",
      tvl30dChange: "TVL 30D Change",
      feePsShort: "Fee P/S",
      stablecoinIntroTitle: "Stablecoin Market Cap Monthly Change",
      stablecoinIntroText: "Stablecoin market cap reflects on-chain dollar liquidity. This page shows current circulating value, value 30 days ago, absolute change, and month-over-month growth.",
      stablecoinFocus1: "Current Scale",
      stablecoinFocus2: "Absolute Change",
      stablecoinFocus3: "MoM Growth",
      stablecoinMetrics: "Stablecoin Market Cap Metrics",
      stablecoinMeta: "Sorted by current circulating value, with 30D absolute and percentage change",
      stablecoin: "Stablecoin",
      currentMarketCap: "Current MCap",
      previous30dMarketCap: "30D Ago MCap",
      marketCapAbsChange: "30D Abs Change",
      marketCap30dChange: "30D Change",
      pegMechanism: "Peg Mechanism",
      chainsCount: "Chains",
      lendingIntroTitle: "On-chain Lending Valuation",
      lendingIntroText: "For lending protocols, the key questions are asset scale, spreads, and how fees flow to token holders. This page aggregates TVL, fees, protocol revenue, holder revenue, and valuation multiples for tokenized lending protocols.",
      lendingFocus1: "Capital Base",
      lendingFocus2: "Revenue Efficiency",
      lendingFocus3: "Value Capture",
      lendingProtocolMetrics: "Lending Protocol Metrics",
      lendingProtocolMeta: "Tokenized lending protocols aggregated across versions; P/S uses annualized 30D revenue",
      protocolRevenue30d: "30D Protocol Revenue",
      protocolRevenuePs: "Protocol Revenue P/S",
      valuationIntroTitle: "Tokenized Protocol PE Top 100",
      valuationIntroText: "This page filters protocols with token market cap and revenue data, ranked by PE from low to high. Holder revenue PE is preferred; protocol revenue PE is used as fallback and labeled.",
      valuationFocus1: "Universe",
      valuationFocus2: "Sort Metric",
      valuationFocus3: "Rows",
      valuationMetrics: "Protocol Valuation Top 100",
      valuationMeta: "Market cap comes from DefiLlama protocol pages; revenue comes from DefiLlama Fees/Revenue/Holders Revenue",
      protocol: "Protocol",
      category: "Category",
      protocolRevenuePe: "Protocol Revenue P/E",
      valuationPe: "Ranking P/E",
      peBasis: "P/E Basis",
      token: "Token",
      volume30d: "30D Volume",
      volume30dChange: "Volume MoM",
      holdersRevenue30d: "30D Buyback / Holder Revenue",
      buybackRatio: "Buyback Ratio",
      feePeShort: "Fee P/S",
      holdersPe: "Holder Revenue P/E",
    },
  };

  function t(key) {
    return (i18n[currentLang] && i18n[currentLang][key]) || i18n.zh[key] || key;
  }

  function applyLanguage() {
    document.documentElement.lang = currentLang === "zh" ? "zh-CN" : "en";
    document.querySelectorAll("[data-i18n]").forEach((node) => {
      node.textContent = t(node.dataset.i18n);
    });
    document.querySelectorAll("[data-i18n-html]").forEach((node) => {
      node.innerHTML = t(node.dataset.i18nHtml);
    });
    document.getElementById("langButton").textContent = t("langButton");
    document.getElementById("updatedAt").textContent = data.generated_at
      ? `${t("updated")} ${data.generated_at}`
      : t("noUpdatedAt");
  }

  function isNumber(value) {
    return typeof value === "number" && Number.isFinite(value);
  }

  const NOT_APPLICABLE_MARKET_CAP = new Set(["base"]);

  function money(value, fallback = t("missing")) {
    if (!isNumber(value)) return `<span class="missing">${fallback}</span>`;
    const abs = Math.abs(value);
    const sign = value < 0 ? "-" : "";
    if (abs >= 1e12) return `${sign}$${(abs / 1e12).toFixed(2)}T`;
    if (abs >= 1e9) return `${sign}$${(abs / 1e9).toFixed(2)}B`;
    if (abs >= 1e6) return `${sign}$${(abs / 1e6).toFixed(2)}M`;
    if (abs >= 1e3) return `${sign}$${(abs / 1e3).toFixed(2)}K`;
    return `${sign}$${abs.toFixed(2)}`;
  }

  function marketCapMoney(value, fallback = t("missing")) {
    if (!isNumber(value)) return `<span class="missing">${fallback}</span>`;
    return `$${(value / 1e9).toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}B`;
  }

  function number(value) {
    if (!isNumber(value)) return `<span class="missing">${t("missing")}</span>`;
    return value.toLocaleString("en-US", { maximumFractionDigits: 0 });
  }

  function pct(value) {
    if (!isNumber(value)) return `<span class="missing">${t("missing")}</span>`;
    const cls = value > 0 ? "positive" : value < 0 ? "negative" : "";
    return `<span class="${cls}">${(value * 100).toFixed(2)}%</span>`;
  }

  function plainPct(value) {
    if (!isNumber(value)) return t("missing");
    return `${(value * 100).toFixed(2)}%`;
  }

  function multiple(value) {
    if (!isNumber(value)) return `<span class="missing">${t("notApplicable")}</span>`;
    return `${value.toFixed(1)}x`;
  }

  function filteredChains() {
    let rows = baseFilteredChains();
    rows.sort((a, b) => {
      const av = isNumber(a[sortBy.value]) ? a[sortBy.value] : -Infinity;
      const bv = isNumber(b[sortBy.value]) ? b[sortBy.value] : -Infinity;
      return bv - av;
    });
    return rows;
  }

  function baseFilteredChains() {
    let rows = chains.slice();
    if (filterMode.value === "stock") {
      rows = rows.filter((row) => isNumber(row.tokenized_stock_value_usd));
    } else if (filterMode.value === "missing") {
      rows = rows.filter((row) => !isNumber(row.tokenized_stock_value_usd));
    }
    return rows;
  }

  function tableRows() {
    const rows = baseFilteredChains();
    rows.sort((a, b) => compareRows(a, b, tableSort.key, tableSort.direction));
    return rows;
  }

  function compareRows(a, b, key, direction) {
    const multiplier = direction === "asc" ? 1 : -1;
    const av = a[key];
    const bv = b[key];
    const aMissing = av === null || av === undefined || av === "";
    const bMissing = bv === null || bv === undefined || bv === "";
    if (aMissing && bMissing) return 0;
    if (aMissing) return 1;
    if (bMissing) return -1;
    if (typeof av === "number" && typeof bv === "number") {
      return (av - bv) * multiplier;
    }
    return String(av).localeCompare(String(bv), "zh-CN") * multiplier;
  }

  function syncTableSortControls() {
    document.querySelectorAll(".sort-head:not(.dex-sort-head):not(.perps-sort-head):not(.stablecoin-sort-head):not(.lending-sort-head):not(.valuation-sort-head)").forEach((button) => {
      const active = button.dataset.sort === tableSort.key;
      button.classList.toggle("active", active);
      button.classList.toggle("asc", active && tableSort.direction === "asc");
      button.classList.toggle("desc", active && tableSort.direction === "desc");
    });
  }

  function syncDexSortControls() {
    document.querySelectorAll(".dex-sort-head").forEach((button) => {
      const active = button.dataset.sort === dexSort.key;
      button.classList.toggle("active", active);
      button.classList.toggle("asc", active && dexSort.direction === "asc");
      button.classList.toggle("desc", active && dexSort.direction === "desc");
    });
  }

  function syncPerpsSortControls() {
    document.querySelectorAll(".perps-sort-head").forEach((button) => {
      const active = button.dataset.sort === perpsSort.key;
      button.classList.toggle("active", active);
      button.classList.toggle("asc", active && perpsSort.direction === "asc");
      button.classList.toggle("desc", active && perpsSort.direction === "desc");
    });
  }

  function syncStablecoinSortControls() {
    document.querySelectorAll(".stablecoin-sort-head").forEach((button) => {
      const active = button.dataset.sort === stablecoinSort.key;
      button.classList.toggle("active", active);
      button.classList.toggle("asc", active && stablecoinSort.direction === "asc");
      button.classList.toggle("desc", active && stablecoinSort.direction === "desc");
    });
  }

  function syncLendingSortControls() {
    document.querySelectorAll(".lending-sort-head").forEach((button) => {
      const active = button.dataset.sort === lendingSort.key;
      button.classList.toggle("active", active);
      button.classList.toggle("asc", active && lendingSort.direction === "asc");
      button.classList.toggle("desc", active && lendingSort.direction === "desc");
    });
  }

  function syncValuationSortControls() {
    document.querySelectorAll(".valuation-sort-head").forEach((button) => {
      const active = button.dataset.sort === valuationSort.key;
      button.classList.toggle("active", active);
      button.classList.toggle("asc", active && valuationSort.direction === "asc");
      button.classList.toggle("desc", active && valuationSort.direction === "desc");
    });
  }

  function sum(rows, key) {
    return rows.reduce((acc, row) => acc + (isNumber(row[key]) ? row[key] : 0), 0);
  }

  function weightedAverage(rows, valueKey, weightKey) {
    const usable = rows.filter((row) => isNumber(row[valueKey]) && isNumber(row[weightKey]));
    const weight = sum(usable, weightKey);
    if (!weight) return null;
    return usable.reduce((acc, row) => acc + row[valueKey] * row[weightKey], 0) / weight;
  }

  function renderSummary() {
    const stockRows = chains.filter((row) => isNumber(row.tokenized_stock_value_usd));
    const metrics = [
      [t("totalTvl"), money(sum(chains, "tvl_usd"))],
      [t("totalTokenizedStocks"), money(sum(chains, "tokenized_stock_value_usd"))],
      [t("coveredChains"), `${stockRows.length}/${chains.length}`],
      [t("feeGrowth"), plainPct(weightedAverage(chains, "network_fees_30d_change", "network_fees_30d_usd"))],
      [t("totalDexVolume"), money(sum(chains, "dex_volume_24h_usd"))],
    ];
    document.getElementById("summaryGrid").innerHTML = metrics
      .map(([label, value]) => `<article class="metric"><span>${label}</span><strong>${value}</strong></article>`)
      .join("");
  }

  function renderBars(id, rows, labelKey, valueKey, limit, options = {}) {
    const usable = rows.filter((row) => isNumber(row[valueKey])).slice(0, limit);
    const max = Math.max(...usable.map((row) => row[valueKey]), 1);
    const changeKey = options.changeKey;
    const showChange = Boolean(changeKey);
    document.getElementById(id).innerHTML = usable
      .map((row) => {
        const width = Math.max(1, (row[valueKey] / max) * 100);
        const valueCell = showChange
          ? `<div class="bar-values"><span>${money(row[valueKey])}</span><span>${pct(row[changeKey])}</span></div>`
          : `<div class="bar-value">${money(row[valueKey])}</div>`;
        return `<div class="bar-row">
          <div class="bar-name" title="${row[labelKey]}">${row[labelKey]}</div>
          <div class="bar-track"><div class="bar-fill" style="width:${width}%"></div></div>
          ${valueCell}
        </div>`;
      })
      .join("");
  }

  function renderPeTable(rows) {
    const sorted = rows
      .slice()
      .sort((a, b) => compareRows(a, b, "fee_pe", "asc"));
    document.getElementById("peRows").innerHTML = sorted
      .map(
        (row) => `<tr>
          <td>${row.llama_name || row.chain}</td>
          <td>${marketCapMoney(row.market_cap_usd, NOT_APPLICABLE_MARKET_CAP.has(row.chain) ? t("notApplicable") : t("missing"))}</td>
          <td>${money(row.network_fees_30d_usd)}</td>
          <td>${multiple(row.fee_pe)}</td>
        </tr>`
      )
      .join("");
  }

  function renderTable(rows) {
    syncTableSortControls();
    document.getElementById("rowCount").textContent = `${rows.length} ${t("rows")}`;
    document.getElementById("chainRows").innerHTML = rows
      .map(
        (row) => `<tr>
          <td>${row.llama_name || row.chain}</td>
          <td>${marketCapMoney(row.market_cap_usd, NOT_APPLICABLE_MARKET_CAP.has(row.chain) ? t("notApplicable") : t("missing"))}</td>
          <td>${money(row.tvl_usd)}</td>
          <td>${money(row.tokenized_stock_value_usd)}</td>
          <td>${pct(row.tokenized_stock_to_tvl)}</td>
          <td>${pct(row.network_fees_30d_change)}</td>
          <td>${money(row.dex_volume_24h_usd)}</td>
          <td>${pct(row.dex_volume_24h_to_tvl)}</td>
        </tr>`
      )
      .join("");
  }

  function sortedDexTokens() {
    return dexTokens
      .slice()
      .sort((a, b) => compareRows(a, b, dexSort.key, dexSort.direction));
  }

  function renderDexTable() {
    syncDexSortControls();
    const rows = sortedDexTokens();
    document.getElementById("dexRowCount").textContent = `${rows.length} ${t("rows")}`;
    document.getElementById("dexRows").innerHTML = rows
      .map(
        (row) => `<tr>
          <td>${row.token}</td>
          <td>${marketCapMoney(row.token_market_cap_usd)}</td>
          <td>${money(row.volume_30d_usd)}</td>
          <td>${pct(row.volume_30d_change)}</td>
          <td>${money(row.fees_30d_usd)}</td>
          <td>${pct(row.fees_30d_change)}</td>
          <td>${money(row.holders_revenue_30d_usd)}</td>
          <td>${pct(row.holders_revenue_to_fees)}</td>
          <td>${multiple(row.fee_pe)}</td>
          <td>${multiple(row.holders_revenue_pe)}</td>
        </tr>`
      )
      .join("");
  }

  function sortedPerpsPlatforms() {
    return perpsPlatforms
      .slice()
      .sort((a, b) => compareRows(a, b, perpsSort.key, perpsSort.direction));
  }

  function truncate(value, length = 34) {
    if (!value) return t("missing");
    return value.length > length ? `${value.slice(0, length)}...` : value;
  }

  function renderPerpsTable() {
    syncPerpsSortControls();
    const rows = sortedPerpsPlatforms();
    document.getElementById("perpsRowCount").textContent = `${rows.length} ${t("rows")}`;
    document.getElementById("perpsRows").innerHTML = rows
      .map(
        (row) => `<tr>
          <td>${row.platform}</td>
          <td>${row.token}</td>
          <td class="text-cell" title="${row.intro || ""}">${truncate(row.intro)}</td>
          <td class="text-cell" title="${row.chains || ""}">${truncate(row.chains, 28)}</td>
          <td>${money(row.tvl_usd)}</td>
          <td>${pct(row.tvl_30d_change)}</td>
          <td>${marketCapMoney(row.token_market_cap_usd)}</td>
          <td>${multiple(row.market_cap_to_tvl)}</td>
          <td>${money(row.fees_30d_usd)}</td>
          <td>${money(row.holders_revenue_30d_usd)}</td>
          <td>${multiple(row.fee_ps)}</td>
          <td>${multiple(row.holders_revenue_pe)}</td>
        </tr>`
      )
      .join("");
  }

  function sortedStablecoins() {
    return stablecoins
      .slice()
      .sort((a, b) => compareRows(a, b, stablecoinSort.key, stablecoinSort.direction));
  }

  function renderStablecoinTable() {
    syncStablecoinSortControls();
    const rows = sortedStablecoins();
    document.getElementById("stablecoinRowCount").textContent = `${rows.length} ${t("rows")}`;
    document.getElementById("stablecoinRows").innerHTML = rows
      .map(
        (row) => `<tr>
          <td>${row.stablecoin}</td>
          <td>${row.symbol}</td>
          <td>${money(row.market_cap_usd)}</td>
          <td>${money(row.market_cap_previous_30d_usd)}</td>
          <td>${money(row.market_cap_30d_abs_change_usd)}</td>
          <td>${pct(row.market_cap_30d_change)}</td>
          <td>${row.peg_mechanism || t("missing")}</td>
          <td>${number(row.chains_count)}</td>
        </tr>`
      )
      .join("");
  }

  function sortedLendingProtocols() {
    return lendingProtocols
      .slice()
      .sort((a, b) => compareRows(a, b, lendingSort.key, lendingSort.direction));
  }

  function renderLendingTable() {
    syncLendingSortControls();
    const rows = sortedLendingProtocols();
    document.getElementById("lendingRowCount").textContent = `${rows.length} ${t("rows")}`;
    document.getElementById("lendingRows").innerHTML = rows
      .map(
        (row) => `<tr>
          <td>${row.platform}</td>
          <td>${row.token}</td>
          <td class="text-cell" title="${row.intro || ""}">${truncate(row.intro)}</td>
          <td class="text-cell" title="${row.chains || ""}">${truncate(row.chains, 28)}</td>
          <td>${money(row.tvl_usd)}</td>
          <td>${pct(row.tvl_30d_change)}</td>
          <td>${marketCapMoney(row.token_market_cap_usd)}</td>
          <td>${multiple(row.market_cap_to_tvl)}</td>
          <td>${money(row.fees_30d_usd)}</td>
          <td>${money(row.protocol_revenue_30d_usd)}</td>
          <td>${money(row.holders_revenue_30d_usd)}</td>
          <td>${multiple(row.fee_ps)}</td>
          <td>${multiple(row.protocol_revenue_ps)}</td>
          <td>${multiple(row.holders_revenue_pe)}</td>
        </tr>`
      )
      .join("");
  }

  function sortedProtocolValuations() {
    return protocolValuations
      .slice()
      .sort((a, b) => compareRows(a, b, valuationSort.key, valuationSort.direction));
  }

  function renderProtocolValuationTable() {
    syncValuationSortControls();
    const rows = sortedProtocolValuations();
    document.getElementById("valuationRowCount").textContent = `${rows.length} ${t("rows")}`;
    document.getElementById("valuationRows").innerHTML = rows
      .map(
        (row) => `<tr>
          <td>${row.protocol}</td>
          <td>${row.token}</td>
          <td>${row.category || t("missing")}</td>
          <td class="text-cell" title="${row.intro_zh || row.intro || ""}">${truncate(row.intro_zh || row.intro, 42)}</td>
          <td>${money(row.market_cap_usd)}</td>
          <td>${money(row.tvl_usd)}</td>
          <td>${money(row.fees_30d_usd)}</td>
          <td>${money(row.protocol_revenue_30d_usd)}</td>
          <td>${money(row.holders_revenue_30d_usd)}</td>
          <td>${multiple(row.fee_ps)}</td>
          <td>${multiple(row.protocol_revenue_pe)}</td>
          <td>${multiple(row.holders_revenue_pe)}</td>
          <td>${multiple(row.valuation_pe)}</td>
          <td>${row.valuation_pe_basis || t("missing")}</td>
        </tr>`
      )
      .join("");
  }

  function renderView() {
    document.getElementById("chainsView").classList.toggle("hidden", currentView !== "chains");
    document.getElementById("dexView").classList.toggle("hidden", currentView !== "dex");
    document.getElementById("perpsView").classList.toggle("hidden", currentView !== "perps");
    document.getElementById("stablecoinsView").classList.toggle("hidden", currentView !== "stablecoins");
    document.getElementById("lendingView").classList.toggle("hidden", currentView !== "lending");
    document.getElementById("valuationsView").classList.toggle("hidden", currentView !== "valuations");
    document.querySelectorAll(".page-tab").forEach((button) => {
      button.classList.toggle("active", button.dataset.view === currentView);
    });
  }

  function render() {
    const rows = filteredChains();
    applyLanguage();
    renderSummary();
    renderBars("stockBars", rows, "llama_name", "tokenized_stock_value_usd", 12, {
      changeKey: "tokenized_stock_30d_change",
    });
    renderPeTable(rows);
    renderTable(tableRows());
    renderDexTable();
    renderPerpsTable();
    renderStablecoinTable();
    renderLendingTable();
    renderProtocolValuationTable();
    renderView();
  }

  document.getElementById("refreshButton").addEventListener("click", () => {
    const button = document.getElementById("refreshButton");
    button.textContent = t("loading");
    button.disabled = true;
    window.location.reload();
  });
  document.getElementById("langButton").addEventListener("click", () => {
    currentLang = currentLang === "zh" ? "en" : "zh";
    localStorage.setItem("dashboard_lang", currentLang);
    render();
  });
  sortBy.addEventListener("change", render);
  filterMode.addEventListener("change", render);
  document.querySelectorAll(".sort-head:not(.dex-sort-head):not(.perps-sort-head):not(.stablecoin-sort-head):not(.lending-sort-head):not(.valuation-sort-head)").forEach((button) => {
    button.addEventListener("click", () => {
      const key = button.dataset.sort;
      if (tableSort.key === key) {
        tableSort.direction = tableSort.direction === "desc" ? "asc" : "desc";
      } else {
        tableSort.key = key;
        tableSort.direction = key === "llama_name" ? "asc" : "desc";
      }
      render();
    });
  });
  document.querySelectorAll(".dex-sort-head").forEach((button) => {
    button.addEventListener("click", () => {
      const key = button.dataset.sort;
      if (dexSort.key === key) {
        dexSort.direction = dexSort.direction === "desc" ? "asc" : "desc";
      } else {
        dexSort.key = key;
        dexSort.direction = key === "token" || key.endsWith("_pe") ? "asc" : "desc";
      }
      renderDexTable();
    });
  });
  document.querySelectorAll(".perps-sort-head").forEach((button) => {
    button.addEventListener("click", () => {
      const key = button.dataset.sort;
      if (perpsSort.key === key) {
        perpsSort.direction = perpsSort.direction === "desc" ? "asc" : "desc";
      } else {
        perpsSort.key = key;
        perpsSort.direction = key === "platform" || key === "token" || key.endsWith("_pe") || key.endsWith("_ps") ? "asc" : "desc";
      }
      renderPerpsTable();
    });
  });
  document.querySelectorAll(".stablecoin-sort-head").forEach((button) => {
    button.addEventListener("click", () => {
      const key = button.dataset.sort;
      if (stablecoinSort.key === key) {
        stablecoinSort.direction = stablecoinSort.direction === "desc" ? "asc" : "desc";
      } else {
        stablecoinSort.key = key;
        stablecoinSort.direction = key === "stablecoin" || key === "symbol" ? "asc" : "desc";
      }
      renderStablecoinTable();
    });
  });
  document.querySelectorAll(".lending-sort-head").forEach((button) => {
    button.addEventListener("click", () => {
      const key = button.dataset.sort;
      if (lendingSort.key === key) {
        lendingSort.direction = lendingSort.direction === "desc" ? "asc" : "desc";
      } else {
        lendingSort.key = key;
        lendingSort.direction = key === "platform" || key === "token" || key.endsWith("_pe") || key.endsWith("_ps") ? "asc" : "desc";
      }
      renderLendingTable();
    });
  });
  document.querySelectorAll(".valuation-sort-head").forEach((button) => {
    button.addEventListener("click", () => {
      const key = button.dataset.sort;
      if (valuationSort.key === key) {
        valuationSort.direction = valuationSort.direction === "desc" ? "asc" : "desc";
      } else {
        valuationSort.key = key;
        valuationSort.direction = key === "protocol" || key === "token" || key === "category" || key.endsWith("_pe") || key.endsWith("_ps") ? "asc" : "desc";
      }
      renderProtocolValuationTable();
    });
  });
  document.querySelectorAll(".page-tab").forEach((button) => {
    button.addEventListener("click", () => {
      currentView = button.dataset.view;
      render();
    });
  });
  render();
})();
