/**
 * Simple LRU Cache-Backed URL Shortener - Analytics Dashboard Logic
 */

document.addEventListener("DOMContentLoaded", () => {
  const valTotalUrls = document.getElementById("val-total-urls");
  const valTotalClicks = document.getElementById("val-total-clicks");
  const valCacheHits = document.getElementById("val-cache-hits");
  const valCacheMisses = document.getElementById("val-cache-misses");
  const valHitRate = document.getElementById("val-hit-rate");
  const hitRateFill = document.getElementById("hit-rate-fill");
  const valCacheOccupancy = document.getElementById("val-cache-occupancy");
  const dbStatusText = document.getElementById("db-status-text");
  const cacheFlowContainer = document.getElementById("cache-flow-container");
  const urlsTableBody = document.getElementById("urls-table-body");
  const btnRefresh = document.getElementById("btn-refresh");

  // Initial load
  loadDashboardData();

  // Manual refresh
  btnRefresh.addEventListener("click", () => {
    loadDashboardData();
  });

  // Auto-refresh every 10 seconds for live monitoring
  setInterval(loadDashboardData, 10000);

  async function loadDashboardData() {
    try {
      const res = await fetch("/api/analytics/details");
      if (!res.ok) throw new Error("Failed to load analytics details");

      const data = await res.json();
      const metrics = data.metrics || {};
      const recentUrls = data.recent_urls || [];
      const cachedItems = data.cached_items || [];

      // Update Metric Cards
      valTotalUrls.textContent = (metrics.total_urls || 0).toLocaleString();
      valTotalClicks.textContent = (metrics.total_clicks || 0).toLocaleString();
      valCacheHits.textContent = (metrics.cache_hits || 0).toLocaleString();
      valCacheMisses.textContent = (metrics.cache_misses || 0).toLocaleString();

      const hitRate = metrics.cache_hit_rate || 0;
      valHitRate.textContent = `${hitRate.toFixed(1)}%`;
      hitRateFill.style.width = `${Math.min(100, Math.max(0, hitRate))}%`;

      valCacheOccupancy.textContent = `${metrics.current_cache_size || 0} / ${metrics.cache_capacity || 100}`;
      if (metrics.database_type) {
        dbStatusText.textContent = metrics.database_type;
      }

      // Render Visual LRU Cache Flow
      renderCacheVisualizer(cachedItems);

      // Render Active URLs Table
      renderUrlsTable(recentUrls);

    } catch (err) {
      console.error("Error loading dashboard data: ", err);
    }
  }

  function renderCacheVisualizer(items) {
    if (!cacheFlowContainer) return;

    if (!items || items.length === 0) {
      cacheFlowContainer.innerHTML = `
        <div class="node-sentinel">HEAD (MRU)</div>
        <div class="node-arrow">⇄</div>
        <div style="color: var(--text-muted); font-size: 0.85rem; font-style: italic; padding: 0.5rem 1rem;">
          Cache is currently empty. Shorten or access URLs to populate cache.
        </div>
        <div class="node-arrow">⇄</div>
        <div class="node-sentinel">TAIL (LRU)</div>
      `;
      return;
    }

    let html = `<div class="node-sentinel">HEAD (MRU)</div>`;

    items.forEach((item, index) => {
      html += `<div class="node-arrow">⇄</div>`;
      html += `
        <div class="cache-node" title="${escapeHtml(item.original_url)}">
          <div class="node-code">${escapeHtml(item.short_code)}</div>
          <div class="node-tag">${item.click_count || 0} clicks</div>
        </div>
      `;
    });

    html += `<div class="node-arrow">⇄</div>`;
    html += `<div class="node-sentinel">TAIL (LRU)</div>`;

    cacheFlowContainer.innerHTML = html;
  }

  function renderUrlsTable(urls) {
    if (!urlsTableBody) return;

    if (!urls || urls.length === 0) {
      urlsTableBody.innerHTML = `
        <tr>
          <td colspan="6" style="text-align: center; color: var(--text-muted); padding: 2rem;">
            No shortened URLs found yet. Create one from the home page!
          </td>
        </tr>
      `;
      return;
    }

    let html = "";
    urls.forEach((u) => {
      const inCachePill = u.in_cache
        ? `<span class="cache-pill hit">In Cache (HIT)</span>`
        : `<span class="cache-pill miss">DB Only (MISS)</span>`;

      const createdTime = u.created_at ? new Date(u.created_at).toLocaleDateString() : "-";

      html += `
        <tr id="row-${escapeHtml(u.short_code)}">
          <td class="td-code">
            <a href="${escapeHtml(u.short_url)}" target="_blank" style="color: inherit; text-decoration: none;">
              ${escapeHtml(u.short_code)}
            </a>
          </td>
          <td class="td-url" title="${escapeHtml(u.original_url)}">
            ${escapeHtml(u.original_url)}
          </td>
          <td style="font-family: var(--font-mono); font-weight: 600;">${u.click_count || 0}</td>
          <td>${inCachePill}</td>
          <td style="color: var(--text-muted); font-size: 0.825rem;">${createdTime}</td>
          <td>
            <button class="btn-delete" data-code="${escapeHtml(u.short_code)}" title="Delete URL">
              Delete
            </button>
          </td>
        </tr>
      `;
    });

    urlsTableBody.innerHTML = html;

    // Attach delete listeners
    document.querySelectorAll(".btn-delete").forEach((btn) => {
      btn.addEventListener("click", async (e) => {
        const code = e.currentTarget.getAttribute("data-code");
        if (!code) return;

        if (confirm(`Are you sure you want to delete short URL "${code}"?`)) {
          try {
            const delRes = await fetch(`/api/url/${encodeURIComponent(code)}`, {
              method: "DELETE",
            });
            const delData = await delRes.json();
            if (delRes.ok && delData.success) {
              loadDashboardData();
            } else {
              alert(delData.error || "Failed to delete URL");
            }
          } catch (err) {
            alert("Error deleting URL: " + err.message);
          }
        }
      });
    });
  }

  function escapeHtml(text) {
    if (!text) return "";
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});
