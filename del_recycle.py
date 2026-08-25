# -*- coding: utf-8 -*-
"""用 Windows SHFileOperationW API 将指定文件/目录送入回收站"""
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
FOF_ALLOWUNDO = 0x40     # 允许撤销 => 进回收站
FOF_NOCONFIRMATION = 0x10
FOF_SILENT = 0x04


def send_to_recycle(paths):
    """paths: 绝对路径列表。返回 (成功数, 失败列表)"""
    ok, failed = 0, []
    for p in paths:
        if not os.path.exists(p):
            failed.append(p + " (不存在)")
            continue
        pfrom = p + "\0\0"
        op = SHFILEOPSTRUCTW()
        op.wFunc = FO_DELETE
        op.pFrom = pfrom
        op.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT
        r = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
        if r == 0 and not os.path.exists(p):
            ok += 1
            print("已送回收站:", p)
        else:
            failed.append(p + " (API错误码 %s)" % r)
    return ok, failed


if __name__ == "__main__":
    base = r"C:\Users\wsvgs\Desktop\jiangsugeo"
    targets = [
        os.path.join(base, "pick_nanjing.html"),
        os.path.join(base, "pick_landmarks.html"),
        os.path.join(base, "pexels_fetch.py"),
        os.path.join(base, "pexels_landmark.py"),
        os.path.join(base, "images", "pexels"),
    ]
    ok, failed = send_to_recycle(targets)
    print("结果: 成功 %d, 失败 %d" % (ok, len(failed)))
    for f in failed:
        print("  ", f)
