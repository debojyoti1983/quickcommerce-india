/* QuickCommerce India — delivery location: browser geolocation (with the
   user's explicit permission) + a manual "search any city in India" fallback.

   No third-party geocoder is called from the browser or the server — lat/lng
   is resolved server-side against an allowlisted city table (see
   app/bootstrap/geo.py, ~70 cities covering every state/UT plus major
   commercial hubs — every one of them serviceable by at least the
   fast-scaling platforms, see app/connectors/city_profiles.py). The browser
   only ever talks to our own /api/*. */

const MAX_SUGGESTIONS = 8;

function LocationModal({ open, status, cities, currentCity, currentPincode, onDetect, onManualSave, onClose }) {
  const [query, setQuery] = React.useState(currentCity || "");
  const [city, setCity] = React.useState(currentCity || "");
  const [pincode, setPincode] = React.useState(currentPincode || "");
  const [showSuggestions, setShowSuggestions] = React.useState(false);
  // A valid pincode is itself a location — resolve it server-side to a city
  // (and therefore a real centroid/coverage tier) rather than treating it as
  // a free-text field with no bearing on what gets suggested.
  const [pincodeMatch, setPincodeMatch] = React.useState(null); // { city } | { error: true } | null

  React.useEffect(() => {
    if (!/^\d{6}$/.test(pincode)) { setPincodeMatch(null); return; }
    let cancelled = false;
    fetch("/api/location/resolve-pincode", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pincode }),
    }).then((r) => {
        if (r.ok) return r.json();
        // 422 = the server actually validated this and rejected the format;
        // anything else (500, a cold-start 502/503, a dropped connection) is
        // a request failure, not proof the pincode is invalid — conflating
        // the two used to tell users a perfectly valid pincode "doesn't look
        // like a valid Indian PIN code" whenever the request merely failed.
        return Promise.reject({ invalid: r.status === 422 });
      })
      .then((m) => {
        if (cancelled) return;
        setPincodeMatch({ city: m.city, serviceable: m.serviceable });
        setCity(m.city);
        setQuery(m.city);
      })
      .catch((err) => {
        if (cancelled) return;
        setPincodeMatch({ error: true, invalid: !!(err && err.invalid) });
      });
    return () => { cancelled = true; };
  }, [pincode]); // eslint-disable-line

  if (!open) return null;

  const q = query.trim().toLowerCase();
  const suggestions = q
    ? cities.filter((c) => c.city.toLowerCase().includes(q)).slice(0, MAX_SUGGESTIONS)
    : cities.slice(0, MAX_SUGGESTIONS);

  function pickCity(c) {
    setQuery(c.city);
    setCity(c.city);
    setPincode(c.pincode);
    setShowSuggestions(false);
  }

  function onQueryChange(value) {
    setQuery(value);
    setShowSuggestions(true);
    // Typing a city that no longer matches the current pick invalidates a
    // previously-resolved pincode too — otherwise a stale pincode from an
    // earlier lookup could get saved paired with an unrelated typed city.
    if (value.trim().toLowerCase() !== city.toLowerCase()) {
      setCity("");
      setPincode("");
      setPincodeMatch(null);
    }
  }

  const exactMatch = cities.find((c) => c.city.toLowerCase() === query.trim().toLowerCase());
  const canSave = !!exactMatch || !!city || !!(pincodeMatch && pincodeMatch.city);

  function save() {
    // A resolved pincode wins first: it's the more specific signal, and the
    // effect above sets `city` to a real city name once resolved, which
    // would otherwise match the city list below and silently overwrite the
    // user's actual typed pincode with that city's generic representative
    // one — exactly the mismatch this whole feature exists to avoid.
    if (pincodeMatch && pincodeMatch.city) { onManualSave({ city: pincodeMatch.city, pincode }); return; }
    const match = exactMatch || cities.find((c) => c.city === city);
    if (match) { onManualSave({ city: match.city, pincode: match.pincode }); return; }
    onManualSave({ city: query.trim(), pincode });
  }

  return (
    <div className="modal-scrim" onMouseDown={(e) => { if (e.target === e.currentTarget && status !== "detecting") onClose(); }}>
      <div className="modal" role="dialog" aria-modal="true" aria-label="Set delivery location">
        <div className="modal-hd">
          <span className="shield"><Icon name="pin" size={20} style={{ color: "var(--primary)" }} /></span>
          <h3>Where should we deliver?</h3>
        </div>
        <div className="modal-bd">
          {status === "detecting" ? (
            <div className="think-line" style={{ fontWeight: 600 }}>
              <span className="spin" /> Detecting your location…
            </div>
          ) : (
            <React.Fragment>
              <p className="modal-note" style={{ margin: "0 0 14px" }}>
                <Icon name="info" size={14} style={{ flex: "none", marginTop: 1 }} />
                We compare live prices for your area and suggest restaurants within 10 km. Share your location, or search any serviceable city — change it anytime from the header.
              </p>
              {status === "denied" && (
                <p className="modal-note" style={{ color: "var(--warn)", margin: "0 0 14px" }}>
                  <Icon name="alert" size={14} style={{ flex: "none", marginTop: 1 }} />
                  Location access was denied — search your city or enter a pincode below instead.
                </p>
              )}
              <button type="button" className="btn-secondary" style={{ width: "100%", marginBottom: 14 }} onClick={onDetect}>
                <Icon name="pin" size={15} /> Use my current location
              </button>
              <div className="loc-or"><span>or search any city in India</span></div>
              <div className="loc-field" style={{ position: "relative" }}>
                <label>City</label>
                <input value={query}
                  onChange={(e) => onQueryChange(e.target.value)}
                  onFocus={() => setShowSuggestions(true)}
                  onBlur={() => setTimeout(() => setShowSuggestions(false), 120)}
                  placeholder="Type a city — Bengaluru, Coimbatore, Jodhpur…"
                  autoComplete="off" />
                {showSuggestions && (
                  <div className="loc-suggest">
                    {cities.length === 0 ? (
                      <div className="loc-suggest-empty">Loading cities…</div>
                    ) : suggestions.length === 0 ? (
                      <div className="loc-suggest-empty">No matching city — enter a pincode below instead.</div>
                    ) : (
                      suggestions.map((c) => (
                        <button type="button" key={c.city} className="loc-suggest-item"
                          onMouseDown={(e) => e.preventDefault()} onClick={() => pickCity(c)}>
                          <Icon name="pin" size={13} style={{ color: "var(--muted)", flex: "none" }} />
                          {c.city} <span className="loc-suggest-pin">{c.pincode}</span>
                        </button>
                      ))
                    )}
                  </div>
                )}
              </div>
              <div className="loc-field">
                <label>Or enter a pincode</label>
                <input value={pincode}
                  onChange={(e) => { setPincode(e.target.value.replace(/\D/g, "").slice(0, 6)); setShowSuggestions(false); }}
                  placeholder="6-digit pincode" inputMode="numeric" maxLength={6} autoComplete="off" />
                {pincode.length === 6 && pincodeMatch && pincodeMatch.city && (
                  <div className={"loc-pin-hint" + (pincodeMatch.serviceable === false ? " warn" : " ok")}>
                    <Icon name={pincodeMatch.serviceable === false ? "alert" : "check"} size={12} />
                    {pincodeMatch.serviceable === false
                      ? `Closest coverage we have is ${pincodeMatch.city} — results may be approximate.`
                      : `Matched to ${pincodeMatch.city}.`}
                  </div>
                )}
                {pincode.length === 6 && pincodeMatch && pincodeMatch.error && (
                  <div className="loc-pin-hint warn">
                    <Icon name="alert" size={12} />
                    {pincodeMatch.invalid
                      ? "That doesn't look like a valid Indian PIN code."
                      : "Couldn't check that pincode right now — try again in a moment."}
                  </div>
                )}
              </div>
            </React.Fragment>
          )}
        </div>
        {status !== "detecting" && (
          <div className="modal-ft">
            <button className="btn-secondary" onClick={onClose}>Cancel</button>
            <button className="btn-order" disabled={!canSave} onClick={save}>Save location</button>
          </div>
        )}
      </div>
    </div>
  );
}

Object.assign(window, { LocationModal });
