import 'dart:io';
import 'dart:math' as math;
import 'dart:typed_data';

import 'package:image/image.dart' as img;
import 'package:path/path.dart' as p;

/// 一页嵌入 PDF：先统一到合适分辨率再编码，控制体积与导出耗时。
class PreparedPage {
  PreparedPage({
    required this.imageBytes,
    required this.pixelWidth,
    required this.pixelHeight,
    required this.displayName,
  });

  /// 规范化后的 JPEG/PNG 字节，供 `pw.MemoryImage` 使用。
  final Uint8List imageBytes;
  final int pixelWidth;
  final int pixelHeight;

  final String displayName;
}

/// 解码 → EXIF 摆正 → **按最长边限制缩放** → JPEG/PNG 编码。
class ImagePipeline {
  ImagePipeline({int? maxLongEdge})
    : maxLongEdge = maxLongEdge ?? defaultNormalizedLongEdge;

  /// 规范化后最长边像素上限（适合 A4 嵌入与屏幕阅读）。
  static const int defaultNormalizedLongEdge = 2200;

  /// JPEG 编码质量（1–100）；略低可明显减小 PDF。
  static const int jpegEncodeQuality = 80;

  final int maxLongEdge;

  /// 与导出缩放规则一致，供预览排版使用（无需真正缩放位图）。
  static ({int width, int height}) normalizedDimensions(
    int srcWidth,
    int srcHeight, {
    int? maxLongEdge,
  }) {
    final cap = maxLongEdge ?? defaultNormalizedLongEdge;
    final m = math.max(srcWidth, srcHeight);
    if (m <= cap) {
      return (width: srcWidth, height: srcHeight);
    }
    final scale = cap / m;
    return (
      width: (srcWidth * scale).round(),
      height: (srcHeight * scale).round(),
    );
  }

  Future<PreparedPage?> prepareFile(String filePath) async {
    try {
      final bytes = await File(filePath).readAsBytes();
      return _prepareDecoded(bytes, _basename(filePath));
    } on Object {
      return null;
    }
  }

  String _basename(String filePath) {
    final raw = p.basename(filePath).trim();
    return raw.isEmpty ? 'image' : raw;
  }

  PreparedPage? _prepareDecoded(Uint8List bytes, String displayName) {
    final decoded = img.decodeImage(bytes);
    if (decoded == null) {
      return null;
    }
    var image = img.bakeOrientation(decoded);

    final target = normalizedDimensions(
      image.width,
      image.height,
      maxLongEdge: maxLongEdge,
    );
    if (target.width != image.width || target.height != image.height) {
      image = img.copyResize(
        image,
        width: target.width,
        height: target.height,
        interpolation: img.Interpolation.linear,
      );
    }

    final Uint8List imageBytes;
    if (image.numChannels == 4) {
      imageBytes = Uint8List.fromList(img.encodePng(image));
    } else {
      imageBytes = Uint8List.fromList(
        img.encodeJpg(image, quality: jpegEncodeQuality),
      );
    }

    return PreparedPage(
      imageBytes: imageBytes,
      pixelWidth: image.width,
      pixelHeight: image.height,
      displayName: displayName,
    );
  }
}
