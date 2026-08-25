#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错配重配：对可疑条目用加严 banned（排除国家/他省地名）+ 精确词重搜
原则：命中就换，配不到就留空（宁缺毋滥）
产出: 更新 images/pexels_all/、picks_all.json
"""
import json
import os
import subprocess
import time
import urllib.parse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEY = open(os.path.join(BASE_DIR, ".pexels_key"), encoding="utf-8").read().strip()

# 全局排除：国外/他省常见错配词（命中即弃）
GLOBAL_BANNED = [
    "kashmir", "india", "poland", "serbia", "roman", "japan", "osaka", "kyoto",
    "vietnam", "canada", "muskoka", "australia", "kazakhstan", "almaty",
    "bangkok", "thailand", "guangzhou", "baiyun", "lijiang", "zhangjiajie",
    "wuzhen", "taiwan", "korea", "korean", "samgyetang", "yichang", "istanbul",
    "greece", "athens", "italy", "italian", "pasta", "venice", "amsterdam",
    "london", "paris", "new york", "san francisco", "sydney", "lighthouse",
    "shirtless", "beach", "surf", "snow", "winter", "desert",
]

# 重配清单: (城市, key, 中文名, [查询词], [must 含其一], [额外 banned])
RETRY = [
    # ===== 南通 =====
    ("南通", "scenery_1", "濠河", ["Nantong Hao River", "Nantong river", "Jiangsu river"], ["nantong", "river"], []),
    ("南通", "scenery_2", "南通博物苑", ["Nantong architecture", "Nantong building", "Nantong museum"], ["nantong"], ["highway", "traffic"]),
    ("南通", "story_0", "张謇与中国近代第一城", ["Nantong city", "Nantong street", "Jiangsu street"], ["nantong"], ["market", "mask"]),
    ("南通", "story_1", "唐闸古镇", ["Nantong ancient town", "Jiangsu ancient town"], ["nantong"], ["highway"]),
    # ===== 宿迁 =====
    ("宿迁", "scenery_0", "项王故里", ["ancient Chinese palace", "Chinese historical architecture", "Xiang Yu"], ["chinese", "ancient", "xiang"], ["guanyu", "taiwan"]),
    ("宿迁", "scenery_1", "三台山森林公园", ["China forest park", "Jiangsu forest"], ["forest", "china"], ["kashmir", "india"]),
    ("宿迁", "scenery_2", "骆马湖", ["Jiangsu lake", "China lake"], ["lake", "china"], ["muskoka", "canada"]),
    ("宿迁", "food_1", "车轮饼", ["round Chinese pastry", "flat cake", "sesame cake"], ["cake", "pastry"], ["mooncake", "birthday"]),
    ("宿迁", "story_1", "黄河故道", ["Yellow River China", "Yellow River bend"], ["yellow river"], ["poland"]),
    # ===== 常州 =====
    ("常州", "scenery_2", "春秋淹城", ["ancient Chinese city", "Chinese city wall ancient"], ["chinese", "ancient"], ["osaka", "japan"]),
    ("常州", "story_1", "淹城与春秋", ["ancient Chinese ruins", "Chinese ancient architecture"], ["chinese", "ancient"], ["osaka", "japan"]),
    # ===== 徐州 =====
    ("徐州", "scenery_0", "云龙湖", ["Xuzhou lake", "Jiangsu lake Xuzhou"], ["xuzhou"], ["shirtless"]),
    ("徐州", "scenery_2", "龟山汉墓", ["ancient Chinese tomb", "Han dynasty"], ["chinese", "han"], ["serbia", "roman"]),
    ("徐州", "food_0", "地锅鸡", ["Chinese clay pot chicken", "stewed chicken pot"], ["chicken"], ["korean", "samgyetang", "raw", "farm"]),
    ("徐州", "story_0", "彭祖与徐州饮食", ["Xuzhou Jiangsu", "Xuzhou"], ["xuzhou"], ["camera", "toy", "coffee"]),
    ("徐州", "story_1", "东方雅典", ["Xuzhou Jiangsu", "Xuzhou city"], ["xuzhou"], ["shirtless", "man"]),
    # ===== 泰州 =====
    ("泰州", "scenery_0", "溱潼古镇", ["Jiangsu ancient town", "Taizhou Jiangsu town"], ["jiangsu", "town"], ["sculpture", "wall"]),
    ("泰州", "scenery_1", "溱湖国家湿地公园", ["China wetland", "Jiangsu wetland"], ["wetland", "china"], ["vietnam"]),
    ("泰州", "scenery_2", "凤城河", ["Taizhou Jiangsu river", "Jiangsu river"], ["jiangsu", "river"], ["lighthouse"]),
    ("泰州", "story_0", "梅兰芳与水城", ["Taizhou Jiangsu", "Jiangsu city"], ["jiangsu"], ["zhejiang", "jiaojiang", "taizhou zhejiang"]),
    ("泰州", "story_1", "尘世幸福", ["Taizhou Jiangsu", "Jiangsu street"], ["jiangsu"], ["zhejiang", "jiaojiang", "baker", "bakery"]),
    # ===== 淮安 =====
    ("淮安", "scenery_0", "里运河文化长廊", ["Huai'an canal", "Grand Canal China"], ["huai'an", "canal"], ["wuzhen"]),
    ("淮安", "story_0", "运河之都", ["Grand Canal China", "Chinese canal"], ["canal", "china"], ["wuzhen", "venice", "amsterdam"]),
    # ===== 连云港 =====
    ("连云港", "scenery_0", "花果山", ["Huaguoshan", "Jiangsu mountain"], ["huaguo", "jiangsu"], ["almaty", "kazakhstan"]),
    ("连云港", "scenery_1", "连岛", ["Lianyungang coast", "Chinese coast island"], ["coast", "island", "lianyungang"], []),
    ("连云港", "scenery_2", "海上云台山", ["Yuntai Mountain", "Jiangsu mountain"], ["yuntai", "jiangsu"], ["guangzhou", "baiyun"]),
    ("连云港", "food_0", "小鱼煎饼", ["Chinese fish pancake", "fish cake China"], ["fish"], ["salmon", "potato"]),
    ("连云港", "story_0", "花果山与西游记", ["monkey China", "macaque monkey"], ["monkey"], ["zhangjiajie", "africa"]),
    # ===== 镇江 =====
    ("镇江", "scenery_0", "金山", ["Jinshan Temple", "Zhenjiang temple"], ["zhenjiang", "jinshan"], []),
    ("镇江", "scenery_1", "北固山", ["Beigu Mountain", "Jiangsu mountain"], ["beigu", "jiangsu"], ["almaty"]),
    ("镇江", "scenery_2", "西津渡古街", ["Zhenjiang street", "Jiangsu old street"], ["zhenjiang", "jiangsu"], ["jingde", "sign"]),
    ("镇江", "food_0", "锅盖面", ["Chinese noodle soup", "noodles China"], ["noodle", "chinese"], ["pasta", "italian", "homemade"]),
    ("镇江", "story_0", "镇江三怪", ["Zhenjiang Jiangsu", "Jiangsu city"], ["zhenjiang", "jiangsu"], ["train", "railway", "station"]),
    ("镇江", "story_1", "江河交汇", ["Yangtze River China", "Yangtze river"], ["yangtze"], ["yichang", "beach", "family"]),
    # ===== 无锡 =====
    ("无锡", "scenery_2", "惠山古镇", ["Wuxi ancient town", "Jiangsu town"], ["wuxi", "jiangsu"], ["lijiang"]),
]


def search(q):
    url = "https://api.pexels.com/v1/search?" + urllib.parse.urlencode({"query": q, "per_page": 30})
    out = subprocess.run(
        ["curl", "-s", "--max-time", "25", "-H", "Authorization: " + KEY, url],
        capture_output=True, text=True
    ).stdout
    return json.loads(out)


def dl(url, path):
    r = subprocess.run(["curl", "-s", "--max-time", "60", "-L", "-o", path, url], capture_output=True)
    return r.returncode == 0 and os.path.isfile(path) and os.path.getsize(path) > 2000


def main():
    picks = json.load(open(os.path.join(BASE_DIR, "picks_all.json"), encoding="utf-8"))
    # 记录全站已用 URL，避免同图重复
    used_urls = set()
    for city, items in picks.items():
        for k, v in items.items():
            if v:
                used_urls.add(v.get("url", ""))

    ok, miss = 0, 0
    for city, key, label, queries, must, extra_banned in RETRY:
        banned = GLOBAL_BANNED + extra_banned
        best, best_score = None, -1
        seen = set()
        for q in queries:
            try:
                data = search(q)
            except Exception:
                time.sleep(1)
                continue
            for ph in data.get("photos", []):
                alt = (ph.get("alt") or "").lower()
                if not alt:
                    continue
                url = ph["src"].get("large")
                if not url or url in seen or url in used_urls:
                    continue
                seen.add(url)
                if not any(w in alt for w in must):
                    continue
                if any(w in alt for w in banned):
                    continue
                sc = sum(1 for w in must if w in alt)
                if sc > best_score:
                    best_score = sc
                    best = {"alt": ph.get("alt") or "", "photographer": (ph.get("photographer") or "") + " (Pexels)",
                            "url": url, "w": ph.get("width"), "h": ph.get("height")}
            time.sleep(0.35)
        if not best:
            print("[%s/%s] 重配未命中 -> 留空" % (city, label))
            picks[city][key] = None
            miss += 1
            continue
        rel = "images/pexels_all/%s/%s.jpg" % (city, key)
        fpath = os.path.join(BASE_DIR, rel)
        if not (os.path.isfile(fpath) and os.path.getsize(fpath) > 2000):
            if not dl(best["url"], fpath):
                print("[%s/%s] 下载失败 -> 留空" % (city, label))
                picks[city][key] = None
                miss += 1
                continue
        best["rel"] = rel
        picks[city][key] = best
        used_urls.add(best["url"])
        print("[%s/%s] 重配命中 | %sx%s | %s" % (city, label, best["w"], best["h"], best["alt"][:70]))
        ok += 1
        time.sleep(0.3)

    with open(os.path.join(BASE_DIR, "picks_all.json"), "w", encoding="utf-8") as f:
        json.dump(picks, f, ensure_ascii=False, indent=2)
    print("\n重配完成: 命中 %d, 留空 %d" % (ok, miss))


if __name__ == "__main__":
    main()
