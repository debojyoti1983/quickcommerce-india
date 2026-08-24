/* QuickCommerce India — app shell: header, search, controls, state, tweaks. */
const { useState: uS, useEffect: uE, useRef: uR, useCallback: uCB } = React;

const ALL_PLATFORMS = Object.keys(window.QC_PLATFORMS);
const MEM_PLATFORM = { "Swiggy One": "swiggy", "Zomato Gold": "zomato", "BB Star": "bigbasket", "Prime": "amazon_fresh" };
const PLAT_URL = {
  swiggy: "https://www.swiggy.com", zomato: "https://www.zomato.com",
  blinkit: "https://blinkit.com", zepto: "https://www.zeptonow.com",
  instamart: "https://www.swiggy.com/instamart", bigbasket: "https://www.bigbasket.com",
  flipkart_minutes: "https://www.flipkart.com", amazon_fresh: "https://www.amazon.in/fresh",
};
const SAMPLES = ["Amul milk", "Chicken biryani", "Tata salt", "Masala dosa", "Onion", "Paneer butter masala"];
const THINK_STEPS = [
  "Probing serviceability across 8 apps in your pincode…",
  "Fetching live prices — Blinkit, Zepto, Instamart…",
  "Comparing 6 of 8 apps — fetching Zomato ETA…",
  "Normalizing to true all-in price (item + tax + delivery − membership)…",
  "Ranking cheapest / fastest / best-rated…",
];

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "theme": "marigold",
  "dark": false,
  "density": "regular"
}/*EDITMODE-END*/;

const LS_KEY = "qc_state_v2";
function loadState() {
  try { return JSON.parse(localStorage.getItem(LS_KEY)) || {}; } catch (e) { return {}; }
}

const LOC_LS_KEY = "qc_loc_v1";
const DEFAULT_LOC = { city: "Bengaluru", pincode: "560001" };
function loadLoc() {
  try { return JSON.parse(localStorage.getItem(LOC_LS_KEY)) || null; } catch (e) { return null; }
}
function saveLoc(loc) {
  try { localStorage.setItem(LOC_LS_KEY, JSON.stringify(loc)); } catch (e) {}
}

/* Backend-powered search — the real FastAPI engine is the source of truth.
   Returns the same per-item result shape the UI components consume. */
async function qcSearch(query, opts) {
  try {
    const loc = opts.loc || DEFAULT_LOC;
    const r = await fetch("/api/ui/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query,
        memberships: opts.memberships || [],
        platforms: opts.platforms || [],
        veg_only: !!opts.vegOnly,
        pincode: loc.pincode,
        city: loc.city,
      }),
    });
    if (!r.ok) return [];
    const data = await r.json();
    return data.results || [];
  } catch (e) { return []; }
}

function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const saved = uR(loadState()).current;

  const [query, setQuery] = uS(saved.query != null ? saved.query : "Amul milk");
  const [submitted, setSubmitted] = uS(saved.query != null ? saved.query : "Amul milk");
  const [vegOnly, setVegOnly] = uS(!!saved.vegOnly);
  const [memberships, setMemberships] = uS(saved.memberships || []);
  const [platforms, setPlatforms] = uS(saved.platforms || ALL_PLATFORMS);
  const [showPlat, setShowPlat] = uS(false);

  const [phase, setPhase] = uS("thinking"); // idle | thinking | done
  const [thinkSub, setThinkSub] = uS(THINK_STEPS[0]);
  const [results, setResults] = uS([]);

  const [pending, setPending] = uS(null);
  const [orderPhase, setOrderPhase] = uS("confirm");
  const [orderId, setOrderId] = uS(null);
  const [toast, setToast] = uS(null);
  const [cartCount, setCartCount] = uS(0);
  const [user, setUser] = uS(null);          // logged-in account (credentials)
  const [activeMems, setActiveMems] = uS([]); // membership programmes the user holds
  const thinkTimer = uR(null);

  /* delivery location — ask the browser for it on first visit, fall back to a
     manual city/pincode picker if it's denied, unsupported, or times out. */
  const [loc, setLocState] = uS(loadLoc());
  const [locStatus, setLocStatus] = uS(loadLoc() ? "resolved" : "detecting");
  const [locModalOpen, setLocModalOpen] = uS(false);
  const [cities, setCities] = uS([]);

  function setLoc(next) { setLocState(next); saveLoc(next); setLocStatus("resolved"); }

  function detectLocation() {
    setLocStatus("detecting");
    if (!("geolocation" in navigator)) { setLocStatus("unsupported"); setLocModalOpen(true); return; }
    let done = false;
    const finishManual = (status) => { if (done) return; done = true; setLocStatus(status); setLocModalOpen(true); };
    const timer = setTimeout(() => finishManual("timeout"), 9000);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        clearTimeout(timer);
        if (done) return;
        fetch("/api/location/resolve", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
        }).then((r) => (r.ok ? r.json() : null)).then((m) => {
          done = true;
          if (m) { setLoc({ city: m.city, pincode: m.pincode }); setLocModalOpen(false); }
          else { setLocStatus("error"); setLocModalOpen(true); }
        }).catch(() => { done = true; setLocStatus("error"); setLocModalOpen(true); });
      },
      () => { clearTimeout(timer); finishManual("denied"); },
      { enableHighAccuracy: false, timeout: 8000, maximumAge: 10 * 60 * 1000 }
    );
  }

  // First visit (no remembered location yet): ask immediately, mobile or desktop.
  uE(() => { if (!loc) detectLocation(); }, []); // eslint-disable-line

  // The manual picker's city dropdown needs the known-city list — fetch once, lazily.
  uE(() => {
    if (locModalOpen && cities.length === 0) {
      fetch("/api/location/cities").then((r) => (r.ok ? r.json() : { cities: [] }))
        .then((d) => setCities(d.cities || [])).catch(() => {});
    }
  }, [locModalOpen]); // eslint-disable-line

  /* who's signed in + which memberships they hold. When signed in, auto-apply the
     detected memberships so compared prices reflect the user's plans immediately. */
  uE(() => {
    Promise.all([
      fetch("/api/auth/me").then((r) => (r.ok ? r.json() : null)).catch(() => null),
      fetch("/api/account/detect").then((r) => (r.ok ? r.json() : [])).catch(() => []),
    ]).then(([u, accts]) => {
      setUser(u);
      const mems = accts.filter((a) => a.membership_active && a.membership).map((a) => a.membership);
      setActiveMems(mems);
      if (u && mems.length) setMemberships(mems); // signed in -> check & apply your memberships
    });
  }, []);

  /* apply theme */
  uE(() => { applyTheme(t.theme, t.dark ? "dark" : "light"); }, [t.theme, t.dark]);
  uE(() => { document.documentElement.setAttribute("data-density", t.density); }, [t.density]);

  /* persist */
  uE(() => {
    try { localStorage.setItem(LS_KEY, JSON.stringify({ query: submitted, vegOnly, memberships, platforms })); } catch (e) {}
  }, [submitted, vegOnly, memberships, platforms]);

  /* Fetch from the real backend whenever the query or any filter changes.
     One effect covers initial load, filter toggles, and submitted-query changes. */
  uE(() => {
    if (!submitted.trim()) { setResults([]); setPhase("done"); return; }
    let cancelled = false;
    qcSearch(submitted, { memberships, platforms, vegOnly, loc }).then((res) => {
      if (cancelled) return;
      clearInterval(thinkTimer.current);
      setResults(res);
      setPhase("done");
    });
    return () => { cancelled = true; };
  }, [submitted, vegOnly, memberships, platforms, loc]); // eslint-disable-line

  function startThinking() {
    setPhase("thinking");
    let i = 0; setThinkSub(THINK_STEPS[0]);
    clearInterval(thinkTimer.current);
    thinkTimer.current = setInterval(() => { i = (i + 1) % THINK_STEPS.length; setThinkSub(THINK_STEPS[i]); }, 360);
  }

  function runSearch(q) {
    const query2 = (q != null ? q : query).trim();
    if (!query2) { setSubmitted(""); setResults([]); setPhase("done"); return; }
    startThinking();
    if (query2 === submitted) {
      // same query — the effect won't refire, so fetch directly
      qcSearch(query2, { memberships, platforms, vegOnly, loc }).then((res) => {
        clearInterval(thinkTimer.current); setResults(res); setPhase("done");
      });
    } else {
      setSubmitted(query2); // triggers the effect above, which fetches
    }
  }

  function pickSample(s) { setQuery(s); runSearch(s); window.scrollTo({ top: 0 }); }
  function toggleMembership(m) {
    setMemberships((prev) => prev.includes(m) ? prev.filter((x) => x !== m) : [...prev, m]);
  }
  function togglePlatform(p) {
    setPlatforms((prev) => prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p]);
  }

  /* order flow (HITL) — backed by the real /api/order endpoints */
  async function onOrder(offer) {
    const meta = window.QC_PLATFORMS[offer.platform] || {};
    const label = meta.label || offer.platform;
    const membership = meta.membership || null;
    const pincode = (loc && loc.pincode) || DEFAULT_LOC.pincode;
    setOrderPhase("confirm"); setOrderId(null);
    setPending({
      platform: offer.platform, label, item_name: offer.item_name, true_price: offer.true_price,
      restaurant: offer.restaurant || null, pincode, idem: null,
      membership, member: membership ? activeMems.includes(membership) : null,
      membership_applied: !!offer.membership_applied,
    });
    // Fetch the real HITL approval decision (server-derived idempotency key).
    try {
      const r = await fetch("/api/order/prepare", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ platform: label, item_name: offer.item_name, true_price_inr: offer.true_price, pincode }),
      });
      if (r.ok) { const dec = await r.json(); setPending((p) => (p ? { ...p, idem: dec.idempotency_key } : p)); }
    } catch (e) {}
  }
  async function confirmOrder() {
    if (!pending || !pending.idem) return;
    setOrderPhase("placing");
    try {
      const r = await fetch("/api/order/place", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          platform: pending.label, item_name: pending.item_name,
          true_price_inr: pending.true_price, pincode: pending.pincode,
          idempotency_key: pending.idem,
        }),
      });
      if (!r.ok) { setOrderPhase("confirm"); return; }
      const order = await r.json();
      // Hand off to the platform's site to complete checkout/payment.
      const url = PLAT_URL[pending.platform];
      if (url) window.open(url, "_blank", "noopener,noreferrer");
      setCartCount((c) => c + 1);
      setToast({ platform: pending.platform, item: pending.item_name, price: pending.true_price, orderId: order.order_id });
      setPending(null); setOrderPhase("confirm");
      setTimeout(() => setToast(null), 5000);
    } catch (e) { setOrderPhase("confirm"); }
  }

  function logout() {
    fetch("/api/auth/logout", { method: "POST" }).then(() => { setUser(null); setMemberships([]); });
  }

  const hasResults = results && results.length > 0;

  return (
    <div className="app-shell">
      <header className="app">
        <div className="wrap hdr-row">
          <div className="brand">
            <span className="mark"><Icon name="bolt" size={19} /></span>
            <span className="wm">QuickCommerce<small>India · compare &amp; decide</small></span>
          </div>
          <div className="hdr-spacer" />
          <button type="button" className="loc clickable" onClick={() => setLocModalOpen(true)}
            title="Change delivery location">
            <Icon name="pin" size={15} style={{ color: "var(--primary)" }} />
            <span className="loc-label">
              {loc ? <React.Fragment>{loc.city} <span className="city">· {loc.pincode}</span></React.Fragment>
                : locStatus === "detecting" ? "Detecting location…" : "Set delivery location"}
            </span>
          </button>
          {user ? (
            <button className="loc" onClick={logout} title="Log out" style={{ cursor: "pointer" }}>
              <Icon name="check" size={14} style={{ color: "var(--good)" }} />
              <span className="loc-label">{user.display.split("@")[0]} <span className="city">· log out</span></span>
            </button>
          ) : (
            <a className="loc" href="/login" style={{ textDecoration: "none" }}>
              <Icon name="shield" size={14} style={{ color: "var(--primary)" }} /> <span className="loc-label">Log in</span>
            </a>
          )}
          <button className="icon-btn" aria-label="Cart">
            <Icon name="cart" size={19} stroke />
            {cartCount > 0 && <span className="cart-dot">{cartCount}</span>}
          </button>
        </div>
      </header>

      <main className="wrap">
        <section className="hero">
          <h1>One search. Every app.<br /><span className="hl">The best deal.</span></h1>
          <p className="lede">Ask in plain language. We compare the true all-in price — item, taxes, delivery and your memberships — across Swiggy, Zomato, Blinkit, Zepto, Instamart, BigBasket, Flipkart Minutes and Amazon Fresh, then recommend one pick and show our reasoning.</p>

          <form className="searchbar" onSubmit={(e) => { e.preventDefault(); runSearch(); }}>
            <span className="spark"><Icon name="spark" size={22} /></span>
            <input value={query} onChange={(e) => setQuery(e.target.value)}
              placeholder="Find me Amul milk, or chicken biryani for tonight…" aria-label="Search" />
            <button className="btn-go" type="submit"><Icon name="search" size={17} /> <span className="t">Compare</span></button>
          </form>

          <div className="chips">
            <span className="lbl">Try:</span>
            {SAMPLES.map((s) => <button key={s} className="chip" onClick={() => pickSample(s)}>{s}</button>)}
          </div>

          <div className="controls">
            <button type="button" className="seg-toggle" onClick={() => setVegOnly(!vegOnly)} aria-pressed={vegOnly}>
              <span className="veg-mark"><i /></span> Veg only
              <span className={"switch" + (vegOnly ? " on" : "")}><i /></span>
            </button>

            <div className="mem-group">
              <span className="lbl" style={{ fontSize: 12.5, color: "var(--muted)", fontWeight: 600 }}>Memberships:</span>
              {window.QC_MEMBERSHIPS.map((m) => {
                const on = memberships.includes(m);
                return (
                  <button key={m} type="button" className={"mem-chip" + (on ? " on" : "")}
                    onClick={() => toggleMembership(m)} aria-pressed={on}>
                    <PlatformBadge id={MEM_PLATFORM[m]} size={18} /> {m}
                    <span className="tick">{on && <Icon name="check" size={11} />}</span>
                  </button>
                );
              })}
            </div>

            <button type="button" className="plat-toggle on" onClick={() => setShowPlat(!showPlat)}
              style={{ fontWeight: 700 }}>
              <Icon name="sliders" size={14} /> {platforms.length} of 8 apps
            </button>
          </div>

          {showPlat && (
            <div className="platrow">
              {ALL_PLATFORMS.map((p) => {
                const on = platforms.includes(p);
                return (
                  <button key={p} type="button" className={"plat-toggle " + (on ? "on" : "off")}
                    onClick={() => togglePlatform(p)} aria-pressed={on}>
                    <PlatformBadge id={p} size={18} /> {window.QC_PLATFORMS[p].label}
                  </button>
                );
              })}
              <button className="linkbtn" onClick={() => setPlatforms(ALL_PLATFORMS)}>all</button>
              <button className="linkbtn" onClick={() => setPlatforms([])}>none</button>
            </div>
          )}
        </section>

        <div className="results">
          {phase !== "thinking" && hasResults && (
            <div className="liveline"><span className="pulse" /> {`Live across ${platforms.length} app${platforms.length === 1 ? "" : "s"} · ${loc ? loc.city + " " + loc.pincode : "detecting location…"} · ${results.length} item${results.length === 1 ? "" : "s"} matched`}</div>
          )}
          {phase === "thinking" ? (
            <Thinking sub={thinkSub} />
          ) : hasResults ? (
            results.map((r) => <ItemResult key={r.key} result={r} onOrder={onOrder} />)
          ) : (
            <EmptyState query={submitted} onPick={pickSample} />
          )}
        </div>
      </main>

      <footer className="app">
        <div className="wrap ft">
          <span className="sim"><Icon name="shield" size={14} style={{ color: "var(--good)" }} /> Simulated demo data — not live platform pricing.</span>
          <span>·</span>
          <span>Every price traces to a sourced, timestamped claim. We abstain rather than guess.</span>
          <span>·</span>
          <span>Orders always need your explicit approval.</span>
        </div>
      </footer>

      <OrderModal pending={pending} phase={orderPhase} orderId={orderId} user={user}
        onClose={() => setPending(null)} onConfirm={confirmOrder} />

      <LocationModal open={locModalOpen} status={locStatus} cities={cities}
        currentCity={loc ? loc.city : ""} currentPincode={loc ? loc.pincode : ""} onDetect={detectLocation}
        onManualSave={(next) => { setLoc(next); setLocModalOpen(false); }}
        onClose={() => { if (!loc) setLoc(DEFAULT_LOC); setLocModalOpen(false); }} />

      {toast && (
        <div className="toast">
          <span className="tk"><Icon name="check" size={15} /></span>
          <div><div className="tt">Order {toast.orderId} placed · opening {window.QC_PLATFORMS[toast.platform].label}</div>
            <div className="ts">{toast.item} · {window.QC_fmtMoney(toast.price)} · approved by you · finish checkout on {window.QC_PLATFORMS[toast.platform].label}</div></div>
        </div>
      )}

      <TweaksPanel>
        <TweakSection label="Theme" />
        <TweakRadio label="Palette" value={t.theme} options={["marigold", "mint", "indigo"]}
          onChange={(v) => setTweak("theme", v)} />
        <TweakToggle label="Dark mode" value={t.dark} onChange={(v) => setTweak("dark", v)} />
        <TweakSection label="Layout" />
        <TweakRadio label="Density" value={t.density} options={["compact", "regular", "comfy"]}
          onChange={(v) => setTweak("density", v)} />
      </TweaksPanel>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
