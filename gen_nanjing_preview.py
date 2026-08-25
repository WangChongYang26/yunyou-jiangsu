# -*- coding: utf-8 -*-
"""生成南京配图效果预览页 nanjing_preview.html"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
s = open(os.path.join(BASE, "city_data.js"), encoding="utf-8").read()
data = json.loads(s[s.index("["):s.rindex("]") + 1])
nj = [c for c in data if c.get("name") == "南京"][0]
picks = json.load(open(os.path.join(BASE, "nanjing_picks.json"), encoding="utf-8"))


def esc(x):
    return str(x).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


cat_names = {"scenery": "风 景", "food": "美 食", "story": "文 化 故 事"}
card_key = {"scenery": ["scenery_0", "scenery_1", "scenery_2"],
            "food": ["food_0", "food_1", "food_2"],
            "story": ["story_0", "story_1"]}

parts = []
for cat in ("scenery", "food", "story"):
    cards = []
    for i, key in enumerate(card_key[cat]):
        it = nj[cat][i]
        pk = picks.get(key) or {}
        src = esc(pk.get("photographer") or "Pexels")
        tag = esc((pk.get("alt") or "")[:80])
        cards.append(
            '<div class="card">'
            '<h4>%s</h4>'
            '<img src="images/nanjing_pexels/%s.jpg" alt="" loading="lazy">'
            '<p class="d">%s</p>'
            '<p class="src">图源：%s &middot; %s</p>'
            "</div>" % (esc(it["t"]), key, esc(it["d"]), src, tag)
        )
    parts.append('<h3>%s</h3><div class="row">%s</div>'
                 % (cat_names[cat], "\n".join(cards)))

html = (
    '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">'
    '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
    '<title>南京 &middot; 配图效果预览</title><style>'
    'body{background:#050a14;color:#dce9f8;font-family:"Microsoft YaHei",sans-serif;padding:30px;max-width:1100px;margin:0 auto}'
    'h2{letter-spacing:.2em;color:#fff;text-align:center}'
    '.sub{text-align:center;color:#8fb6dd;font-size:13px;margin-bottom:26px;letter-spacing:.08em}'
    'h3{margin:30px 0 14px;color:#9fc3e8;letter-spacing:.15em;border-bottom:1px solid rgba(140,200,255,.2);padding-bottom:8px}'
    '.row{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}'
    '.card{background:rgba(10,28,50,.65);border:1px solid rgba(140,200,255,.22);border-radius:14px;padding:16px;display:flex;flex-direction:column}'
    '.card h4{font-size:17px;color:#8fd8ff;letter-spacing:.1em;margin-bottom:10px}'
    '.card img{width:100%;height:170px;object-fit:cover;border-radius:10px;border:1px solid rgba(140,200,255,.25)}'
    '.card .d{font-size:13px;line-height:1.8;color:rgba(220,240,255,.85);margin-top:10px;flex:1}'
    '.card .src{font-size:11px;color:#7fd8a8;margin-top:8px;letter-spacing:.03em}'
    '</style></head><body>'
    '<h2>南京 &middot; 配图效果预览</h2>'
    '<p class="sub">8 个条目均已挂图到 city_data.js，网站南京页实时生效 &middot; 图片来自 Pexels（CC0 免费商用）</p>'
    + "\n".join(parts) + "</body></html>"
)

with open(os.path.join(BASE, "nanjing_preview.html"), "w", encoding="utf-8") as f:
    f.write(html)
print("已生成 nanjing_preview.html")
