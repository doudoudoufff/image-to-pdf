# 图片转PDF工具

这是一个简单的图片转PDF工具，支持将文件夹中的图片转换为PDF文件，每页显示一张图片，并在图片下方显示文件名。

## 功能特点

- 支持中英文文件名
- 支持横竖屏图片混排
- 每页显示一张图片
- 图片下方显示文件名
- 显示转换进度条
- 图形用户界面操作简单
- 跨平台支持（Windows/macOS）

## 下载使用

### Windows用户

1. 从 [GitHub Releases](../../releases) 下载最新的 `ImageToPDF-Windows.zip`
2. 解压下载的文件
3. 双击运行 `ImageToPDF-Windows.exe`
4. 如果提示安全警告，点击"仍要运行"

### Intel Mac 用户

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

## 使用方法

1. 运行程序
2. 点击"选择图片文件"按钮
3. 选择要转换的图片文件（支持多选）
4. 点击"转换为PDF"按钮
5. 选择保存位置和文件名
6. 等待转换完成

## 开发者信息

### 系统要求

- Python 3.6+
- Windows 10/11 或 macOS

### 安装依赖

```bash
pip install -r requirements.txt
```

### 本地构建

#### Windows版本
```bash
python build_windows.py
```

#### macOS版本
```bash
pyinstaller --onefile --windowed main.py
```

### GitHub Actions自动构建

项目配置了GitHub Actions，当推送tag时会自动构建：

```bash
git tag v1.0.0
git push origin v1.0.0
```

构建完成后会在GitHub Releases页面生成对应的安装包。

## 技术实现

- **GUI框架**: tkinter
- **图片处理**: Pillow (PIL)
- **PDF生成**: reportlab + PyPDF2
- **打包工具**: PyInstaller
- **跨平台**: 自动检测操作系统并使用相应的实现方式 