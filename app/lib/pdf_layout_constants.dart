import 'dart:math' as math;

import 'package:pdf/pdf.dart';

/// 与导出 PDF 共用：边距、A4、底部条高度。
class PdfLayoutConstants {
  PdfLayoutConstants._();

  static const double marginPt = 36;

  static double captionBandForFontPt(double fontPt) {
    return math.max(40, fontPt * 2.75);
  }

  /// 与导出相同的 [PdfPageFormat]（A4 + 四边 [marginPt]）。
  static PdfPageFormat pageFormatForPixels({
    required double pixelWidth,
    required double pixelHeight,
  }) {
    final landscape = pixelWidth >= pixelHeight;
    final base = PdfPageFormat.a4.copyWith(
      marginLeft: marginPt,
      marginRight: marginPt,
      marginTop: marginPt,
      marginBottom: marginPt,
    );
    return landscape ? base.landscape : base;
  }

  /// 当前图对应的纸张宽高（pt），与 [pageFormatForPixels] 一致。
  static ({double width, double height}) pageSizeForImage({
    required double pixelWidth,
    required double pixelHeight,
  }) {
    final f = pageFormatForPixels(
      pixelWidth: pixelWidth,
      pixelHeight: pixelHeight,
    );
    return (width: f.width, height: f.height);
  }
}

/// 单页版式：与 [PdfExportService] 使用同一公式，预览与导出对齐。
class PdfPageLayout {
  PdfPageLayout._({
    required this.format,
    required this.drawWidthPt,
    required this.drawHeightPt,
    required this.captionBandPt,
  });

  final PdfPageFormat format;

  /// 嵌入 PDF 的绘制尺寸（pt），与 `pw.Image(width:, height:)` 一致。
  final double drawWidthPt;
  final double drawHeightPt;

  final double captionBandPt;

  /// 页面上方图片区域高度（整张纸高度减去底部说明条）。
  double get imageRowHeightPt => format.height - captionBandPt;

  /// 由像素尺寸与底部字号计算版式；[captionFontPt] 会先按导出规则 clamp 到 6–24。
  factory PdfPageLayout.fromPixelSize({
    required double pixelWidth,
    required double pixelHeight,
    required double captionFontPt,
  }) {
    final target = captionFontPt.clamp(6.0, 24.0);
    final cap = PdfLayoutConstants.captionBandForFontPt(target);
    final format = PdfLayoutConstants.pageFormatForPixels(
      pixelWidth: pixelWidth,
      pixelHeight: pixelHeight,
    );
    final cw = format.availableWidth;
    final ch = format.availableHeight - cap;
    final s = math.min(cw / pixelWidth, ch / pixelHeight);
    return PdfPageLayout._(
      format: format,
      drawWidthPt: pixelWidth * s,
      drawHeightPt: pixelHeight * s,
      captionBandPt: cap,
    );
  }
}
