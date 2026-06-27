/* QuickCommerce India — result rendering: best pick, alternatives, compare table, HITL modal. */
const { useState: useStateR } = React;
const fmt = window.QC_fmtMoney;
const PL = window.QC_PLATFORMS;

function plLabel(id) { return (PL[id] || {}).label || id; }

/* ---- the hero recommendation card ---- */
function BestPick({ rec, comparison, opts, onOrder }) {
  const b = rec.best.offer;
  const prices = comparison.available.map((s) => s.offer.true_price);
  const maxP = Math.max.apply(null, prices);
  const save = Math.round((maxP - b.true_price) * 100) / 100;
  const dearest = comparison.available.find((s) => s.offer.true_price === maxP);
  const src = rec.evidence[0];

  return (
    <div className="bestpick">
      <div className="bp-ribbon"><Icon name="spark" size={14} /> Best overall pick</div>
      <div className="bp-body">
        <div className="bp-top">
          <div className="bp-plat">
            <PlatformBadge id={b.platform} size={46} />
            <div>
              <div className="pname">{plLabel(b.platform)}</div>
              <div className="ptier">
                <Icon name="shield" size={13} style={{ color: "var(--good)" }} />
                {src.source_label} · checked {src.freshness}
              </div>
            </div>
          </div>
          <div className="bp-price">
            <div className="now tnum">{fmt(b.true_price)}</div>
            {save >= 1 && (
              <div className="save"><Icon name="bolt" size={12} /> Save {fmt(save)} vs {plLabel(dearest.offer.platform)}</div>
            )}
          </div>
        </div>

        <div className="bp-stats">
          {b.eta_minutes != null && (
            <span className="stat"><Icon name="clock" size={15} style={{ color: "var(--blue)" }} />
              <span className="k">ETA</span> {b.eta_minutes} min</span>
          )}
          {b.rating != null && (
            <span className="stat"><Icon name="star" size={15} style={{ color: "var(--star)" }} />
              {b.rating} <span className="k">rating</span></span>
          )}
          <span className="stat"><Icon name="check" size={15} style={{ color: "var(--good)" }} />
            <span className="k">all-in price, incl. taxes &amp; delivery</span></span>
          {b.membership_applied && (
            <span className="stat" style={{ borderColor: "color-mix(in srgb, var(--primary) 40%, var(--line))" }}>
              <Icon name="check" size={14} style={{ color: "var(--primary)" }} />
              <span style={{ color: "var(--primary)", fontWeight: 700 }}>Membership applied</span></span>
          )}
        </div>

        {b.offer_text && (
          <div style={{ marginTop: 12 }}>
            <span className="offer-chip"><Icon name="tag" size={13} /> {b.offer_text}</span>
          </div>
        )}

        <div className="because">
          <div className="head"><Icon name="spark" size={13} /> Why this pick</div>
          <ul>
            {rec.because.map((line, i) => (
              <li key={i}><span className="dot"><Icon name="check" size={15} /></span>
                <span><RichText text={line} /></span></li>
            ))}
          </ul>
        </div>

        <ConfBar value={rec.confidence_value} label={rec.confidence_label} />

        <div className="bp-cta">
          <button className="btn-order" onClick={() => onOrder(b)}>
            Order on {plLabel(b.platform)} · {fmt(b.true_price)} <Icon name="arrow" size={17} />
          </button>
        </div>
      </div>
    </div>
  );
}

/* ---- small alternative cards (cheapest / fastest / top-rated) ---- */
function AltCard({ offer, tag, onOrder }) {
  const tagMap = {
    cheapest: { cls: "tag-cheap", txt: "Cheapest", ic: "bolt" },
    fastest: { cls: "tag-fast", txt: "Fastest", ic: "clock" },
    rated: { cls: "tag-rated", txt: "Top rated", ic: "star" },
  };
  const t = tagMap[tag];
  return (
    <div className="alt">
      <div className="alt-top">
        <PlatformBadge id={offer.platform} size={30} />
        <span className="nm">{plLabel(offer.platform)}</span>
        {t && <span className={"alt-tag " + t.cls}>{t.txt}</span>}
      </div>
      <div className="alt-price tnum">{fmt(offer.true_price)}</div>
      <div className="alt-meta">
        {offer.eta_minutes != null && <span><Icon name="clock" size={13} /> {offer.eta_minutes}m</span>}
        {offer.rating != null && <span><Icon name="star" size={13} style={{ color: "var(--star)" }} /> {offer.rating}</span>}
        {offer.membership_applied && <span style={{ color: "var(--primary)", fontWeight: 700 }}>Member ✓</span>}
      </div>
      <button className="alt-order" onClick={() => onOrder(offer)}>Order on {plLabel(offer.platform)}</button>
    </div>
  );
}

/* ---- full comparison table (collapsible) ---- */
function CompareTable({ comparison, onOrder }) {
  const [open, setOpen] = useStateR(false);
  const best = comparison.available[0].offer.platform;
  const cheap = comparison.cheapest && comparison.cheapest.platform;
  const fast = comparison.fastest && comparison.fastest.platform;
  const rated = comparison.best_rated && comparison.best_rated.platform;
  const rows = comparison.available.map((s) => s.offer);
  const total = rows.length + comparison.unavailable.length;

  function tags(p) {
    const out = [];
    if (p === cheap) out.push(<span key="c" className="minitag tag-cheap">Cheapest</span>);
    if (p === fast) out.push(<span key="f" className="minitag tag-fast">Fastest</span>);
    if (p === rated) out.push(<span key="r" className="minitag tag-rated">Top rated</span>);
    return out;
  }

  return (
    <div className="table-card">
      <div className={"table-head" + (open ? " open" : "")} onClick={() => setOpen(!open)}
        role="button" aria-expanded={open}>
        <Icon name="store" size={15} />
        {`All ${total} app${total === 1 ? "" : "s"} compared, ranked best-overall first`}
        <Icon name="chevron" size={16} className="chev" />
        <Icon name="chevron" size={16} style={{ marginLeft: "auto" }} />
      </div>
      {open && (
        <React.Fragment>
          <table className="cmp">
            <thead>
              <tr>
                <th>App</th>
                <th className="num">All-in price</th>
                <th className="num">ETA</th>
                <th className="num">Rating</th>
                <th>Offer</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((o) => (
                <tr key={o.platform} className={o.platform === best ? "best-row" : ""}>
                  <td>
                    <span className="row-plat"><PlatformBadge id={o.platform} size={26} /> {plLabel(o.platform)}
                      <span className="row-tags">{tags(o.platform)}</span></span>
                  </td>
                  <td className="num price-cell tnum">{fmt(o.true_price)}</td>
                  <td className="num tnum">{o.eta_minutes != null ? o.eta_minutes + "m" : "—"}</td>
                  <td className="num tnum">{o.rating != null ? o.rating + "★" : "—"}</td>
                  <td style={{ color: "var(--muted)", fontSize: 13 }}>{o.offer_text || "—"}</td>
                  <td className="num"><button className="tbtn" onClick={() => onOrder(o)}>Order</button></td>
                </tr>
              ))}
              {comparison.unavailable.map((o) => (
                <tr key={o.platform} style={{ opacity: 0.6 }}>
                  <td><span className="row-plat"><PlatformBadge id={o.platform} size={26} /> {plLabel(o.platform)}</span></td>
                  <td className="num" colSpan={4}><span className="oos">Out of stock</span></td>
                  <td className="num"><button className="tbtn" disabled>Order</button></td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* mobile cards */}
          <div className="cmp-cards">
            {rows.map((o) => (
              <div key={o.platform} className={"cmp-card" + (o.platform === best ? " best-row" : "")}>
                <PlatformBadge id={o.platform} size={32} />
                <div className="cc-main">
                  <div className="cc-nm">{plLabel(o.platform)} {tags(o.platform)}</div>
                  <div className="cc-meta">
                    {o.eta_minutes != null ? o.eta_minutes + "m" : "—"} · {o.rating != null ? o.rating + "★" : "—"}
                    {o.offer_text ? " · " + o.offer_text : ""}
                  </div>
                </div>
                <div>
                  <div className="cc-price tnum">{fmt(o.true_price)}</div>
                  <button className="tbtn" style={{ marginTop: 6, padding: "6px 12px", fontSize: 12 }}
                    onClick={() => onOrder(o)}>Order</button>
                </div>
              </div>
            ))}
            {comparison.unavailable.map((o) => (
              <div key={o.platform} className="cmp-card" style={{ opacity: 0.6 }}>
                <PlatformBadge id={o.platform} size={32} />
                <div className="cc-main"><div className="cc-nm">{plLabel(o.platform)}</div>
                  <div className="cc-meta oos">Out of stock</div></div>
              </div>
            ))}
          </div>
        </React.Fragment>
      )}
    </div>
  );
}

/* ---- one item's full result block ---- */
function ItemResult({ result, onOrder }) {
  const { item, comparison, recommendation: rec } = result;
  const live = comparison.available.length;
  const oos = comparison.unavailable.length;

  return (
    <section>
      <div className="item-head">
        <VegMark veg={item.veg} />
        <h2>{item.name}</h2>
        <span className="unit-badge">{item.unit}</span>
        <span className="kind-badge">{item.kind}</span>
      </div>

      {rec.abstained ? (
        <div className="abstain">
          <span className="ic"><Icon name="alert" size={22} /></span>
          <div>
            <h3>I can't confirm a reliable pick</h3>
            <p>{rec.abstain_reason} Showing what we have rather than guessing.</p>
          </div>
        </div>
      ) : (
        <React.Fragment>
          <BestPick rec={rec} comparison={comparison} onOrder={onOrder} />

          {rec.alternatives.length > 0 && (
            <React.Fragment>
              <div className="alts-h">Other strong options</div>
              <div className="alts">
                {rec.alternatives.map((s) => {
                  const p = s.offer.platform;
                  let tag = null;
                  if (comparison.cheapest && comparison.cheapest.platform === p) tag = "cheapest";
                  else if (comparison.fastest && comparison.fastest.platform === p) tag = "fastest";
                  else if (comparison.best_rated && comparison.best_rated.platform === p) tag = "rated";
                  return <AltCard key={p} offer={s.offer} tag={tag} onOrder={onOrder} />;
                })}
              </div>
            </React.Fragment>
          )}

          <CompareTable comparison={comparison} onOrder={onOrder} />
        </React.Fragment>
      )}

      <div className="softnote">
        <span className="ic"><Icon name="info" size={15} /></span>
        <span>
          {`${live} app${live === 1 ? "" : "s"} stock this now`}{oos ? ` · out of stock on ${comparison.unavailable.map((o) => plLabel(o.platform)).join(", ")}` : ""}.
          Prices are all-in (item + tax + delivery + surge − membership). Simulated demo data.
        </span>
      </div>
    </section>
  );
}

/* ---- HITL order confirmation modal ---- */
function OrderModal({ pending, onClose, onConfirm, phase, orderId, user }) {
  if (!pending) return null;
  const ready = !!pending.idem;
  const signedIn = !!user;
  const canPlace = phase === "confirm" && ready && signedIn;

  return (
    <div className="modal-scrim" onMouseDown={(e) => { if (e.target === e.currentTarget && phase === "confirm") onClose(); }}>
      <div className="modal" role="dialog" aria-modal="true" aria-label="Confirm order">
        <div className="modal-hd">
          <span className="shield"><Icon name="shield" size={20} /></span>
          <h3>Confirm order — your approval required</h3>
        </div>
        <div className="modal-bd">
          <div className="order-line">
            <PlatformBadge id={pending.platform} size={42} />
            <div>
              <div className="ol-nm">{pending.item_name}</div>
              <div className="ol-sub">{plLabel(pending.platform)} · delivery to {pending.pincode}</div>
            </div>
            <div className="ol-price tnum">{fmt(pending.true_price)}</div>
          </div>

          {/* credentials check */}
          <div className="idem">
            {signedIn
              ? <React.Fragment><Icon name="check" size={13} style={{ color: "var(--good)" }} /> Signed in as <code>{user.display}</code></React.Fragment>
              : <React.Fragment><Icon name="alert" size={13} style={{ color: "var(--warn)" }} /> Not signed in — <a href="/login" style={{ color: "var(--primary)", fontWeight: 700 }}>log in</a> to place this order.</React.Fragment>}
          </div>

          {/* membership check */}
          {pending.membership && (
            <div className="idem">
              {pending.member
                ? <React.Fragment><Icon name="check" size={13} style={{ color: "var(--good)" }} /> {pending.membership} member ✓{pending.membership_applied ? " · member price applied" : ""}</React.Fragment>
                : <React.Fragment><Icon name="info" size={13} /> {pending.membership} — you're not a member · standard price</React.Fragment>}
            </div>
          )}

          <div className="idem">
            <Icon name="shield" size={13} /> Idempotency key <code>{pending.idem || "…"}</code> · a retry won't double-order.
          </div>
          <p className="modal-note">
            <Icon name="info" size={14} style={{ flex: "none", marginTop: 1 }} />
            Approving records the order, then opens {plLabel(pending.platform)} to finish checkout. We never pay on your behalf — demo, no real payment.
          </p>
          {phase === "placing" && <p className="modal-note" style={{ color: "var(--primary)", fontWeight: 600 }}>
            <span className="spin" style={{ width: 14, height: 14, border: "2px solid var(--line)", borderTopColor: "var(--primary)", borderRadius: "50%", display: "inline-block", animation: "spin .7s linear infinite" }} />
            Placing your order…</p>}
        </div>
        <div className="modal-ft">
          {signedIn ? (
            <button className="btn-order" disabled={!canPlace} onClick={onConfirm}>
              {ready ? <React.Fragment>Approve &amp; place · {fmt(pending.true_price)} <Icon name="arrow" size={17} /></React.Fragment> : "Preparing…"}
            </button>
          ) : (
            <a className="btn-order" href="/login" style={{ textDecoration: "none", textAlign: "center" }}>
              Log in to continue <Icon name="arrow" size={17} />
            </a>
          )}
          <button className="btn-secondary" disabled={phase !== "confirm"} onClick={onClose}>Cancel</button>
        </div>
      </div>
    </div>
  );
}

/* ---- thinking / loading ---- */
function Thinking({ sub }) {
  return (
    <div className="thinking">
      <div className="think-line"><span className="spin" /> Comparing across India's quick-commerce apps…</div>
      <div className="think-sub">{sub}</div>
      <div className="skel-row"><div className="skel" style={{ width: 46, height: 46, borderRadius: 12 }} />
        <div style={{ flex: 1 }}><div className="skel" style={{ height: 16, width: "40%", marginBottom: 9 }} />
          <div className="skel" style={{ height: 12, width: "62%" }} /></div>
        <div className="skel" style={{ width: 90, height: 34, borderRadius: 10 }} /></div>
      <div className="skel-row"><div className="skel" style={{ height: 12, width: "100%" }} /></div>
      <div className="skel-row"><div className="skel" style={{ height: 12, width: "84%" }} /></div>
    </div>
  );
}

/* ---- empty / no results ---- */
function EmptyState({ query, onPick }) {
  const sample = Object.values(window.QC_CATALOG).slice(0, 8).map((c) => c.name);
  return (
    <div className="empty">
      <div style={{ color: "var(--muted)", display: "inline-flex" }}><Icon name="search" size={40} /></div>
      <div className="big">{query ? `No match for "${query}"` : "Search across every app at once"}</div>
      <p>{query ? "We compare a focused demo catalog. Try one of these — typo-tolerant search will still find it:"
        : "Type what you want in plain language and we'll find the best all-in deal across 8 apps."}</p>
      <div className="chips" style={{ justifyContent: "center" }}>
        {sample.map((s) => (
          <button key={s} className="chip" onClick={() => onPick(s)}>{s}</button>
        ))}
      </div>
    </div>
  );
}

Object.assign(window, { ItemResult, BestPick, AltCard, CompareTable, OrderModal, Thinking, EmptyState });
