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
    // Typing invalidates a previous exact pick until it matches again — the
    // pincode field still works standalone either way.
    if (value.trim().toLowerCase() !== city.toLowerCase()) setCity("");
  }

  const pinValid = /^\d{6}$/.test(pincode);
  const exactMatch = cities.find((c) => c.city.toLowerCase() === query.trim().toLowerCase());
  const canSave = pinValid || !!city || !!exactMatch;

  function save() {
    const match = exactMatch || cities.find((c) => c.city === city);
    onManualSave({
      city: match ? match.city : (city || query.trim()),
      pincode: pinValid ? pincode : (match ? match.pincode : pincode),
    });
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
                <label>Pincode</label>
                <input value={pincode} onChange={(e) => setPincode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                  placeholder="6-digit pincode (optional)" inputMode="numeric" maxLength={6} />
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
