# -*- coding: utf-8 -*-
"""生成全站配图预览页 all_cities_preview.html（13 市）"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
s = open(os.path.join(BASE, "city_data.js"), encoding="utf-8").read()
data = json.loads(s[s.index("["):s.rindex("]") + 1])
picks = {}
if os.path.exists(os.path.join(BASE, "picks_all.json")):
    picks = json.load(open(os.path.join(BASE, "picks_all.json"), encoding="utf-8"))
nj_picks = {}
if os.path.exists(os.path.join(BASE, "nanjing_picks.json")):
    nj_picks = json.load(open(os.path.join(BASE, "nanjing_picks.json"), encoding="utf-8"))


def esc(x):
    return str(x).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


cat_names = {"scenery": "风 景", "food": "美 食", "story": "文 化 故 事"}
cat_keys = {"scenery": ["scenery_0", "scenery_1", "scenery_2"],
            "food": ["food_0", "food_1", "food_2"],
            "story": ["story_0", "story_1"]}

city_parts = []
for c in data:
    name = c["name"]
    block = ['<div class="city">', '<h2>%s</h2>' % esc(name)]
    for cat in ("scenery", "food", "story"):
        cards = []
        for i, key in enumerate(cat_keys[cat]):
            it = c[cat][i]
            img = it.get("img")
            if img:
                src_ph = ""
                pk = (picks.get(name) or {}).get(key) or (nj_picks.get(key) if name == "南京" else None)
                if pk:
                    src_ph = esc(pk.get("photographer") or "Pexels")
                cards.append(
                    '<div class="card"><h4>%s</h4>'
                    '<img src="%s" alt="" loading="lazy">'
                    '<p class="d">%s</p>'
                    '<p class="src">%s</p></div>'
                    % (esc(it["t"]), esc(img), esc(it["d"]), src_ph)
                )
            else:
                cards.append(
                    '<div class="card miss"><h4>%s</h4>'
                    '<div class="noimg">未配图</div>'
                    '<p class="d">%s</p></div>'
                    % (esc(it["t"]), esc(it["d"]))
                )
        block.append('<h3>%s</h3><div class="row">%s</div>' % (cat_names[cat], "\n".join(cards)))
    block.append("</div>")
    city_parts.append("\n".join(block))

html = (
    '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">'
    '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
    '<title>全站配图效果预览</title><style>'
    'body{background:#050a14;color:#dce9f8;font-family:"Microsoft YaHei",sans-serif;padding:30px;max-width:1200px;margin:0 auto}'
    'h1{letter-spacing:.2em;color:#fff;text-align:center}'
    '.sub{text-align:center;color:#8fb6dd;font-size:13px;margin-bottom:20px;letter-spacing:.08em}'
    '.city{background:rgba(8,20,38,.5);border:1px solid rgba(140,200,255,.18);border-radius:16px;padding:22px 24px;margin-bottom:28px}'
    '.city h2{color:#ffd98a;letter-spacing:.15em;font-size:22px;margin-bottom:4px}'
    'h3{margin:22px 0 12px;color:#9fc3e8;letter-spacing:.15em;border-bottom:1px solid rgba(140,200,255,.18);padding-bottom:6px;font-size:15px}'
    '.row{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px}'
    '.card{background:rgba(10,28,50,.65);border:1px solid rgba(140,200,255,.22);border-radius:12px;padding:14px;display:flex;flex-direction:column}'
    '.card h4{font-size:15px;color:#8fd8ff;letter-spacing:.08em;margin-bottom:8px}'
    '.card img{width:100%;height:150px;object-fit:cover;border-radius:8px;border:1px solid rgba(140,200,255,.25)}'
    '.card .d{font-size:12px;line-height:1.7;color:rgba(220,240,255,.8);margin-top:8px;flex:1}'
    '.card .src{font-size:11px;color:#7fd8a8;margin-top:6px}'
    '.card.miss{border-color:rgba(255,180,90,.35);background:rgba(30,20,10,.4)}'
    '.noimg{width:100%;height:150px;display:flex;align-items:center;justify-content:center;border-radius:8px;border:1px dashed rgba(255,200,120,.4);color:#c99a5a;font-size:13px;letter-spacing:.3em}'
    '</style></head><body>'
    '<h1>全站配图效果预览</h1>'
    '<p class="sub">13 市 · 94 条已配图（Pexels CC0）· 未配图条目用虚线框标注</p>'
    + "\n".join(city_parts) + "</body></html>"
)

with open(os.path.join(BASE, "all_cities_preview.html"), "w", encoding="utf-8") as f:
    f.write(html)
print("已生成 all_cities_preview.html")
