import 'package:path/path.dart' as p;

/// 队列中的一张图：[path] 为实际读取路径（可能是临时副本），[displayName] 为用户可见的原始文件名。
class ImageQueueItem {
  const ImageQueueItem({
    required this.path,
    required this.displayName,
  });

  final String path;

  /// 用于列表、预览与 PDF 页底说明；与磁盘临时文件名无关。
  final String displayName;

  /// 仅当路径即真实文件且无需单独展示名时使用。
  factory ImageQueueItem.fromPathOnly(String path) {
    final n = p.basename(path).trim();
    return ImageQueueItem(
      path: path,
      displayName: n.isEmpty ? 'image' : n,
    );
  }
}
