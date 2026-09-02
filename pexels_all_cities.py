#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
12 市 96 条目批量精准配图：Pexels 多关键词 + alt 二次过滤
产出:
  images/pexels_all/<城市>/<cat>_<idx>.jpg   每条目最佳 1 张
  picks_all.json                              全部配图清单
用法: python pexels_all_cities.py [城市名...]   (默认全部 12 市)
"""
import json
import os
import subprocess
import sys
import time
import urllib.parse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEY = open(os.path.join(BASE_DIR, ".pexels_key"), encoding="utf-8").read().strip()
OUT_DIR = os.path.join(BASE_DIR, "images", "pexels_all")
os.makedirs(OUT_DIR, exist_ok=True)

PER_QUERY = 25
OUTPUT_SIZE = "large"

# PLAN: (城市, 类别, 序号, 中文名, [搜索词], [must 含其一], [banned 排除其一])
PLAN = [
    # ========== 苏州 ==========
    ("苏州", "scenery", 0, "拙政园", ["Humble Administrator's Garden Suzhou", "Suzhou classical garden"], ["suzhou", "garden"], ["west lake", "beijing", "hangzhou", "kyoto"]),
    ("苏州", "scenery", 1, "平江路", ["Pingjiang Road Suzhou", "Suzhou canal street", "Suzhou water town"], ["suzhou"], ["venice", "beijing"]),
    ("苏州", "scenery", 2, "金鸡湖", ["Jinji Lake Suzhou", "Suzhou lake"], ["suzhou", "lake"], []),
    ("苏州", "food", 0, "苏式汤面", ["Suzhou noodle soup", "Chinese noodle soup bowl"], ["noodle"], ["burger", "pizza"]),
    ("苏州", "food", 1, "松鼠鳜鱼", ["sweet and sour fish Chinese", "squirrel fish", "fried whole fish"], ["fish"], ["aquarium", "raw", "sashimi", "swimming"]),
    ("苏州", "food", 2, "桂花糖藕", ["sweet lotus root", "lotus root dessert", "stuffed lotus root"], ["lotus"], []),
    ("苏州", "story", 0, "东方水城", ["Suzhou canal boats", "Suzhou water town"], ["suzhou", "canal"], ["venice"]),
    ("苏州", "story", 1, "园林与气候", ["Suzhou garden pavilion", "Chinese garden"], ["garden"], ["beijing"]),
    # ========== 南通 ==========
    ("南通", "scenery", 0, "狼山", ["Langshan Mountain", "Nantong Langshan"], ["mountain", "nantong"], []),
    ("南通", "scenery", 1, "濠河", ["Nantong Hao River", "Nantong river"], ["nantong", "river"], []),
    ("南通", "scenery", 2, "南通博物苑", ["Nantong Museum", "Nantong building"], ["nantong", "museum"], []),
    ("南通", "food", 0, "炒文蛤", ["stir fried clams", "Chinese clams"], ["clam"], ["raw", "beach", "seashore"]),
    ("南通", "food", 1, "醉泥螺", ["marinated snails", "pickled snails Chinese"], ["snail"], ["garden", "raw"]),
    ("南通", "food", 2, "河豚宴", ["pufferfish dish", "fugu dish"], ["puffer", "fugu"], []),
    ("南通", "story", 0, "张謇与中国近代第一城", ["Nantong city", "Nantong street"], ["nantong"], []),
    ("南通", "story", 1, "唐闸古镇", ["Nantong ancient town", "Chinese ancient town"], ["nantong", "town"], []),
    # ========== 连云港 ==========
    ("连云港", "scenery", 0, "花果山", ["Huaguoshan Mountain", "Huaguo Mountain"], ["huaguo", "mountain"], []),
    ("连云港", "scenery", 1, "连岛", ["Lianyungang island", "Lianyungang coast"], ["lianyungang", "island", "coast"], []),
    ("连云港", "scenery", 2, "海上云台山", ["Yuntai Mountain", "Lianyungang mountain"], ["yuntai", "lianyungang", "mountain"], []),
    ("连云港", "food", 0, "小鱼煎饼", ["fish pancake", "seafood pancake"], ["pancake", "fish"], ["american", "breakfast"]),
    ("连云港", "food", 1, "葛根粉", ["kudzu jelly", "kudzu dessert"], ["kudzu"], []),
    ("连云港", "food", 2, "灌云豆丹", ["soybean worm", "soybean dish"], ["soybean"], []),
    ("连云港", "story", 0, "花果山与西游记", ["monkey mountain China", "macaque monkey"], ["monkey"], ["africa", "india"]),
    ("连云港", "story", 1, "海州古港与海上丝路", ["Lianyungang port", "sea port China"], ["port", "harbor"], []),
    # ========== 宿迁 ==========
    ("宿迁", "scenery", 0, "项王故里", ["Xiang Yu statue", "ancient warrior statue China"], ["statue", "suqian"], []),
    ("宿迁", "scenery", 1, "三台山森林公园", ["forest park China", "mountain forest"], ["forest", "mountain"], ["snow"]),
    ("宿迁", "scenery", 2, "骆马湖", ["Luoma Lake", "Suqian lake"], ["lake", "suqian"], []),
    ("宿迁", "food", 0, "黄狗猪头肉", ["braised pork", "Chinese pork dish"], ["pork"], ["raw", "bbq", "burger"]),
    ("宿迁", "food", 1, "车轮饼", ["round pastry", "wheel pastry"], ["pastry", "cake"], ["birthday"]),
    ("宿迁", "food", 2, "骆马湖银鱼蒸蛋", ["steamed egg fish", "silver fish dish", "fish egg soup"], ["fish", "egg"], []),
    ("宿迁", "story", 0, "霸王与酒都", ["Suqian", "Chinese liquor"], ["suqian", "liquor"], []),
    ("宿迁", "story", 1, "黄河故道", ["Yellow River", "Yellow River China"], ["yellow river"], []),
    # ========== 淮安 ==========
    ("淮安", "scenery", 0, "里运河文化长廊", ["Grand Canal Huai'an", "Huai'an canal", "China Grand Canal"], ["canal", "huai'an"], ["venice"]),
    ("淮安", "scenery", 1, "周恩来故里", ["Zhou Enlai memorial", "Huai'an"], ["huai'an", "zhou enlai"], []),
    ("淮安", "scenery", 2, "河下古镇", ["Huai'an ancient town", "Chinese ancient town"], ["huai'an", "town"], []),
    ("淮安", "food", 0, "软兜长鱼", ["eel dish Chinese", "braised eel"], ["eel"], ["raw", "aquarium"]),
    ("淮安", "food", 1, "平桥豆腐", ["tofu dish Chinese", "mapo tofu"], ["tofu"], []),
    ("淮安", "food", 2, "盱眙龙虾", ["spicy crayfish", "crawfish boil"], ["crayfish", "crawfish"], []),
    ("淮安", "story", 0, "运河之都", ["Grand Canal China", "Chinese canal"], ["canal"], ["venice", "amsterdam"]),
    ("淮安", "story", 1, "西游记与淮安", ["monkey king statue", "monkey statue"], ["monkey"], []),
    # ========== 徐州 ==========
    ("徐州", "scenery", 0, "云龙湖", ["Yunlong Lake", "Xuzhou lake"], ["yunlong", "lake", "xuzhou"], []),
    ("徐州", "scenery", 1, "汉文化景区", ["Han dynasty museum", "Chinese han dynasty"], ["han", "xuzhou"], []),
    ("徐州", "scenery", 2, "龟山汉墓", ["Han tomb", "Xuzhou tomb"], ["tomb", "xuzhou"], []),
    ("徐州", "food", 0, "地锅鸡", ["iron pot chicken", "pot stew chicken"], ["chicken", "pot"], ["raw", "farm", "coop"]),
    ("徐州", "food", 1, "饣它汤配八股油条", ["youtiao", "Chinese fried dough", "breakfast soup"], ["dough", "youtiao", "soup"], []),
    ("徐州", "food", 2, "伏羊节羊肉汤", ["lamb soup", "mutton soup Chinese"], ["lamb", "mutton"], ["raw"]),
    ("徐州", "story", 0, "彭祖与徐州饮食", ["Xuzhou city", "Xuzhou"], ["xuzhou"], []),
    ("徐州", "story", 1, "东方雅典", ["Xuzhou"], ["xuzhou"], []),
    # ========== 常州 ==========
    ("常州", "scenery", 0, "中华恐龙园", ["dinosaur park", "dinosaur skeleton museum"], ["dinosaur"], []),
    ("常州", "scenery", 1, "天目湖", ["Tianmu Lake", "Tianmu lake China"], ["tianmu", "lake"], []),
    ("常州", "scenery", 2, "春秋淹城", ["ancient city moat", "ancient city China"], ["ancient", "moat"], []),
    ("常州", "food", 0, "天目湖砂锅鱼头", ["fish head soup", "clay pot fish"], ["fish"], ["aquarium", "raw"]),
    ("常州", "food", 1, "常州大麻糕", ["sesame cake", "Chinese sesame pastry"], ["sesame", "pastry"], []),
    ("常州", "food", 2, "银丝面", ["thin noodles", "noodle soup Chinese"], ["noodle"], ["burger"]),
    ("常州", "story", 0, "龙城之名", ["Changzhou", "Changzhou city"], ["changzhou"], []),
    ("常州", "story", 1, "淹城与春秋", ["ancient city moat", "ancient ruins China"], ["ancient", "moat"], []),
    # ========== 盐城 ==========
    ("盐城", "scenery", 0, "中华麋鹿园", ["Pere David's deer", "milu deer", "elk deer"], ["deer"], ["hunting", "snow"]),
    ("盐城", "scenery", 1, "丹顶鹤湿地", ["red-crowned crane", "tancho crane", "japanese crane"], ["red", "japanese", "tancho"], ["grey", "crowned", "africa", "savanna", "hungary", "brolga", "sandhill", "demoiselle", "sarus", "wattled", "black-crowned", "gray-crowned"]),
    ("盐城", "scenery", 2, "荷兰花海", ["tulip field", "flower field colorful"], ["tulip", "flower"], []),
    ("盐城", "food", 0, "东台鱼汤面", ["fish soup noodles", "fish noodle soup"], ["fish", "noodle"], []),
    ("盐城", "food", 1, "建湖藕粉圆子", ["lotus root balls", "lotus dessert"], ["lotus"], []),
    ("盐城", "food", 2, "大纵湖大闸蟹", ["hairy crab", "Chinese mitten crab", "steamed crab"], ["crab"], ["raw", "beach"]),
    ("盐城", "story", 0, "因盐得名", ["salt field", "salt pans China"], ["salt"], []),
    ("盐城", "story", 1, "世界自然遗产", ["coastal wetland", "wetland birds"], ["wetland"], []),
    # ========== 泰州 ==========
    ("泰州", "scenery", 0, "溱潼古镇", ["Qintong", "Taizhou ancient town"], ["qintong", "town", "taizhou"], []),
    ("泰州", "scenery", 1, "溱湖国家湿地公园", ["wetland park", "wetland China"], ["wetland"], []),
    ("泰州", "scenery", 2, "凤城河", ["Taizhou river", "city river China"], ["river", "taizhou"], []),
    ("泰州", "food", 0, "靖江蟹黄汤包", ["crab soup dumpling", "xiaolongbao"], ["dumpling", "xiaolongbao"], []),
    ("泰州", "food", 1, "泰州早茶", ["dim sum", "Chinese breakfast"], ["dim sum", "breakfast"], []),
    ("泰州", "food", 2, "溱湖八鲜", ["freshwater fish dish", "river fish"], ["fish"], ["aquarium", "raw"]),
    ("泰州", "story", 0, "梅兰芳与水城", ["Taizhou", "Taizhou Jiangsu"], ["taizhou"], []),
    ("泰州", "story", 1, "尘世幸福", ["Taizhou street", "Taizhou"], ["taizhou"], []),
    # ========== 扬州 ==========
    ("扬州", "scenery", 0, "瘦西湖", ["Slender West Lake Yangzhou", "Slender West Lake"], ["slender west lake", "yangzhou"], ["hangzhou"]),
    ("扬州", "scenery", 1, "个园", ["Geyuan Garden", "Yangzhou garden"], ["geyuan", "yangzhou", "garden"], []),
    ("扬州", "scenery", 2, "东关街", ["Dongguan Street Yangzhou", "Yangzhou street"], ["yangzhou", "street"], []),
    ("扬州", "food", 0, "扬州炒饭", ["Yangzhou fried rice", "Chinese fried rice"], ["fried rice"], []),
    ("扬州", "food", 1, "狮子头", ["lion's head meatball", "Chinese meatball"], ["meatball"], []),
    ("扬州", "food", 2, "三丁包子", ["Chinese steamed bun", "baozi"], ["bun", "baozi", "steamed"], []),
    ("扬州", "story", 0, "运河与繁华", ["Grand Canal Yangzhou", "canal China"], ["canal", "yangzhou"], ["venice"]),
    ("扬州", "story", 1, "盐商与园林", ["Yangzhou garden", "Chinese garden"], ["yangzhou", "garden"], []),
    # ========== 镇江 ==========
    ("镇江", "scenery", 0, "金山", ["Jinshan Temple", "Zhenjiang Jinshan"], ["jinshan", "zhenjiang"], []),
    ("镇江", "scenery", 1, "北固山", ["Beigu Mountain", "Beigushan", "Zhenjiang mountain"], ["beigu", "zhenjiang", "mountain"], []),
    ("镇江", "scenery", 2, "西津渡古街", ["Xijindu", "Zhenjiang street"], ["xijindu", "zhenjiang", "street"], []),
    ("镇江", "food", 0, "锅盖面", ["knife cut noodles", "Chinese knife noodles"], ["noodle"], ["burger"]),
    ("镇江", "food", 1, "肴肉", ["pork jelly", "Chinese jelly meat"], ["jelly", "pork"], []),
    ("镇江", "food", 2, "镇江香醋", ["Chinese black vinegar", "vinegar bottle"], ["vinegar"], []),
    ("镇江", "story", 0, "镇江三怪", ["Zhenjiang", "Zhenjiang city"], ["zhenjiang"], []),
    ("镇江", "story", 1, "江河交汇", ["Yangtze River", "river confluence"], ["river", "yangtze"], ["beach", "family"]),
    # ========== 无锡 ==========
    ("无锡", "scenery", 0, "鼋头渚", ["Yuantouzhu", "Taihu Lake"], ["yuantouzhu", "taihu"], []),
    ("无锡", "scenery", 1, "灵山胜境", ["Lingshan Grand Buddha", "Lingshan Buddha"], ["buddha", "lingshan"], []),
    ("无锡", "scenery", 2, "惠山古镇", ["Huishan ancient town", "Wuxi ancient town"], ["wuxi", "town"], []),
    ("无锡", "food", 0, "无锡酱排骨", ["braised pork ribs", "Chinese pork ribs"], ["ribs"], ["raw", "bbq"]),
    ("无锡", "food", 1, "无锡小笼包", ["xiaolongbao", "soup dumpling"], ["dumpling", "xiaolongbao"], []),
    ("无锡", "food", 2, "太湖三白", ["whitebait", "Taihu fish", "silver fish"], ["fish", "whitebait"], ["aquarium"]),
    ("无锡", "story", 0, "泰伯奔吴", ["Wuxi", "Wuxi city"], ["wuxi"], []),
    ("无锡", "story", 1, "二泉映月", ["erhu", "Chinese erhu music"], ["erhu"], []),
]


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


def pick_best(queries, must, banned):
    seen = set()
    best, best_score = None, -1
    for q in queries:
        try:
            data = search(q)
        except Exception as e:
            print("    搜索失败 %s: %s" % (q, e))
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
            score = sum(1 for w in must if w in alt)
            if score > best_score:
                best_score = score
                best = {"alt": ph.get("alt") or "", "photographer": (ph.get("photographer") or "") + " (Pexels)",
                        "url": url, "w": ph.get("width"), "h": ph.get("height")}
        time.sleep(0.35)
    return best


def main():
    cities = sys.argv[1:] or sorted(set(p[0] for p in PLAN))
    results = {}
    for city in cities:
        city_dir = os.path.join(OUT_DIR, city)
        os.makedirs(city_dir, exist_ok=True)
        for _city, cat, idx, label, queries, must, banned in [p for p in PLAN if p[0] == city]:
            key = "%s_%d" % (cat, idx)
            best = pick_best(queries, must, banned)
            if not best:
                print("[%s/%s] 未命中" % (city, label))
                results.setdefault(city, {})[key] = None
                continue
            rel = os.path.join("images", "pexels_all", city, "%s.jpg" % key).replace("\\", "/")
            fpath = os.path.join(BASE_DIR, rel)
            if os.path.isfile(fpath) and os.path.getsize(fpath) > 2000:
                pass
            elif curl_download(best["url"], fpath):
                pass
            else:
                print("[%s/%s] 下载失败" % (city, label))
                results.setdefault(city, {})[key] = None
                continue
            best["rel"] = rel
            results.setdefault(city, {})[key] = best
            print("[%s/%s] 命中 | %sx%s | %s" % (city, label, best["w"], best["h"], best["alt"][:60]))
            time.sleep(0.3)

    with open(os.path.join(BASE_DIR, "picks_all.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("\n完成，已生成 picks_all.json")


if __name__ == "__main__":
    main()
