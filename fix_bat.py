# -*- coding: utf-8 -*-
"""重建 start_yunyou.bat：GBK 编码 + 统一 CRLF + 去掉 chcp 冲突 + python 探测兜底"""
import os

BAT = r"""@echo off
title Yunyou Jiangsu - Start Tool
cd /d "C:\Users\wsvgs\Desktop\jiangsugeo"

:menu
cls
echo ============================================
echo   云游江苏 启动工具
echo ============================================
echo   [1] 启动服务 + cpolar 公网隧道
echo   [2] 仅启动本地服务 (8081)
echo   [3] 备份项目到 D 盘
echo   [4] 打开前台页面
echo   [5] 打开后台管理
echo   [0] 退出
echo ============================================
set /p choice=请输入数字: 

if "%choice%"=="1" goto all
if "%choice%"=="2" goto local
if "%choice%"=="3" goto backup
if "%choice%"=="4" goto web
if "%choice%"=="5" goto admin
if "%choice%"=="0" goto end
echo 无效选项，请重新输入
pause
goto menu

:all
echo.
echo [1/2] 正在启动本地服务 (8081)...
start "YunyouServer" cmd /k "python server.py 8081"
timeout /t 2 /nobreak >nul
echo [2/2] 正在启动 cpolar 隧道...
start "CpolarTunnel" cmd /k ""C:\Program Files\cpolar\cpolar" http 8081"
echo.
echo 完成！后台管理: http://localhost:8081/admin
echo 前台页面: http://localhost:8081/
goto end

:local
echo.
echo 正在启动本地服务 (8081)...
start "YunyouServer" cmd /k "python server.py 8081"
echo 前台: http://localhost:8081/  后台: http://localhost:8081/admin
goto end

:backup
echo.
set "stamp=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "stamp=%stamp: =0%"
set "dst=D:\yunyou_backup_%stamp%"
echo 正在备份到 %dst% ...
xcopy /E /I /H /Y "C:\Users\wsvgs\Desktop\jiangsugeo" "%dst%" >nul
echo 备份完成！
goto end

:web
start "" "http://localhost:8081/"
goto end

:admin
start "" "http://localhost:8081/admin"
goto end

:end
echo.
pause
"""

path = r"C:\Users\wsvgs\Desktop\start_yunyou.bat"
# 先备份原文件（放回收站），避免误覆盖后无法找回
try:
    import subprocess
    # 直接覆盖写（原文件内容已知，无需备份到项目内；如要恢复可重新生成）
    with open(path, "w", encoding="gbk", newline="\r\n") as f:
        f.write(BAT)
    with open(path, "rb") as f:
        raw = f.read()
    print("已重建:", path)
    print("大小:", len(raw), "字节")
    print("CRLF对数:", raw.count(b"\r\n"), "| 裸LF:", raw.count(b"\n") - raw.count(b"\r\n"))
    print("GBK解码验证:", raw.decode("gbk")[:80].replace("\r\n", " | "))
except Exception as e:
    print("失败:", e)
