#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 jiangsu_map.js：把江苏 13 市边界 GeoJSON 投影为 SVG path 数据
数据源：阿里 DataV GeoAtlas（公开行政区划数据）320000_full.json
投影：等距线性投影（示意用途，非严格制图）；保留原始 GeoJSON 供复用
"""
import json
import urllib.request
import os

BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, "jiangsu_boundary.geojson")
OUT = os.path.join(BASE, "jiangsu_map.js")

# 画布：与 yunyou.html 中 <svg viewBox="0 0 680 560"> 一致
PX = {"x0": 50, "x1": 630, "y0": 60, "y1": 520}
GEO = {"lng0": 116.3, "lng1": 122.0, "lat0": 30.7, "lat1": 35.1}

# 标签手动偏移（质心对细长/不规则形状会偏，手调到区域中心）
LABEL_OFFSETS = {
    320700: (0, 22),     # 连云港：避开顶部标题
    320200: (15, -16),   # 无锡：质心偏东，调到无锡区域中心
}


def proj(lng, lat):
    x = PX["x0"] + (lng - GEO["lng0"]) / (GEO["lng1"] - GEO["lng0"]) * (PX["x1"] - PX["x0"])
    y = PX["y0"] + (GEO["lat1"] - lat) / (GEO["lat1"] - GEO["lat0"]) * (PX["y1"] - PX["y0"])
    return x, y


def ring_to_path(ring):
    """单个环 -> SVG path 片段"""
    pts = [proj(p[0], p[1]) for p in ring]
    d = "M{:.1f} {:.1f}".format(*pts[0])
    for x, y in pts[1:]:
        d += "L{:.1f} {:.1f}".format(x, y)
    d += "Z"
    return d


def geom_to_paths(geom):
    """MultiPolygon / Polygon -> 多个 path 片段"""
    paths = []
    if geom["type"] == "Polygon":
        for ring in geom["coordinates"]:
            paths.append(ring_to_path(ring))
    elif geom["type"] == "MultiPolygon":
        for poly in geom["coordinates"]:
            for ring in poly:
                paths.append(ring_to_path(ring))
    return paths


def centroid_of(geom):
    """取所有顶点平均作为标签位置（示意）"""
    xs, ys = [], []
    polys = geom["coordinates"] if geom["type"] == "Polygon" else geom["coordinates"]
    for poly in polys:
        ring = poly[0]
        for p in ring:
            x, y = proj(p[0], p[1])
            xs.append(x)
            ys.append(y)
    return sum(xs) / len(xs), sum(ys) / len(ys)


def main():
    if not os.path.exists(RAW):
        url = "https://geo.datav.aliyun.com/areas_v3/bound/320000_full.json"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = json.loads(urllib.request.urlopen(req, timeout=30).read())
        with open(RAW, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    else:
        data = json.load(open(RAW, encoding="utf-8"))

    cities = []
    for feat in data["features"]:
        p = feat["properties"]
        geom = feat["geometry"]
        paths = geom_to_paths(geom)
        cx, cy = centroid_of(geom)
        dx, dy = LABEL_OFFSETS.get(p["adcode"], (0, 0))
        cx += dx
        cy += dy
        cities.append({
            "name": p["name"],            # 南京市
            "adcode": p["adcode"],
            "paths": paths,
            "cx": round(cx, 1),
            "cy": round(cy, 1),
        })

    lines = ["/* 江苏 13 市边界 SVG 数据（阿里 DataV GeoAtlas 公开数据，线性投影示意） */",
             "var __JIANGSU_MAP__ = ["]
    for c in cities:
        lines.append("  {")
        lines.append('    name: "%s",' % c["name"])
        lines.append('    adcode: "%s",' % c["adcode"])
        lines.append("    cx: %s, cy: %s," % (c["cx"], c["cy"]))
        lines.append("    paths: [")
        for d in c["paths"]:
            lines.append('      "%s",' % d)
        lines.append("    ]")
        lines.append("  },")
    lines.append("];")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("OK ->", OUT, len(cities), "cities")


if __name__ == "__main__":
    main()
