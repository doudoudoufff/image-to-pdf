#!/usr/bin/env python3
"""
Windows版本构建脚本
用于本地构建Windows可执行文件
"""

import os
import sys
import subprocess
import shutil

def build_windows_exe():
    """构建Windows可执行文件"""
    print("开始构建Windows版本...")
    
    # 检查PyInstaller是否安装
    try:
        import PyInstaller
        print("PyInstaller已安装")
    except ImportError:
        print("正在安装PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # 清理之前的构建
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("ImageToPDF-Windows.spec"):
        os.remove("ImageToPDF-Windows.spec")
    
    # 构建命令
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name", "ImageToPDF-Windows",
        "--add-data", "README.md;.",
        "main.py"
    ]
    
    print("执行构建命令:", " ".join(cmd))
    result = subprocess.run(cmd, check=True)
    
    if result.returncode == 0:
        print("构建成功！")
        print("可执行文件位置: dist/ImageToPDF-Windows.exe")
        
        # 创建zip包
        if os.path.exists("dist/ImageToPDF-Windows.exe"):
            import zipfile
            with zipfile.ZipFile("dist/ImageToPDF-Windows.zip", 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write("dist/ImageToPDF-Windows.exe", "ImageToPDF-Windows.exe")
                zipf.write("README.md", "README.md")
            print("ZIP包已创建: dist/ImageToPDF-Windows.zip")
    else:
        print("构建失败！")
        sys.exit(1)

if __name__ == "__main__":
    build_windows_exe()
