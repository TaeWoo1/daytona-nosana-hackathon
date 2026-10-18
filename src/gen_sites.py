"""Generate layout variants A/B/C from the gold facts so every layout carries identical facts.

Run:  .venv/bin/python src/gen_sites.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
F = json.loads((ROOT / "data/gold/daytona_pricing_facts.draft.json").read_text())["facts"]

GPU_NAMES = {
    "b300": "Nvidia B300", "b200": "Nvidia B200", "amd_mi355x": "AMD MI355X", "h200": "Nvidia H200",
    "h100": "Nvidia H100", "rtx_pro_6000": "Nvidia RTX PRO 6000", "rtx_5090": "Nvidia RTX 5090",
    "rtx_4090": "Nvidia RTX 4090",
}
GPU_ORDER = ["b300", "b200", "amd_mi355x", "h200", "h100", "rtx_pro_6000", "rtx_5090", "rtx_4090"]
GPU = F["gpu_usd_per_hour"]

NAV = '<nav><a href="/">/</a> <a href="/docs">DOCS</a> <a href="/customers">CUSTOMERS</a> <a href="/pricing">PRICING</a> <a href="/startups">STARTUPS</a> <a href="/blog">BLOG</a> <a href="/signin">Sign in</a> <a href="/contact">Contact us</a></nav>'

COMMON_BOTTOM = f"""
<section>
  <h2>Instant Sandboxes. Pay-as-You-Go.</h2>
  <p>Daytona lets you spin up sandboxes in milliseconds and shut them down just as fast.</p>
  <p>Use what you need, when you need it. <span>${F['free_compute_credit_usd']} in free compute included.</span></p>
</section>
<section>
  <p>All billing is calculated per second.</p>
  <ul>
    <li>Sign up for a free trial - no credit card required</li>
    <li>Pay as you go with usage-based pricing</li>
    <li>Unlock volume discounts as you scale</li>
  </ul>
</section>
<section>
  <h3>Start-ups</h3>
  <p>Daytona supports startups with up to ${F['startup_program_max_credits_usd'] // 1000}k in credits for free.</p>
  <a href="/startups">Sign up for credits</a>
  <h3>Enterprise</h3>
  <p>Designed for businesses that need larger limits, SSO, audit logs, or BYOC</p>
  <a href="/contact">Contact Sales</a>
</section>
<footer>COMPANY <a href="/about">About</a> <a href="/careers">Careers</a></footer>
"""


def page(title, body, head_extra=""):
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{title}</title>
<style>body{{font-family:sans-serif;max-width:900px;margin:auto;padding:16px}} table{{border-collapse:collapse}} td,th{{border:1px solid #ccc;padding:4px 8px}}</style>
{head_extra}</head><body>
{NAV}
{body}
</body></html>
"""


def gpu_rows(kind):
    return "\n".join(
        f'<div class="row"><p>{GPU_NAMES[k]}</p><p>${GPU[k][kind]:.2f}/h</p></div>' for k in GPU_ORDER
    )


# A: mirrors the real page. Compute prices with a far-away footnote; GPU tabs with the
# On-demand panel present in the HTML but hidden (hidden attr + display:none), Preemptible shown by default.
A_BODY = f"""
<header><h1>Build for free, <br>pay as you scale.</h1><a href="/signup">Start for free</a> <a href="/contact">Contact Sales</a></header>
<section>
  <h2>Compute</h2>
  <div class="row"><p>vCPU</p><p>${F['vcpu_usd_per_hour']}/h</p></div>
  <div class="row"><p>Memory</p><p><strong>GiB</strong></p><p>${F['memory_usd_per_gib_hour']}/h</p></div>
  <div class="row"><p>Storage</p><p><strong>GiB</strong></p><p>${F['storage_usd_per_gib_hour']}/h</p></div>
  <p><em>*</em>Price per <strong>GiB</strong> after first {F['storage_free_gib']} free</p>
  <h2>OS</h2>
  <div class="row"><p>Windows</p><p>${F['windows_usd_per_vcpu_hour']}/vCPU/h</p></div>
</section>
<section>
  <h2>GPU</h2>
  <div role="tablist">
    <button role="tab" aria-selected="true" id="tab-pre" aria-controls="panel-pre">Preemptible</button>
    <button role="tab" aria-selected="false" id="tab-od" aria-controls="panel-od">On-demand</button>
  </div>
  <div role="tabpanel" id="panel-pre" aria-labelledby="tab-pre">
    <h3>Preemptible ($/hour)</h3>
{gpu_rows('preemptible')}
  </div>
  <div role="tabpanel" id="panel-od" aria-labelledby="tab-od" aria-label="On-demand GPU prices per hour" hidden style="display: none; height: 0px; overflow: hidden;">
    <h3>On-demand ($/hour)</h3>
{gpu_rows('on_demand')}
  </div>
</section>
{COMMON_BOTTOM}
<script>
// tab behaviour like the real page: clicking a tab shows its panel and hides the other
document.querySelectorAll('[role=tab]').forEach(function (tab) {{
  tab.addEventListener('click', function () {{
    document.querySelectorAll('[role=tab]').forEach(function (t) {{
      var panel = document.getElementById(t.getAttribute('aria-controls'));
      var on = t === tab;
      t.setAttribute('aria-selected', on ? 'true' : 'false');
      if (on) {{ panel.removeAttribute('hidden'); panel.style.cssText = ''; }}
      else {{ panel.setAttribute('hidden', ''); panel.style.cssText = 'display: none; height: 0px; overflow: hidden;'; }}
    }});
  }});
}});
</script>
"""

# B: same facts; one GPU table with both columns visible and explicitly labelled; storage free tier next to the price.
gpu_table = "\n".join(
    f"<tr><td>{GPU_NAMES[k]}</td><td>${GPU[k]['preemptible']:.2f}/h</td><td>${GPU[k]['on_demand']:.2f}/h</td></tr>"
    for k in GPU_ORDER
)
B_COMPUTE = f"""
<header><h1>Build for free, pay as you scale.</h1><a href="/signup">Start for free</a> <a href="/contact">Contact Sales</a></header>
<section>
  <h2>Compute (CPU sandboxes)</h2>
  <table>
    <tr><th>Resource</th><th>Price</th></tr>
    <tr><td>vCPU</td><td>${F['vcpu_usd_per_hour']} per vCPU per hour</td></tr>
    <tr><td>Memory</td><td>${F['memory_usd_per_gib_hour']} per GiB per hour</td></tr>
    <tr><td>Storage (disk)</td><td>${F['storage_usd_per_gib_hour']} per GiB per hour &mdash; the first {F['storage_free_gib']} GiB are free; you pay only for storage above {F['storage_free_gib']} GiB</td></tr>
    <tr><td>Windows OS</td><td>${F['windows_usd_per_vcpu_hour']} per vCPU per hour</td></tr>
  </table>
</section>
<section>
  <h2>GPU prices ($ per hour)</h2>
  <table>
    <tr><th>GPU</th><th>Preemptible (may be interrupted)</th><th>On-demand (not interrupted)</th></tr>
{gpu_table}
  </table>
</section>
"""
B_BODY = B_COMPUTE + COMMON_BOTTOM

# C: B + plain-text FAQ + JSON-LD offers.
FAQ = [
    ("What does an RTX 4090 GPU cost if I need it not to be interrupted?",
     f"On-demand RTX 4090 costs ${GPU['rtx_4090']['on_demand']:.2f} per hour. The preemptible price (${GPU['rtx_4090']['preemptible']:.2f} per hour) can be interrupted."),
    ("How do I calculate the cost of a CPU sandbox?",
     f"Add vCPU count x ${F['vcpu_usd_per_hour']}/h, plus memory GiB x ${F['memory_usd_per_gib_hour']}/h, plus disk GiB above the first {F['storage_free_gib']} free GiB x ${F['storage_usd_per_gib_hour']}/h."),
    ("Do I need a credit card to start?",
     f"No. The free trial requires no credit card and includes ${F['free_compute_credit_usd']} in free compute."),
    ("How is usage billed?", "All billing is calculated per second."),
    ("How much does a Windows sandbox cost?", f"Windows costs ${F['windows_usd_per_vcpu_hour']} per vCPU per hour."),
]
faq_html = "\n".join(f"<h3>Q: {q}</h3>\n<p>A: {a}</p>" for q, a in FAQ)
offers = [
    {"@type": "Offer", "name": f"{GPU_NAMES[k]} {label}",
     "priceSpecification": {"@type": "UnitPriceSpecification", "price": GPU[k][kind], "priceCurrency": "USD", "unitText": "hour"}}
    for k in GPU_ORDER for kind, label in (("on_demand", "on-demand"), ("preemptible", "preemptible (may be interrupted)"))
] + [
    {"@type": "Offer", "name": "vCPU", "priceSpecification": {"@type": "UnitPriceSpecification", "price": F["vcpu_usd_per_hour"], "priceCurrency": "USD", "unitText": "vCPU hour"}},
    {"@type": "Offer", "name": "Memory", "priceSpecification": {"@type": "UnitPriceSpecification", "price": F["memory_usd_per_gib_hour"], "priceCurrency": "USD", "unitText": "GiB hour"}},
    {"@type": "Offer", "name": f"Storage (first {F['storage_free_gib']} GiB free)", "priceSpecification": {"@type": "UnitPriceSpecification", "price": F["storage_usd_per_gib_hour"], "priceCurrency": "USD", "unitText": "GiB hour"}},
    {"@type": "Offer", "name": "Windows", "priceSpecification": {"@type": "UnitPriceSpecification", "price": F["windows_usd_per_vcpu_hour"], "priceCurrency": "USD", "unitText": "vCPU hour"}},
]
JSONLD = {"@context": "https://schema.org", "@type": "Product", "name": "Daytona Sandboxes", "offers": offers}
C_HEAD = f'<script type="application/ld+json">{json.dumps(JSONLD)}</script>'
C_BODY = B_COMPUTE + f'<section><h2>Pricing FAQ</h2>\n{faq_html}\n</section>' + COMMON_BOTTOM

INDEX = page("Daytona", '<h1>Daytona</h1><p>Secure and elastic infrastructure for running AI-generated code.</p><a href="/pricing">Pricing</a>')

for name, body, head in (("A_original", A_BODY, ""), ("B_explicit", B_BODY, ""), ("C_faq_structured", C_BODY, C_HEAD)):
    d = ROOT / "sites" / name
    (d / "pricing").mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(INDEX)
    (d / "pricing" / "index.html").write_text(page("Pricing | Daytona", body, head))
    print("wrote", d)

# ---- v2 (styled): A and C restyled to look like the real daytona.io/pricing (dark theme, pill GPU toggle, 2-column card).
# Same facts from gold. No external fonts/CDN/images (Daytona Tier 1 network). v1 above is kept byte-identical.
CSS2 = """
*{box-sizing:border-box}
body{margin:0;background:#0a0a0a;color:#a1a1a1;font-family:Inter,"Helvetica Neue",Arial,sans-serif;font-size:16px;line-height:1.5}
a{color:inherit;text-decoration:none}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;letter-spacing:.02em}
nav{display:flex;align-items:center;gap:22px;max-width:1200px;margin:0 auto;padding:18px 24px;color:#fff}
nav .logo{font-size:24px;font-weight:600;letter-spacing:-.02em}
nav .sep{color:#666}
nav .links{display:flex;gap:22px;font-size:14px}
nav .right{margin-left:auto;display:flex;gap:10px}
.btn{display:inline-block;padding:8px 18px;border-radius:6px;font-size:14px}
.btn-signin{background:#0f1f3d;color:#4b8cff}.btn-dark{background:#1f1f1f;color:#fff}
.hero{text-align:center;padding:90px 24px 80px}
.hero h1{color:#fff;font-size:64px;font-weight:500;line-height:1.15;letter-spacing:-.02em;margin:0 0 40px}
.hero .cta{display:flex;justify-content:center;gap:24px}
.btn-blue{background:#3b82f6;color:#fff;padding:16px 32px;border-radius:4px;font-size:18px}
.btn-outline{border:1px solid #444;color:#fff;padding:16px 32px;border-radius:4px;font-size:18px}
.grid{display:grid;grid-template-columns:400px 1fr;max-width:1200px;margin:0 auto;border:1px solid #262626}
.left{border-right:1px solid #262626}
.card{padding:26px 30px;border-bottom:1px solid #262626}
.card:last-child{border-bottom:0}
.card h2{color:#fff;font-size:20px;font-weight:400;margin:0 0 12px;display:flex;align-items:center;gap:10px}
.card h2 .ico{display:inline-block;width:20px;height:20px;border:2px solid #fff;border-radius:3px}
.row{display:flex;justify-content:space-between;font-size:18px;margin:6px 0}
.row p{margin:0}.row .v{color:#a1a1a1}
.note{font-size:13px;color:#737373;margin-top:8px}
.gpuhead{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}
.gpuhead h2{margin:0}
.pill{display:flex;border:1px solid #333;border-radius:10px;padding:4px}
.pill button{background:transparent;border:0;color:#8a8a8a;font:inherit;font-size:16px;padding:8px 14px;border-radius:7px;cursor:pointer}
.pill button[aria-selected=true]{background:#1c1c1c;color:#fff;box-shadow:0 0 0 1px #333}
.gpucols{display:flex;justify-content:space-between;font-size:12px;color:#737373;margin-bottom:6px}
.right-col{padding:44px}
.right-col h2{color:#fff;font-size:46px;font-weight:400;letter-spacing:-.01em;margin:0 0 26px}
.right-col p{font-size:20px;margin:0}.right-col .hl{color:#fff}
.sec{max-width:1200px;margin:0 auto;padding:40px 24px}
.sec h2,.sec h3{color:#fff;font-weight:400}
.sec ul{padding-left:20px}
.faq h3{font-size:18px;margin:22px 0 6px}.faq p{margin:0}
footer{max-width:1200px;margin:0 auto;padding:40px 24px;color:#666;font-size:13px}
"""

NAV2 = """<nav><a class="logo" href="/">Daytona</a><span class="sep">/</span>
<div class="links mono"><a href="/docs">DOCS</a><a href="/customers">CUSTOMERS</a><a href="/pricing">PRICING</a><a href="/startups">STARTUPS</a><a href="/blog">BLOG</a></div>
<div class="right mono"><a class="btn btn-signin" href="/signin">Sign in</a><a class="btn btn-dark" href="/contact">Contact us</a></div></nav>"""

HERO2 = """<header class="hero"><h1>Build for free,<br>pay as you scale.</h1>
<div class="cta mono"><a class="btn-blue" href="/signup">Start for free</a><a class="btn-outline" href="/contact">Contact Sales</a></div></header>"""

RIGHT2 = f"""<div class="right-col"><h2>Instant Sandboxes. Pay-as-You-Go.</h2>
<p>Daytona lets you spin up sandboxes in milliseconds and shut them down just as fast.</p>
<p>Use what you need, when you need it. <span class="hl">${F['free_compute_credit_usd']} in free compute included.</span></p></div>"""

BOTTOM2 = f"""<section class="sec">
  <p>All billing is calculated per second.</p>
  <ul><li>Sign up for a free trial - no credit card required</li><li>Pay as you go with usage-based pricing</li><li>Unlock volume discounts as you scale</li></ul>
  <h3>Start-ups</h3>
  <p>Daytona supports startups with up to ${F['startup_program_max_credits_usd'] // 1000}k in credits for free.</p>
  <a class="mono" href="/startups">Sign up for credits</a>
  <h3>Enterprise</h3>
  <p>Designed for businesses that need larger limits, SSO, audit logs, or BYOC</p>
  <a class="mono" href="/contact">Contact Sales</a>
</section>
<footer class="mono">COMPANY &nbsp; <a href="/about">About</a> &nbsp; <a href="/careers">Careers</a></footer>"""


def page2(title, body, head_extra=""):
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title>
<style>{CSS2}</style>
{head_extra}</head><body>
{NAV2}
{body}
</body></html>
"""


def gpu_rows2(kind):
    return "\n".join(
        f'<div class="row"><p>{GPU_NAMES[k]}</p><p class="v">${GPU[k][kind]:.2f}/h</p></div>' for k in GPU_ORDER
    )


# A v2: like the real page, the GPU panels carry no visible heading (only aria-label); the pill toggle's
# highlight is the only on-screen cue for which price set is shown. On-demand panel hidden until clicked.
A2_BODY = f"""{HERO2}
<div class="grid"><div class="left">
  <div class="card"><h2><span class="ico"></span>Compute</h2>
    <div class="row"><p>vCPU</p><p class="v">${F['vcpu_usd_per_hour']}/h</p></div></div>
  <div class="card"><div class="gpuhead"><h2><span class="ico"></span>GPU</h2>
    <div class="pill" role="tablist">
      <button role="tab" aria-selected="true" id="tab-pre" aria-controls="panel-pre">Preemptible</button>
      <button role="tab" aria-selected="false" id="tab-od" aria-controls="panel-od">On-demand</button>
    </div></div>
    <div role="tabpanel" id="panel-pre" aria-labelledby="tab-pre" aria-label="Preemptible GPU prices per hour">
{gpu_rows2('preemptible')}
    </div>
    <div role="tabpanel" id="panel-od" aria-labelledby="tab-od" aria-label="On-demand GPU prices per hour" hidden style="display: none; height: 0px; overflow: hidden;">
{gpu_rows2('on_demand')}
    </div></div>
  <div class="card"><h2><span class="ico"></span>Memory</h2>
    <div class="row"><p>GiB</p><p class="v">${F['memory_usd_per_gib_hour']}/h</p></div></div>
  <div class="card"><h2><span class="ico"></span>Storage</h2>
    <div class="row"><p>GiB<sup>*</sup></p><p class="v">${F['storage_usd_per_gib_hour']}/h</p></div></div>
  <div class="card"><h2><span class="ico"></span>OS</h2>
    <div class="row"><p>Windows</p><p class="v">${F['windows_usd_per_vcpu_hour']}/vCPU/h</p></div></div>
</div>
{RIGHT2}
</div>
<p class="sec note">* Price per GiB after first {F['storage_free_gib']} free</p>
{BOTTOM2}
<script>
document.querySelectorAll('[role=tab]').forEach(function (tab) {{
  tab.addEventListener('click', function () {{
    document.querySelectorAll('[role=tab]').forEach(function (t) {{
      var panel = document.getElementById(t.getAttribute('aria-controls'));
      var on = t === tab;
      t.setAttribute('aria-selected', on ? 'true' : 'false');
      if (on) {{ panel.removeAttribute('hidden'); panel.style.cssText = ''; }}
      else {{ panel.setAttribute('hidden', ''); panel.style.cssText = 'display: none; height: 0px; overflow: hidden;'; }}
    }});
  }});
}});
</script>
"""

# C v2: same design; both GPU prices visible with explicit labels; storage free tier next to the price; FAQ + JSON-LD.
gpu_rows_both = "\n".join(
    f'<div class="row"><p>{GPU_NAMES[k]}</p><p class="v">${GPU[k]["preemptible"]:.2f}/h &nbsp;|&nbsp; ${GPU[k]["on_demand"]:.2f}/h</p></div>'
    for k in GPU_ORDER
)
C2_BODY = f"""{HERO2}
<div class="grid"><div class="left">
  <div class="card"><h2><span class="ico"></span>Compute</h2>
    <div class="row"><p>vCPU</p><p class="v">${F['vcpu_usd_per_hour']} per vCPU per hour</p></div></div>
  <div class="card"><h2><span class="ico"></span>GPU prices ($ per hour)</h2>
    <div class="gpucols"><span>GPU</span><span>Preemptible (may be interrupted) | On-demand (not interrupted)</span></div>
{gpu_rows_both}
  </div>
  <div class="card"><h2><span class="ico"></span>Memory</h2>
    <div class="row"><p>GiB</p><p class="v">${F['memory_usd_per_gib_hour']} per GiB per hour</p></div></div>
  <div class="card"><h2><span class="ico"></span>Storage (disk)</h2>
    <div class="row"><p>GiB</p><p class="v">${F['storage_usd_per_gib_hour']} per GiB per hour</p></div>
    <p class="note">The first {F['storage_free_gib']} GiB are free; you pay only for storage above {F['storage_free_gib']} GiB.</p></div>
  <div class="card"><h2><span class="ico"></span>Windows OS</h2>
    <div class="row"><p>Windows</p><p class="v">${F['windows_usd_per_vcpu_hour']} per vCPU per hour</p></div></div>
</div>
{RIGHT2}
</div>
<section class="sec faq"><h2>Pricing FAQ</h2>
{faq_html}
</section>
{BOTTOM2}
"""

INDEX2 = page2("Daytona", '<header class="hero"><h1>Daytona</h1><p>Secure and elastic infrastructure for running AI-generated code.</p><a class="btn-blue mono" href="/pricing">Pricing</a></header>')

for name, body, head in (("A_original", A2_BODY, ""), ("C_faq_structured", C2_BODY, C_HEAD)):
    d = ROOT / "sites_v2" / name
    (d / "pricing").mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(INDEX2)
    (d / "pricing" / "index.html").write_text(page2("Pricing | Daytona", body, head))
    print("wrote", d)
