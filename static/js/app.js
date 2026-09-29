/**
 * Simple LRU Cache-Backed URL Shortener - Main Client Application Logic
 */

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("shorten-form");
  const urlInput = document.getElementById("url-input");
  const expirySelect = document.getElementById("expiry-select");
  const btnShorten = document.getElementById("btn-shorten");
  const btnText = document.getElementById("btn-text");
  const btnSpinner = document.getElementById("btn-spinner");
  const alertBox = document.getElementById("alert-box");
  const resultCard = document.getElementById("result-card");
  const shortUrlLink = document.getElementById("short-url-link");
  const btnCopy = document.getElementById("btn-copy");
  const copyText = document.getElementById("copy-text");
  const copyIcon = document.getElementById("copy-icon");
  const resultStatusBadge = document.getElementById("result-status-badge");
  const expiryInfo = document.getElementById("expiry-info");
  const navCacheText = document.getElementById("nav-cache-text");

  // Fetch initial LRU cache stats for navbar badge
  updateCacheBadge();

  // Form submission handler
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearAlert();

    const rawUrl = urlInput.value.trim();
    if (!rawUrl) {
      showAlert("Please enter a valid URL.", "error");
      urlInput.focus();
      return;
    }

    // Prepare payload
    const payload = { url: rawUrl };
    const expiryVal = expirySelect.value;
    if (expiryVal) {
      payload.expires_in = parseInt(expiryVal, 10);
    }

    // Set loading state
    setLoading(true);

    try {
      const response = await fetch("/api/shorten", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.error || "Failed to shorten URL.");
      }

      // Display short URL result
      displayResult(data);
      updateCacheBadge();

    } catch (err) {
      showAlert(err.message || "An unexpected error occurred.", "error");
    } finally {
      setLoading(false);
    }
  });

  // Copy to clipboard handler
  btnCopy.addEventListener("click", async () => {
    const textToCopy = shortUrlLink.href;
    if (!textToCopy) return;

    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(textToCopy);
      } else {
        // Fallback for older browsers
        const temp = document.createElement("textarea");
        temp.value = textToCopy;
        document.body.appendChild(temp);
        temp.select();
        document.execCommand("copy");
        document.body.removeChild(temp);
      }

      // Visual feedback
      copyIcon.textContent = "✅";
      copyText.textContent = "Copied!";
      btnCopy.style.borderColor = "var(--accent-emerald)";

      setTimeout(() => {
        copyIcon.textContent = "📋";
        copyText.textContent = "Copy";
        btnCopy.style.borderColor = "var(--border-subtle)";
      }, 2500);

    } catch (err) {
      console.error("Clipboard copy failed: ", err);
      showAlert("Could not copy automatically. Please copy the URL manually.", "error");
    }
  });

  function displayResult(data) {
    shortUrlLink.href = data.short_url;
    shortUrlLink.textContent = data.short_url;

    if (data.is_duplicate) {
      resultStatusBadge.textContent = "Existing Active URL";
      resultStatusBadge.style.color = "#38bdf8";
      showAlert("Identical URL already shortened. Returned existing short code.", "success");
    } else {
      resultStatusBadge.textContent = "Short URL Created";
      resultStatusBadge.style.color = "#a5b4fc";
      showAlert("Short URL created and cached in LRU memory!", "success");
    }

    if (data.expires_at) {
      const expDate = new Date(data.expires_at);
      expiryInfo.textContent = `Expires: ${expDate.toLocaleString()}`;
    } else {
      expiryInfo.textContent = "Expires: Never (Permanent)";
    }

    resultCard.classList.add("active");
  }

  function setLoading(isLoading) {
    if (isLoading) {
      btnShorten.disabled = true;
      btnSpinner.style.display = "inline-block";
      btnText.textContent = "Shortening...";
    } else {
      btnShorten.disabled = false;
      btnSpinner.style.display = "none";
      btnText.textContent = "Shorten URL";
    }
  }

  function showAlert(message, type = "error") {
    alertBox.textContent = message;
    alertBox.className = `alert alert-${type}`;
    alertBox.style.display = "flex";
  }

  function clearAlert() {
    alertBox.style.display = "none";
    alertBox.textContent = "";
  }

  async function updateCacheBadge() {
    try {
      const res = await fetch("/api/cache/stats");
      if (res.ok) {
        const stats = await res.json();
        navCacheText.textContent = `LRU Cache: ${stats.current_size}/${stats.capacity} items (${stats.hit_rate}% hit)`;
      }
    } catch {
      navCacheText.textContent = "LRU Operational";
    }
  }
});
