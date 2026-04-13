import 'dart:math' as math;
import 'dart:typed_data';

import 'package:flutter/services.dart' show rootBundle;
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;

import '../image_queue_item.dart';
import '../pdf_layout_constants.dart';
import 'image_pipeline.dart';

/// Builds a multi-page PDF: A4 per page, orientation from image aspect ratio,
/// image scaled to fit above a caption band, caption uses embedded Noto SC.
class PdfExportService {
  PdfExportService({ImagePipeline? pipeline})
    : _pipeline = pipeline ?? ImagePipeline();

  final ImagePipeline _pipeline;

  /// 同时解码/编码的图片数（多核利用）；过大易占内存。
  static const int prepareConcurrency = 4;

  Future<Uint8List> buildPdf(
    List<ImageQueueItem> items, {

    /// PDF 底部文件名的目标字号（pt），过小会自动缩小以适配行宽。
    double captionFontSizePt = 10,

    /// 底部文件名在说明条内的水平位置，-1 左对齐 … 1 右对齐（pdf [Alignment] 的 x）。
    double captionAlignX = 0,

    /// 底部文件名在说明条内的垂直位置，-1 靠底 … 1 靠顶（pdf [Alignment] 的 y）。
    double captionAlignY = 0.62,

    /// 每处理完一条路径调用（含解码失败跳过）：[completed] 为 1..total。
    void Function(int completed, int total)? onPageCompleted,

    /// 所有页面已加入文档，即将执行 [Document.save]（可能较久）。
    void Function()? onPdfEncodingStarted,
  }) async {
    final fontData = await rootBundle.load(
      'assets/fonts/NotoSansSC-Regular.ttf',
    );
    final font = pw.Font.ttf(fontData);

    final captionTarget = captionFontSizePt.clamp(6.0, 24.0);
    final captionShrinkMin = math.max(5.0, captionTarget * 0.45);
    final ax = captionAlignX.clamp(-1.0, 1.0);
    final ay = captionAlignY.clamp(-1.0, 1.0);

    final doc = pw.Document();
    final total = items.length;
    if (total == 0) {
      throw StateError('请先添加至少一张图片。');
    }

    onPageCompleted?.call(0, total);

    const captionSideInsetPt = 8.0;
    final captionTextAlign = ax <= -0.33
        ? pw.TextAlign.left
        : ax >= 0.33
            ? pw.TextAlign.right
            : pw.TextAlign.center;
    final frameBorder = PdfColor.fromInt(0xff9a9184);

    var pagesAdded = 0;
    var index = 0;
    while (index < total) {
      final batchEnd = math.min(index + prepareConcurrency, total);
      final batch = await Future.wait(
        <Future<PreparedPage?>>[
          for (var k = index; k < batchEnd; k++)
            _pipeline.prepareFile(
              items[k].path,
              displayName: items[k].displayName,
            ),
        ],
      );

      for (var b = 0; b < batch.length; b++) {
        final i = index + b;
        final prepared = batch[b];
        if (prepared == null) {
          onPageCompleted?.call(i + 1, total);
          continue;
        }
        pagesAdded++;

        final w = prepared.pixelWidth.toDouble();
        final h = prepared.pixelHeight.toDouble();
        final layout = PdfPageLayout.fromPixelSize(
          pixelWidth: w,
          pixelHeight: h,
          captionFontPt: captionFontSizePt,
        );

        final contentW = layout.format.availableWidth;
        final captionTextMaxW =
            math.max(8.0, contentW - 2 * captionSideInsetPt);

        doc.addPage(
          pw.Page(
            pageFormat: layout.format,
            margin: pw.EdgeInsets.zero,
            build: (context) {
              return pw.Column(
                crossAxisAlignment: pw.CrossAxisAlignment.stretch,
                children: [
                  pw.Expanded(
                    child: pw.DecoratedBox(
                      decoration: pw.BoxDecoration(
                        color: PdfColors.white,
                        border: pw.Border.all(color: frameBorder, width: 1.2),
                        borderRadius:
                            const pw.BorderRadius.all(pw.Radius.circular(6)),
                      ),
                      child: pw.Column(
                        crossAxisAlignment: pw.CrossAxisAlignment.stretch,
                        children: [
                          pw.Expanded(
                            child: pw.Center(
                              child: pw.Image(
                                pw.MemoryImage(prepared.imageBytes),
                                width: layout.drawWidthPt,
                                height: layout.drawHeightPt,
                                fit: pw.BoxFit.contain,
                              ),
                            ),
                          ),
                          pw.SizedBox(
                            height: layout.captionBandPt,
                            child: pw.Padding(
                              padding: pw.EdgeInsets.fromLTRB(
                                captionSideInsetPt,
                                2,
                                captionSideInsetPt,
                                6,
                              ),
                              child: pw.Align(
                                alignment: pw.Alignment(ax, ay),
                                child: _captionText(
                                  context: context,
                                  text: prepared.displayName,
                                  font: font,
                                  maxWidth: captionTextMaxW,
                                  targetSize: captionTarget,
                                  minSize: captionShrinkMin,
                                  textAlign: captionTextAlign,
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              );
            },
          ),
        );
        onPageCompleted?.call(i + 1, total);
      }
      index = batchEnd;
    }

    if (pagesAdded == 0) {
      throw StateError('没有成功解码的图片，请检查文件格式是否为 PNG / JPEG / BMP / GIF。');
    }

    onPdfEncodingStarted?.call();
    return doc.save(enableEventLoopBalancing: true);
  }

  /// 底部文件名：嵌入的 Noto Sans SC。
  ///
  /// 不能只用 [TextStyle.copyWith] 的 `font:`：实现里仍会保留 `fontNormal` 等为
  /// defaultStyle 的 Helvetica，且 **显式 `fontNormal` 会盖过 `font` 简写**，
  /// 结果中文在 PDF 里变成方框（预览用 Flutter 字体则正常）。
  pw.TextStyle _captionStyle(pw.Font noto, double fontSize) {
    return pw.TextStyle.defaultStyle().copyWith(
      fontNormal: noto,
      fontBold: noto,
      fontItalic: noto,
      fontBoldItalic: noto,
      fontSize: fontSize,
      color: PdfColors.black,
    );
  }

  pw.Widget _captionText({
    required pw.Context context,
    required String text,
    required pw.Font font,
    required double maxWidth,
    required double targetSize,
    required double minSize,
    required pw.TextAlign textAlign,
  }) {
    var fontSize = targetSize;
    while (fontSize >= minSize) {
      final widget = pw.Text(
        text,
        style: _captionStyle(font, fontSize),
        maxLines: 1,
        overflow: pw.TextOverflow.clip,
        textAlign: textAlign,
      );
      final size = pw.Widget.measure(
        widget,
        context: context,
        constraints: pw.BoxConstraints(maxWidth: maxWidth),
      );
      if (size.x <= maxWidth) {
        return widget;
      }
      fontSize -= 0.5;
    }
    return pw.Text(
      text,
      style: _captionStyle(font, minSize),
      maxLines: 1,
      overflow: pw.TextOverflow.clip,
      textAlign: textAlign,
    );
  }
}
