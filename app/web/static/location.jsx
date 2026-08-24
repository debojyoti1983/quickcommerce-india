/* QuickCommerce India — delivery location: browser geolocation (with the
   user's explicit permission) + a manual city/pincode fallback.

   No third-party geocoder is called from the browser or the server — lat/lng
   is resolved server-side against a small allowlisted metro table (see
   app/bootstrap/geo.py). The browser only ever talks to our own /api/*. */

function LocationModal({ open, status, cities, currentCity, currentPincode, onDetect, onManualSave, onClose }) {
  const [city, setCity] = React.useState(currentCity || "");
  const [pincode, setPincode] = React.useState(currentPincode || "");

  React.useEffect(() => {
    if (open && !city && cities.length) setCity(cities[0].city);
  }, [open, cities]); // eslint-disable-line

  if (!open) return null;

  function pickCity(name) {
    setCity(name);
    const match = cities.find((c) => c.city === name);
    setPincode(match ? match.pincode : "");
  }

  const pinValid = /^\d{6}$/.test(pincode);
  const cityMatch = cities.find((c) => c.city === city);
  const canSave = pinValid || !!cityMatch;

  function save() {
    onManualSave({ city, pincode: pinValid ? pincode : (cityMatch ? cityMatch.pincode : pincode) });
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
                We compare live prices for your area. Share your location, or set it manually — change it anytime from the header.
              </p>
              {status === "denied" && (
                <p className="modal-note" style={{ color: "var(--warn)", margin: "0 0 14px" }}>
                  <Icon name="alert" size={14} style={{ flex: "none", marginTop: 1 }} />
                  Location access was denied — pick your city or pincode below instead.
                </p>
              )}
              <button type="button" className="btn-secondary" style={{ width: "100%", marginBottom: 14 }} onClick={onDetect}>
                <Icon name="pin" size={15} /> Use my current location
              </button>
              <div className="loc-or"><span>or set it manually</span></div>
              <div className="loc-field">
                <label>City</label>
                <select value={city} onChange={(e) => pickCity(e.target.value)}>
                  {cities.length === 0 && <option value="">Loading…</option>}
                  {cities.map((c) => <option key={c.city} value={c.city}>{c.city}</option>)}
                </select>
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
