(function () {
  const data = window.DASHBOARD_DATA || {};
  const chains = Array.isArray(data.chains) ? data.chains : [];

  const sortBy = document.getElementById("sortBy");
  const filterMode = document.getElementById("filterMode");
  let currentLang = localStorage.getItem("dashboard_lang") || "zh";
  const tableSort = {
    key: "market_cap_usd",
    direction: "desc",
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
      feePe: "手续费 PE",
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
      feePe: "Fee P/E",
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
    if (abs >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
    if (abs >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
    if (abs >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
    if (abs >= 1e3) return `$${(value / 1e3).toFixed(2)}K`;
    return `$${value.toFixed(2)}`;
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
    document.querySelectorAll(".sort-head").forEach((button) => {
      const active = button.dataset.sort === tableSort.key;
      button.classList.toggle("active", active);
      button.classList.toggle("asc", active && tableSort.direction === "asc");
      button.classList.toggle("desc", active && tableSort.direction === "desc");
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

  function render() {
    const rows = filteredChains();
    applyLanguage();
    renderSummary();
    renderBars("stockBars", rows, "llama_name", "tokenized_stock_value_usd", 12, {
      changeKey: "tokenized_stock_30d_change",
    });
    renderPeTable(rows);
    renderTable(tableRows());
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
  document.querySelectorAll(".sort-head").forEach((button) => {
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
  render();
})();
