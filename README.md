# 图片转 PDF 工具

将多张图片合并为一个 PDF 的桌面应用，支持 **Windows** 与 **macOS**。主程序为 Flutter 实现，源码位于 [`app/`](app/)。

## 功能特点

- 可多次「添加图片」，从**不同文件夹**累积到同一列表（自动按路径去重）
- 列表支持**拖拽排序**、单条移除
- 每张图片一页；按校正后的宽高比自动选择 **A4 横版或竖版** 页面
- 图片在页内**等比缩放**以适配可编辑区域（不放大，避免模糊）
- 每页底部显示**文件名**（嵌入 Noto Sans SC，支持中文与英文）
- 自动处理 **EXIF 方向**（手机竖拍等）
- 支持格式：PNG、JPG/JPEG、BMP、GIF

## 下载使用（发行包）

在仓库的 GitHub Releases 页面下载对应平台的 zip：

- **Windows**：解压后运行目录中的 `image_to_pdf.exe`（具体文件名以构建产物为准）。
- **macOS**：解压后打开 `image_to_pdf.app`；若提示无法打开，请在 Finder 中对该 app **右键 → 打开**。

## 开发者：本地运行

环境：**Flutter**（stable，需启用桌面支持）、本仓库已包含 `windows/` 与 `macos/` 工程。

```bash
cd app
flutter pub get
flutter run -d macos
# 或
flutter run -d windows
```

中文字体文件已包含在 `app/assets/fonts/NotoSansSC-Regular.otf`（见 `app/pubspec.yaml` 资源声明）。

## 构建发行版

```bash
cd app
flutter build macos --release
flutter build windows --release
```

- macOS 产物：`app/build/macos/Build/Products/Release/image_to_pdf.app`
- Windows 产物：`app/build/windows/x64/runner/Release/` 下可执行文件及依赖

推送以 `v` 开头的 tag 时，GitHub Actions 会构建并上传上述平台的 zip 包（见 [.github/workflows/build.yml](.github/workflows/build.yml)）。

## 旧版 Python 工具

改造前的 tkinter 版本源码在 [`legacy/`](legacy/)，仅供参考。

## 技术栈（Flutter）

- UI：Flutter / Material 3  
- 图片：`image`（解码与 EXIF）  
- PDF：`pdf`  
- 文件选择：`file_picker`  
- 字体：Noto Sans SC（OFL，随应用打包）
