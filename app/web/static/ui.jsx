/* QuickCommerce India — UI primitives, icons, theme palettes. Exports to window. */
const { useState, useEffect, useRef, useCallback } = React;

/* ---------------- theme palettes ---------------- */
const QC_THEMES = {
  marigold: {
    light: { bg:"#FFF8EF", surface:"#FFFFFF", "surface-2":"#FBF3E7", ink:"#2A1C0E", muted:"#927A57",
      line:"#EEE0CB", primary:"#EC6A1E", "primary-ink":"#FFFFFF", "primary-soft":"#FDEEE0",
      good:"#1E9E5A", "good-soft":"#E4F6EC", star:"#F5A623", warn:"#D8553C", blue:"#3B7DD8" },
    dark:  { bg:"#181106", surface:"#221809", "surface-2":"#2C2010", ink:"#F4E7D2", muted:"#B89C76",
      line:"#392B17", primary:"#FB8B3D", "primary-ink":"#2A1604", "primary-soft":"#2E2010",
      good:"#43C07F", "good-soft":"#16301F", star:"#F5B43F", warn:"#F08163", blue:"#7FA9EE" },
  },
  mint: {
    light: { bg:"#F1FAF5", surface:"#FFFFFF", "surface-2":"#E8F5EE", ink:"#102019", muted:"#5C7A6A",
      line:"#D6EAE0", primary:"#10A56B", "primary-ink":"#FFFFFF", "primary-soft":"#E1F5EC",
      good:"#0D9488", "good-soft":"#DBF3EF", star:"#E89A1F", warn:"#E0594A", blue:"#3B82C4" },
    dark:  { bg:"#0B1611", surface:"#122019", "surface-2":"#16271E", ink:"#E4F2EA", muted:"#88A89A",
      line:"#233A2E", primary:"#2BC288", "primary-ink":"#04140C", "primary-soft":"#14271D",
      good:"#34D0A0", "good-soft":"#103024", star:"#F2BB55", warn:"#F0837A", blue:"#6FB0E0" },
  },
  indigo: {
    light: { bg:"#F4F4FB", surface:"#FFFFFF", "surface-2":"#EDEDF8", ink:"#1A1730", muted:"#6A6588",
      line:"#E2E0F0", primary:"#5B4BE3", "primary-ink":"#FFFFFF", "primary-soft":"#EAE7FC",
      good:"#18A05E", "good-soft":"#E2F5EB", star:"#E89A1F", warn:"#E0594A", blue:"#4B7FE3" },
    dark:  { bg:"#0E0C1A", surface:"#171429", "surface-2":"#1E1A36", ink:"#E9E7F6", muted:"#9892C0",
      line:"#2C2750", primary:"#8576F5", "primary-ink":"#0C0820", "primary-soft":"#211C42",
      good:"#3CCB82", "good-soft":"#122C20", star:"#F2BB55", warn:"#F0837A", blue:"#7C9BF2" },
  },
};

function applyTheme(theme, mode) {
  const pal = (QC_THEMES[theme] || QC_THEMES.marigold)[mode] || QC_THEMES.marigold.light;
  const root = document.documentElement;
  Object.keys(pal).forEach((k) => root.style.setProperty("--" + k, pal[k]));
  root.style.colorScheme = mode;
}

/* ---------------- icons ---------------- */
const ICONS = {
  search: "M11 4a7 7 0 1 0 4.2 12.6L20 21l1.4-1.4-4.4-4.4A7 7 0 0 0 11 4Zm0 2a5 5 0 1 1 0 10 5 5 0 0 1 0-10Z",
  spark: "M12 2l1.6 5.2L19 9l-5.4 1.8L12 16l-1.6-5.2L5 9l5.4-1.8L12 2Zm6 9l.8 2.4L21 14l-2.2.6L18 17l-.8-2.4L15 14l2.2-.6L18 11Z",
  bolt: "M13 2 4 14h6l-1 8 9-12h-6l1-8Z",
  clock: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm0 2a7 7 0 1 1 0 14 7 7 0 0 1 0-14Zm-1 3v5l4 2 .8-1.6L13 11.4V8h-2Z",
  leaf: "M5 20c0-7 4-13 14-14 0 10-5 15-12 15-1 0-2 0-2-1Zm3-2c4-4 6-7 7-9",
  shield: "M12 2 4 5v6c0 5 3.4 8.5 8 10 4.6-1.5 8-5 8-10V5l-8-3Zm0 2.2 6 2.2V11c0 3.8-2.5 6.6-6 7.9C8.5 17.6 6 14.8 6 11V6.4l6-2.2Z",
  check: "M9 16.2 4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2Z",
  chevron: "M6 9l6 6 6-6",
  tag: "M2 12 12 2h8v8L10 20l-8-8Zm14-6a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3Z",
  info: "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm0 2a8 8 0 1 1 0 16 8 8 0 0 1 0-16Zm-1 6h2v7h-2v-7Zm1-4.2a1.3 1.3 0 1 1 0 2.6 1.3 1.3 0 0 1 0-2.6Z",
  alert: "M12 2 1 21h22L12 2Zm0 4 7.5 13h-15L12 6Zm-1 5v4h2v-4h-2Zm0 5v2h2v-2h-2Z",
  pin: "M12 2a7 7 0 0 0-7 7c0 5 7 13 7 13s7-8 7-13a7 7 0 0 0-7-7Zm0 4.5A2.5 2.5 0 1 1 12 11a2.5 2.5 0 0 1 0-4.5Z",
  cart: "M3 3h2l2.4 12.3a2 2 0 0 0 2 1.7h7.7a2 2 0 0 0 2-1.6L22 8H6.2M9 21a1 1 0 1 0 0-2 1 1 0 0 0 0 2Zm9 0a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z",
  x: "M6 6l12 12M18 6 6 18",
  star: "M12 2l2.9 6.3 6.9.7-5.1 4.6 1.4 6.8L12 17.6 5.9 20.4l1.4-6.8L2.2 9l6.9-.7L12 2Z",
  store: "M4 4h16l1 5a3 3 0 0 1-6 .5A3 3 0 0 1 12 11a3 3 0 0 1-3-1.5A3 3 0 0 1 3 9l1-5Zm1 9v7h14v-7",
  sliders: "M4 6h10M18 6h2M4 12h2M10 12h10M4 18h8M16 18h4M14 4v4M6 10v4M12 16v4",
  arrow: "M5 12h14M13 6l6 6-6 6",
};
const STROKE = new Set(["clock_line","chevron","leaf","arrow","sliders","x","store","search_line"]);
function Icon({ name, size = 18, stroke = false, style }) {
  const d = ICONS[name];
  const useStroke = stroke || name === "chevron" || name === "leaf" || name === "arrow" ||
    name === "sliders" || name === "x" || name === "store";
  if (useStroke) {
    return (
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
        strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" style={style} aria-hidden="true">
        <path d={d} />
      </svg>
    );
  }
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" style={style} aria-hidden="true">
      <path d={d} />
    </svg>
  );
}

/* ---------------- platform badge (real logos via logo.dev, monogram fallback) ---------------- */
const PLAT_MONO = {
  swiggy: "S", zomato: "Z", blinkit: "b", zepto: "Z",
  instamart: "im", bigbasket: "bb", flipkart_minutes: "F", amazon_fresh: "a",
};
const PLAT_DOMAIN = {
  swiggy: "swiggy.com", zomato: "zomato.com", blinkit: "blinkit.com",
  zepto: "zeptonow.com", instamart: "instamart.com", bigbasket: "bigbasket.com",
  flipkart_minutes: "flipkart.com", amazon_fresh: "amazon.com",
};
const LOGO_TOKEN = "pk_P3r9v61VQBKshUOKtqDoYg";

function PlatformBadge({ id, size = 38 }) {
  const p = window.QC_PLATFORMS[id] || { label: "?", color: "#888" };
  const mono = PLAT_MONO[id] || p.label[0].toUpperCase();
  const txt = p.ink || "#fff";
  const c = p.color;
  const radius = Math.max(7, size * 0.27);
  const [err, setErr] = useState(false);
  const domain = PLAT_DOMAIN[id];

  if (domain && !err) {
    const src = `https://img.logo.dev/${domain}?token=${LOGO_TOKEN}&size=160&format=png&retina=true`;
    return (
      <span className="pbadge" title={p.label}
        style={{ width: size, height: size, borderRadius: radius, overflow: "hidden",
          background: "#fff",
          boxShadow: "inset 0 0 0 1px rgba(0,0,0,.07), 0 1px 3px rgba(0,0,0,.2)" }}>
        <img src={src} alt={p.label + " logo"} width={size} height={size}
          style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
          onError={() => setErr(true)} />
      </span>
    );
  }

  return (
    <span className="pbadge" title={p.label}
      style={{
        width: size, height: size, borderRadius: radius,
        background: `linear-gradient(155deg, color-mix(in srgb, ${c} 72%, #fff) 0%, ${c} 52%, color-mix(in srgb, ${c} 86%, #000) 100%)`,
        color: txt,
        fontSize: size * (mono.length > 1 ? 0.4 : 0.52),
        letterSpacing: mono.length > 1 ? "-.04em" : "-.02em",
        boxShadow: "inset 0 1px 0 color-mix(in srgb, #fff 40%, transparent), inset 0 -1.5px 3px color-mix(in srgb, #000 20%, transparent), 0 1px 3px rgba(0,0,0,.2)",
      }}>
      {mono}
    </span>
  );
}

/* ---------------- confidence bar ---------------- */
function ConfBar({ value, label }) {
  const pct = Math.round((value || 0) * 100);
  const color = label === "high" ? "var(--good)" : label === "medium" ? "var(--primary)" : "var(--warn)";
  return (
    <div className="conf">
      <span className="label">Confidence</span>
      <div className="conf-bar"><i style={{ width: pct + "%", background: color }} /></div>
      <span className={"conf-tag conf-" + label}>{`${(label || "").toUpperCase()} · ${pct}% sure`}</span>
    </div>
  );
}

/* ---------------- bold-text renderer (**word**) ---------------- */
function RichText({ text }) {
  const parts = String(text).split(/(\*\*[^*]+\*\*)/g);
  return parts.map((p, i) =>
    p.startsWith("**") && p.endsWith("**")
      ? <strong key={i}>{p.slice(2, -2)}</strong>
      : <React.Fragment key={i}>{p}</React.Fragment>
  );
}

function VegMark({ veg }) {
  if (veg === false) {
    return (
      <span className="veg-mark" title="Non-veg" style={{ borderColor: "var(--warn)" }}>
        <i style={{ background: "var(--warn)", borderRadius: 0, width: 0, height: 0,
          borderLeft: "4px solid transparent", borderRight: "4px solid transparent",
          borderBottom: "7px solid var(--warn)" }} />
      </span>
    );
  }
  if (veg === true) return <span className="veg-mark" title="Veg"><i /></span>;
  return null;
}

Object.assign(window, { Icon, PlatformBadge, ConfBar, RichText, VegMark, applyTheme, QC_THEMES });
