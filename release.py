#!/usr/bin/env python3
"""
发布脚本
用于自动化版本发布流程
"""

import os
import sys
import subprocess
import re
from datetime import datetime

def run_command(cmd, check=True):
    """运行命令并返回结果"""
    print(f"执行命令: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"命令执行失败: {result.stderr}")
        sys.exit(1)
    return result

def get_current_version():
    """获取当前版本号"""
    # 从git tag中获取最新版本
    result = run_command("git tag --sort=-version:refname | head -1", check=False)
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return "v0.0.0"

def get_next_version(current_version):
    """获取下一个版本号"""
    # 移除v前缀
    version = current_version.lstrip('v')
    parts = version.split('.')
    
    if len(parts) >= 3:
        major, minor, patch = parts[:3]
        patch = str(int(patch) + 1)
        return f"v{major}.{minor}.{patch}"
    else:
        return "v1.0.0"

def check_git_status():
    """检查git状态"""
    result = run_command("git status --porcelain")
    if result.stdout.strip():
        print("⚠️  有未提交的更改，请先提交或暂存")
        print("未提交的文件:")
        print(result.stdout)
        return False
    return True

def create_release():
    """创建发布"""
    print("🚀 开始创建发布...")
    
    # 检查git状态
    if not check_git_status():
        response = input("是否继续？(y/N): ")
        if response.lower() != 'y':
            print("取消发布")
            return
    
    # 获取版本号
    current_version = get_current_version()
    next_version = get_next_version(current_version)
    
    print(f"当前版本: {current_version}")
    print(f"新版本: {next_version}")
    
    # 确认版本号
    custom_version = input(f"请输入版本号 (直接回车使用 {next_version}): ").strip()
    if custom_version:
        next_version = custom_version if custom_version.startswith('v') else f"v{custom_version}"
    
    print(f"将发布版本: {next_version}")
    
    # 确认发布
    response = input("确认发布？(y/N): ")
    if response.lower() != 'y':
        print("取消发布")
        return
    
    # 创建tag
    print(f"创建tag: {next_version}")
    run_command(f"git tag {next_version}")
    
    # 推送tag
    print("推送tag到远程仓库...")
    run_command(f"git push origin {next_version}")
    
    print("✅ 发布创建成功！")
    print(f"版本: {next_version}")
    print("GitHub Actions将自动构建并发布到Releases页面")
    print("请访问: https://github.com/你的用户名/image-to-pdf/releases")

def show_help():
    """显示帮助信息"""
    print("""
图片转PDF工具发布脚本

使用方法:
  python release.py          # 创建新版本发布
  python release.py help     # 显示帮助信息

功能:
  - 自动检测当前版本
  - 生成下一个版本号
  - 创建git tag
  - 触发GitHub Actions构建
  - 自动发布到Releases页面

注意事项:
  - 确保代码已提交到git
  - 确保GitHub Actions配置正确
  - 发布后会自动构建Windows和macOS版本
""")

def main():
    """主函数"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command in ['help', '-h', '--help']:
            show_help()
            return
        else:
            print(f"未知命令: {command}")
            show_help()
            return
    
    create_release()

if __name__ == "__main__":
    main()
