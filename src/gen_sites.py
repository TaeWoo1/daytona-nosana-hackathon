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
