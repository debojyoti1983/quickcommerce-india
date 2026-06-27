/* QuickCommerce India — seed data transcribed from app/connectors/mock_data.py
   Simulated data, NOT live platform pricing. Money in INR. */
(function () {
  // ---- platform metadata --------------------------------------------------
  // membership = the paid plan whose discount applies on this platform (if held)
  window.QC_PLATFORMS = {
    swiggy:           { label: "Swiggy",          kind: "food",    color: "#FC8019", membership: "Swiggy One" },
    zomato:           { label: "Zomato",          kind: "food",    color: "#E23744", membership: "Zomato Gold" },
    blinkit:          { label: "Blinkit",         kind: "grocery", color: "#F8CB46", ink: "#1a1a1a", membership: null },
    zepto:            { label: "Zepto",           kind: "grocery", color: "#7B2CBF", membership: null },
    instamart:        { label: "Instamart",       kind: "grocery", color: "#F15A29", membership: "Swiggy One" },
    bigbasket:        { label: "BigBasket",       kind: "grocery", color: "#84C225", membership: "BB Star" },
    flipkart_minutes: { label: "Flipkart Minutes",kind: "grocery", color: "#2874F0", membership: null },
    amazon_fresh:     { label: "Amazon Fresh",    kind: "grocery", color: "#1F8E3D", membership: "Prime" },
  };

  window.QC_MEMBERSHIPS = ["Swiggy One", "Zomato Gold", "BB Star", "Prime"];

  // ---- canonical catalog ---------------------------------------------------
  window.QC_CATALOG = {
    amul_milk_500ml:     { name: "Amul Taaza Toned Milk 500ml", kind: "grocery", unit: "500 ml", veg: null,  aliases: ["amul", "milk", "toned milk", "amul milk"] },
    aashirvaad_atta_5kg: { name: "Aashirvaad Whole Wheat Atta 5kg", kind: "grocery", unit: "5 kg", veg: null, aliases: ["atta", "aashirvaad", "wheat", "flour"] },
    tata_salt_1kg:       { name: "Tata Salt 1kg", kind: "grocery", unit: "1 kg", veg: null, aliases: ["salt", "tata salt"] },
    onion_1kg:           { name: "Onion 1kg", kind: "grocery", unit: "1 kg", veg: null, aliases: ["onion", "pyaz", "kanda"] },
    paneer_butter_masala:{ name: "Paneer Butter Masala", kind: "food", unit: "1 plate", veg: true, aliases: ["paneer", "paneer butter masala", "pbm", "paneer makhani"] },
    chicken_biryani:     { name: "Chicken Biryani", kind: "food", unit: "1 plate", veg: false, aliases: ["biryani", "chicken biryani", "biriyani"] },
    masala_dosa:         { name: "Masala Dosa", kind: "food", unit: "1 plate", veg: true, aliases: ["dosa", "masala dosa"] },
    chicken_curry:       { name: "Chicken Curry", kind: "food", unit: "1 plate", veg: false, aliases: ["chicken curry", "curry", "chicken gravy", "murgh curry", "chicken"] },
    butter_chicken:      { name: "Butter Chicken", kind: "food", unit: "1 plate", veg: false, aliases: ["butter chicken", "murgh makhani", "chicken makhani", "chicken"] },
    veg_biryani:         { name: "Veg Biryani", kind: "food", unit: "1 plate", veg: true, aliases: ["veg biryani", "vegetable biryani", "veg biriyani", "biryani"] },
    dal_makhani:         { name: "Dal Makhani", kind: "food", unit: "1 bowl", veg: true, aliases: ["dal makhani", "dal", "daal", "dal makhni", "lentils"] },
    chole_bhature:       { name: "Chole Bhature", kind: "food", unit: "1 plate", veg: true, aliases: ["chole bhature", "chole", "chhole", "bhature"] },
    eggs_6:              { name: "Farm Eggs (6 pcs)", kind: "grocery", unit: "6 pcs", veg: false, aliases: ["eggs", "egg", "anda", "ande"] },
    bread:               { name: "Britannia Bread 400g", kind: "grocery", unit: "400 g", veg: true, aliases: ["bread", "loaf", "sandwich bread"] },
    basmati_rice_1kg:    { name: "India Gate Basmati Rice 1kg", kind: "grocery", unit: "1 kg", veg: null, aliases: ["rice", "basmati", "basmati rice", "chawal"] },
  };

  // ---- per-platform offers -------------------------------------------------
  // o(base, tax, delivery, surge, memDisc, eta, rating, offer, tier, available=true)
  function o(base, tax, delivery, surge, memDisc, eta, rating, offer, tier, available) {
    return {
      base_price: base, tax: tax, delivery_fee: delivery, surge: surge,
      membership_discount: memDisc, eta_minutes: eta, rating: rating,
      offer_text: offer, tier: tier, available: available !== false,
    };
  }

  window.QC_OFFERS = {
    // ---------------- FOOD ----------------
    swiggy: {
      paneer_butter_masala: o(249, 12.45, 35, 0, 35, 32, 4.3, "Free delivery with Swiggy One", 1),
      chicken_biryani:      o(279, 13.95, 35, 20, 35, 38, 4.1, "20% off up to ₹50", 1),
      masala_dosa:          o(129, 6.45, 35, 0, 35, 27, 4.5, null, 1),
      chicken_curry:        o(219, 10.95, 35, 0, 35, 34, 4.2, null, 1),
      butter_chicken:       o(289, 14.45, 35, 0, 35, 36, 4.4, "20% off up to ₹50", 1),
      veg_biryani:          o(169, 8.45, 35, 0, 35, 30, 4.1, null, 1),
      dal_makhani:          o(179, 8.95, 35, 0, 35, 29, 4.3, null, 1),
      chole_bhature:        o(129, 6.45, 35, 0, 35, 26, 4.4, null, 1),
    },
    zomato: {
      paneer_butter_masala: o(239, 11.95, 45, 0, 45, 41, 4.4, "Free delivery with Gold", 1),
      chicken_biryani:      o(265, 13.25, 45, 0, 45, 35, 4.3, "Buy 1 Get 1", 1),
      masala_dosa:          o(119, 5.95, 45, 0, 0, 44, 4.2, null, 2),
      chicken_curry:        o(229, 11.45, 45, 0, 45, 39, 4.3, "Buy 1 Get 1", 1),
      butter_chicken:       o(279, 13.95, 45, 0, 45, 40, 4.5, null, 1),
      veg_biryani:          o(159, 7.95, 45, 0, 45, 37, 4.2, null, 1),
      dal_makhani:          o(169, 8.45, 45, 0, 45, 35, 4.4, "Free delivery with Gold", 1),
      chole_bhature:        o(139, 6.95, 45, 0, 0, 33, 4.2, null, 2),
    },
    // ---------------- GROCERY ----------------
    blinkit: {
      amul_milk_500ml:     o(34, 0, 15, 0, 0, 11, 4.6, null, 1),
      aashirvaad_atta_5kg: o(255, 0, 15, 0, 0, 12, 4.5, "₹10 off", 1),
      tata_salt_1kg:       o(28, 0, 15, 0, 0, 11, 4.6, null, 1),
      onion_1kg:           o(39, 0, 15, 0, 0, 12, 4.2, null, 1),
      eggs_6:              o(47, 0, 15, 0, 0, 11, 4.5, null, 1),
      bread:               o(40, 0, 15, 0, 0, 11, 4.4, null, 1),
      basmati_rice_1kg:    o(99, 0, 15, 0, 0, 12, 4.5, null, 1),
    },
    zepto: {
      amul_milk_500ml:     o(33, 0, 19, 0, 0, 9, 4.5, "₹19 delivery", 1),
      aashirvaad_atta_5kg: o(259, 0, 19, 0, 0, 10, 4.4, null, 1),
      tata_salt_1kg:       o(27, 0, 19, 0, 0, 9, 4.5, null, 1),
      onion_1kg:           o(36, 0, 19, 0, 0, 10, 4.1, "₹5 off", 1),
      eggs_6:              o(45, 0, 19, 0, 0, 9, 4.4, null, 1),
      bread:               o(42, 0, 19, 0, 0, 10, 4.3, null, 1),
      basmati_rice_1kg:    o(95, 0, 19, 0, 0, 10, 4.4, null, 1),
    },
    instamart: {
      amul_milk_500ml:     o(35, 0, 25, 0, 25, 14, 4.3, "Free delivery with Swiggy One", 1),
      tata_salt_1kg:       o(29, 0, 25, 0, 25, 15, 4.2, null, 2),
      onion_1kg:           o(42, 0, 25, 0, 25, 14, 4.0, null, 2),
      eggs_6:              o(49, 0, 25, 0, 25, 14, 4.3, "Free delivery with Swiggy One", 1),
      bread:               o(44, 0, 25, 0, 25, 15, 4.2, null, 2),
    },
    bigbasket: {
      amul_milk_500ml:     o(32, 0, 0, 0, 3, 120, 4.4, "BB Star member price", 2),
      aashirvaad_atta_5kg: o(245, 0, 0, 0, 15, 120, 4.5, "Lowest price · ₹15 off with BB Star", 2),
      tata_salt_1kg:       o(26, 0, 0, 0, 2, 120, 4.5, "BB Star member price", 2),
      onion_1kg:           o(33, 0, 0, 0, 3, 150, 4.3, "Farm fresh", 2),
      eggs_6:              o(42, 0, 0, 0, 2, 120, 4.5, "BB Star member price", 2),
      bread:               o(38, 0, 0, 0, 2, 120, 4.5, null, 2),
      basmati_rice_1kg:    o(89, 0, 0, 0, 5, 120, 4.6, "Lowest price · ₹5 off with BB Star", 2),
    },
    flipkart_minutes: {
      amul_milk_500ml:     o(34, 0, 0, 0, 0, 16, 4.2, "Free delivery", 2),
      tata_salt_1kg:       o(28, 0, 0, 0, 0, 18, 4.1, null, 2),
      aashirvaad_atta_5kg: o(249, 0, 0, 0, 0, 18, 4.2, null, 2, false), // out of stock
      eggs_6:              o(46, 0, 0, 0, 0, 17, 4.2, "Free delivery", 2),
      bread:               o(39, 0, 0, 0, 0, 18, 4.1, null, 2),
    },
    amazon_fresh: {
      amul_milk_500ml:     o(35, 0, 0, 0, 2, 180, 4.3, "Free delivery with Prime", 2),
      aashirvaad_atta_5kg: o(252, 0, 0, 0, 10, 180, 4.4, "₹10 off with Prime", 2),
      tata_salt_1kg:       o(27, 0, 0, 0, 2, 180, 4.3, "Prime member price", 2),
      basmati_rice_1kg:    o(92, 0, 0, 0, 3, 180, 4.4, "₹3 off with Prime", 2),
    },
  };

  // ---- catalog search (mirrors mock_data.match_catalog_keys) ---------------
  var STOPWORDS = new Set(["and", "with", "the", "for", "of", "in", "my", "some"]);
  function haystack(key, item) {
    return [item.name.toLowerCase(), key.replace(/_/g, " ")].concat(item.aliases);
  }
  function tokens(text) {
    var out = new Set();
    (text.toLowerCase().match(/[a-z]+/g) || []).forEach(function (t) {
      if (t.length >= 3 && !STOPWORDS.has(t)) out.add(t);
    });
    return out;
  }
  window.QC_matchKeys = function (query) {
    var q = (query || "").trim().toLowerCase();
    if (!q) return [];
    var substring = Object.keys(window.QC_CATALOG).filter(function (key) {
      var item = window.QC_CATALOG[key];
      return haystack(key, item).some(function (h) { return q.indexOf(h) >= 0 || h.indexOf(q) >= 0; });
    });
    if (substring.length) return substring;
    var qt = tokens(q);
    if (!qt.size) return [];
    return Object.keys(window.QC_CATALOG).filter(function (key) {
      var item = window.QC_CATALOG[key];
      var ht = new Set();
      haystack(key, item).forEach(function (h) { tokens(h).forEach(function (t) { ht.add(t); }); });
      for (var t of qt) if (ht.has(t)) return true;
      return false;
    });
  };
})();
