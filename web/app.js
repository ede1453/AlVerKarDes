(() => {
  const API = "/api/v1";
  let accessToken = null;
  let currentUserId = null;
  let currentEmail = null;

  const $ = (id) => document.getElementById(id);

  function showMsg(el, text, kind) {
    el.textContent = text;
    el.className = "msg " + kind;
  }
  function clearMsg(el) {
    el.textContent = "";
    el.className = "msg";
  }

  async function api(path, options = {}) {
    const headers = Object.assign({ "Content-Type": "application/json" }, options.headers || {});
    if (accessToken) headers["Authorization"] = "Bearer " + accessToken;
    const res = await fetch(API + path, Object.assign({}, options, { headers }));
    let body = null;
    try { body = await res.json(); } catch (_) { /* no body */ }
    if (!res.ok) {
      const detail = body && (body.detail || body.code) ? (body.detail || body.code) : res.status;
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    return body;
  }

  // --- Auth tab switching ---
  $("tab-login").addEventListener("click", () => {
    $("login-form").classList.remove("hidden");
    $("register-form").classList.add("hidden");
    $("tab-login").classList.remove("secondary");
    $("tab-register").classList.add("secondary");
    clearMsg($("auth-msg"));
  });
  $("tab-register").addEventListener("click", () => {
    $("register-form").classList.remove("hidden");
    $("login-form").classList.add("hidden");
    $("tab-register").classList.remove("secondary");
    $("tab-login").classList.add("secondary");
    clearMsg($("auth-msg"));
  });

  function enterApp(email, userId, token) {
    currentEmail = email;
    currentUserId = userId;
    accessToken = token;
    $("auth-forms").classList.add("hidden");
    $("whoami").classList.remove("hidden");
    $("whoami-email").textContent = email;
    $("search-panel").classList.remove("hidden");
  }

  function exitApp() {
    currentEmail = null;
    currentUserId = null;
    accessToken = null;
    $("auth-forms").classList.remove("hidden");
    $("whoami").classList.add("hidden");
    $("search-panel").classList.add("hidden");
    $("result-panel").classList.add("hidden");
  }

  $("logout-link").addEventListener("click", exitApp);

  // --- Register (POST /identity/register -> POST /auth/login, gercek iki cagri) ---
  $("register-form").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const email = $("register-email").value.trim();
    const password = $("register-password").value;
    const btn = $("register-submit");
    btn.disabled = true;
    clearMsg($("auth-msg"));
    try {
      await api("/identity/register", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      const pair = await api("/auth/login", {
        method: "POST",
        body: JSON.stringify({ identifier: email, password }),
      });
      const me = await api("/identity/me", {
        headers: { Authorization: "Bearer " + pair.access_token },
      });
      accessToken = pair.access_token;
      enterApp(me.email, me.id, pair.access_token);
    } catch (err) {
      showMsg($("auth-msg"), "Kayıt başarısız: " + err.message, "error");
    } finally {
      btn.disabled = false;
    }
  });

  // --- Login (POST /auth/login, gercek cagri) ---
  $("login-form").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const email = $("login-email").value.trim();
    const password = $("login-password").value;
    const btn = $("login-submit");
    btn.disabled = true;
    clearMsg($("auth-msg"));
    try {
      const pair = await api("/auth/login", {
        method: "POST",
        body: JSON.stringify({ identifier: email, password }),
      });
      accessToken = pair.access_token;
      const me = await api("/identity/me", {
        headers: { Authorization: "Bearer " + pair.access_token },
      });
      enterApp(me.email, me.id, pair.access_token);
    } catch (err) {
      showMsg($("auth-msg"), "Giriş başarısız: " + err.message, "error");
    } finally {
      btn.disabled = false;
    }
  });

  // --- Search (POST /shopping-pipeline/run, gercek cagri, offers verilmiyor) ---
  $("search-form").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const query = $("search-query").value.trim();
    const btn = $("search-submit");
    btn.disabled = true;
    btn.textContent = "Aranıyor…";
    clearMsg($("search-msg"));
    $("result-panel").classList.add("hidden");
    try {
      const result = await api("/shopping-pipeline/run", {
        method: "POST",
        body: JSON.stringify({ user_id: currentUserId, query }),
      });
      renderResult(query, result);
    } catch (err) {
      showMsg($("search-msg"), "Arama başarısız: " + err.message, "error");
    } finally {
      btn.disabled = false;
      btn.textContent = "Ara";
    }
  });

  function renderResult(query, result) {
    const body = $("result-body");
    $("result-panel").classList.remove("hidden");

    if (result.status !== "COMPLETED" || !result.top_recommendation) {
      body.innerHTML =
        '<p class="meta">"' + escapeHtml(query) + '" için ingest edilmiş gerçek veri bulunamadı.<br>' +
        'Durum: <strong>' + escapeHtml(result.status) + '</strong> — sahte bir sonuç üretilmedi.</p>';
      return;
    }

    const top = result.top_recommendation;
    const source = top.source || {};
    const isReal = (source.metadata && source.metadata.is_real_data) || false;
    const priceHistory = result.price_history;
    const explanation = result.explanation && result.explanation.text
      ? result.explanation.text
      : (result.explanation && result.explanation.explanation) || null;

    let html = "";
    html += '<div class="row" style="justify-content: space-between; align-items: flex-start;">';
    html += '<div><div class="meta">' + escapeHtml(source.marketplace || "—") + '</div>';
    html += '<div class="price">' + escapeHtml(String(source.price || "—")) + " " + escapeHtml(source.currency || "") + '</div></div>';
    html += '<span class="pill ' + (isReal ? "real" : "fixture") + '">' + (isReal ? "gerçek veri" : "test/fixture verisi") + '</span>';
    html += '</div>';

    if (priceHistory && priceHistory.status === "OK") {
      html += '<div class="grid2">';
      html += statBox("En düşük", priceHistory.min_price);
      html += statBox("En yüksek", priceHistory.max_price);
      html += statBox("Ortalama", priceHistory.average_price);
      html += statBox("Trend", priceHistory.trend);
      html += '</div>';
    } else {
      html += '<p class="meta" style="margin-top:14px;">Fiyat geçmişi: <strong>' +
        escapeHtml((priceHistory && priceHistory.status) || "INSUFFICIENT_DATA") + '</strong></p>';
    }

    if (result.deal_detection) {
      const dd = result.deal_detection;
      html += '<p class="meta">Fırsat sinyali: <strong>' + escapeHtml(dd.deal_signal || dd.status || "—") + '</strong></p>';
    }

    if (explanation) {
      html += '<div class="explanation">' + escapeHtml(explanation) + '</div>';
    }

    body.innerHTML = html;
  }

  function statBox(label, value) {
    return '<div class="stat"><div class="label">' + escapeHtml(label) + '</div><div class="value">' +
      escapeHtml(value === undefined || value === null ? "—" : String(value)) + '</div></div>';
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
})();
