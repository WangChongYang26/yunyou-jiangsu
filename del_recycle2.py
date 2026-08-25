# -*- coding: utf-8 -*-
"""用 SHFileOperationW（正确双null格式）将路径送入回收站"""
import ctypes
import os
from ctypes import wintypes


class SHFILEOPSTRUCTW(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("wFunc", ctypes.c_uint),
        ("pFrom", wintypes.LPCWSTR),
        ("pTo", wintypes.LPCWSTR),
        ("fFlags", ctypes.c_ushort),
        ("fAnyOperationsAborted", wintypes.BOOL),
        ("hNameMappings", ctypes.c_void_p),
        ("lpszProgressTitle", wintypes.LPCWSTR),
    ]

FO_DELETE = 3
FOF_ALLOWUNDO = 0x40
FOF_NOCONFIRMATION = 0x10
FOF_SILENT = 0x04
FOF_NOERRORUI = 0x0400


def send_to_recycle(paths):
    ok, failed = 0, []
    for p in paths:
        if not os.path.exists(p):
            failed.append(p + " (不存在)")
            continue
        # 关键：pFrom 必须是 双null 结尾的宽字符缓冲区
        buf = ctypes.create_unicode_buffer(p + "\0")  # 内容 path\0 + 隐式 \0 => path\0\0
        op = SHFILEOPSTRUCTW()
        op.wFunc = FO_DELETE
        op.pFrom = ctypes.cast(buf, wintypes.LPCWSTR)
        op.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT | FOF_NOERRORUI
        r = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
        if r == 0 and not os.path.exists(p):
            ok += 1
            print("已送回收站:", p)
        else:
            failed.append("%s (错误码 %s)" % (p, r))
    return ok, failed


if __name__ == "__main__":
    base = r"C:\Users\wsvgs\Desktop\jiangsugeo"
    targets = [
        os.path.join(base, "images", "pexels"),
    ]
    ok, failed = send_to_recycle(targets)
    print("结果: 成功 %d, 失败 %d" % (ok, len(failed)))
    for f in failed:
        print("  ", f)
    # 顺带确认之前 4 个文件状态
    for name in ("pick_nanjing.html", "pick_landmarks.html", "pexels_fetch.py", "pexels_landmark.py"):
        p = os.path.join(base, name)
        print(("仍存在: " if os.path.exists(p) else "已删除: ") + name)
