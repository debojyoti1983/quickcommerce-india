/* QuickCommerce India — comparison engine (JS port of app/engine/*).
   normalize -> compare -> recommend, explanation-first.
   NOTE: backend uses Decimal; here we round to paise for display parity. */
(function () {
  var TIER_SCORE = { 1: 1.0, 2: 0.8, 3: 0.5 };
  var ABSTAIN_THRESHOLD = 0.55;
  var WEIGHTS = { price: 0.5, eta: 0.3, rating: 0.2 };

  function round2(n) { return Math.round((n + Number.EPSILON) * 100) / 100; }
  function fmtMoney(n) {
    // ₹ with up to 2 decimals, trimming trailing .00
    var r = round2(n);
    return "₹" + (Number.isInteger(r) ? r.toString() : r.toFixed(2));
  }

  // True all-in price: item + tax + delivery + surge − membership (if held)
  function truePrice(offer, platformId, memberships) {
    var plat = window.QC_PLATFORMS[platformId];
    var memDisc = 0;
    if (plat.membership && memberships && memberships.has(plat.membership)) {
      memDisc = offer.membership_discount;
    }
    var total = offer.base_price + offer.tax + offer.delivery_fee + offer.surge - memDisc;
    if (total < 0) total = 0;
    return round2(total);
  }

  function confidence(offer) {
    var tier = TIER_SCORE[offer.tier] || 0.5;
    var recency = 1.0;            // all seed data captured "now"
    var avail = offer.available ? 1.0 : 0.2;
    return round2(tier * recency * avail);
  }

  // Build normalized offers for one catalog item across all selected platforms.
  function normalizeItem(key, opts) {
    var memberships = opts.memberships;        // Set of membership names
    var platforms = opts.platforms;            // Set of platform ids
    var out = [];
    Object.keys(window.QC_OFFERS).forEach(function (pid) {
      if (platforms && !platforms.has(pid)) return;
      var offer = window.QC_OFFERS[pid][key];
      if (!offer) return;
      var memDisc = 0;
      var plat = window.QC_PLATFORMS[pid];
      if (plat.membership && memberships && memberships.has(plat.membership)) memDisc = offer.membership_discount;
      out.push({
        platform: pid,
        item_name: window.QC_CATALOG[key].name,
        unit: window.QC_CATALOG[key].unit,
        kind: window.QC_CATALOG[key].kind,
        veg: window.QC_CATALOG[key].veg,
        available: offer.available,
        eta_minutes: offer.eta_minutes,
        rating: offer.rating,
        offer_text: offer.offer_text,
        base_price: offer.base_price,
        tax: offer.tax,
        delivery_fee: offer.delivery_fee,
        surge: offer.surge,
        membership_discount: memDisc,
        membership_applied: memDisc > 0,
        true_price: truePrice(offer, pid, memberships),
        tier: offer.tier,
        confidence: confidence(offer),
      });
    });
    return out;
  }

  function norm(value, lo, hi, invert) {
    if (hi === lo) return 1.0;
    var pos = (value - lo) / (hi - lo);
    return invert ? 1.0 - pos : pos;
  }

  function buildComparison(query, offers) {
    var available = offers.filter(function (o) { return o.available; });
    var unavailable = offers.filter(function (o) { return !o.available; });
    if (!available.length) return { query: query, available: [], unavailable: unavailable };

    var prices = available.map(function (o) { return o.true_price; });
    var etas = available.filter(function (o) { return o.eta_minutes != null; }).map(function (o) { return o.eta_minutes; });
    var ratings = available.filter(function (o) { return o.rating != null; }).map(function (o) { return o.rating; });
    var pLo = Math.min.apply(null, prices), pHi = Math.max.apply(null, prices);
    var eLo = etas.length ? Math.min.apply(null, etas) : 0, eHi = etas.length ? Math.max.apply(null, etas) : 0;
    var rLo = ratings.length ? Math.min.apply(null, ratings) : 0, rHi = ratings.length ? Math.max.apply(null, ratings) : 0;

    var scored = available.map(function (o) {
      var sPrice = norm(o.true_price, pLo, pHi, true);
      var sEta = o.eta_minutes != null ? norm(o.eta_minutes, eLo, eHi, true) : 0.5;
      var sRating = o.rating != null ? norm(o.rating, rLo, rHi, false) : 0.5;
      var raw = WEIGHTS.price * sPrice + WEIGHTS.eta * sEta + WEIGHTS.rating * sRating;
      return { offer: o, overall_score: round2(raw * o.confidence) };
    });
    scored.sort(function (a, b) { return b.overall_score - a.overall_score; });

    var cheapest = available.reduce(function (a, b) { return b.true_price < a.true_price ? b : a; });
    var timed = available.filter(function (o) { return o.eta_minutes != null; });
    var rated = available.filter(function (o) { return o.rating != null; });
    return {
      query: query,
      available: scored,
      unavailable: unavailable,
      cheapest: cheapest,
      fastest: timed.length ? timed.reduce(function (a, b) { return b.eta_minutes < a.eta_minutes ? b : a; }) : null,
      best_rated: rated.length ? rated.reduce(function (a, b) { return b.rating > a.rating ? b : a; }) : null,
    };
  }

  function confLabel(v) { return v >= 0.75 ? "high" : v >= 0.55 ? "medium" : "low"; }
  var SOURCE_LABEL = { 1: "Live price", 2: "Catalog listing", 3: "Cached estimate" };

  function recommend(comparison) {
    var c = comparison;
    var rec = {
      query: c.query, abstained: false, abstain_reason: null,
      best: null, alternatives: [], because: [], evidence: [],
      confidence_value: 0, confidence_label: "low",
      assumptions: [], missing_data: [],
    };
    if (c.unavailable.length) {
      rec.missing_data.push("Out of stock: " + c.unavailable.map(function (o) {
        return window.QC_PLATFORMS[o.platform].label;
      }).join(", "));
    }
    if (!c.available.length) {
      rec.abstained = true;
      rec.abstain_reason = "No available options across the live platforms for this query.";
      return rec;
    }
    var best = c.available[0];
    var conf = best.offer.confidence;
    rec.confidence_value = conf;
    rec.confidence_label = confLabel(conf);
    rec.best = best;

    if (conf < ABSTAIN_THRESHOLD) {
      rec.abstained = true;
      rec.abstain_reason = "Top option confidence " + conf.toFixed(2) + " is below the " +
        ABSTAIN_THRESHOLD.toFixed(2) + " threshold (stale or low-authority data). I can't confirm this reliably.";
      return rec;
    }

    var b = best.offer;
    var bLabel = window.QC_PLATFORMS[b.platform].label;
    rec.because.push(
      "Best overall on " + bLabel + ": " + b.item_name + " at " + fmtMoney(b.true_price) + " all-in" +
      (b.eta_minutes != null ? ", ETA " + b.eta_minutes + " min" : "") +
      (b.rating != null ? ", rated " + b.rating + "★" : "") +
      " — best balance of price, speed, and rating."
    );
    if (c.cheapest && c.cheapest.platform !== b.platform) {
      rec.because.push("Cheapest is " + window.QC_PLATFORMS[c.cheapest.platform].label + " at " +
        fmtMoney(c.cheapest.true_price) + ", but it trades off speed/rating.");
    }
    if (c.fastest && c.fastest.platform !== b.platform) {
      rec.because.push("Fastest is " + window.QC_PLATFORMS[c.fastest.platform].label + " at " + c.fastest.eta_minutes + " min.");
    }
    if (b.offer_text) rec.because.push("Active offer applied: " + b.offer_text + ".");

    // alternatives = next distinct platforms (up to 3)
    var seen = new Set([b.platform]);
    for (var i = 1; i < c.available.length && rec.alternatives.length < 3; i++) {
      var so = c.available[i];
      if (!seen.has(so.offer.platform)) { rec.alternatives.push(so); seen.add(so.offer.platform); }
    }

    // evidence (friendly provenance) for the chosen option
    var facts = [fmtMoney(b.true_price)];
    if (b.eta_minutes != null) facts.push(b.eta_minutes + " min delivery");
    if (b.rating != null) facts.push(b.rating + "★ rating");
    facts.push(b.available ? "In stock" : "Out of stock");
    rec.evidence.push({
      platform: b.platform, source_label: SOURCE_LABEL[b.tier] || "Unverified",
      freshness: "just now", tier: b.tier, facts: facts,
    });
    return rec;
  }

  // Top-level: run a query -> list of per-item results
  window.QC_compare = function (query, opts) {
    opts = opts || {};
    var memberships = new Set(opts.memberships || []);
    var platforms = opts.platforms ? new Set(opts.platforms) : null;
    var vegOnly = !!opts.vegOnly;

    var keys = window.QC_matchKeys(query);
    if (vegOnly) keys = keys.filter(function (k) {
      var v = window.QC_CATALOG[k].veg;
      return v === true || v === null; // veg or not-applicable (grocery)
    });

    return keys.map(function (key) {
      var offers = normalizeItem(key, { memberships: memberships, platforms: platforms });
      var comparison = buildComparison(query, offers);
      var rec = recommend(comparison);
      return { key: key, item: window.QC_CATALOG[key], comparison: comparison, recommendation: rec };
    });
  };

  window.QC_fmtMoney = fmtMoney;
  window.QC_confLabel = confLabel;
})();
