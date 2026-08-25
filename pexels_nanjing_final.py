#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
南京 8 条目精准配图：Pexels 多关键词 + alt 二次过滤，自动选最佳
产出:
  images/nanjing_pexels/<key>.jpg   每条目最佳 1 张
  nanjing_picks.json                配图清单（key/alt/摄影师/相关性）
"""
import json
import os
import re
import subprocess
import time
import urllib.parse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEY = open(os.path.join(BASE_DIR, ".pexels_key"), encoding="utf-8").read().strip()
OUT_DIR = os.path.join(BASE_DIR, "images", "nanjing_pexels")
os.makedirs(OUT_DIR, exist_ok=True)

# 条目: 搜索词列表 + must(alt必须含其一) + banned(alt排除其一)
ITEMS = [
    ("scenery_0", "紫金山", ["Zijin Mountain Nanjing", "Sun Yat-sen Mausoleum Nanjing"], ["nanjing", "mausoleum"], ["west lake", "hangzhou", "beijing", "shanghai"]),
    ("scenery_1", "玄武湖", ["Xuanwu Lake Nanjing", "Nanjing Xuanwu Lake"], ["xuanwu"], ["west lake", "hangzhou", "beijing"]),
    ("scenery_2", "明城墙·秦淮河", ["Nanjing City Wall", "Qinhuai River Nanjing", "Nanjing ancient city wall"], ["nanjing"], ["great wall", "beijing", "xi'an", "xian"]),
    ("food_0", "鸭血粉丝汤", ["duck blood vermicelli soup", "vermicelli soup Chinese", "Nanjing duck soup", "duck noodle soup"], ["soup", "vermicelli", "noodle"], ["burger", "pizza", "salad", "raw duck"]),
    ("food_1", "盐水鸭", ["roast duck Chinese", "braised duck", "Chinese duck dish", "Nanjing salted duck dish", "plated duck"], ["duck"], ["burger", "pizza", "salad", "swimming", "splashing", "lake", "wild", "flying", "pond", "river", "feather", "beak", "wildlife", "animal", "water", "wet"]),
    ("food_2", "赤豆元宵", ["red bean glutinous rice balls", "tangyuan red bean", "Chinese sweet rice balls"], ["rice ball", "tangyuan", "red bean", "glutinous", "sweet rice"], ["mochi ice", "burger"]),
    ("story_0", "六朝烟水", ["Qinhuai River Nanjing night", "Nanjing Fuzimiao Confucius Temple", "Nanjing ancient street"], ["nanjing"], ["west lake", "hangzhou", "beijing"]),
    ("story_1", "石头城与长江", ["Nanjing Yangtze River Bridge", "Nanjing Yangtze Bridge", "Yangtze River Nanjing bridge"], ["nanjing", "bridge", "yangtze"], ["three gorges", "wuhan", "chongqing", "family", "kids", "children", "beach"]),
]

PER_QUERY = 30
OUTPUT_SIZE = "large"


def curl_json(url):
    out = subprocess.run(
        ["curl", "-s", "--max-time", "25", "-H", "Authorization: " + KEY, url],
        capture_output=True, text=True
    ).stdout
    return json.loads(out)


def curl_download(url, path):
    out = subprocess.run(
        ["curl", "-s", "--max-time", "60", "-L", "-o", path, url],
        capture_output=True
    )
    return out.returncode == 0 and os.path.isfile(path) and os.path.getsize(path) > 2000


def search(query):
    url = "https://api.pexels.com/v1/search?" + urllib.parse.urlencode(
        {"query": query, "per_page": PER_QUERY, "page": 1}
    )
    return curl_json(url)


def pick_best(key, label, queries, must, banned):
    """返回最佳命中（相关性分：alt 含 must 且含 label 英文核心词越高分）"""
    seen = set()
    best = None
    best_score = -1
    for q in queries:
        try:
            data = search(q)
        except Exception as e:
            print("  [%s] 搜索失败 %s: %s" % (label, q, e))
            time.sleep(1)
            continue
        for ph in data.get("photos", []):
            alt = (ph.get("alt") or "").lower()
            if not alt:
                continue
            url = ph["src"].get(OUTPUT_SIZE)
            if not url or url in seen:
                continue
            seen.add(url)
            if not any(w in alt for w in must):
                continue
            if any(w in alt for w in banned):
                continue
            score = sum(1 for w in must if w in alt) + (1 if label.lower() in alt else 0)
            if score > best_score:
                best_score = score
                best = {
                    "key": key, "label": label, "alt": ph.get("alt") or "",
                    "photographer": (ph.get("photographer") or "") + " (Pexels)",
                    "page": ph.get("url", ""), "url": url,
                    "w": ph.get("width"), "h": ph.get("height"),
                }
        time.sleep(0.4)
        if best and best_score >= 2:  # 已命中较精准，提前结束
            break
    return best, best_score


def main():
    results = {}
    for key, label, queries, must, banned in ITEMS:
        best, score = pick_best(key, label, queries, must, banned)
        if not best:
            print("[%s] 未找到精准图" % label)
            results[key] = None
            continue
        fname = key + ".jpg"
        rel = os.path.join("images", "nanjing_pexels", fname).replace("\\", "/")
        fpath = os.path.join(BASE_DIR, rel)
        if curl_download(best["url"], fpath):
            best["rel"] = rel
            best["score"] = score
            results[key] = best
            print("[%s] 命中%d | %s | %sx%s | %s" % (label, score, best["alt"][:70], best["w"], best["h"], best["photographer"]))
        else:
            print("[%s] 下载失败 %s" % (label, best["url"][:70]))
            results[key] = None
        time.sleep(0.3)

    with open(os.path.join(BASE_DIR, "nanjing_picks.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("\n已生成 nanjing_picks.json")


if __name__ == "__main__":
    main()
