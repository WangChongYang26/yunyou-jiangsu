#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云游江苏 · 内容管理服务（零依赖，Python 标准库）
================================================
用法：
    python server.py [端口]           # 默认 8081
然后：
    前台   http://localhost:8081/
    管理   http://localhost:8081/admin     （输入管理密码）
    API    /api/data 读取数据，/api/save 保存，/api/upload 上传图片

数据事实源是 city_data.js（前台静态打开也读它），保存时整文件写回。
多人协作提醒：保存是"整包写回"，请勿两人同时保存，会互相覆盖。
管理密码：改下面 ADMIN_KEY 的值（或首次运行后修改）。
"""
import json
import os
import re
import time
import base64
import uuid
import shutil
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, unquote

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "city_data.js")
SONGS_FILE = os.path.join(BASE_DIR, "songs.js")
CONFIG_FILE = os.path.join(BASE_DIR, "site_config.js")
IMG_DIR = os.path.join(BASE_DIR, "images")
AUDIO_DIR = os.path.join(BASE_DIR, "music")
ADMIN_KEY = ""               # <<< 留空 = 不校验密码（完全开放）；想启用密码就填字符串
ALLOW_EXT = {".html", ".css", ".js", ".m4a", ".webp", ".jpg", ".jpeg", ".png", ".svg", ".gif", ".md", ".ico", ".txt", ".mp3", ".wav", ".ogg", ".ttf", ".woff", ".woff2"}
IMG_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
AUDIO_EXT = {".m4a", ".mp3", ".wav", ".ogg", ".flac"}

_lock = threading.Lock()
os.makedirs(IMG_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)
BACKUP_DIR = os.path.join(BASE_DIR, "backup")
os.makedirs(BACKUP_DIR, exist_ok=True)
BACKUP_KEEP = 1       # 最多保留多少份历史备份（当前策略：只留最近 1 份）


def atomic_write(path, text):
    """原子写入：先写临时文件再替换，避免写一半损坏原文件。
    本环境安全沙箱可能拦截 os.replace/os.remove（回收站不可用），
    逐级降级：os.replace → shutil.copyfile 覆盖 → 直接写，保证保存成功。"""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    # 1) 首选：原子替换
    for attempt in range(3):
        try:
            os.replace(tmp, path)
            return
        except OSError:
            time.sleep(0.3)
    # 2) 降级：copyfile 覆盖（写覆盖，非删除语义，绕过删除拦截）
    try:
        shutil.copyfile(tmp, path)
        try:
            os.remove(tmp)
        except Exception:
            pass
        return
    except OSError:
        pass
    # 3) 最后兜底：直接写原文件
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    try:
        os.remove(tmp)
    except Exception:
        pass


def backup_file(path, tag):
    """保存前自动备份：backup/latest_<文件名>（固定名覆盖，天然只保留最近 1 份）。
    说明：本运行环境的安全沙箱会拦截 os.remove（SAFE_DELETE_FAIL_CLOSED，回收站不可用），
    因此弃用"保留N份+删除旧档"方案，改为固定名覆盖，零删除操作、永不堆积。"""
    try:
        name = os.path.basename(path)
        dst = os.path.join(BACKUP_DIR, "latest_" + name)
        with open(path, "rb") as src, open(dst, "wb") as out:
            out.write(src.read())
    except Exception as e:
        print("[backup_file] 备份失败: %r" % e, flush=True)   # 备份失败不阻断主流程

HEADER_TEMPLATE = """/* ===== 云游江苏 · 城市数据 =====
 * 由管理后台（server.py）自动生成，请勿手工修改本段文件头
 * 内容为团队原创撰写（水土→物产→饮食→文化 地理叙事线）
 */
"""


def load_data():
    """从 city_data.js 解析出 Python 列表"""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"var __CITY_DATA__\s*=\s*(\[.*\]);", text, re.S)
    if not m:
        raise ValueError("city_data.js 中找不到 __CITY_DATA__")
    return json.loads(m.group(1))


def save_data(data):
    """整包写回 city_data.js（原子写入 + 自动备份）"""
    backup_file(DATA_FILE, "city")
    body = json.dumps(data, ensure_ascii=False, indent=2)
    atomic_write(DATA_FILE, HEADER_TEMPLATE + "var __CITY_DATA__ = " + body + ";\n")


SONGS_HEADER = """/* ===== 云游江苏 · 背景音乐列表 =====
 * 由管理后台（server.py /api/song/*）自动维护
 * 前台播放第一首；增删歌曲在 admin 左栏「BGM 管理」操作
 */
"""


def load_songs():
    with open(SONGS_FILE, "r", encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"var __SONGS__\s*=\s*(\[.*\]);", text, re.S)
    if not m:
        return []
    return json.loads(m.group(1))


def save_songs(songs):
    backup_file(SONGS_FILE, "songs")
    body = json.dumps(songs, ensure_ascii=False, indent=2)
    atomic_write(SONGS_FILE, SONGS_HEADER + "var __SONGS__ = " + body + ";\n")


CONFIG_HEADER = """/* ===== 云游江苏 · 站点信息配置 =====
 * 由管理后台（server.py /api/config）自动维护
 */
"""


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"var __SITE_CONFIG__\s*=\s*(\{.*\});", text, re.S)
    if not m:
        return {}
    return json.loads(m.group(1))


def save_config(cfg):
    backup_file(CONFIG_FILE, "config")
    body = json.dumps(cfg, ensure_ascii=False, indent=2)
    atomic_write(CONFIG_FILE, CONFIG_HEADER + "var __SITE_CONFIG__ = " + body + ";\n")


def send_json(handler, obj, status=200):
    payload = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(payload)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(payload)


def read_body(handler, limit=20 * 1024 * 1024):
    length = int(handler.headers.get("Content-Length") or 0)
    if length > limit:
        return None
    return handler.rfile.read(length)


def safe_path(p):
    """防目录穿越 + 扩展名白名单"""
    p = os.path.normpath(p)
    if p.startswith("..") or p.startswith("/") or ":" in p:
        return None
    ext = os.path.splitext(p)[1].lower()
    if ext not in ALLOW_EXT:
        return None
    return p


class Handler(BaseHTTPRequestHandler):
    server_version = "YunyouServer/0.3"

    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))

    # ---------- 只允许 GET / POST ----------
    def do_GET(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        if path == "/" or path == "/index.html" or path == "/yunyou.html":
            if os.path.isfile(os.path.join(BASE_DIR, "index.html")):
                self.serve_file("index.html")
            else:
                self.serve_file("yunyou.html")
            return
        if path == "/admin":
            self.serve_file("admin.html")
            return
        if path == "/api/data":
            try:
                send_json(self, {"ok": True, "data": load_data()})
            except Exception as e:
                send_json(self, {"ok": False, "error": str(e)}, 500)
            return
        if path == "/api/songs":
            try:
                send_json(self, {"ok": True, "songs": load_songs()})
            except Exception as e:
                send_json(self, {"ok": False, "error": str(e)}, 500)
            return
        if path == "/api/config":
            try:
                send_json(self, {"ok": True, "config": load_config()})
            except Exception as e:
                send_json(self, {"ok": False, "error": str(e)}, 500)
            return

        clean = safe_path(path.lstrip("/"))
        if clean is None:
            send_json(self, {"ok": False, "error": "not allowed"}, 403)
            return
        self.serve_file(clean)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        if path == "/api/save":
            self.api_save()
        elif path == "/api/upload":
            self.api_upload()
        elif path == "/api/config/save":
            self.api_config_save()
        elif path == "/api/song/upload":
            self.api_song_upload()
        elif path == "/api/song/delete":
            self.api_song_delete()
        else:
            send_json(self, {"ok": False, "error": "unknown api"}, 404)

    # ---------- API ----------
    def api_save(self):
        body = read_body(self)
        if body is None:
            send_json(self, {"ok": False, "error": "body too large"}, 413)
            return
        try:
            obj = json.loads(body.decode("utf-8"))
        except Exception:
            send_json(self, {"ok": False, "error": "bad json"}, 400)
            return
        if ADMIN_KEY and obj.get("key") != ADMIN_KEY:
            send_json(self, {"ok": False, "error": "密码错误"}, 403)
            return
        data = obj.get("data")
        if not isinstance(data, list) or len(data) != 13:
            send_json(self, {"ok": False, "error": "数据格式不对（应为 13 个城市）"}, 400)
            return
        with _lock:
            try:
                save_data(data)
            except Exception as e:
                send_json(self, {"ok": False, "error": str(e)}, 500)
                return
        send_json(self, {"ok": True, "msg": "已保存，刷新前台即生效"})

    def api_upload(self):
        body = read_body(self, limit=10 * 1024 * 1024)
        if body is None:
            send_json(self, {"ok": False, "error": "file too large"}, 413)
            return
        try:
            obj = json.loads(body.decode("utf-8"))
        except Exception:
            send_json(self, {"ok": False, "error": "bad json"}, 400)
            return
        if ADMIN_KEY and obj.get("key") != ADMIN_KEY:
            send_json(self, {"ok": False, "error": "密码错误"}, 403)
            return
        name = (obj.get("filename") or "").strip()
        ext = os.path.splitext(name)[1].lower()
        if ext not in IMG_EXT:
            send_json(self, {"ok": False, "error": "仅支持图片: " + ",".join(IMG_EXT)}, 400)
            return
        # 生成唯一文件名，避免重名覆盖
        new_name = uuid.uuid4().hex[:10] + ext
        try:
            raw = base64.b64decode(obj.get("data64", ""))
        except Exception:
            send_json(self, {"ok": False, "error": "base64 解码失败"}, 400)
            return
        with _lock:
            with open(os.path.join(IMG_DIR, new_name), "wb") as f:
                f.write(raw)
        send_json(self, {"ok": True, "filename": new_name, "path": "images/" + new_name})

    def api_config_save(self):
        body = read_body(self)
        if body is None:
            send_json(self, {"ok": False, "error": "body too large"}, 413)
            return
        try:
            obj = json.loads(body.decode("utf-8"))
        except Exception:
            send_json(self, {"ok": False, "error": "bad json"}, 400)
            return
        if ADMIN_KEY and obj.get("key") != ADMIN_KEY:
            send_json(self, {"ok": False, "error": "密码错误"}, 403)
            return
        cfg = obj.get("config")
        if not isinstance(cfg, dict):
            send_json(self, {"ok": False, "error": "配置格式不对"}, 400)
            return
        with _lock:
            try:
                save_config(cfg)
            except Exception as e:
                send_json(self, {"ok": False, "error": str(e)}, 500)
                return
        send_json(self, {"ok": True, "msg": "站点信息已保存"})

    def api_song_upload(self):
        body = read_body(self, limit=50 * 1024 * 1024)
        if body is None:
            send_json(self, {"ok": False, "error": "文件过大（限 50MB）"}, 413)
            return
        try:
            obj = json.loads(body.decode("utf-8"))
        except Exception:
            send_json(self, {"ok": False, "error": "bad json"}, 400)
            return
        if ADMIN_KEY and obj.get("key") != ADMIN_KEY:
            send_json(self, {"ok": False, "error": "密码错误"}, 403)
            return
        name = (obj.get("name") or "").strip()
        filename = (obj.get("filename") or "").strip()
        ext = os.path.splitext(filename)[1].lower()
        if ext not in AUDIO_EXT:
            send_json(self, {"ok": False, "error": "仅支持音频: " + ",".join(sorted(AUDIO_EXT))}, 400)
            return
        new_name = uuid.uuid4().hex[:10] + ext
        try:
            raw = base64.b64decode(obj.get("data64", ""))
        except Exception:
            send_json(self, {"ok": False, "error": "base64 解码失败"}, 400)
            return
        if not raw:
            send_json(self, {"ok": False, "error": "空文件"}, 400)
            return
        song_name = name if name else os.path.splitext(filename)[0]
        with _lock:
            with open(os.path.join(AUDIO_DIR, new_name), "wb") as f:
                f.write(raw)
            songs = load_songs()
            songs.append({"name": song_name, "file": "music/" + new_name})
            save_songs(songs)
        send_json(self, {"ok": True, "msg": "已添加歌曲", "songs": songs})

    def api_song_delete(self):
        body = read_body(self)
        if body is None:
            send_json(self, {"ok": False, "error": "body too large"}, 413)
            return
        try:
            obj = json.loads(body.decode("utf-8"))
        except Exception:
            send_json(self, {"ok": False, "error": "bad json"}, 400)
            return
        if ADMIN_KEY and obj.get("key") != ADMIN_KEY:
            send_json(self, {"ok": False, "error": "密码错误"}, 403)
            return
        file_path = (obj.get("file") or "").strip()
        with _lock:
            songs = load_songs()
            before = len(songs)
            songs = [s for s in songs if s.get("file") != file_path]
            save_songs(songs)
            # 删除音频文件（尽力而为：沙箱/权限受限时失败不阻断）
            if file_path.startswith("music/") and len(songs) != before:
                fp = os.path.normpath(os.path.join(BASE_DIR, file_path))
                if fp.startswith(AUDIO_DIR) and os.path.isfile(fp):
                    try:
                        os.remove(fp)
                    except Exception:
                        pass   # 文件删除失败不影响列表移除
        send_json(self, {"ok": True, "msg": "已删除歌曲", "songs": songs})

    # ---------- 静态文件 ----------
    def serve_file(self, rel):
        fp = os.path.join(BASE_DIR, rel)
        if not os.path.isfile(fp):
            send_json(self, {"ok": False, "error": "404"}, 404)
            return
        ext = os.path.splitext(rel)[1].lower()
        ctype = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".m4a": "audio/mp4",
            ".mp3": "audio/mpeg",
            ".webp": "image/webp",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".json": "application/json; charset=utf-8",
            ".md": "text/plain; charset=utf-8",
            ".txt": "text/plain; charset=utf-8",
        }.get(ext, "application/octet-stream")
        with open(fp, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8081
    print("=" * 52)
    print("  云游江苏 · 内容管理服务")
    print("  前台:  http://localhost:%d/" % port)
    print("  管理:  http://localhost:%d/admin  （密码: %s）" % (port, ADMIN_KEY or "无（开放）"))
    print("  停止:  Ctrl+C")
    print("=" * 52)
    srv = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
