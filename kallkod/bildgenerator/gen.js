// gen.js — procedural 3D cars for Bilkollen studio renders (three.js r160)
// Generic shapes only: proportions come from real dimensions and body style; no brand design features.
const DEG = Math.PI / 180;
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const lerp = (a, b, t) => a + (b - a) * t;
const sst = (a, b, x) => { const t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };

/* ---------- monotone cubic interpolation ---------- */
export function pchip(raw) {
  const pts = raw.slice().sort((a, b) => a[0] - b[0]).filter((p, i, a) => i === 0 || p[0] - a[i - 1][0] > 1e-6);
  const n = pts.length, xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
  if (n === 1) return () => ys[0];
  const h = [], d = [];
  for (let i = 0; i < n - 1; i++) { h.push(xs[i + 1] - xs[i]); d.push((ys[i + 1] - ys[i]) / h[i]); }
  const m = new Array(n).fill(0);
  if (n === 2) { m[0] = m[1] = d[0]; }
  else {
    for (let i = 1; i < n - 1; i++) {
      if (d[i - 1] * d[i] <= 0) m[i] = 0;
      else { const w1 = 2 * h[i] + h[i - 1], w2 = h[i] + 2 * h[i - 1]; m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i]); }
    }
    const end = (h0, h1, d0, d1) => {
      let mm = ((2 * h0 + h1) * d0 - h0 * d1) / (h0 + h1);
      if (Math.sign(mm) !== Math.sign(d0)) mm = 0;
      else if (Math.sign(d0) !== Math.sign(d1) && Math.abs(mm) > Math.abs(3 * d0)) mm = 3 * d0;
      return mm;
    };
    m[0] = end(h[0], h[1], d[0], d[1]);
    m[n - 1] = end(h[n - 2], h[n - 3], d[n - 2], d[n - 3]);
  }
  const f = x => {
    if (x <= xs[0]) return ys[0];
    if (x >= xs[n - 1]) return ys[n - 1];
    let lo = 0, hi = n - 1;
    while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (xs[mid] <= x) lo = mid; else hi = mid; }
    const i = lo, t = (x - xs[i]) / h[i], t2 = t * t, t3 = t2 * t;
    return (2 * t3 - 3 * t2 + 1) * ys[i] + (t3 - 2 * t2 + t) * h[i] * m[i] + (-2 * t3 + 3 * t2) * ys[i + 1] + (t3 - t2) * h[i] * m[i + 1];
  };
  f.pts = pts;
  return f;
}
const bez = (p0, p1, p2, p3, t) => {
  const u = 1 - t;
  return [u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0],
          u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1]];
};
// deterministic hash 0..1
export function hash01(s, salt = 0) {
  let h = 2166136261 ^ salt;
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
  h ^= h >>> 13; h = Math.imul(h, 0x5bd1e995); h ^= h >>> 15;
  return (h >>> 0) / 4294967296;
}

/* ---------- body styles ----------
   heights are fractions of the car height H unless noted; x offsets in metres.
   nose: most forward bumper point, he: hood leading edge, cowl: windshield base at the centre line,
   dash: cowl distance behind the front axle as a share of the wheelbase, ws: windshield angle from horizontal,
   bF/bR: belt (window line) front/rear, tum: side-glass tumblehome, inset: body side to glass base,
   fr/rc: plan-view corner radii [along x, along z] front and rear, rb/fb: rear/front bumper bottom (m). */
const BASE = { crownHood: .03, rs: .48, gc: .165, gap: .032, nose: .33, he: .515, heDx: .10, cowl: .665, dash: .145, ws: 27, hd: .022,
  bF: .69, bR: .72, tum: 21, inset: .075, insetHood: .028, fr: [.42, .30], rc: [.28, .20], rb: .30, fb: .205,
  ledge: .018, rr: .065, tuckB: .035, tuckS: .014, bulge: .012, crownRoof: .03, crownWs: .055 };
export const STY = {
  hatch: { ...BASE, bF: 0.695, dash: 0.145, bR: 0.735, rear: 'hatch', rp: { re: .40, rd: .075, sp: .27, gx: .09, gy: .695, tl: .565, ta: .37 }, dlo: 'hatch', doors: 4 },
  hatch3: { ...BASE, bF: 0.695, dash: 0.15, bR: 0.735, rear: 'hatch', rp: { re: .38, rd: .07, sp: .27, gx: .07, gy: .695, tl: .565, ta: .37 }, dlo: 'hatch3', doors: 2, bulge: .02 },
  city: { ...BASE, rs: .44, gc: .16, nose: .345, he: .535, heDx: .075, cowl: .665, dash: 0.1, ws: 31, hd: .03, bF: 0.66, bR: 0.69, tum: 18, inset: .068,
    fr: [.34, .26], rc: [.22, .17], rb: .32, fb: .22, rear: 'hatch', rp: { re: .22, rd: .08, sp: .13, gx: .06, gy: .685, tl: .56, ta: .38 }, dlo: 'city', doors: 4 },
  wagon: { ...BASE, bF: 0.69, rs: .50, dash: 0.17, bR: 0.725, rear: 'hatch', rp: { re: .10, rd: .045, sp: .055, gx: .035, gy: .70, tl: .57, ta: .37 }, dlo: 'wagon', doors: 4, rc: [.24, .18] },
  sedan: { ...BASE, bF: 0.69, rs: .55, gc: .16, nose: .32, dash: 0.19, ws: 26, hd: .024, bR: 0.715, tum: 22, inset: .078, fr: [.44, .30], rc: [.32, .22], fb: .20,
    rear: 'sedan', rp: { re: .46, dk: .35, dy: .715, lip: .045, ta: .44 }, dlo: 'sedan', doors: 4 },
  fastback: { ...BASE, rs: .54, gc: .15, gap: .034, nose: .31, he: .50, cowl: .655, dash: 0.15, ws: 25, hd: .03, bF: 0.685, bR: 0.715, tum: 23, inset: .08,
    fr: [.45, .31], rc: [.32, .22], fb: .19, rear: 'fast', rp: { re: .62, gx: .16, gy: .72, lip: .04, ta: .43 }, dlo: 'fast', doors: 4 },
  cross: { ...BASE, rs: .48, gc: .20, gap: .04, nose: .39, he: .575, heDx: .09, cowl: .70, dash: 0.155, ws: 30, hd: .03, bF: 0.685, bR: 0.735, tum: 17, inset: .07,
    fr: [.38, .28], rc: [.22, .17], rb: .40, fb: .27, rear: 'hatch', rp: { re: .24, rd: .09, sp: .14, gx: .075, gy: .70, tl: .57, ta: .41 }, dlo: 'suv', doors: 4, bulge: .016 },
  suv: { ...BASE, rs: .50, gc: .215, gap: .042, nose: .41, he: .595, heDx: .085, cowl: .70, dash: 0.18, ws: 31, hd: .025, bF: 0.685, bR: 0.725, tum: 15, inset: .066,
    fr: [.36, .27], rc: [.20, .16], rb: .43, fb: .29, rear: 'hatch', rp: { re: .10, rd: .07, sp: .055, gx: .045, gy: .69, tl: .57, ta: .43 }, dlo: 'suv', doors: 4, bulge: .016 },
  suvcoupe: { ...BASE, rs: .50, gc: .19, gap: .04, nose: .38, he: .565, heDx: .095, cowl: .69, dash: 0.165, ws: 29, hd: .03, bF: 0.685, bR: 0.74, tum: 19, inset: .075,
    fr: [.40, .29], rc: [.26, .19], rb: .40, fb: .27, rear: 'scoupe', rp: { re: .82, gx: .11, gy: .755, sp: .045, tl: .58, ta: .42 }, dlo: 'scoupe', doors: 4, bulge: .018 },
  box: { ...BASE, rs: .50, gc: .235, gap: .05, nose: .44, he: .63, heDx: .055, cowl: .685, dash: 0.17, ws: 37, hd: .014, bF: .625, bR: .635, tum: 8, inset: .052,
    fr: [.26, .18], rc: [.14, .10], rb: .45, fb: .33, rear: 'box', rp: { re: .035, rd: .012, gx: .018, gy: .655, tl: .58, ta: .44 }, dlo: 'box', doors: 4, rr: .045, crownRoof: .018, crownWs: .03 },
  mpv: { ...BASE, rs: .50, gc: .18, gap: .05, nose: .30, he: .47, heDx: .05, cowl: .555, dash: -.07, ws: 52, hd: .03, bF: .545, bR: .56, tum: 10, inset: .055,
    fr: [.30, .26], rc: [.16, .12], rb: .40, fb: .26, rear: 'box', rp: { re: .04, rd: .015, gx: .02, gy: .58, tl: .52, ta: .40 }, dlo: 'mpv', doors: 4, rr: .07, crownRoof: .025, crownWs: .045 },
  coupe: { ...BASE, rs: .50, gc: .13, gap: .03, nose: .30, he: .48, heDx: .10, cowl: .635, dash: 0.21, ws: 24, hd: .035, bF: .655, bR: .69, tum: 25, inset: .09,
    fr: [.44, .32], rc: [.34, .24], rb: .27, fb: .15, rear: 'fast', rp: { re: .42, gx: .15, gy: .715, lip: .03, ta: .41 }, dlo: 'coupe', doors: 2, bulge: .028, tuckB: .04 },
  roadster: { ...BASE, rs: .50, gc: .13, gap: .03, nose: .30, he: .48, heDx: .10, cowl: .63, dash: 0.3, ws: 24, hd: .04, bF: .66, bR: .70, tum: 25, inset: .09,
    fr: [.42, .32], rc: [.30, .22], rb: .27, fb: .15, rear: 'road', rp: { re: .10, dk: .40, dy: .70, lip: .03, ta: .42 }, dlo: 'road', doors: 2, bulge: .03, tuckB: .04, crownRoof: .035 }
};

/* ---------- derived dimensions and profile curves ---------- */
export function derive(spec) {
  const st = { ...STY[spec.style] };
  st.rp = { ...st.rp };
  // per-model variation inside the style (seeded, so every render of a model is identical)
  const hv = k => hash01(spec.id, 100 + k);
  st.clH = lerp(0.075, 0.125, hv(1)) * (/cross|suv|box/.test(spec.style) ? 1.1 : 1);
  st.clA = lerp(15, 26, hv(2));
  st.bulge = st.bulge * lerp(0.6, 1.6, hv(3));
  st.bR = st.bR + lerp(-0.012, 0.018, hv(4));
  if (st.rp.rd != null) st.rp.rd = st.rp.rd * lerp(0.8, 1.3, hv(5));
  st.ws = st.ws + lerp(-1.5, 1.5, hv(6));
  st.he = st.he + lerp(-0.012, 0.012, hv(7));
  const L = spec.L / 1000, H = spec.H / 1000, Wd = spec.W / 1000, WB = spec.WB / 1000;
  const F = L / 2, Rr = -L / 2, hw = Wd / 2;
  const ro = (L - WB) * (spec.rs ?? st.rs), fo = L - WB - ro;
  const xf = F - fo, xr = Rr + ro;
  const suvish = /cross|suv|box|mpv|suvcoupe/.test(spec.style);
  let D = (suvish ? 0.36 : 0.30) + 0.08 * L + (spec.style === 'box' ? 0.045 : 0) + (spec.sp ? 0.02 : 0) - (spec.old ? 0.012 : 0);
  D = clamp(D, 0.56, 0.84);
  const R = D / 2;
  let rimIn = spec.rim || Math.round(8 + 2 * L + (suvish ? 1 : 0) + (spec.lux ? 1 : 0) + (spec.sp ? 1 : 0) - (spec.old ? 1 : 0));
  rimIn = clamp(rimIn, 14, 22);
  while (R - rimIn * 0.0127 < (suvish ? 0.085 : 0.07) && rimIn > 14) rimIn--;
  const rimR = rimIn * 0.0127;
  const tw = clamp(0.06 + 0.09 * Wd + (spec.sp ? 0.022 : 0) + (suvish ? 0.01 : 0), 0.18, 0.3);
  const gap = st.gap + (spec.gcAdj || 0) * 0.3;
  const Ra = R + gap;
  const gcS = st.gc + (spec.gcAdj || 0);
  const d = { spec, st, L, H, Wd, WB, F, Rr, hw, xf, xr, ro, fo, R, Ra, rimIn, rimR, tw, gcS, suvish, style: spec.style, dna: dnaFor(spec) };

  /* --- top silhouette (centre line), from front to rear --- */
  const ev = !!spec.ev && !spec.old;
  const dash = st.dash - (ev && /cross|suv|fast|hatch|scoupe/.test(st.rear + spec.style) ? 0.045 : 0) + (spec.lux && !ev ? 0.025 : 0) - (spec.old ? 0.01 : 0);
  const ws = st.ws - (ev ? 2 : 0) + (spec.old ? 3 : 0);
  const yN = st.nose * H, yHE = st.he * H, heDx = st.heDx, xHE = F - heDx;
  const xC = xf - dash * WB, yC = st.cowl * H, yHdr = H - st.hd;
  const run = (yHdr - yC) / Math.tan(ws * DEG), xH = xC - run;
  const bzs = (p0, p1, p2, p3, n, skip0 = true) => { const o = []; for (let i = skip0 ? 1 : 0; i <= n; i++) o.push(bez(p0, p1, p2, p3, i / n)); return o; };
  const top = [[F, yN]];
  // rounded upper front face: vertical at the nose, rolling into the hood edge
  { const Dy = yHE - yN;
    top.push([F - 0.014, yN + Dy * 0.18], [F - heDx * 0.2, yN + Dy * 0.42], [F - heDx * 0.32, yN + Dy * 0.68], [F - heDx * 0.58, yN + Dy * 0.88], [F - heDx * 0.8, yHE - 0.006], [xHE, yHE]); }
  // hood: convex, steeper near the front edge
  const hoodL = xHE - xC;
  for (let k = 1; k < 7; k++) { const t = k / 7; top.push([xHE - t * hoodL, yHE + (yC - yHE) * (t * (1.4 - 0.4 * t))]); }
  top.push([xC, yC]);
  // windshield (slightly convex) rolling into the roof
  for (let k = 1; k < 4; k++) { const t = k / 4; top.push([xC - t * run, yC + (yHdr - yC) * (t * (1.12 - 0.12 * t))]); }
  top.push([xH, yHdr], [xH - 0.1, H - st.hd * 0.22]);
  const rp = st.rp;
  let xRE, xPeak, xRW = null, yDeck = null, xGB = null, yGB = null, yTa = rp.ta * H;
  const roofArc = (x0, x1, y0, y1, n = 4) => { // ease-out when rising to the peak, ease-in when falling from it
    const o = []; for (let k = 1; k <= n; k++) { const t = k / n, e = y1 >= y0 ? 1 - (1 - t) * (1 - t) : 0.45 * t + 0.55 * t * t; o.push([lerp(x0, x1, t), lerp(y0, y1, e)]); } return o; };
  const tailFace = (xs, ys) => bzs([xs, ys], [Rr + (xs - Rr) * 0.35, ys - (ys - yTa) * 0.08], [Rr, yTa + (ys - yTa) * 0.55], [Rr, yTa], 10);
  if (st.rear === 'hatch' || st.rear === 'box') {
    xRE = Rr + rp.re; xPeak = lerp(xH - 0.1, xRE, st.rear === 'box' ? 0.4 : 0.3);
    top.push(...roofArc(xH - 0.1, xPeak, H - st.hd * 0.22, H, 3), ...roofArc(xPeak, xRE, H, H - rp.rd, 4));
    xGB = Rr + rp.gx; yGB = rp.gy * H;
    const ySp = H - rp.rd - (st.rear === 'box' ? 0.01 : 0.03);
    if (rp.sp) top.push([Rr + rp.sp, ySp]);
    const xs0 = rp.sp ? Rr + rp.sp : xRE, ys0 = rp.sp ? ySp : H - rp.rd;
    top.push([lerp(xs0, xGB, 0.5), lerp(ys0, yGB, 0.5) + 0.006], [xGB, yGB]);
    top.push(...tailFace(xGB, yGB));
  } else if (st.rear === 'sedan' || st.rear === 'road') {
    if (st.rear === 'sedan') { xRE = xr + rp.re; xPeak = lerp(xH - 0.1, xRE, 0.42); }
    else { xRE = xH - 0.62; xPeak = lerp(xH, xRE, 0.35); }
    const xDk = Rr + rp.dk; yDeck = rp.dy * H; xRW = xDk;
    top.push(...roofArc(xH - 0.1, xPeak, H - st.hd * 0.22, H, 3), ...roofArc(xPeak, xRE, H, H - 0.045, 3));
    // rear window: concave-to-convex flow down to the deck
    top.push([lerp(xRE, xDk, 0.35), lerp(H - 0.045, yDeck, 0.47)], [lerp(xRE, xDk, 0.72), lerp(H - 0.045, yDeck, 0.84)], [xDk + 0.05, yDeck + 0.01], [xDk, yDeck]);
    top.push([lerp(xDk, Rr + rp.lip, 0.5), yDeck - 0.006], [Rr + rp.lip, yDeck - 0.012]);
    top.push(...tailFace(Rr + rp.lip, yDeck - 0.012));
  } else { // fast / scoupe: roof slopes down to a short tail
    xRE = st.rear === 'scoupe' ? Rr + rp.re : xr + rp.re; xPeak = lerp(xH - 0.1, xRE, 0.3);
    xGB = Rr + rp.gx; yGB = rp.gy * H; xRW = xGB;
    const yRE = H - (st.rear === 'scoupe' ? 0.06 : 0.07);
    top.push(...roofArc(xH - 0.1, xPeak, H - st.hd * 0.22, H, 3), ...roofArc(xPeak, xRE, H, yRE, 3));
    top.push([lerp(xRE, xGB, 0.4), lerp(yRE, yGB, 0.52)], [lerp(xRE, xGB, 0.75), lerp(yRE, yGB, 0.86)], [xGB + 0.04, yGB + 0.006], [xGB, yGB]);
    if (st.rear === 'scoupe') {
      if (rp.sp) top.push([Rr + rp.sp, yGB - 0.02]);
      top.push(...tailFace(Rr + (rp.sp || 0.04) - 0.01, yGB - 0.03));
    } else {
      top.push([Rr + (rp.lip || 0.04), yGB - 0.006]);
      top.push(...tailFace(Rr + (rp.lip || 0.04), yGB - 0.006));
    }
  }
  const yt = pchip(top);

  /* --- bottom (without arches) --- */
  const rbY = st.rb, fbY = st.fb;
  const xrA = xr - Ra, xfA = xf + Ra;
  const lipF = d.suvish ? 0.085 : 0.065, lipR = 0.1;
  const bot = [[Rr, yTa]];
  bot.push(...bzs([Rr, yTa], [Rr, yTa - (yTa - rbY) * 0.62], [Rr + lipR * 0.45, rbY + 0.006], [Rr + lipR, rbY], 8));
  bot.push([Math.min(xrA - 0.03, Rr + 0.32), rbY - 0.012], [xrA, rbY - 0.02], [xr, lerp(rbY, gcS, 0.7)], [xr + Ra + 0.02, gcS], [xf - Ra - 0.02, gcS], [xf, lerp(gcS, fbY, 0.5)], [xfA, fbY + 0.006]);
  bot.push([Math.max(xfA + 0.03, F - 0.3), fbY], [F - lipF, fbY + 0.002]);
  { const Dy = yN - fbY;
    bot.push([F - lipF * 0.6, fbY + 0.012], [F - lipF * 0.3, fbY + Dy * 0.2], [F - 0.022, fbY + Dy * 0.55], [F - 0.009, fbY + Dy * 0.84], [F, yN]); }
  const ybBase = pchip(bot);
  const arch = (x, xa) => { const dx = x - xa; return Math.abs(dx) < Ra ? R + Math.sqrt(Ra * Ra - dx * dx) : -1; };
  const yb = x => Math.max(ybBase(x), arch(x, xf), arch(x, xr));

  /* --- belt (window line) --- */
  const xBF = xC - 0.12;
  const xBR = st.rear === 'sedan' || st.rear === 'road' ? xRW : (xGB ?? Rr + 0.05);
  const bR = st.bR + (spec.old ? -0.015 : 0.012), bF = st.bF + (spec.old ? -0.01 : 0);
  const belt = pchip([[xBR, bR * H], [lerp(xBR, xBF, 0.5), lerp(bR, bF, 0.55) * H], [xBF, bF * H]]);

  /* --- crown (roof/hood curvature across the car) --- */
  const cr = [[F, st.crownHood * 0.6], [xHE, st.crownHood], [xC + 0.05, st.crownHood + 0.004], [xC - 0.12, st.crownWs], [xH + 0.1, st.crownWs * 0.9],
    [xH - 0.15, st.crownRoof + 0.006], [xPeak, st.crownRoof], [xRE, st.crownRoof + 0.004]];
  if (xRW != null && st.rear !== 'fast' && st.rear !== 'scoupe') cr.push([xRW + 0.05, st.crownWs * 0.8], [xRW - 0.08, st.crownHood * 0.9], [Rr, st.crownHood * 0.5]);
  else if (xGB != null && (st.rear === 'fast' || st.rear === 'scoupe')) cr.push([lerp(xRE, xGB, 0.5), st.crownWs * 0.85], [xGB, st.crownHood * 0.9], [Rr, st.crownHood * 0.5]);
  else cr.push([Rr + 0.06, st.crownRoof * 0.7], [Rr, st.crownHood * 0.5]);
  const crown = pchip(cr);

  /* --- plan view half width --- */
  const [rxF, rzF] = st.fr, [rxR, rzR] = st.rc;
  const corner = (t, rz, n = 2) => t <= 0 ? 0 : rz * (1 - Math.pow(Math.max(0, 1 - Math.pow(Math.min(1, t), n)), 1 / n));
  const hw0 = x => hw - corner((x - (F - rxF * 1.35)) / (rxF * 1.35), rzF * 1.05, 1.7) - corner(((Rr + rxR * 1.3) - x) / (rxR * 1.3), rzR, 1.8);
  const bul = st.bulge * 0.6 + (spec.sp ? 0.01 : 0);
  const hwB = x => hw0(x) - bul + bul * (Math.exp(-Math.pow((x - xf) / 0.48, 2)) + Math.exp(-Math.pow((x - xr) / 0.48, 2)));

  Object.assign(d, { yN, yHE, xHE, xC, yC, yHdr, xH, xRE, xPeak, xRW, yDeck, xGB, yGB, yTa, yt, ybBase, yb, belt, crown, hw0, hwB, top, bot, run, ev });
  return d;
}

/* ---------- cross-section ---------- */
export const SEG = { A: 6, B: 5, C: 6, D1: 5, D2: 5, E: 6, Fg: 8, G: 8, Hc: 16 };
export const NHALF = Object.values(SEG).reduce((a, b) => a + b, 0) + 1;
export function secInfo(d, x) {
  const st = d.st;
  const yb = d.yb(x), yt = d.yt(x), h = Math.max(1e-4, yt - yb);
  const ybB = d.ybBase(x), hB = Math.max(1e-4, yt - ybB);
  const crown = Math.min(d.crown(x), 0.3 * hB);
  const ledge = Math.min(st.ledge, 0.12 * hB);
  let ys = Math.min(d.belt(x), yt - crown - ledge);
  ys = Math.max(ys, ybB + 0.5 * hB, yb + 0.06);
  let ye = Math.max(ys + ledge, yt - crown); ye = Math.min(ye, yt);
  const gh = Math.max(0, ye - (ys + ledge));
  const W = d.hwB(x), W0 = d.hw0(x);
  const tb = Math.min(st.tuckB, 0.25 * W);
  const rb = Math.min(0.055, 0.32 * h);
  const ymid = Math.min(ys - 0.03, Math.max(yb + rb + 0.012, ybB + 0.42 * (ys - ybB)));
  // character line: crease below the belt, the band above it leans inwards and catches the light
  const clH = Math.min(st.clH ?? (d.suvish ? 0.105 : 0.09), 0.42 * (ys - ymid));
  const ycl = ys - clH;
  const wcl = W - 0.005;
  const hws = wcl - clH * Math.tan((st.clA ?? 21) * DEG);
  const inset = lerp(st.insetHood, st.inset, sst(0, 0.14, gh));
  const hwg = Math.max(0.04, Math.min(hws - 0.012, W0 - 0.045 - inset));
  const hwr = Math.max(0.04, hwg - gh * Math.tan(st.tum * DEG));
  const rr = Math.min(st.rr, 0.5 * gh + 0.014, 0.45 * (yt - ys) + 0.002);
  return { x, yb, yt, h, crown, ledge, ys, ye, gh, W, W0, tb, rb, ymid, ycl, wcl, inset, hws, hwg, hwr, rr };
}
export function sectionHalf(d, x) {
  const s = secInfo(d, x);
  const { yb, yt, ys, ye, W, tb, rb, ymid, ycl, wcl, hws, hwg, hwr, rr, ledge } = s;
  const out = [];
  const seg = (n, f) => { for (let i = 0; i < n; i++) out.push(f(i / n)); };
  const rbz = Math.min(0.07, 0.4 * W);
  const xA1 = W - tb - rbz;
  seg(SEG.A, t => [lerp(0, xA1, t), yb]);
  const pB0 = [xA1, yb], pB3 = [W - tb * 0.45, yb + rb];
  seg(SEG.B, t => bez(pB0, [xA1 + rbz * 0.6, yb], [W - tb * 0.62, yb + rb * 0.35], pB3, t));
  const pC3 = [W, ymid];
  seg(SEG.C, t => bez(pB3, [W - tb * 0.2, yb + rb + (ymid - yb - rb) * 0.4], [W, ymid - (ymid - yb - rb) * 0.3], pC3, t));
  const pD3 = [wcl, ycl];
  seg(SEG.D1, t => bez(pC3, [W, ymid + (ycl - ymid) * 0.45], [wcl + 0.002, ycl - (ycl - ymid) * 0.25], pD3, t));
  const pD5 = [hws, ys];
  seg(SEG.D2, t => bez(pD3, [lerp(wcl, hws, 0.3), lerp(ycl, ys, 0.3)], [lerp(wcl, hws, 0.72), lerp(ycl, ys, 0.75)], pD5, t));
  const pE3 = [hwg, ys + ledge];
  seg(SEG.E, t => bez(pD5, [hws - (hws - hwg) * 0.12, ys + ledge * 0.75], [hwg + (hws - hwg) * 0.35, ys + ledge], pE3, t));
  const pF3 = [hwr, Math.max(ys + ledge, ye - rr)];
  seg(SEG.Fg, t => [lerp(pE3[0], pF3[0], t) + 0.006 * Math.sin(Math.PI * t) * Math.min(1, s.gh / 0.2), lerp(pE3[1], pF3[1], t)]);
  const tn = Math.tan(d.st.tum * DEG);
  const pG3 = [Math.max(0.02, hwr - rr), ye];
  seg(SEG.G, t => bez(pF3, [hwr - rr * tn * 0.55, pF3[1] + rr * 0.55], [hwr - rr * 0.42, ye], pG3, t));
  const zE = pG3[0];
  const hk = (1 - sst(0.01, 0.06, s.gh)) * sst(d.xC + 0.12, d.xC + 0.3, x) * (1 - sst(d.xHE - 0.25, d.xHE - 0.05, x));
  const uc = 0.62, a = 0.35, fC = u => u < uc ? a * u * u / (uc * uc) * uc * uc : a * uc * uc + (1 - a * uc * uc) * Math.pow((u - uc) / (1 - uc), 1.15);
  const nO = 6, nI = SEG.Hc - nO;
  for (let i = 0; i <= SEG.Hc; i++) {
    const u = i <= nO ? lerp(1, uc, i / nO) : lerp(uc, 0, (i - nO) / nI);
    const f = lerp(u * u, fC(u), hk);
    out.push([zE * u, yt - (yt - ye) * f]);
  }
  return { pts: out, info: s };
}

/* ---------- body mesh ---------- */
function stations(d) {
  // adaptive: dense where the silhouette is steep, at the ends and around the wheel arches
  const N = 4000, xs = [], w = [];
  for (let i = 0; i <= N; i++) xs.push(lerp(d.Rr, d.F, i / N));
  let acc = 0; const cum = [0];
  for (let i = 1; i <= N; i++) {
    const x0 = xs[i - 1], x1 = xs[i], dx = x1 - x0;
    const a = Math.hypot(dx, d.yt(x1) - d.yt(x0)) + Math.hypot(dx, d.ybBase(x1) - d.ybBase(x0)) * 0.7;
    const nearArch = Math.min(Math.abs(x1 - d.xf), Math.abs(x1 - d.xr)) < d.Ra + 0.05 ? 1.4 : 0;
    const nearEnd = (x1 > d.F - 0.25 || x1 < d.Rr + 0.25) ? 1.5 : 0;
    acc += a + dx * (nearArch + nearEnd + 0.25);
    cum.push(acc);
  }
  const M = 340, out = [];
  let j = 0;
  for (let k = 0; k <= M; k++) {
    const target = acc * k / M;
    while (j < N && cum[j + 1] < target) j++;
    const t = j < N ? (target - cum[j]) / Math.max(1e-9, cum[j + 1] - cum[j]) : 0;
    out.push(lerp(xs[j], xs[Math.min(N, j + 1)], t));
  }
  // exact arch edges (vertical walls)
  for (const xa of [d.xf, d.xr]) for (const s of [-1, 1]) { const xe = xa + s * d.Ra; out.push(xe - 0.0008 * s * -1, xe + 0.0008 * s * -1); }
  out.sort((a, b) => a - b);
  const res = [out[0]];
  for (const x of out) if (x - res[res.length - 1] > 0.0006) res.push(x);
  res[0] = d.Rr; res[res.length - 1] = d.F;
  return res;
}
export function buildBodyGeometry(THREE, d) {
  const xs = stations(d);
  const ringN = NHALF + (NHALF - 2);
  const pos = new Float32Array(xs.length * ringN * 3);
  let k = 0;
  const infos = [];
  for (const x of xs) {
    const { pts, info } = sectionHalf(d, x); infos.push(info);
    for (let j = 0; j < NHALF; j++) { pos[k++] = x; pos[k++] = pts[j][1]; pos[k++] = pts[j][0]; }
    for (let j = NHALF - 2; j >= 1; j--) { pos[k++] = x; pos[k++] = pts[j][1]; pos[k++] = -pts[j][0]; }
  }
  const idx = [];
  for (let i = 0; i < xs.length - 1; i++) {
    for (let j = 0; j < ringN; j++) {
      const a = i * ringN + j, b = i * ringN + (j + 1) % ringN, c = (i + 1) * ringN + j, e = (i + 1) * ringN + (j + 1) % ringN;
      idx.push(a, c, b, b, c, e);
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setIndex(idx);
  g.computeVertexNormals();
  // orientation check: roof normal must point up
  const nrm = g.attributes.normal, mid = Math.floor(xs.length * 0.45) * ringN + (NHALF - 1);
  if (nrm.getY(mid) < 0) {
    for (let i = 0; i < idx.length; i += 3) { const t = idx[i + 1]; idx[i + 1] = idx[i + 2]; idx[i + 2] = t; }
    g.setIndex(idx); g.computeVertexNormals();
  }
  d.xs = xs; d.infos = infos;
  return g;
}

/* ---------- materials painted into view textures ---------- */
const hex = c => { const n = parseInt(c.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; };
function mats(d) {
  const col = d.spec.color || '#888888';
  const [r, g, b] = hex(col), lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  const metal = lum > 0.75 ? 0.15 : lum > 0.55 ? 0.35 : 0.55;
  return {
    paint: { alb: col, cc: 1, ro: lum > 0.75 ? 0.36 : 0.30, me: metal },
    glass: { alb: '#0c1014', cc: 1, ro: 0.03, me: 0.32 },
    lens: { alb: '#1a2026', cc: 1, ro: 0.05, me: 0.5 },
    tint: { alb: '#06080a', cc: 1, ro: 0.03, me: 0 },
    gloss: { alb: '#070707', cc: 1, ro: 0.14, me: 0 },
    pillar: { alb: '#0a0b0c', cc: 0.15, ro: 0.5, me: 0 },
    trim: { alb: '#0c0d0e', cc: 0.3, ro: 0.4, me: 0 },
    matte: { alb: '#141516', cc: 0, ro: 0.72, me: 0 },
    clad: { alb: '#1e2022', cc: 0, ro: 0.86, me: 0 },
    chrome: { alb: '#e2e5e8', cc: 0, ro: 0.07, me: 1 },
    alu: { alb: '#b9bdc1', cc: 0, ro: 0.28, me: 1 },
    lamp: { alb: '#aab1b8', cc: 1, ro: 0.06, me: 0.9 },
    lampIn: { alb: '#24292e', cc: 1, ro: 0.1, me: 0.6 },
    drl: { alb: '#f4f7fa', cc: 1, ro: 0.1, me: 0, em: '#e8f0ff' },
    tail: { alb: '#5a0707', cc: 1, ro: 0.06, me: 0, em: '#1a0000' },
    tailLed: { alb: '#c81010', cc: 1, ro: 0.08, me: 0, em: '#8a0000' },
    amber: { alb: '#d07a12', cc: 1, ro: 0.1, me: 0, em: '#2a1200' },
    grille: { alb: '#0b0c0d', cc: 0.7, ro: 0.3, me: 0.2 },
    grilleLine: { alb: '#2a2d30', cc: 0.4, ro: 0.4, me: 0.5 },
    grilleDot: { alb: '#6a7076', cc: 0.6, ro: 0.25, me: 0.8 },
    under: { alb: '#111213', cc: 0, ro: 0.9, me: 0 }
  };
}

/* View rasters: side (x,y), top (x,|z|), front (|z|,y), rear (|z|,y) packed in one atlas; three canvases share the layout:
   albedo (sRGB), orm (R clearcoat, G roughness, B metalness), emissive. */
export function paintViews(d) {
  const S = 520; // px per metre
  const M = mats(d);
  const hwM = d.hw + 0.07, Hm = d.H + 0.07;
  const side = { x0: d.Rr - 0.06, x1: d.F + 0.06, y1: Hm };
  side.w = Math.ceil((side.x1 - side.x0) * S); side.h = Math.ceil(Hm * S);
  const ZM = 0.04;
  const top = { x0: side.x0, z1: hwM, w: side.w, h: Math.ceil((hwM + ZM) * S) };
  const front = { w: Math.ceil((hwM + ZM) * S), h: side.h, y1: Hm };
  const rear = { w: front.w, h: side.h, y1: Hm };
  side.ox = 0; side.oy = 0; front.ox = side.w; front.oy = 0; rear.ox = side.w + front.w; rear.oy = 0; top.ox = 0; top.oy = side.h;
  const AW = side.w + front.w + rear.w, AH = side.h + top.h;
  const mk = () => { const c = document.createElement('canvas'); c.width = AW; c.height = AH; return c; };
  const C = { alb: mk(), orm: mk(), emi: mk() };
  const X = { alb: C.alb.getContext('2d'), orm: C.orm.getContext('2d'), emi: C.emi.getContext('2d') };
  X.emi.fillStyle = '#000'; X.emi.fillRect(0, 0, AW, AH);
  const view = v => {
    // world -> pixel: px = ox + (a - a0) * S, py = oy + (b1 - b) * S
    const a0 = v === side || v === top ? v.x0 : -ZM, b1 = v === top ? v.z1 : v.y1;
    for (const k in X) { X[k].setTransform(S, 0, 0, -S, v.ox - a0 * S, v.oy + b1 * S); }
    for (const k in X) { X[k].save(); X[k].beginPath(); X[k].rect(a0, b1 - v.h / S, v.w / S, v.h / S); X[k].clip(); }
  };
  const endView = (v) => {
    for (const k in X) X[k].restore();
    if (!v) return;
    // mirror the strip next to the centre line into the margin so filtering never sees the neighbouring view
    const m = Math.round(ZM * S);
    for (const k in X) {
      const c = X[k]; c.save(); c.setTransform(1, 0, 0, 1, 0, 0);
      if (v === top) { const yz0 = Math.round(v.oy + v.z1 * S); c.translate(0, yz0 * 2); c.scale(1, -1); c.drawImage(C[k], v.ox, yz0 - m, v.w, m, v.ox, yz0 - m, v.w, m); }
      else { const x0 = Math.round(v.ox + m); c.translate(x0 * 2, 0); c.scale(-1, 1); c.drawImage(C[k], x0, v.oy, m, v.h, x0, v.oy, m, v.h); }
      c.restore();
    }
  };
  const ormCol = m => `rgb(${Math.round(m.cc * 255)},${Math.round(m.ro * 255)},${Math.round(m.me * 255)})`;
  const fill = (path, m, a = 1) => {
    X.alb.globalAlpha = a; X.orm.globalAlpha = a; X.emi.globalAlpha = a;
    X.alb.fillStyle = m.alb; X.alb.fill(path);
    X.orm.fillStyle = ormCol(m); X.orm.fill(path);
    X.emi.fillStyle = m.em || '#000'; X.emi.fill(path);
    X.alb.globalAlpha = X.orm.globalAlpha = X.emi.globalAlpha = 1;
  };
  const stroke = (path, w, col, a = 1, orm = null) => {
    X.alb.globalAlpha = a; X.alb.lineWidth = w; X.alb.strokeStyle = col; X.alb.lineJoin = 'round'; X.alb.lineCap = 'round'; X.alb.stroke(path); X.alb.globalAlpha = 1;
    if (orm) { X.orm.globalAlpha = a; X.orm.lineWidth = w; X.orm.strokeStyle = ormCol(orm); X.orm.stroke(path); X.orm.globalAlpha = 1; }
  };
  const poly = (pts, close = true) => { const p = new Path2D(); pts.forEach((q, i) => i ? p.lineTo(q[0], q[1]) : p.moveTo(q[0], q[1])); if (close) p.closePath(); return p; };
  const rect = (a, b, w, h) => { const p = new Path2D(); p.rect(a, b, w, h); return p; };
  const rrect = (a, b, w, h, r) => { const p = new Path2D(); p.roundRect(a, b, w, h, r); return p; };
  const g = d.geo;
  const drawItem = p => {
    if (p.clip) for (const k in X) { X[k].save(); X[k].clip(poly(p.clip)); }
    if (p.stroke) {
      const path = poly(p.pts, !!p.close);
      stroke(path, p.w, p.col, p.a ?? 1, p.m ? M[p.m] : null);
      if (p.em && M[p.m] && M[p.m].em) { X.emi.lineWidth = p.w; X.emi.strokeStyle = M[p.m].em; X.emi.lineCap = 'round'; X.emi.stroke(path); }
    } else if (p.circle) { const c = new Path2D(); c.arc(p.circle[0], p.circle[1], p.circle[2], 0, Math.PI * 2); fill(c, M[p.m], p.a ?? 1); }
    else fill(p.path || poly(p.pts), M[p.m] || p.mat, p.a ?? 1);
    if (p.clip) for (const k in X) X[k].restore();
  };

  /* ===== SIDE ===== */
  view(side);
  fill(rect(side.x0, 0, side.x1 - side.x0, Hm), M.paint);
  // dark underside edge
  const lowPts = [];
  for (let x = d.Rr; x <= d.F; x += 0.005) lowPts.push([x, d.yb(x) + 0.012]);
  fill(poly([[d.Rr - 0.1, -0.1], ...lowPts, [d.F + 0.1, -0.1]]), M.under);
  // lower bumpers and cladding
  if (g.clad) {
    const ct = [];
    for (let x = d.Rr; x <= d.F; x += 0.004) {
      let y = d.ybBase(x) + g.cladH;
      for (const xa of [d.xf, d.xr]) { const r = d.Ra + g.cladW, dx = x - xa; if (Math.abs(dx) < r) y = Math.max(y, d.R + Math.sqrt(r * r - dx * dx)); }
      ct.push([x, y]);
    }
    fill(poly([[d.Rr - 0.1, -0.1], ...ct, [d.F + 0.1, -0.1]]), M.clad);
  } else {
    const ct = [];
    for (let x = d.Rr; x <= d.F; x += 0.004) {
      let y = -1;
      if (x > d.xf + d.Ra + 0.02) y = d.st.fb + 0.055 * sst(d.xf + d.Ra, d.xf + d.Ra + 0.12, x);
      else if (x < d.xr - d.Ra - 0.02) y = d.st.rb + 0.05 * sst(d.xr - d.Ra, d.xr - d.Ra - 0.15, x);
      else if (x > d.xr + d.Ra && x < d.xf - d.Ra) y = d.gcS + g.sill;
      ct.push([x, Math.max(y, d.yb(x) - 0.01)]);
    }
    fill(poly([[d.Rr - 0.1, -0.1], ...ct, [d.F + 0.1, -0.1]]), M.matte);
  }
  // side moulding (older cars)
  if (g.moulding) fill(rrect(d.xr + d.Ra + 0.05, g.moulding - 0.018, (d.xf - d.Ra - 0.05) - (d.xr + d.Ra + 0.05), 0.036, 0.012), M.matte);

  // greenhouse: DLO
  const pil = g.pillarMat === 'gloss' ? M.gloss : M.paint;
  const dlo = g.dlo; // polygon in side view
  if (dlo) {
    if (g.tt) fill(g.ttSidePath, M.gloss);
    fill(poly(dlo.outer), g.trim === 'chrome' ? M.chrome : M.trim);
    if (g.dPillar) fill(poly(g.dPillar), M.gloss);
    for (const w of dlo.glass) fill(poly(w), M.glass);
    for (const p of dlo.pillars) fill(poly(p), g.bPillar === 'paint' ? M.paint : M.pillar);
    if (g.trim === 'chrome') stroke(poly(dlo.outer), 0.012, '#e8ebee', 1, M.chrome);
  }
  // door shut lines
  for (const s of g.seams) stroke(poly(s, false), 0.006, '#000', 0.72, { cc: 0.2, ro: 0.7, me: 0 });
  for (const hd of g.handles) {
    fill(rrect(hd[0], hd[1] - 0.012, hd[2], 0.03, 0.012), { alb: '#000', cc: 0.2, ro: 0.6, me: 0 }, 0.38);
    fill(rrect(hd[0] + 0.006, hd[1] - 0.006, hd[2] - 0.012, 0.022, 0.01), g.handleMat === 'chrome' ? M.chrome : M.paint);
    stroke(poly([[hd[0] + 0.012, hd[1] + 0.014], [hd[0] + hd[2] - 0.012, hd[1] + 0.014]], false), 0.003, '#fff', 0.35);
  }
  if (g.fuel) stroke(rrect(g.fuel[0], g.fuel[1], 0.17, 0.115, 0.02), 0.004, '#000', 0.5);
  if (g.indicator) fill(rrect(g.indicator[0], g.indicator[1], 0.055, 0.022, 0.011), M.amber);
  // lamps (side wraps)
  for (const p of g.sideLamps) fill(poly(p.pts), M[p.m]);
  endView();

  /* ===== TOP ===== */
  view(top);
  fill(rect(top.x0, -ZM, side.x1 - side.x0, hwM + ZM), M.paint);
  if (g.roofTop) fill(poly(g.roofTop), M.gloss);
  if (g.wsTop) { fill(poly(g.wsTopOuter), M.gloss); fill(poly(g.wsTop), M.glass); }
  if (g.rwTop) { fill(poly(g.rwTopOuter), M.gloss); fill(poly(g.rwTop), M.glass); }
  for (const s of g.topSeams) stroke(poly(s, false), 0.0045, '#000', 0.5);
  for (const p of g.topLamps) fill(poly(p.pts), M[p.m]);
  if (g.softTop) fill(poly(g.softTop), { alb: '#1b1c1e', cc: 0, ro: 0.9, me: 0 });
  endView(top);

  /* ===== FRONT ===== */
  view(front);
  fill(rect(-ZM, 0, hwM + ZM, Hm), M.paint);
  if (g.wsFront) { fill(poly(g.wsFrontOuter), M.gloss); fill(poly(g.wsFront), M.glass); }
  for (const p of g.front) drawItem(p);
  endView(front);

  /* ===== REAR ===== */
  view(rear);
  fill(rect(-ZM, 0, hwM + ZM, Hm), M.paint);
  if (g.rwRear) { fill(poly(g.rwRearOuter), M.gloss); fill(poly(g.rwRear), M.glass); }
  for (const p of g.rear) drawItem(p);
  endView(rear);

  const map = v => { // returns vec4 (ax,bx,ay,by): u=ax*a+bx, v=ay*b+by  (flipY texture)
    const a0 = v === side || v === top ? v.x0 : -ZM, b1 = v === top ? v.z1 : v.y1;
    return [S / AW, (v.ox - a0 * S) / AW, S / AH, 1 - (v.oy + b1 * S) / AH];
  };
  return { C, AW, AH, maps: { side: map(side), top: map(top), front: map(front), rear: map(rear) } };
}

/* ---------- design layout (pillars, doors, lamps) computed from geometry ---------- */
export function layout(d) {
  const st = d.st, sp = d.spec, s = x => secInfo(d, x);
  const g = { seams: [], handles: [], sideLamps: [], topSeams: [], topLamps: [], front: [], rear: [] };
  const old = !!sp.old, ev = !!sp.ev, lux = !!sp.lux, sport = !!sp.sp;
  g.tt = !!sp.tt;
  g.clad = sp.clad != null ? !!sp.clad : (/^(cross|suv|box|suvcoupe)$/.test(d.style) && !lux);
  g.cladH = d.style === 'box' ? 0.12 : 0.09; g.cladW = 0.055;
  g.sill = sport ? 0.05 : 0.03;
  g.trim = lux && !old ? 'chrome' : (old ? 'gloss' : 'gloss');
  g.bPillar = old ? 'paint' : 'gloss';
  if (old) g.trim = 'chrome';
  g.handleMat = lux || old ? 'chrome' : 'paint';
  if (ev && !old && hash01(sp.id, 7) > 0.45) g.handleMat = 'flush';
  if (old && /volvo|saab/.test(sp.id)) g.moulding = 0.52 + (d.suvish ? 0.08 : 0);
  if (old) g.indicator = [d.xf + d.Ra + 0.06, d.ybBase(d.xf + d.Ra) + 0.36];

  // --- DLO (side windows) ---
  const step = 0.004;
  const topEdge = x => {
    const i = s(x);
    const sl = Math.abs((s(x + 0.01).ye - s(x - 0.01).ye) / 0.02), cosA = 1 / Math.sqrt(1 + sl * sl);
    const wPil = lerp(0.034, 0.062, sst(d.xH - 0.05, d.xH + 0.2, x)); // A-pillar wider than the roof frame
    return i.ye - Math.max(i.rr * 0.5, 0.012) - wPil / cosA;
  };
  const botEdge = x => { const i = s(x); return i.ys + i.ledge + 0.008; };
  const xF = d.xC - (d.style === 'mpv' ? 0.02 : 0.055);
  // rear end of the DLO per style
  let rB, rT, pillars = [];
  const xr = d.xr, Ra = d.Ra;
  const DL = st.dlo;
  if (DL === 'hatch') { rB = xr + 0.10; rT = xr + 0.40; }
  else if (DL === 'hatch3') { rB = xr + 0.12; rT = xr + 0.36; }
  else if (DL === 'city') { rB = d.Rr + 0.4; rT = d.Rr + 0.5; }
  else if (DL === 'wagon') { rB = d.Rr + 0.26; rT = d.Rr + 0.30; }
  else if (DL === 'suv') { rB = d.Rr + 0.36; rT = d.Rr + 0.44; }
  else if (DL === 'box') { rB = d.Rr + 0.18; rT = d.Rr + 0.15; }
  else if (DL === 'mpv') { rB = d.Rr + 0.30; rT = d.Rr + 0.24; }
  else if (DL === 'sedan') { rB = xr - 0.13; rT = xr + 0.2; }
  else if (DL === 'fast') { rB = xr - 0.16; rT = xr + 0.14; }
  else if (DL === 'scoupe') { rB = xr + 0.10; rT = xr + 0.38; }
  else if (DL === 'coupe') { rB = xr + 0.12; rT = xr + 0.42; }
  else if (DL === 'road') { rB = d.xH - 0.85; rT = d.xH - 0.55; }
  // window area polygon (outer = frame incl. trim)
  const outerTop = [], outerBot = [];
  for (let x = rB - 0.02; x <= xF + 0.02; x += step) {
    const yT = topEdge(x) + 0.014, yB = botEdge(x) - 0.012;
    if (yT > yB + 0.01) { outerTop.push([x, yT]); outerBot.push([x, yB]); }
  }
  const rearEdge = y => { const yb = botEdge(rB), yt = topEdge(rT); const t = clamp((y - yb) / Math.max(0.05, yt - yb), 0, 1); return lerp(rB, rT, t); };
  const inside = (x, y) => y > botEdge(x) && y < topEdge(x) && x > rearEdge(y) && x < xF;
  if (outerTop.length > 4) {
    // clip outer polygon at the slanted rear edge
    const outer = [];
    const yb0 = botEdge(rB) - 0.012, yt0 = topEdge(rT) + 0.014;
    outer.push([rB - 0.016, yb0]);
    for (const p of outerBot) if (p[0] > rB - 0.016) outer.push(p);
    for (let i = outerTop.length - 1; i >= 0; i--) if (outerTop[i][0] > rT - 0.016) outer.push(outerTop[i]);
    outer.push([rT - 0.016, yt0]);
    // glass: sample a mask boundary along x
    const glass = [];
    const gl = [], gu = [];
    for (let x = rB; x <= xF; x += step) {
      const yB = botEdge(x), yT = topEdge(x);
      if (yT <= yB + 0.006) continue;
      const xe0 = rearEdge(yB), xe1 = rearEdge(yT);
      if (x < Math.min(xe0, xe1)) continue;
      gl.push([x, yB]); gu.push([x, x >= xe1 ? yT : lerp(yB, yT, clamp((x - xe0) / Math.max(1e-3, xe1 - xe0), 0, 1))]);
    }
    if (gl.length) glass.push([[rB, botEdge(rB)], ...gl, ...gu.reverse(), [rT, topEdge(rT)]]);
    // pillars (bands across the glass)
    const band = (xc, w, slant = 0) => {
      const yb = botEdge(xc) - 0.013, yt = topEdge(xc) + 0.013;
      return [[xc - w / 2, yb], [xc + w / 2, yb], [xc + w / 2 + slant, yt], [xc - w / 2 + slant, yt]];
    };
    const span = xF - rB;
    if (st.doors === 4) {
      let xBp = rB + span * (DL === 'sedan' || DL === 'fast' ? 0.47 : DL === 'city' ? 0.43 : 0.5);
      if (DL === 'wagon' || DL === 'suv' || DL === 'box' || DL === 'mpv' || DL === 'city') xBp = (d.xr + d.xf) / 2 + 0.06;
      pillars.push(band(xBp, 0.075, -0.012));
      g.xB = xBp;
      if (DL === 'wagon' || DL === 'suv' || DL === 'box' || DL === 'mpv' || DL === 'city') {
        const xCp = d.xr + (DL === 'mpv' ? 0.15 : DL === 'city' ? 0.12 : 0.32);
        pillars.push(band(xCp, DL === 'box' ? 0.07 : 0.05, 0.03));
        g.xCq = xCp;
      }
    } else if (DL !== 'road') {
      const xQ = rB + span * 0.28;
      pillars.push(band(xQ, 0.04, 0.03));
      g.xB = xQ;
    }
    g.dlo = { outer, glass, pillars };
    const modernFloat = !old && !g.tt && /cross|suvcoupe|hatch|city/.test(d.style) && hash01(sp.id, 23) > 0.62;
    if (modernFloat || sp.blackD) {
      const xe = d.st.rear === 'hatch' || d.st.rear === 'box' ? d.Rr + 0.02 : rB - 0.3;
      const pts2 = [];
      for (let x = Math.min(rB, rT) - 0.01; x >= xe; x -= 0.01) { const yb2 = botEdge(x) - 0.012, yt2 = topEdge(x) + 0.014; if (yt2 > yb2 + 0.02) pts2.push([x, yb2, yt2]); }
      if (pts2.length > 2) g.dPillar = [[rB, botEdge(rB) - 0.012], ...pts2.map(p => [p[0], p[1]]), ...pts2.slice().reverse().map(p => [p[0], p[2]]), [rT, topEdge(rT) + 0.014]];
    }
    // two-tone roof: black band above the windows in side view
    if (g.tt) {
      const tp = [];
      for (let x = rT - 0.06; x <= xF + 0.05; x += step) tp.push([x, topEdge(x) + 0.012]);
      const yR = x => s(x).yt + 0.05;
      g.ttSidePath = poly2([...tp, ...tp.slice().reverse().map(p => [p[0], yR(p[0])])]);
    }
  }
  // --- doors ---
  const ybAt = x => d.ybBase(x);
  const yBeltAt = x => s(x).ys;
  const archLine = (xa, r, a0, a1) => { const pts = []; for (let a = a0; a <= a1 + 1e-6; a += (a1 - a0) / 18) pts.push([xa + r * Math.cos(a), d.R + r * Math.sin(a)]); return pts; };
  const xFD = Math.min(xF + 0.02, d.xf - Ra - 0.07);
  const fdTop = yBeltAt(xFD);
  if (DL !== 'road' || true) {
    g.seams.push([[d.xf - Ra - 0.08, ybAt(d.xf - Ra - 0.08) + 0.05], [xFD - 0.01, fdTop - 0.05], [xFD + 0.01, fdTop + 0.002]]);
  }
  if (st.doors === 4 && g.xB != null) {
    const xb = g.xB + 0.005;
    g.seams.push([[xb, ybAt(xb) + 0.035], [xb + 0.008, yBeltAt(xb) + 0.01]]);
    // rear door rear edge: down from the belt, around the rear arch
    const xrd = (g.xCq != null ? g.xCq + 0.02 : Math.max(rB + 0.04, d.xr + Ra * 0.45));
    const yA = d.R + Math.sqrt(Math.max(0, (Ra + 0.035) ** 2 - (xrd - d.xr) ** 2));
    const pts = [[xrd, yBeltAt(xrd) + 0.005], [xrd, Math.max(yA, d.R + 0.05)]];
    const aStart = Math.acos(clamp((xrd - d.xr) / (Ra + 0.035), -1, 1));
    if (xrd < d.xr + Ra + 0.035) for (let a = aStart; a >= 0.15; a -= 0.08) pts.push([d.xr + (Ra + 0.035) * Math.cos(a), d.R + (Ra + 0.035) * Math.sin(a)]);
    g.seams.push(pts);
    // handles
    const hy = yBeltAt(g.xB) - 0.065;
    g.handles.push([g.xB + 0.14, hy, 0.19]);
    g.handles.push([xrd + 0.12, yBeltAt(xrd + 0.12) - 0.065, 0.18]);
    g.fuel = [Math.min(xrd - 0.25, d.xr - 0.05), Math.max(d.R + Ra + 0.06, yBeltAt(d.xr) - 0.2)];
    if (g.xCq == null && g.fuel[0] < d.xr - Ra + 0.02) g.fuel[0] = d.xr - 0.1;
  } else {
    const xd = Math.max(rB + 0.02, d.xr + Ra + 0.12);
    g.seams.push([[xd, yBeltAt(xd) + 0.005], [xd + 0.01, ybAt(xd) + 0.04]]);
    g.handles.push([xd + 0.10, yBeltAt(xd) - 0.065, 0.17]);
    g.fuel = [d.xr - 0.05, Math.max(d.R + Ra + 0.06, yBeltAt(d.xr) - 0.2)];
  }
  if (g.handleMat === 'flush') { g.handles = g.handles.map(h => [h[0], h[1], h[2] * 0.9]); g.handleMat = 'paint'; }

  // --- windshield, roof, rear window in top view ---
  const wsTop = [], wsOuter = [];
  const pw = 0.05; // pillar width on the top surface
  const zEdge = x => { const i = s(x); return Math.max(0.03, i.hwr - i.rr * 0.6); };
  const zAt = (x, y) => { // centre-line crown solve: z where the crown height drops to y
    const i = s(x); const zE = Math.max(0.03, i.hwr - i.rr); const c = i.yt - i.ye;
    if (y >= i.yt) return 0; if (y <= i.ye || c < 1e-4) return zE;
    return zE * Math.sqrt((i.yt - y) / c);
  };
  // windshield spans from header to the cowl; its lower edge is where the surface rises above the cowl
  const xWs0 = d.xH - 0.02, xWs1 = d.xC + 0.02;
  const wsL = [], wsR = [];
  for (let x = xWs0; x <= xWs1; x += 0.006) {
    const zb = Math.min(zEdge(x) - pw, zAt(x, d.yC + 0.012));
    if (zb > 0.02) { wsL.push([x, 0]); wsR.push([x, zb]); }
  }
  if (wsR.length > 3) {
    g.wsTop = [[wsR[0][0], 0], ...wsR, [wsR[wsR.length - 1][0], 0]];
    g.wsTopOuter = [[wsR[0][0] - 0.015, 0], ...wsR.map(p => [p[0], p[1] + 0.016]), [wsR[wsR.length - 1][0] + 0.012, 0]];
    // cowl panel just ahead of the glass
    const cw = wsR.map(p => [p[0] + 0.07 * (1 - sst(0.5, 1.0, p[1] / Math.max(0.1, zEdge(p[0])))), p[1]]);
    const xc0 = d.xC + 0.01;
    g.cowlTop = [[xc0, 0], [xc0 + 0.075, 0], [xc0 + 0.075, zEdge(d.xC) * 0.92], [xc0 - 0.05, zEdge(d.xC) * 0.92]];
  }
  // roof (two-tone)
  if (g.tt) {
    const rf = [];
    for (let x = d.xRE - 0.02; x <= d.xH + 0.02; x += 0.01) rf.push([x, zEdge(x) + 0.03]);
    g.roofTop = [[rf[0][0], 0], ...rf, [rf[rf.length - 1][0], 0]];
  }
  // rear window for sedans / fastbacks / roadster deck
  if (d.xRW != null) {
    const xa = d.xRW + 0.03, xb = d.xRE + 0.02;
    const rw = [];
    const yRef = d.st.rear === 'sedan' || d.st.rear === 'road' ? d.yDeck : d.yGB;
    for (let x = xa; x <= xb; x += 0.006) {
      const zb = Math.min(zEdge(x) - pw * 1.1, zAt(x, yRef + 0.02));
      if (zb > 0.02) rw.push([x, zb]);
    }
    if (rw.length > 3 && d.st.rear !== 'road') {
      g.rwTop = [[rw[0][0], 0], ...rw, [rw[rw.length - 1][0], 0]];
      g.rwTopOuter = [[rw[0][0] - 0.012, 0], ...rw.map(p => [p[0], p[1] + 0.016]), [rw[rw.length - 1][0] + 0.012, 0]];
    }
  }
  if (d.st.rear === 'road') {
    const rf = [];
    for (let x = d.xRW + 0.03; x <= d.xH - 0.02; x += 0.01) rf.push([x, zEdge(x) + 0.02]);
    g.softTop = [[rf[0][0], 0], ...rf, [rf[rf.length - 1][0], 0]];
  }
  // hood shut lines
  const xHood0 = d.xC + 0.085, xHood1 = d.xHE - 0.012;
  const zh = x => s(x).hwg - 0.01;
  const hl = []; for (let x = xHood0; x <= xHood1 - 0.05; x += 0.02) hl.push([x, Math.min(zh(x), zh(xHood0))]);
  if (hl.length > 2) {
    g.topSeams.push(hl);
    g.topSeams.push([[xHood0, 0], [xHood0, zh(xHood0)]]);
  }

  // --- front design ---
  frontDesign(d, g);
  rearDesign(d, g);
  return g;
}
function poly2(pts) { const p = new Path2D(); pts.forEach((q, i) => i ? p.lineTo(q[0], q[1]) : p.moveTo(q[0], q[1])); p.closePath(); return p; }

/* Brand families: generic lamp/grille archetypes so models of one make share a look.
   Deliberately generic shapes (no logos, no trademark grilles or lamp signatures). */
const DNA = {
  'Dacia': { lamp: 'block', drl: 'lower', grille: 'bars', fill: 'hbars', intake: 'trap', rim: ['std', 'double'] },
  'Kia': { lamp: 'slim', drl: 'hook', grille: 'slim', fill: 'mesh', intake: 'wide', rim: ['double', 'twist'] },
  'Hyundai': { lamp: 'split', drl: 'line', grille: 'large', fill: 'dots', intake: 'none', rim: ['twist', 'multi'] },
  'Toyota': { lamp: 'slim', drl: 'line', grille: 'slim', fill: 'hbars', intake: 'trap', rim: ['double', 'std'] },
  'Volvo': { lamp: 'block', drl: 'double', grille: 'mid', fill: 'vbars', intake: 'wide', chrome: 1, rim: ['multi', 'twist'] },
  'Tesla': { lamp: 'slim', drl: 'lower', grille: 'closed', intake: 'slim', rim: ['aero', 'twist'] },
  'Volkswagen': { lamp: 'slim', drl: 'line', grille: 'band', fill: 'hbars', intake: 'wide', rim: ['double', 'std'] },
  'Skoda': { lamp: 'block', drl: 'line', grille: 'mid', fill: 'vbars', intake: 'wide', chrome: 1, rim: ['twist', 'double'] },
  'Nissan': { lamp: 'slim', drl: 'hook', grille: 'mid', fill: 'hbars', intake: 'trap', chrome: 1, rim: ['double', 'std'] },
  'BMW': { lamp: 'slim', drl: 'double', grille: 'slim', fill: 'vbars', intake: 'three', rim: ['sport', 'double'] },
  'BYD': { lamp: 'slim', drl: 'dots', grille: 'closed', intake: 'wide', rim: ['aero', 'twist'] },
  'Audi': { lamp: 'slim', drl: 'dots', grille: 'large', fill: 'hex', intake: 'three', rim: ['multi', 'twist'] },
  'Ford': { lamp: 'block', drl: 'line', grille: 'mid', fill: 'mesh', intake: 'wide', rim: ['std', 'double'] },
  'Mercedes-Benz': { lamp: 'slim', drl: 'hook', grille: 'mid', fill: 'dots', intake: 'three', chrome: 1, rim: ['multi', 'twist'] },
  'Mazda': { lamp: 'slim', drl: 'line', grille: 'mid', fill: 'mesh', intake: 'slim', chrome: 1, rim: ['std', 'twist'] },
  'Renault': { lamp: 'block', drl: 'hook', grille: 'mid', fill: 'mesh', intake: 'wide', rim: ['twist', 'double'] },
  'Peugeot': { lamp: 'slim', drl: 'lower', grille: 'large', fill: 'dots', intake: 'none', rim: ['twist', 'double'] },
  'Lynk & Co': { lamp: 'split', drl: 'line', grille: 'band', fill: 'hbars', intake: 'wide', rim: ['multi', 'std'] },
  'Polestar': { lamp: 'slim', drl: 'double', grille: 'closed', intake: 'slim', rim: ['twist', 'aero'] },
  'Lexus': { lamp: 'slim', drl: 'hook', grille: 'large', fill: 'mesh', intake: 'none', chrome: 1, rim: ['multi', 'twist'] },
  'Porsche': { lamp: 'block', drl: 'dots', grille: 'none', intake: 'three', rim: ['sport', 'multi'] },
  'Land Rover': { lamp: 'slim', drl: 'line', grille: 'band', fill: 'mesh', intake: 'slim', rim: ['twist', 'multi'] },
  'Cupra': { lamp: 'slim', drl: 'dots', grille: 'large', fill: 'hex', intake: 'none', rim: ['sport', 'twist'] },
  'Mitsubishi': { lamp: 'slim', drl: 'line', grille: 'mid', fill: 'hbars', intake: 'trap', chrome: 1, rim: ['double', 'std'] },
  'MG': { lamp: 'slim', drl: 'line', grille: 'large', fill: 'dots', intake: 'none', rim: ['twist', 'double'] },
  'Subaru': { lamp: 'block', drl: 'hook', grille: 'mid', fill: 'hbars', intake: 'wide', chrome: 1, rim: ['std', 'double'] },
  'Saab': { lamp: 'block', drl: 'line', grille: 'mid', fill: 'hbars', intake: 'wide', chrome: 1, rim: ['multi', 'std'] },
  'Opel': { lamp: 'slim', drl: 'line', grille: 'band', fill: 'gloss', intake: 'wide', rim: ['double', 'std'] },
  'Fiat': { lamp: 'slim', drl: 'line', grille: 'slim', fill: 'hbars', intake: 'wide', rim: ['std', 'twist'] },
  'Seat': { lamp: 'slim', drl: 'hook', grille: 'large', fill: 'hex', intake: 'none', rim: ['double', 'sport'] },
  'Suzuki': { lamp: 'block', drl: 'line', grille: 'mid', fill: 'hbars', intake: 'trap', chrome: 1, rim: ['std', 'double'] },
  'Honda': { lamp: 'slim', drl: 'line', grille: 'slim', fill: 'mesh', intake: 'wide', rim: ['double', 'std'] },
  'Mini': { lamp: 'block', drl: 'lower', grille: 'bars', fill: 'gloss', intake: 'slim', rim: ['std', 'multi'] }
};
export function dnaFor(sp) {
  const base = DNA[sp.brand] || { lamp: 'slim', drl: 'line', grille: 'mid', fill: 'mesh', intake: 'wide', rim: ['std', 'double'] };
  const o = { ...base };
  const ev = !!sp.ev && !sp.old;
  if (sp.old) { o.lamp = 'old'; o.drl = 'none'; if (o.grille === 'large' || o.grille === 'band' || o.grille === 'closed') o.grille = 'mid'; if (o.intake === 'none') o.intake = 'wide'; o.chrome = 1; }
  if (ev && o.grille !== 'none') { o.grille = 'closed'; if (o.intake === 'none') o.intake = 'slim'; }
  if ((sp.sp || sp.style === 'coupe' || sp.style === 'roadster') && !/suv|cross/.test(sp.style)) { if (o.grille === 'mid' || o.grille === 'bars') o.grille = 'slim'; o.intake = o.intake === 'none' ? 'none' : 'three'; }
  return o;
}

/* Front: lamps, grille, intakes painted into the front view (z >= 0 half, y up). */
function frontDesign(d, g) {
  const sp = d.spec, D = d.dna;
  const old = !!sp.old, suv = d.suvish, lux = !!sp.lux || !!D.chrome;
  const hwF = d.hw - d.st.fr[1];
  const yHE = d.yHE, yN = d.yN, fb = d.st.fb;
  const pick = hash01(sp.id, 3), pick2 = hash01(sp.id, 9), pick3 = hash01(sp.id, 13);
  const F = g.front, push = o => F.push(o);
  const zOut = d.hw + 0.06;
  const upH = yHE - yN, loH = yN - fb;
  const mirrorPts = half => half.concat(half.slice(1, half.length - 1).reverse().map(([z, y]) => [-z, y]));
  // ---- headlamps ----
  const L = D.lamp;
  let lh = L === 'old' ? Math.min(0.15, upH * 0.62) : L === 'block' ? Math.min(upH * 0.6, 0.105 + pick * 0.03) : L === 'split' ? 0.03 : Math.min(upH * 0.55, (suv ? 0.088 : 0.074) + pick * 0.022);
  const yL1 = yHE - (L === 'old' ? 0.03 : 0.022), yL0 = yL1 - lh;
  const zIn = hwF * (L === 'old' ? 0.5 : L === 'block' ? 0.5 + pick2 * 0.1 : 0.4 + pick2 * 0.14);
  const N = 16, lamp = [];
  const taper = L === 'slim' || L === 'split' ? 0.42 : 0.12;
  for (let i = 0; i <= N; i++) { const u = i / N; lamp.push([lerp(zIn, zOut, u), yL1 - (L === 'slim' ? 0.012 : 0.004) * (1 - u)]); }
  for (let i = N; i >= 0; i--) { const u = i / N; lamp.push([lerp(zIn, zOut, u), yL0 + lh * taper * Math.pow(1 - u, 1.6)]); }
  const lampR = roundPoly(lamp, 2);
  push({ pts: lampR, m: L === 'split' ? 'lampIn' : 'lamp' });
  const drlW = 0.011;
  const drlLine = (yOff, z0 = zIn + 0.012) => { const o = []; for (let i = 0; i <= N; i++) { const u = i / N; o.push([lerp(z0, zOut, u), yL1 - yOff - (L === 'slim' ? 0.011 : 0.003) * (1 - u)]); } return o; };
  if (L !== 'split') {
    push({ pts: roundPoly(lamp.map(([z, y]) => [Math.max(z, zIn + 0.012), lerp(y, (yL0 + yL1) / 2, 0.2)]), 2), m: 'lampIn' });
    const nP = L === 'old' ? 1 : L === 'block' ? 3 : 2;
    for (let k = 0; k < nP; k++) {
      const u = nP === 1 ? 0.48 : nP === 3 ? 0.25 + k * 0.22 : 0.3 + k * 0.28;
      const zc = lerp(zIn, Math.min(zOut, d.hw), u), yc = (yL0 + yL1) / 2 + (L === 'block' ? lh * 0.08 : -0.004 + (1 - u) * 0.006);
      const r = L === 'old' ? lh * 0.3 : L === 'block' ? lh * 0.19 : lh * 0.25;
      push({ circle: [zc, yc, r], m: 'chrome' });
      push({ circle: [zc, yc, r * 0.62], m: 'lens' });
      push({ circle: [zc - r * 0.2, yc + r * 0.22, r * 0.16], m: 'drl', a: 0.8 });
    }
  }
  const DR = D.drl;
  if (L === 'old') push({ pts: [[zOut - 0.07, yL0 + 0.012], [zOut, yL0 + 0.012], [zOut, yL1 - 0.012], [zOut - 0.07, yL1 - 0.012]], m: 'amber', a: 0.85 });
  else if (L === 'split') {
    push({ stroke: true, pts: drlLine(0.012, zIn), w: 0.016, col: '#f4f8ff', m: 'drl', em: true });
    // main lamp lower in the bumper
    const my1 = yN + Math.min(0.1, upH * 0.35), my0 = my1 - 0.085, mz0 = hwF * 0.6, mz1 = Math.min(zOut, d.hw - 0.02);
    push({ pts: roundPoly([[mz0, my0 + 0.01], [mz1, my0], [mz1, my1], [mz0, my1 - 0.004]], 2), m: 'lamp' });
    push({ pts: roundPoly([[mz0 + 0.01, my0 + 0.018], [mz1, my0 + 0.01], [mz1, my1 - 0.01], [mz0 + 0.01, my1 - 0.012]], 2), m: 'lampIn' });
    for (let k = 0; k < 2; k++) { const zc = lerp(mz0 + 0.04, mz1 - 0.06, k); push({ circle: [zc, (my0 + my1) / 2, 0.024], m: 'chrome' }); push({ circle: [zc, (my0 + my1) / 2, 0.015], m: 'lens' }); }
  } else if (DR === 'line' || DR === 'hook' || DR === 'double') {
    push({ stroke: true, pts: drlLine(0.013), w: drlW, col: '#f4f8ff', m: 'drl', em: true });
    if (DR === 'double') push({ stroke: true, pts: drlLine(lh * 0.45), w: drlW * 0.8, col: '#f4f8ff', m: 'drl', em: true });
    if (DR === 'hook') push({ stroke: true, pts: [[zIn + 0.016, yL1 - 0.026], [zIn + 0.02, yL0 + lh * 0.42]], w: drlW, col: '#f4f8ff', m: 'drl', em: true });
  } else if (DR === 'lower') {
    const o = []; for (let i = 0; i <= N; i++) { const u = i / N; o.push([lerp(zIn + 0.03, zOut, u), yL0 + lh * taper * Math.pow(1 - u, 1.6) + 0.012]); }
    push({ stroke: true, pts: o, w: drlW, col: '#f4f8ff', m: 'drl', em: true });
  } else if (DR === 'dots') {
    for (let k = 0; k < 4; k++) { const z = lerp(zIn + 0.05, d.hw - 0.04, k / 3); push({ stroke: true, pts: [[z - 0.014, yL0 + lh * 0.2], [z + 0.014, yL0 + lh * 0.2]], w: 0.012, col: '#f4f8ff', m: 'drl', em: true }); }
  }
  if (d.ev && (pick > 0.5 || D.grille === 'closed' && pick > 0.3)) push({ stroke: true, pts: [[-0.05, yL1 - 0.015], [zIn + 0.02, yL1 - 0.015]], w: 0.009, col: '#f4f8ff', m: 'drl', em: true });

  // ---- upper grille ----
  const G = D.grille, fillP = D.fill || 'mesh';
  const frameM = lux ? 'chrome' : 'gloss';
  g.gStyle = G;
  const pattern = (clip, z0, z1, y0, y1) => {
    if (fillP === 'hbars') for (let y = y0 + 0.014; y < y1 - 0.004; y += 0.022) push({ stroke: true, pts: [[-0.05, y], [z1 + 0.03, y]], w: 0.0065, col: lux ? '#a0a6ac' : '#34383c', m: lux ? 'chrome' : 'grilleLine', clip });
    else if (fillP === 'vbars') for (let z = 0.012; z < z1 + 0.03; z += 0.03) push({ stroke: true, pts: [[z, y0 - 0.02], [z, y1 + 0.02]], w: 0.008, col: lux ? '#a0a6ac' : '#34383c', m: lux ? 'chrome' : 'grilleLine', clip });
    else if (fillP === 'dots') for (let z = 0.0; z < z1 + 0.03; z += 0.026) for (let y = y0; y < y1 + 0.02; y += 0.026) push({ circle: [z + ((Math.round((y - y0) / 0.026) % 2) ? 0.013 : 0), y, 0.0068], m: 'grilleDot', clip });
    else if (fillP === 'hex') for (let z = -0.04; z < z1 + 0.03; z += 0.036) for (let y = y0 - 0.02; y < y1 + 0.02; y += 0.031) { const zz = z + ((Math.round((y - y0) / 0.031) % 2) ? 0.018 : 0); push({ stroke: true, close: true, pts: [0, 1, 2, 3, 4, 5].map(k => [zz + 0.013 * Math.cos(k * Math.PI / 3), y + 0.013 * Math.sin(k * Math.PI / 3)]), w: 0.0045, col: '#5b6066', m: 'grilleLine', clip }); }
    else if (fillP === 'mesh') for (let z = -0.05; z < z1 + 0.03; z += 0.028) for (let y = y0 - 0.02; y < y1 + 0.02; y += 0.028) push({ stroke: true, pts: [[z, y], [z + 0.014, y + 0.014], [z + 0.028, y]], w: 0.005, col: '#4f5459', m: 'grilleLine', clip });
  };
  let gBotUsed = yN;
  if (G === 'closed') {
    push({ pts: roundPoly(mirrorPts([[0, yL0 + lh * 0.3], [zIn - 0.04, yL0 + lh * 0.3], [zIn - 0.06, yL0 + lh * 0.12], [0, yL0 + lh * 0.12]]), 1), m: 'gloss', a: 0.85 });
  } else if (G === 'band') {
    const bTop = yL1 + 0.002, bBot = Math.max(yL0 - 0.01, yN + upH * 0.25);
    const band = roundPoly(mirrorPts([[0, bTop], [zIn + 0.03, bTop], [zIn + 0.03, bBot], [0, bBot]]), 1);
    push({ pts: band, m: 'gloss' });
    if (fillP !== 'gloss') pattern(band, 0, zIn, bBot, bTop);
    gBotUsed = bBot;
  } else if (G !== 'none') {
    const gTop = yL1 - 0.004;
    let gBot, wTop, wBot;
    const gW = Math.max(zIn - 0.012, hwF * 0.5);
    if (G === 'slim') { gBot = yL0 + lh * 0.22; wTop = gW; wBot = gW - 0.01; }
    else if (G === 'large') { gBot = fb + loH * (suv ? 0.62 : 0.5); wTop = gW * 0.95; wBot = Math.min(hwF * 0.86, gW * 1.18); }
    else { gBot = Math.max(yN + upH * 0.06, yL0 - (suv ? 0.12 : 0.07)); wTop = gW; wBot = gW - 0.04; }
    const half = [[0, gTop], [wTop, gTop], [Math.max(wTop, wBot) + 0.004, lerp(gTop, gBot, 0.5)], [wBot, gBot], [0, gBot]];
    const gp = roundPoly(mirrorPts(half), 1);
    const yc = (gTop + gBot) / 2;
    push({ pts: gp.map(([z, y]) => [z * 1.035 + Math.sign(z) * 0.004, (y - yc) * 1.08 + yc]), m: frameM });
    push({ pts: gp, m: 'grille' });
    if (fillP !== 'gloss') pattern(gp, 0, Math.max(wTop, wBot), gBot, gTop);
    if (G === 'bars') for (let k = 1; k <= 2; k++) { const y = lerp(gBot, gTop, k / 3); push({ stroke: true, pts: [[-0.05, y], [wTop + 0.02, y]], w: 0.014, col: lux ? '#c9ced3' : '#26292c', m: lux ? 'chrome' : 'gloss', clip: gp }); }
    gBotUsed = gBot;
  }
  // ---- lower bumper ----
  const I = D.intake;
  if (I !== 'none' || G !== 'large') {
    const iTop = Math.min(gBotUsed - 0.05, fb + loH * (I === 'slim' ? 0.32 : G === 'slim' || G === 'closed' || G === 'band' ? 0.7 : 0.56)), iBot = fb + Math.min(0.045, loH * 0.18);
    const iW = hwF * (I === 'three' ? 0.42 : I === 'slim' ? 0.55 : 0.66);
    let half;
    if (I === 'trap') half = [[0, iTop], [iW * 0.8, iTop], [iW + 0.03, iBot], [0, iBot]];
    else half = [[0, iTop], [iW - 0.03, iTop], [iW + 0.04, iBot + (iTop - iBot) * 0.35], [iW, iBot], [0, iBot]];
    if (iTop > iBot + 0.03) {
      const lowI = roundPoly(mirrorPts(half), 1);
      const lyc = (iTop + iBot) / 2;
      push({ pts: lowI.map(([z, y]) => [z * 1.03 + Math.sign(z) * 0.006, (y - lyc) * 1.12 + lyc]), m: 'gloss' });
      push({ pts: lowI, m: 'grille' });
      for (let z = -0.05; z < iW + 0.06; z += 0.03) for (let y = iBot - 0.02; y < iTop + 0.02; y += 0.03) push({ stroke: true, pts: [[z, y], [z + 0.015, y + 0.015], [z + 0.03, y]], w: 0.0055, col: '#34383c', m: 'grilleLine', clip: lowI });
      if (pick3 > 0.5 && !old && I !== 'slim') push({ stroke: true, pts: [[-0.05, iTop - (iTop - iBot) * 0.4], [iW, iTop - (iTop - iBot) * 0.4]], w: 0.012, col: lux ? '#c9ced3' : '#202326', m: lux ? 'chrome' : 'gloss' });
    }
  }
  // side intakes / fog lamps
  const cz = Math.min(hwF * 0.9, hwF * 0.66 + 0.13), cy = fb + loH * 0.42;
  if (old) { push({ circle: [cz, cy, 0.042], m: 'chrome' }); push({ circle: [cz, cy, 0.032], m: 'lamp' }); }
  else if (I === 'three') push({ pts: roundPoly([[hwF * 0.5, fb + 0.04], [hwF * 0.96, fb + 0.05], [hwF * 0.98, fb + loH * 0.75], [hwF * 0.56, fb + loH * 0.68]], 2), m: 'grille' });
  else { const vp = roundPoly([[cz - 0.025, cy - loH * 0.2], [cz + 0.045, cy - loH * 0.22], [cz + 0.06, cy + loH * 0.2], [cz - 0.01, cy + loH * 0.18]], 2); push({ pts: vp.map(([z, y]) => [z + (z - cz) * 0.15, cy + (y - cy) * 1.1]), m: lux ? 'chrome' : 'gloss' }); push({ pts: vp, m: 'grille' }); }
  push({ pts: [[-0.05, 0], [zOut, 0], [zOut, fb + 0.022], [-0.05, fb + 0.022]], m: 'matte' });
  if (suv) push({ pts: mirrorPts([[0, fb + 0.004], [hwF * 0.4, fb + 0.004], [hwF * 0.36, fb + 0.034], [0, fb + 0.034]]), m: 'alu' });
  push({ stroke: true, pts: [[-0.05, yHE - 0.004], [hwF * 0.6, yHE - 0.006], [d.hw, yHE - 0.012]], w: 0.004, col: '#000', a: 0.45 });

  // ---- side wrap of the headlamp (side view) ----
  const xs0 = d.F - d.st.fr[0] * 0.78 - (old ? 0.06 : 0.14);
  if (L === 'split') {
    g.sideLamps.push({ pts: [[d.F + 0.05, yL1 - 0.02], [xs0 + 0.04, yL1 - 0.017], [xs0 + 0.02, yL1 - 0.004], [d.F + 0.05, yL1 - 0.002]], m: 'drl' });
  } else {
    const wrap = [[d.F + 0.05, yL0 - 0.004], [xs0 + 0.08, yL0 + lh * 0.12], [xs0, yL0 + lh * 0.62], [xs0 + 0.02, yL1 - 0.004], [d.F + 0.05, yL1]];
    g.sideLamps.push({ pts: roundPoly(wrap, 2), m: 'lamp' });
    g.sideLamps.push({ pts: roundPoly(wrap.map(([x, y]) => [Math.min(x, d.F + 0.05) + 0.01, lerp(y, (yL0 + yL1) / 2, 0.25)]), 2), m: 'lampIn' });
    if (!old && DR !== 'none') g.sideLamps.push({ pts: [[d.F + 0.05, yL1 - 0.018], [xs0 + 0.05, yL1 - 0.014], [xs0 + 0.04, yL1 - 0.005], [d.F + 0.05, yL1 - 0.007]], m: 'drl' });
    else if (old) g.sideLamps.push({ pts: [[xs0 + 0.01, yL0 + 0.01], [xs0 + 0.07, yL0 + 0.01], [xs0 + 0.07, yL1 - 0.01], [xs0 + 0.03, yL1 - 0.01]], m: 'amber' });
  }
  g.sideLamps.push({ pts: [[d.F + 0.05, fb + 0.02], [d.F - 0.12, fb + 0.02], [d.F - 0.16, fb + loH * 0.25], [d.F + 0.05, fb + loH * 0.3]], m: 'grille' });
  g.lampBand = [yL0, yL1];
}
function rearDesign(d, g) {
  const sp = d.spec, old = !!sp.old;
  const hwR = d.hw - d.st.rc[1];
  const pick = hash01(sp.id, 5);
  const sedanLike = /sedan|fast|road/.test(d.st.rear) || d.style === 'coupe';
  const yT1 = sedanLike ? (d.yDeck ?? d.yGB ?? d.H * 0.7) - 0.02 : (d.yGB ?? d.H * 0.7) - 0.01;
  const th = old ? 0.13 : 0.08 + pick * 0.03;
  const yT0 = yT1 - th;
  const zIn = hwR * (pick > 0.5 ? 0.35 : 0.6);
  g.rear.push({ pts: [[zIn, yT0 + 0.01], [d.hw + 0.05, yT0 - 0.01], [d.hw + 0.05, yT1 + 0.01], [zIn, yT1]], m: 'tail' });
  g.rear.push({ pts: [[zIn + 0.03, yT1 - 0.03], [d.hw + 0.05, yT1 - 0.025], [d.hw + 0.05, yT1 - 0.012], [zIn + 0.03, yT1 - 0.018]], m: 'tailLed' });
  if (pick > 0.6 && !old) g.rear.push({ pts: [[0, yT1 - 0.03], [zIn, yT1 - 0.03], [zIn, yT1 - 0.018], [0, yT1 - 0.018]], m: 'tailLed' });
  g.rear.push({ pts: [[0, 0], [d.hw + 0.05, 0], [d.hw + 0.05, d.st.rb + 0.05], [0, d.st.rb + 0.05]], m: 'matte' });
  // side wrap of tail lamps
  const xs1 = d.Rr + d.st.rc[0] * 0.8 + 0.1;
  g.sideLamps.push({ pts: roundPoly([[d.Rr - 0.05, yT0 - 0.01], [xs1 - 0.04, yT0 + 0.012], [xs1, yT1 - 0.012], [d.Rr - 0.05, yT1 + 0.01]], 2), m: 'tail' });
  g.sideLamps.push({ pts: [[d.Rr - 0.05, yT1 - 0.028], [xs1 - 0.03, yT1 - 0.024], [xs1 - 0.022, yT1 - 0.014], [d.Rr - 0.05, yT1 - 0.016]], m: 'tailLed' });
  // rear window seen from behind (hatch / wagon / suv)
  if (d.yGB != null && !sedanLike) {
    const s = x => secInfo(d, x);
    const pts = [];
    for (let x = d.Rr + 0.004; x <= d.xRE; x += 0.004) {
      const i = s(x); if (i.yt < d.yGB + 0.03 || i.yt > d.H - 0.045) continue;
      pts.push([Math.max(0.05, i.hwr - 0.13), i.yt]);
    }
    if (pts.length > 2) {
      g.rwRear = [[0, pts[0][1]], ...pts, [0, pts[pts.length - 1][1]]];
      g.rwRearOuter = [[0, pts[0][1] - 0.02], ...pts.map(p => [p[0] + 0.025, p[1]]), [0, pts[pts.length - 1][1] + 0.02]];
    }
  }
}

/* ---------- triplanar body material ---------- */
export function bodyMaterial(THREE, views) {
  const tex = (c, srgb) => { const t = new THREE.CanvasTexture(c); t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace; t.anisotropy = 8; t.generateMipmaps = true; t.minFilter = THREE.LinearMipmapLinearFilter; t.needsUpdate = true; return t; };
  const tA = tex(views.C.alb, true), tO = tex(views.C.orm, false), tE = tex(views.C.emi, true);
  const m = new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 1, metalness: 1, clearcoat: 1, clearcoatRoughness: 0.035, envMapIntensity: 1 });
  const V = views.maps;
  m.onBeforeCompile = sh => {
    sh.uniforms.uAlb = { value: tA }; sh.uniforms.uOrm = { value: tO }; sh.uniforms.uEmi = { value: tE };
    sh.uniforms.uSide = { value: new THREE.Vector4(...V.side) }; sh.uniforms.uTop = { value: new THREE.Vector4(...V.top) };
    sh.uniforms.uFront = { value: new THREE.Vector4(...V.front) }; sh.uniforms.uRear = { value: new THREE.Vector4(...V.rear) };
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vOP;\nvarying vec3 vON;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvOP = position;\nvON = normal;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', `#include <common>
varying vec3 vOP; varying vec3 vON;
uniform sampler2D uAlb; uniform sampler2D uOrm; uniform sampler2D uEmi;
uniform vec4 uSide; uniform vec4 uTop; uniform vec4 uFront; uniform vec4 uRear;
void tri(in vec2 uv, in float w, inout vec4 a, inout vec4 o, inout vec4 e){ a += texture2D(uAlb, uv)*w; o += texture2D(uOrm, uv)*w; e += texture2D(uEmi, uv)*w; }
`).replace('#include <map_fragment>', `
vec3 nO = normalize(vON);
vec3 an = abs(nO);
float wS = pow(an.z, 6.0);
float wT = nO.y > 0.0 ? pow(an.y, 6.0) : 0.0;
float wB = nO.y < 0.0 ? pow(an.y, 6.0) : 0.0;
float wF = nO.x > 0.0 ? pow(an.x, 6.0) : 0.0;
float wR = nO.x < 0.0 ? pow(an.x, 6.0) : 0.0;
float ws = wS + wT + wB + wF + wR + 1e-5;
vec4 tA = vec4(0.0); vec4 tO = vec4(0.0); vec4 tE = vec4(0.0);
float az = abs(vOP.z);
tri(vec2(uSide.x*vOP.x + uSide.y, uSide.z*vOP.y + uSide.w), wS/ws, tA, tO, tE);
tri(vec2(uTop.x*vOP.x + uTop.y, uTop.z*az + uTop.w), wT/ws, tA, tO, tE);
tri(vec2(uFront.x*az + uFront.y, uFront.z*vOP.y + uFront.w), wF/ws, tA, tO, tE);
tri(vec2(uRear.x*az + uRear.y, uRear.z*vOP.y + uRear.w), wR/ws, tA, tO, tE);
float wb = wB/ws;
tA += vec4(0.006,0.0065,0.007,1.0)*wb; tO += vec4(0.0,0.9,0.0,1.0)*wb;
diffuseColor.rgb *= tA.rgb;
`).replace('#include <roughnessmap_fragment>', 'float roughnessFactor = clamp(tO.g, 0.02, 1.0);')
      .replace('#include <metalnessmap_fragment>', 'float metalnessFactor = tO.b;')
      .replace('#include <emissivemap_fragment>', 'totalEmissiveRadiance += tE.rgb * 1.6;')
      .replace('#include <lights_physical_fragment>', '#include <lights_physical_fragment>\n#ifdef USE_CLEARCOAT\nmaterial.clearcoat *= tO.r;\n#endif');
  };
  m.userData.textures = [tA, tO, tE];
  return m;
}

/* ---------- wheels ---------- */
function roundPoly(pts, it = 2) {
  let p = pts;
  for (let k = 0; k < it; k++) {
    const q = [];
    for (let i = 0; i < p.length; i++) { const a = p[i], b = p[(i + 1) % p.length]; q.push([a[0] * 0.75 + b[0] * 0.25, a[1] * 0.75 + b[1] * 0.25], [a[0] * 0.25 + b[0] * 0.75, a[1] * 0.25 + b[1] * 0.75]); }
    p = q;
  }
  return p;
}
function spokeHoles(rIn, rOut, n, wIn, wOut, phase = 0, pairGap = 0, twist = 0) {
  // holes between spokes; spoke width given in metres at hub and rim
  const holes = [];
  const centers = [];
  for (let i = 0; i < n; i++) {
    const a = phase + i * 2 * Math.PI / n;
    if (pairGap) { centers.push(a - pairGap / 2, a + pairGap / 2); } else centers.push(a);
  }
  centers.sort((a, b) => a - b);
  const m = centers.length;
  for (let i = 0; i < m; i++) {
    const a0 = centers[i], a1 = i + 1 < m ? centers[i + 1] : centers[0] + 2 * Math.PI;
    const inner = pairGap && (i % 2 === 0); // gap inside a pair
    const r0 = inner ? lerp(rIn, rOut, 0.45) : rIn;
    const pts = [];
    const N = 10;
    for (let k = 0; k <= N; k++) { const r = lerp(r0, rOut, k / N), w = lerp(wIn, wOut, (r - rIn) / (rOut - rIn)); pts.push([r, a0 + Math.asin(Math.min(0.95, w / 2 / r))]); }
    const aOut0 = pts[pts.length - 1][1];
    const back = [];
    for (let k = N; k >= 0; k--) { const r = lerp(r0, rOut, k / N), w = lerp(wIn, wOut, (r - rIn) / (rOut - rIn)); back.push([r, a1 - Math.asin(Math.min(0.95, w / 2 / r))]); }
    const aOut1 = back[0][1];
    if (aOut1 - aOut0 < 0.02) continue;
    const poly = [];
    const tw = r => twist * (r - rIn) / (rOut - rIn);
    pts.forEach(([r, a]) => poly.push([r * Math.cos(a + tw(r)), r * Math.sin(a + tw(r))]));
    for (let k = 1; k < 8; k++) { const a = lerp(aOut0, aOut1, k / 8) + tw(rOut); poly.push([rOut * Math.cos(a), rOut * Math.sin(a)]); }
    back.forEach(([r, a]) => poly.push([r * Math.cos(a + tw(r)), r * Math.sin(a + tw(r))]));
    const aIn0 = pts[0][1], aIn1 = back[back.length - 1][1];
    for (let k = 7; k >= 1; k--) { const a = lerp(aIn0, aIn1, k / 8) + tw(r0); poly.push([r0 * Math.cos(a), r0 * Math.sin(a)]); }
    holes.push(roundPoly(poly, 2));
  }
  return holes;
}
export function buildWheel(THREE, d, opts) {
  const { R, rimR, tw } = d;
  const grp = new THREE.Group();
  const sp = d.spec;
  // tyre
  const rin = rimR + 0.012, s = R - rin;
  const prof = [[rin, -0.41], [rin + 0.18 * s, -0.47], [rin + 0.55 * s, -0.5], [R - 0.035, -0.485], [R - 0.012, -0.455], [R - 0.002, -0.4], [R, -0.32], [R, 0.32], [R - 0.002, 0.4], [R - 0.012, 0.455], [R - 0.035, 0.485], [rin + 0.55 * s, 0.5], [rin + 0.18 * s, 0.47], [rin, 0.41]]
    .map(([r, w]) => new THREE.Vector2(r, w * tw));
  const tg = new THREE.LatheGeometry(prof, 96); tg.rotateX(Math.PI / 2);
  const tyre = new THREE.Mesh(tg, opts.mat.tyre); grp.add(tyre);
  // inner barrel and back plate
  const bg = new THREE.CylinderGeometry(rimR, rimR, tw * 0.82, 64, 1, true); bg.rotateX(Math.PI / 2);
  grp.add(new THREE.Mesh(bg, opts.mat.barrel));
  const bp = new THREE.CircleGeometry(rimR, 48); bp.translate(0, 0, -tw * 0.38);
  grp.add(new THREE.Mesh(bp, opts.mat.dark));
  // brake disc + caliper
  const rD = Math.min(0.19, rimR * 0.8);
  const dg = new THREE.CylinderGeometry(rD, rD, 0.026, 64); dg.rotateX(Math.PI / 2); dg.translate(0, 0, -0.02);
  grp.add(new THREE.Mesh(dg, opts.mat.disc));
  const hat = new THREE.CylinderGeometry(rD * 0.45, rD * 0.45, 0.04, 32); hat.rotateX(Math.PI / 2); hat.translate(0, 0, -0.005);
  grp.add(new THREE.Mesh(hat, opts.mat.barrel));
  const cal = new THREE.TorusGeometry(rD - 0.03, 0.032, 10, 16, 0.75); cal.scale(1, 1, 0.9); cal.rotateZ(Math.PI * 0.5); cal.translate(0, 0, 0.012);
  grp.add(new THREE.Mesh(cal, opts.mat.caliper));
  // rim face with spoke openings
  const style = opts.rimStyle;
  const rFace = rimR + 0.004, rHub = 0.062;
  let holes;
  if (style === 'aero') holes = spokeHoles(rFace * 0.62, rFace * 0.9, 5, 0.12, 0.2, 0.3);
  else if (style === 'multi') holes = spokeHoles(rHub + 0.01, rFace * 0.9, 10, 0.026, 0.02, 0.1);
  else if (style === 'sport') holes = spokeHoles(rHub + 0.005, rFace * 0.9, 5, 0.034, 0.016, 0.2, 0.16);
  else if (style === 'double') holes = spokeHoles(rHub + 0.008, rFace * 0.9, 5, 0.022, 0.018, 0.05, 0.13);
  else if (style === 'old') holes = spokeHoles(rHub + 0.012, rFace * 0.86, 7, 0.04, 0.03, 0.2);
  else if (style === 'twist') holes = spokeHoles(rHub + 0.006, rFace * 0.9, 6, 0.04, 0.026, 0.3, 0, 0.42);
  else holes = spokeHoles(rHub + 0.006, rFace * 0.9, 5, 0.06, 0.042, 0.4);
  const shp = new THREE.Shape(); shp.absarc(0, 0, rFace, 0, Math.PI * 2, false);
  for (const h of holes) { const p = new THREE.Path(); h.forEach(([x, y], i) => i ? p.lineTo(x, y) : p.moveTo(x, y)); p.closePath(); shp.holes.push(p); }
  const depth = 0.02;
  const fg = new THREE.ExtrudeGeometry(shp, { depth, bevelEnabled: true, bevelThickness: 0.007, bevelSize: 0.0055, bevelSegments: 3, curveSegments: 72, steps: 1 });
  const zFace = tw * 0.36;
  fg.translate(0, 0, zFace - depth);
  grp.add(new THREE.Mesh(fg, opts.mat.rim));
  // rim lip ring
  const lip = new THREE.TorusGeometry(rFace + 0.004, 0.0075, 10, 96); lip.translate(0, 0, zFace + 0.004);
  grp.add(new THREE.Mesh(lip, opts.mat.lip));
  // hub cap + nuts
  const cap = new THREE.CylinderGeometry(0.034, 0.038, 0.016, 32); cap.rotateX(Math.PI / 2); cap.translate(0, 0, zFace + 0.008);
  grp.add(new THREE.Mesh(cap, opts.mat.cap));
  for (let i = 0; i < 5; i++) {
    const a = i * 2 * Math.PI / 5 + 0.3, ng = new THREE.CylinderGeometry(0.0085, 0.0085, 0.014, 6); ng.rotateX(Math.PI / 2);
    ng.translate(Math.cos(a) * 0.052, Math.sin(a) * 0.052, zFace + 0.004); grp.add(new THREE.Mesh(ng, opts.mat.nut));
  }
  return grp;
}

/* ---------- mirrors, rails, wheel wells ---------- */
function superEllipsoid(THREE, rx, ry, rz, p = 0.55) {
  const g = new THREE.SphereGeometry(1, 36, 24), a = g.attributes.position;
  for (let i = 0; i < a.count; i++) {
    const v = [a.getX(i), a.getY(i), a.getZ(i)].map(c => Math.sign(c) * Math.pow(Math.abs(c), p));
    a.setXYZ(i, v[0] * rx, v[1] * ry, v[2] * rz);
  }
  g.computeVertexNormals();
  return g;
}
function buildMirror(THREE, d, mat, sg = 1) {
  const g = new THREE.Group();
  const x = d.xC - 0.17, i = secInfo(d, x);
  const y = i.ys + 0.085 + (d.suvish ? 0.015 : 0);
  const zH = i.W + 0.085;
  const hm = new THREE.Mesh(superEllipsoid(THREE, 0.115, 0.07, 0.1, 0.6), mat.paint);
  hm.position.set(x, y, sg * zH); hm.rotation.y = -0.12 * sg; hm.rotation.z = 0.05;
  g.add(hm);
  const face = new THREE.Mesh(superEllipsoid(THREE, 0.02, 0.06, 0.088, 0.5), mat.black);
  face.position.set(x - 0.1, y, sg * zH); face.rotation.y = -0.12 * sg; g.add(face);
  const arm = new THREE.Mesh(superEllipsoid(THREE, 0.06, 0.026, 0.07, 0.7), mat.black);
  arm.position.set(x + 0.01, y - 0.045, sg * (i.hwg + 0.06)); g.add(arm);
  return g;
}
export function surfY(d, x, z) {
  // height of the upper surface at (x, |z|) from the section polyline
  const pts = sectionHalf(d, x).pts;
  let best = -1;
  for (let j = pts.length - 1; j > 0; j--) {
    const [z0, y0] = pts[j], [z1, y1] = pts[j - 1];
    if ((z0 - z) * (z1 - z) <= 0 && Math.abs(z1 - z0) > 1e-6) { const t = (z - z0) / (z1 - z0); best = Math.max(best, y0 + (y1 - y0) * t); break; }
  }
  return best > 0 ? best : d.yt(x);
}
function buildRails(THREE, d, mat) {
  const g = new THREE.Group();
  const x0 = d.xH - 0.12, x1 = d.xRE + 0.1;
  for (const sgn of [1, -1]) {
    const pts = [];
    for (let k = 0; k <= 24; k++) {
      const x = lerp(x0, x1, k / 24), i = secInfo(d, x);
      const z = (Math.max(0.1, i.hwr - i.rr * 0.9) - 0.012) * sgn;
      const yy = surfY(d, x, Math.abs(z)) + 0.024;
      pts.push(new THREE.Vector3(x, yy, z));
    }
    const curve = new THREE.CatmullRomCurve3(pts);
    const tg = new THREE.TubeGeometry(curve, 64, 0.012, 10, false);
    tg.scale(1, 1, 1);
    g.add(new THREE.Mesh(tg, mat));
    for (const k of [1, 23]) {
      const p = pts[k];
      const ft = new THREE.BoxGeometry(0.07, 0.04, 0.026); const fm = new THREE.Mesh(ft, mat);
      fm.position.set(p.x, p.y - 0.014, p.z); g.add(fm);
    }
  }
  return g;
}
function buildWells(THREE, d, mat) {
  const g = new THREE.Group();
  for (const xa of [d.xf, d.xr]) {
    const r = d.Ra - 0.006, y0 = Math.max(d.gcS - 0.02, 0.05);
    const ph0 = Math.asin(clamp((y0 - d.R) / r, -1, 1));
    const shape = [];
    const n = 48;
    for (let k = 0; k <= n; k++) { const a = lerp(ph0, Math.PI - ph0, k / n); shape.push([xa + r * Math.cos(a), d.R + r * Math.sin(a)]); }
    const zz = d.hw - 0.02;
    const pos = [], idx = [];
    shape.forEach(([x, y]) => { pos.push(x, y, -zz, x, y, zz); });
    for (let k = 0; k < n; k++) { const a = k * 2; idx.push(a, a + 2, a + 1, a + 1, a + 2, a + 3); }
    const geo = new THREE.BufferGeometry(); geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); geo.setIndex(idx); geo.computeVertexNormals();
    g.add(new THREE.Mesh(geo, mat));
    // inner walls behind the tyres
    const wall = new THREE.Shape(); wall.moveTo(shape[0][0] - xa, shape[0][1]); shape.forEach(([x, y]) => wall.lineTo(x - xa, y)); wall.closePath();
    for (const zs of [-1, 1]) {
      const wg = new THREE.ShapeGeometry(wall, 24); wg.translate(xa, 0, zs * (d.hw - d.tw - 0.07));
      g.add(new THREE.Mesh(wg, mat));
    }
  }
  return g;
}

/* ---------- assemble ---------- */
export function buildCar(THREE, spec) {
  const d = derive(spec);
  const body = buildBodyGeometry(THREE, d);
  d.geo = layout(d);
  const views = paintViews(d);
  const bodyMat = bodyMaterial(THREE, views);
  const car = new THREE.Group();
  const bm = new THREE.Mesh(body, bodyMat); bm.castShadow = true; car.add(bm);
  const col = new THREE.Color(spec.color || '#888');
  const sport = !!spec.sp, ev = !!spec.ev, old = !!spec.old;
  const prefs = d.dna.rim || ['std', 'double'];
  let rimStyle = spec.rimStyle || (old ? 'old' : sport ? 'sport' : prefs[hash01(spec.id, 11) > 0.5 ? 1 : 0]);
  if (ev && !old && !spec.rimStyle && hash01(spec.id, 17) > 0.45 && rimStyle !== 'sport') rimStyle = 'aero';
  const rc = hash01(spec.id, 19);
  const rimCol = sport ? (rc > 0.5 ? 0x2a2d31 : 0x4a4f55) : rimStyle === 'aero' ? 0xb7bcc1 : (rc > 0.82 && !old ? 0x3d4146 : rc > 0.66 && !old ? 0x8a8f95 : 0xc3c8cd);
  const M = {
    tyre: new THREE.MeshPhysicalMaterial({ color: 0x141516, roughness: 0.82, metalness: 0, sheen: 0.3, sheenRoughness: 0.8, sheenColor: 0x333333 }),
    barrel: new THREE.MeshStandardMaterial({ color: 0x2b2e31, roughness: 0.45, metalness: 0.8, side: THREE.DoubleSide }),
    dark: new THREE.MeshStandardMaterial({ color: 0x050505, roughness: 1, metalness: 0, side: THREE.DoubleSide }),
    disc: new THREE.MeshStandardMaterial({ color: 0x8d9195, roughness: 0.38, metalness: 1 }),
    caliper: new THREE.MeshPhysicalMaterial({ color: sport ? 0xb3151b : 0x3b3f44, roughness: 0.35, metalness: 0.2, clearcoat: 0.6 }),
    rim: new THREE.MeshPhysicalMaterial({ color: rimCol, roughness: 0.24, metalness: 0.95, clearcoat: 0.5, clearcoatRoughness: 0.1 }),
    lip: new THREE.MeshStandardMaterial({ color: sport ? 0x5a6066 : 0xd4d8dc, roughness: 0.15, metalness: 1 }),
    cap: new THREE.MeshStandardMaterial({ color: 0x2a2d30, roughness: 0.3, metalness: 0.6 }),
    nut: new THREE.MeshStandardMaterial({ color: 0xa8adb2, roughness: 0.3, metalness: 1 })
  };
  for (const [xa, zs] of [[d.xf, 1], [d.xf, -1], [d.xr, 1], [d.xr, -1]]) {
    const w = buildWheel(THREE, d, { mat: M, rimStyle });
    w.position.set(xa, d.R, zs * (d.hw - d.tw / 2 - 0.006));
    if (zs < 0) w.rotation.y = Math.PI;
    if (xa === d.xf) w.rotation.z = 0.0; // keep spokes aligned
    w.traverse(o => { if (o.isMesh) o.castShadow = true; });
    car.add(w);
  }
  const blackM = new THREE.MeshStandardMaterial({ color: 0x0b0b0c, roughness: 0.6, metalness: 0 });
  const paintM = new THREE.MeshPhysicalMaterial({ color: col, roughness: 0.3, metalness: 0.5, clearcoat: 1, clearcoatRoughness: 0.035 });
  if (spec.tt) paintM.color.set(0x0a0a0a);
  for (const zs of [1, -1]) { const mr = buildMirror(THREE, d, { paint: paintM, black: blackM }, zs); mr.traverse(o => { if (o.isMesh) o.castShadow = true; }); car.add(mr); }
  if (spec.rails) car.add(buildRails(THREE, d, new THREE.MeshStandardMaterial({ color: spec.lux ? 0xb7bbbf : 0x1a1b1c, roughness: 0.35, metalness: spec.lux ? 1 : 0.2 })));
  car.add(buildWells(THREE, d, new THREE.MeshStandardMaterial({ color: 0x050505, roughness: 1, metalness: 0, side: THREE.DoubleSide })));
  return { car, d, views };
}
