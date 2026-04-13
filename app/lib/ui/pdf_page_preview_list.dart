import 'dart:io';
import 'dart:isolate';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:image/image.dart' as img;
import 'package:path/path.dart' as p;

import '../pdf_layout_constants.dart';
import '../services/image_pipeline.dart';

/// 轻量预览：与 [PdfExportService] 共用 [PdfPageLayout]，保证与导出 PDF 版式一致。
class PdfPagePreviewList extends StatelessWidget {
  const PdfPagePreviewList({
    super.key,
    required this.paths,
    required this.captionFontPt,
    required this.maxContentWidth,
    required this.captionAlignX,
    required this.captionAlignY,
    this.scrollController,
  });

  final List<String> paths;
  final double captionFontPt;

  /// 与 PDF [pw.Alignment] x 一致：-1 左 … 1 右。
  final double captionAlignX;

  /// 与 PDF [pw.Alignment] y 一致：-1 底 … 1 顶。
  final double captionAlignY;

  final ScrollController? scrollController;

  /// 逻辑纸宽上限（可含预览缩放系数）。
  final double maxContentWidth;

  @override
  Widget build(BuildContext context) {
    return ListView.separated(
      controller: scrollController,
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 16),
      itemCount: paths.length,
      separatorBuilder: (_, _) => const SizedBox(height: 14),
      itemBuilder: (context, index) {
        return _PdfPagePreviewCard(
          key: ValueKey(paths[index]),
          path: paths[index],
          captionFontPt: captionFontPt,
          captionAlignX: captionAlignX,
          captionAlignY: captionAlignY,
          maxPageWidth: maxContentWidth,
        );
      },
    );
  }
}

Future<Size> _decodeImageSizeForPreview(String path) {
  return Isolate.run(() async {
    final bytes = await File(path).readAsBytes();
    final decoded = img.decodeImage(bytes);
    if (decoded == null) {
      throw StateError('无法解码图片');
    }
    final baked = img.bakeOrientation(decoded);
    final n = ImagePipeline.normalizedDimensions(
      baked.width,
      baked.height,
    );
    return Size(n.width.toDouble(), n.height.toDouble());
  });
}

String _displayNameForPath(String path) {
  final raw = p.basename(path).trim();
  return raw.isEmpty ? 'image' : raw;
}

class _PdfPagePreviewCard extends StatefulWidget {
  const _PdfPagePreviewCard({
    super.key,
    required this.path,
    required this.captionFontPt,
    required this.captionAlignX,
    required this.captionAlignY,
    required this.maxPageWidth,
  });

  final String path;
  final double captionFontPt;
  final double captionAlignX;
  final double captionAlignY;
  final double maxPageWidth;

  @override
  State<_PdfPagePreviewCard> createState() => _PdfPagePreviewCardState();
}

class _PdfPagePreviewCardState extends State<_PdfPagePreviewCard> {
  Size? _pixelSize;
  Object? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void didUpdateWidget(covariant _PdfPagePreviewCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.path != widget.path) {
      _pixelSize = null;
      _error = null;
      _load();
    }
  }

  Future<void> _load() async {
    try {
      final s = await _decodeImageSizeForPreview(widget.path);
      if (mounted) {
        setState(() => _pixelSize = s);
      }
    } on Object catch (e) {
      if (mounted) {
        setState(() => _error = e);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_error != null) {
      return _ErrorTile(path: widget.path, error: _error!);
    }
    if (_pixelSize == null) {
      return const SizedBox(
        height: 120,
        child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
      );
    }

    final pw = _pixelSize!.width;
    final ph = _pixelSize!.height;
    final layout = PdfPageLayout.fromPixelSize(
      pixelWidth: pw,
      pixelHeight: ph,
      captionFontPt: widget.captionFontPt,
    );

    final paperW = layout.format.width;
    final paperH = layout.format.height;
    final ui = widget.maxPageWidth / paperW;

    final drawW = layout.drawWidthPt * ui;
    final drawH = layout.drawHeightPt * ui;
    final capBand = layout.captionBandPt * ui;
    final imageRowH = layout.imageRowHeightPt * ui;
    final fontPx = widget.captionFontPt.clamp(6.0, 24.0) * ui;
    const captionSideInsetPt = 8.0;
    final captionMaxW = math.max(
      40.0,
      (layout.format.availableWidth - 2 * captionSideInsetPt) * ui,
    );

    final name = _displayNameForPath(widget.path);
    final ax = widget.captionAlignX.clamp(-1.0, 1.0);
    final ay = widget.captionAlignY.clamp(-1.0, 1.0);
    final nameAlign = ax <= -0.33
        ? TextAlign.left
        : ax >= 0.33
            ? TextAlign.right
            : TextAlign.center;

    return Center(
      child: SizedBox(
        width: paperW * ui,
        height: paperH * ui,
        child: DecoratedBox(
          decoration: BoxDecoration(
            color: Colors.white,
            border: Border.all(color: const Color(0xFF9A9184), width: 1.5),
            borderRadius: BorderRadius.circular(8),
            boxShadow: const [
              BoxShadow(
                color: Color(0x14000000),
                blurRadius: 6,
                offset: Offset(0, 2),
              ),
            ],
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(7),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                SizedBox(
                  height: imageRowH,
                  child: Center(
                    child: SizedBox(
                      width: drawW,
                      height: drawH,
                      child: Image.file(
                        File(widget.path),
                        fit: BoxFit.contain,
                        alignment: Alignment.center,
                        filterQuality: FilterQuality.medium,
                        cacheWidth: (drawW * MediaQuery.of(context).devicePixelRatio)
                            .round()
                            .clamp(64, 4096),
                        cacheHeight: (drawH * MediaQuery.of(context).devicePixelRatio)
                            .round()
                            .clamp(64, 4096),
                        errorBuilder: (_, _, _) =>
                            const Icon(Icons.broken_image_outlined),
                      ),
                    ),
                  ),
                ),
                SizedBox(
                  height: capBand,
                  child: Padding(
                    padding: EdgeInsets.fromLTRB(
                      captionSideInsetPt * ui,
                      2,
                      captionSideInsetPt * ui,
                      6 * ui,
                    ),
                    child: Align(
                      alignment: Alignment(ax, -ay),
                      child: FittedBox(
                        fit: BoxFit.scaleDown,
                        child: ConstrainedBox(
                          constraints: BoxConstraints(maxWidth: captionMaxW),
                          child: Text(
                            name,
                            textAlign: nameAlign,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(
                              fontFamily: 'NotoSansSC',
                              fontSize: fontPx,
                              height: 1.15,
                              color: const Color(0xFF2B2620),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _ErrorTile extends StatelessWidget {
  const _ErrorTile({required this.path, required this.error});

  final String path;
  final Object error;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: const Icon(Icons.error_outline),
      title: Text(p.basename(path)),
      subtitle: Text('$error', maxLines: 2, overflow: TextOverflow.ellipsis),
    );
  }
}
