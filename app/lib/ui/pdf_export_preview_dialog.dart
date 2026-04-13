import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../constants.dart';
import '../image_queue_item.dart';
import '../services/pdf_export_service.dart';
import 'pdf_page_preview_list.dart';

/// 左侧预览、右侧设置；文件名位置可水平/垂直调节，与导出 PDF 一致。
class PdfExportPreviewDialog extends StatefulWidget {
  const PdfExportPreviewDialog({
    super.key,
    required this.items,
    required this.pdfService,
  });

  final List<ImageQueueItem> items;
  final PdfExportService pdfService;

  @override
  State<PdfExportPreviewDialog> createState() => _PdfExportPreviewDialogState();
}

class _PdfExportPreviewDialogState extends State<PdfExportPreviewDialog> {
  static const double _minFont = 6;
  static const double _maxFont = 22;

  late final ScrollController _previewScrollController;

  double _captionFontPt = 10;

  /// 与 `pw.Alignment.x` 一致：左 -1 … 右 1。
  double _captionAlignX = 0;

  /// 与 `pw.Alignment.y` 一致：底 -1 … 顶 1（默认略靠上）。
  double _captionAlignY = 0.62;

  bool _saveInProgress = false;

  int _exportPagesDone = 0;
  int _exportPagesTotal = 0;

  bool _exportEncodingPdf = false;

  double _previewLayoutScale = 1;

  static const double _minPreviewScale = 0.35;
  static const double _maxPreviewScale = 1.35;

  void _onFontSliderChanged(double v) {
    setState(() => _captionFontPt = v);
  }

  @override
  void initState() {
    super.initState();
    _previewScrollController = ScrollController();
  }

  @override
  void dispose() {
    _previewScrollController.dispose();
    super.dispose();
  }

  Future<void> _saveToFile() async {
    if (_saveInProgress) {
      return;
    }
    setState(() {
      _saveInProgress = true;
      _exportPagesDone = 0;
      _exportPagesTotal = widget.items.length;
      _exportEncodingPdf = false;
    });
    try {
      final bytes = await widget.pdfService.buildPdf(
        List<ImageQueueItem>.from(widget.items),
        captionFontSizePt: _captionFontPt,
        captionAlignX: _captionAlignX,
        captionAlignY: _captionAlignY,
        onPageCompleted: (completed, total) {
          if (!mounted) {
            return;
          }
          setState(() {
            _exportPagesDone = completed;
            _exportPagesTotal = total;
          });
        },
        onPdfEncodingStarted: () {
          if (!mounted) {
            return;
          }
          setState(() => _exportEncodingPdf = true);
        },
      );
      if (!mounted) {
        return;
      }
      if (bytes.isEmpty) {
        throw StateError('生成的 PDF 为空');
      }
      // 传入 bytes 由插件写入面板返回的路径；勿自行改路径加后缀，否则 macOS 沙盒会拒写。
      final savePath = await FilePicker.saveFile(
        dialogTitle: '保存 PDF',
        fileName: 'output.pdf',
        type: FileType.custom,
        allowedExtensions: const ['pdf'],
        bytes: bytes,
      );
      if (savePath == null || !mounted) {
        return;
      }
      Navigator.of(context).pop<String>(savePath);
    } on PlatformException catch (e) {
      if (mounted) {
        final detail = e.message ?? e.code;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('保存失败（系统对话框）：$detail')),
        );
      }
    } on Object catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('保存失败：$e')));
      }
    } finally {
      if (mounted) {
        setState(() {
          _saveInProgress = false;
          _exportEncodingPdf = false;
        });
      }
    }
  }

  Widget _buildSettingsColumn(BuildContext context) {
    final secondary = Theme.of(context).colorScheme.secondary;
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(4, 0, 4, 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '导出设置',
            style: Theme.of(context).textTheme.titleSmall?.copyWith(
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            '文件名字号：${_captionFontPt.toStringAsFixed(1)} pt',
            style: Theme.of(context).textTheme.bodySmall,
          ),
          Slider(
            value: _captionFontPt.clamp(_minFont, _maxFont),
            min: _minFont,
            max: _maxFont,
            divisions: 32,
            label: '${_captionFontPt.toStringAsFixed(1)} pt',
            onChanged: _onFontSliderChanged,
          ),
          Text(
            '长文件名会在该字号附近自动缩小以适配行宽。',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(color: secondary),
          ),
          const SizedBox(height: 14),
          Text(
            '文件名左右：${_captionAlignX.toStringAsFixed(2)}（−1 左 · 0 中 · 1 右）',
            style: Theme.of(context).textTheme.bodySmall,
          ),
          Slider(
            value: _captionAlignX.clamp(-1, 1),
            min: -1,
            max: 1,
            divisions: 40,
            label: _captionAlignX.toStringAsFixed(2),
            onChanged: (v) => setState(() => _captionAlignX = v),
          ),
          Text(
            '← 靠左 · 居中 · 靠右 →',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(color: secondary),
          ),
          const SizedBox(height: 10),
          Text(
            '文件名上下：${_captionAlignY.toStringAsFixed(2)}（−1 贴底 · 1 贴顶）',
            style: Theme.of(context).textTheme.bodySmall,
          ),
          Slider(
            value: _captionAlignY.clamp(-1, 1),
            min: -1,
            max: 1,
            divisions: 40,
            label: _captionAlignY.toStringAsFixed(2),
            onChanged: (v) => setState(() => _captionAlignY = v),
          ),
          Text(
            '← 靠页面底边 · 靠图片侧 →',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(color: secondary),
          ),
          const SizedBox(height: 14),
          Text(
            '预览缩放：${(_previewLayoutScale * 100).round()}%（仅预览）',
            style: Theme.of(context).textTheme.bodySmall,
          ),
          Slider(
            value: _previewLayoutScale.clamp(
              _minPreviewScale,
              _maxPreviewScale,
            ),
            min: _minPreviewScale,
            max: _maxPreviewScale,
            divisions: 20,
            label: '${(_previewLayoutScale * 100).round()}%',
            onChanged: (v) => setState(() => _previewLayoutScale = v),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.sizeOf(context);
    final dialogW = (size.width * 0.94).clamp(720.0, 1200.0);
    final dialogH = (size.height * 0.88).clamp(460.0, 920.0);

    return Dialog(
      insetPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 20),
      child: SizedBox(
        width: dialogW,
        height: dialogH,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 14, 8, 8),
              child: Row(
                children: [
                  const Expanded(
                    child: Text(
                      '导出 PDF',
                      style: TextStyle(
                        fontFamily: 'Courier New',
                        fontSize: 17,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  IconButton(
                    tooltip: '关闭',
                    onPressed: () => Navigator.of(context).pop(),
                    icon: const Icon(Icons.close),
                  ),
                ],
              ),
            ),
            const Divider(height: 1),
            Expanded(
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Expanded(
                    flex: 56,
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(12, 10, 8, 8),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Text(
                            '页面预览',
                            style: Theme.of(context).textTheme.titleSmall
                                ?.copyWith(fontWeight: FontWeight.w600),
                          ),
                          const SizedBox(height: 8),
                          Expanded(
                            child: LayoutBuilder(
                              builder: (context, constraints) {
                                final lw = constraints.maxWidth;
                                return ClipRRect(
                                  borderRadius:
                                      BorderRadius.circular(kAppRadius),
                                  child: Scrollbar(
                                    controller: _previewScrollController,
                                    thumbVisibility: true,
                                    child: PdfPagePreviewList(
                                      scrollController:
                                          _previewScrollController,
                                      items: widget.items,
                                      captionFontPt: _captionFontPt,
                                      captionAlignX: _captionAlignX,
                                      captionAlignY: _captionAlignY,
                                      maxContentWidth:
                                          lw * 0.96 * _previewLayoutScale,
                                    ),
                                  ),
                                );
                              },
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const VerticalDivider(width: 1),
                  Expanded(
                    flex: 44,
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(8, 10, 14, 8),
                      child: _buildSettingsColumn(context),
                    ),
                  ),
                ],
              ),
            ),
            if (_saveInProgress) ...[
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 4, 20, 8),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    LinearProgressIndicator(
                      value: _exportEncodingPdf
                          ? null
                          : (_exportPagesTotal > 0
                                ? _exportPagesDone / _exportPagesTotal
                                : 0),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      _exportEncodingPdf
                          ? '正在打包 PDF…'
                          : '正在处理图片 $_exportPagesDone / $_exportPagesTotal',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ),
              ),
            ],
            const Divider(height: 1),
            Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  OutlinedButton(
                    onPressed: () => Navigator.of(context).pop<String>(),
                    child: const Text('取消'),
                  ),
                  const SizedBox(width: 12),
                  FilledButton.icon(
                    onPressed: (_saveInProgress || widget.items.isEmpty)
                        ? null
                        : _saveToFile,
                    icon: _saveInProgress
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.save_alt_outlined),
                    label: Text(
                      _saveInProgress
                          ? (_exportEncodingPdf ? '正在打包…' : '处理图片中…')
                          : '保存到文件…',
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
