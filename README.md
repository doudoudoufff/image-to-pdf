# 图片转PDF工具

这是一个简单的图片转PDF工具，支持将文件夹中的图片转换为PDF文件，每页显示一张图片，并在图片下方显示文件名。

## 功能特点

- 支持中英文文件名
- 支持横竖屏图片混排
- 每页显示一张图片
- 图片下方显示文件名
- 显示转换进度条
- 图形用户界面操作简单

## Intel Mac 用户使用方法

1. 从 [GitHub Releases](../../releases) 下载最新的 `ImageToPDF-Intel-Mac.zip`
2. 解压下载的文件
3. 双击运行 `ImageToPDF.app`
4. 如果提示"无法打开"，请：
   - 在 Finder 中找到 ImageToPDF.app
   - 按住 Control 键并点击程序图标
   - 从菜单中选择"打开"
   - 在弹出的对话框中点击"打开"

## 支持的图片格式

- PNG
- JPG/JPEG
- BMP
- GIF

## 开发者信息

### 系统要求

- Python 3.6+
- macOS系统

### 安装依赖

```bash
pip install -r requirements.txt
```

### 手动打包

```bash
pyinstaller --onefile --windowed main.py
```

打包后的程序将位于 `dist` 目录下。 