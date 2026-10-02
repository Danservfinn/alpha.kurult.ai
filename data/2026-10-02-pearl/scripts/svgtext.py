"""Read the non-tick text lines (string, x, baseline y, font size, colour, rotation) from a
matplotlib SVG so a redraw can place every annotation exactly where the approved v4 chart had it."""
import re, xml.etree.ElementTree as ET
NS = "{http://www.w3.org/2000/svg}"

def texts(path):
    tb = ET.TreeBuilder(insert_comments=True)
    root = ET.parse(path, parser=ET.XMLParser(target=tb)).getroot()
    W = float(root.get("width").replace("pt", "")); H = float(root.get("height").replace("pt", ""))
    out = []
    def walk(el, anc):
        gid = el.get("id") or ""
        anc = anc + [gid]
        kids = list(el)
        for i, k in enumerate(kids):
            if k.tag is ET.Comment and i + 1 < len(kids) and kids[i + 1].tag == NS + "g":
                g = kids[i + 1]
                m = re.match(r"translate\(([\-\d.]+) ([\-\d.]+)\)(?: rotate\(([\-\d.]+)\))? scale\(([\d.]+) -[\d.]+\)", g.get("transform") or "")
                if m and not any(a.startswith(("xtick_", "ytick_")) for a in anc):
                    x, y, r, sc = m.groups()
                    col = re.search(r"fill: (#[0-9a-f]+)", g.get("style") or "")
                    out.append(dict(s=k.text.strip(), x=float(x) / W, y=1 - float(y) / H, fs=round(float(sc) * 100, 3),
                                    color=col.group(1) if col else "#000000", rot=-float(r) if r else 0.0, group=gid))
            elif k.tag is not ET.Comment:
                walk(k, anc)
    walk(root, [])
    return out

def replay(fig, items, replace=None, skip=()):
    """Draw each recorded line at its exact left/baseline position. replace maps old string -> new string."""
    replace = replace or {}
    for t in items:
        if t["s"] in skip:
            continue
        s = replace.get(t["s"], t["s"])
        fig.text(t["x"], t["y"], s, fontsize=t["fs"], color=t["color"], ha="left", va="baseline",
                 rotation=t["rot"], rotation_mode="anchor")
