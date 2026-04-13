import 'dart:io';

import 'package:desktop_drop/desktop_drop.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:path/path.dart' as p;
import 'package:reorderable_grid_view/reorderable_grid_view.dart';

import '../constants.dart';
import '../image_queue_item.dart';
import '../services/pdf_export_service.dart';
import 'pdf_export_preview_dialog.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final List<ImageQueueItem> _items = [];
  final PdfExportService _pdf = PdfExportService();

  bool _dropHighlight = false;

  /// 有对话框叠在上面时应关闭 DropTarget，避免仍接收拖放事件（desktop_drop 文档说明）。
  bool _exportDialogOpen = false;

  static const _line = Color(0xFF9A9184);
  static const _ink = Color(0xFF2B2620);
  static const _inkMuted = Color(0xFF6B6458);

  static const Set<String> _allowedExtensions = {
    '.png',
    '.jpg',
    '.jpeg',
    '.bmp',
    '.gif',
  };

  /// 用户可见的文件名（去掉路径分隔符；保留中文等 Unicode）。
  static String _sanitizeDisplayName(String raw) {
    final t = raw.trim();
    if (t.isEmpty) {
      return 'image';
    }
    return t.replaceAll(RegExp(r'[/\\\x00]'), '_');
  }

  void _appendItems(List<ImageQueueItem> incoming) {
    final fresh = <ImageQueueItem>[];
    for (final item in incoming) {
      if (item.path.isEmpty) {
        continue;
      }
      if (_items.any((e) => e.path == item.path) ||
          fresh.any((e) => e.path == item.path)) {
        continue;
      }
      fresh.add(item);
    }
    if (fresh.isEmpty) {
      return;
    }
    setState(() => _items.addAll(fresh));
  }

  Future<void> _addImages() async {
    final result = await FilePicker.pickFiles(
      allowMultiple: true,
      type: FileType.image,
      withData: true,
      lockParentWindow: true,
      dialogTitle: '选择图片',
    );
    if (result == null || result.files.isEmpty) {
      return;
    }

    final added = <ImageQueueItem>[];
    for (final f in result.files) {
      final name = f.name;
      final ext = p.extension(name).toLowerCase();
      if (!_allowedExtensions.contains(ext)) {
        continue;
      }

      final displayName = _sanitizeDisplayName(name);
      var resolved = f.path;
      if (resolved == null || resolved.isEmpty) {
        final bytes = f.bytes;
        if (bytes == null || bytes.isEmpty) {
          continue;
        }
        final extSeg = ext.isEmpty ? '.img' : ext;
        final tmp = File(
          '${Directory.systemTemp.path}/img2pdf_${DateTime.now().microsecondsSinceEpoch}$extSeg',
        );
        await tmp.writeAsBytes(bytes);
        resolved = tmp.path;
      }

      if (resolved.isNotEmpty) {
        added.add(
          ImageQueueItem(path: resolved, displayName: displayName),
        );
      }
    }

    if (!mounted) {
      return;
    }
    if (added.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('没有可添加的图片（需为 PNG / JPEG / BMP / GIF）。')),
      );
      return;
    }
    _appendItems(added);
  }

  Future<void> _handleDrop(DropDoneDetails details) async {
    final added = <ImageQueueItem>[];
    for (final item in details.files) {
      if (item is DropItemDirectory) {
        await _collectFromDropDirectory(item, added);
      } else {
        await _collectFromDropFile(item, added);
      }
    }

    if (!mounted) {
      return;
    }
    if (added.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('未识别到可添加的图片（支持 PNG / JPEG / BMP / GIF）。')),
      );
      return;
    }
    _appendItems(added);
  }

  Future<void> _collectFromDropFile(DropItem item, List<ImageQueueItem> added) async {
    final name = item.name;
    final rawPath = item.path;
    final ext = p.extension(rawPath.isNotEmpty ? rawPath : name).toLowerCase();
    if (!_allowedExtensions.contains(ext)) {
      return;
    }

    final bm = item.extraAppleBookmark;
    if (bm != null && bm.isNotEmpty) {
      await DesktopDrop.instance.startAccessingSecurityScopedResource(
        bookmark: bm,
      );
    }
    try {
      if (rawPath.isEmpty) {
        final bytes = await item.readAsBytes();
        if (bytes.isEmpty) {
          return;
        }
        final displayName = _sanitizeDisplayName(name);
        final ext = p.extension(name).toLowerCase();
        final extSeg = ext.isEmpty ? '.img' : ext;
        final tmp = File(
          '${Directory.systemTemp.path}/img2pdf_${DateTime.now().microsecondsSinceEpoch}$extSeg',
        );
        await tmp.writeAsBytes(bytes);
        added.add(ImageQueueItem(path: tmp.path, displayName: displayName));
        return;
      }

      final src = File(rawPath);
      if (!await src.exists()) {
        return;
      }

      final displayName = _sanitizeDisplayName(p.basename(rawPath));
      if (bm != null && bm.isNotEmpty) {
        final ext = p.extension(rawPath).toLowerCase();
        final extSeg = ext.isEmpty ? '.img' : ext;
        final tmp = File(
          '${Directory.systemTemp.path}/img2pdf_${DateTime.now().microsecondsSinceEpoch}$extSeg',
        );
        await src.copy(tmp.path);
        added.add(ImageQueueItem(path: tmp.path, displayName: displayName));
      } else {
        added.add(ImageQueueItem(path: rawPath, displayName: displayName));
      }
    } finally {
      if (bm != null && bm.isNotEmpty) {
        await DesktopDrop.instance.stopAccessingSecurityScopedResource(
          bookmark: bm,
        );
      }
    }
  }

  Future<void> _collectFromDropDirectory(
    DropItemDirectory dir,
    List<ImageQueueItem> added,
  ) async {
    if (dir.children.isNotEmpty) {
      for (final child in dir.children) {
        if (child is DropItemDirectory) {
          await _collectFromDropDirectory(child, added);
        } else {
          await _collectFromDropFile(child, added);
        }
      }
      return;
    }

    final bm = dir.extraAppleBookmark;
    if (bm != null && bm.isNotEmpty) {
      await DesktopDrop.instance.startAccessingSecurityScopedResource(
        bookmark: bm,
      );
    }
    try {
      final root = dir.path;
      if (root.isEmpty) {
        return;
      }
      await for (final entity in Directory(root).list(recursive: true)) {
        if (entity is! File) {
          continue;
        }
        final ext = p.extension(entity.path).toLowerCase();
        if (!_allowedExtensions.contains(ext)) {
          continue;
        }
        final displayName = _sanitizeDisplayName(p.basename(entity.path));
        if (bm != null && bm.isNotEmpty) {
          final ext = p.extension(entity.path).toLowerCase();
          final extSeg = ext.isEmpty ? '.img' : ext;
          final tmp = File(
            '${Directory.systemTemp.path}/img2pdf_${DateTime.now().microsecondsSinceEpoch}$extSeg',
          );
          await entity.copy(tmp.path);
          added.add(ImageQueueItem(path: tmp.path, displayName: displayName));
        } else {
          added.add(
            ImageQueueItem(path: entity.path, displayName: displayName),
          );
        }
      }
    } finally {
      if (bm != null && bm.isNotEmpty) {
        await DesktopDrop.instance.stopAccessingSecurityScopedResource(
          bookmark: bm,
        );
      }
    }
  }

  void _removeItem(ImageQueueItem item) {
    setState(() {
      _items.remove(item);
    });
  }

  Future<void> _openExportPreview() async {
    if (_items.isEmpty) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('请先添加图片。')));
      return;
    }
    setState(() => _exportDialogOpen = true);
    try {
      final saved = await showDialog<String>(
        context: context,
        barrierDismissible: true,
        builder: (ctx) => PdfExportPreviewDialog(
          items: List<ImageQueueItem>.from(_items),
          pdfService: _pdf,
        ),
      );
      if (!mounted || saved == null) {
        return;
      }
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('已保存：$saved')));
    } finally {
      if (mounted) {
        setState(() => _exportDialogOpen = false);
      }
    }
  }

  /// 缩略图区域像素上限：按格子尺寸解码，避免对高像素原图全尺寸解码（主线程与内存压力极大）。
  Widget _buildGridTile(ImageQueueItem item, TextTheme text) {
    final name = item.displayName;
    return Padding(
      padding: const EdgeInsets.all(4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Expanded(
            child: Stack(
              clipBehavior: Clip.none,
              children: [
                Positioned.fill(
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(6),
                    child: ColoredBox(
                      color: const Color(0xFFE8E4DF),
                      child: LayoutBuilder(
                        builder: (context, constraints) {
                          final dpr = MediaQuery.devicePixelRatioOf(context);
                          final cw = (constraints.maxWidth * dpr)
                              .round()
                              .clamp(1, 4096);
                          final ch = (constraints.maxHeight * dpr)
                              .round()
                              .clamp(1, 4096);
                          return Image.file(
                            File(item.path),
                            fit: BoxFit.contain,
                            alignment: Alignment.center,
                            filterQuality: FilterQuality.low,
                            cacheWidth: cw,
                            cacheHeight: ch,
                            errorBuilder: (_, _, _) => Center(
                              child: Icon(
                                Icons.broken_image_outlined,
                                color: _inkMuted,
                                size: 32,
                              ),
                            ),
                          );
                        },
                      ),
                    ),
                  ),
                ),
                Positioned(
                  top: 0,
                  right: 0,
                  child: Material(
                    color: const Color(0xE6F2EFE8),
                    shape: const CircleBorder(),
                    clipBehavior: Clip.antiAlias,
                    child: InkWell(
                      onTap: () => _removeItem(item),
                      child: Padding(
                        padding: const EdgeInsets.all(4),
                        child: Icon(Icons.close, size: 16, color: _ink),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 6),
          Text(
            name,
            textAlign: TextAlign.center,
            maxLines: 3,
            overflow: TextOverflow.ellipsis,
            style: text.bodySmall?.copyWith(height: 1.2),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('图片 → PDF'),
        bottom: const PreferredSize(
          preferredSize: Size.fromHeight(1),
          child: Divider(height: 1, thickness: 1, color: _line),
        ),
      ),
      body: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                OutlinedButton(
                  onPressed: _addImages,
                  child: const Text('+ 添加'),
                ),
                const SizedBox(width: 10),
                OutlinedButton(
                  onPressed: _items.isEmpty ? null : _openExportPreview,
                  child: const Text('预览并导出 PDF'),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text('可「添加」或拖入图片/文件夹；长按格子拖拽可排序。', style: text.bodySmall),
            const SizedBox(height: 14),
            Text('— 队列 —', style: text.titleMedium),
            const SizedBox(height: 8),
            Expanded(
              child: DropTarget(
                enable: !_exportDialogOpen,
                onDragEntered: (_) {
                  setState(() => _dropHighlight = true);
                },
                onDragExited: (_) {
                  setState(() => _dropHighlight = false);
                },
                onDragDone: (d) {
                  setState(() => _dropHighlight = false);
                  _handleDrop(d);
                },
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 150),
                  curve: Curves.easeOut,
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.surface,
                    border: Border.all(
                      color: _dropHighlight ? _ink : _line,
                      width: _dropHighlight ? 2 : 1,
                    ),
                    borderRadius: BorderRadius.circular(kAppRadius),
                  ),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(kAppRadius),
                    child: _items.isEmpty
                        ? Center(
                            child: Padding(
                              padding: const EdgeInsets.all(24),
                              child: Column(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(
                                    Icons.add_photo_alternate_outlined,
                                    size: 40,
                                    color: _inkMuted,
                                  ),
                                  const SizedBox(height: 10),
                                  Text(
                                    '（空）',
                                    style: text.bodyMedium?.copyWith(
                                      color: _inkMuted,
                                    ),
                                  ),
                                  const SizedBox(height: 6),
                                  Text('将图片或文件夹拖到这里', style: text.bodySmall),
                                ],
                              ),
                            ),
                          )
                        : ReorderableGridView.count(
                            padding: const EdgeInsets.all(10),
                            crossAxisCount: 3,
                            crossAxisSpacing: 6,
                            mainAxisSpacing: 6,
                            childAspectRatio: 0.68,
                            onReorder: (oldIndex, newIndex) {
                              setState(() {
                                if (newIndex > oldIndex) {
                                  newIndex -= 1;
                                }
                                final item = _items.removeAt(oldIndex);
                                _items.insert(newIndex, item);
                              });
                            },
                            children: [
                              for (final item in _items)
                                KeyedSubtree(
                                  key: ValueKey(item.path),
                                  child: _buildGridTile(item, text),
                                ),
                            ],
                          ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
