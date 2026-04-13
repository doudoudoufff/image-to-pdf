import 'dart:io';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import 'constants.dart';
import 'ui/home_page.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  // 注意：file_picker 在 macOS 上须在引擎注册插件之后再调用 skipEntitlementsChecks，
  // 否则 channel 未就绪，静默失败，打开文件对话框会直接返回 null。
  runApp(const ImageToPdfApp());
}

/// 复古简约：纸色、深褐字、细线框；统一圆角。
class ImageToPdfApp extends StatefulWidget {
  const ImageToPdfApp({super.key});

  @override
  State<ImageToPdfApp> createState() => _ImageToPdfAppState();
}

class _ImageToPdfAppState extends State<ImageToPdfApp> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      if (!mounted) {
        return;
      }
      if (Platform.isMacOS) {
        await FilePicker.skipEntitlementsChecks();
      }
    });
  }

  static const Color _paper = Color(0xFFE8E4DB);
  static const Color _paperHi = Color(0xFFF2EFE8);
  static const Color _ink = Color(0xFF2B2620);
  static const Color _inkMuted = Color(0xFF6B6458);
  static const Color _line = Color(0xFF9A9184);

  @override
  Widget build(BuildContext context) {
    final base = ThemeData(
      useMaterial3: false,
      brightness: Brightness.light,
      scaffoldBackgroundColor: _paper,
      dividerColor: _line,
      fontFamily: 'Courier New',
      colorScheme: const ColorScheme.light(
        primary: _ink,
        onPrimary: _paperHi,
        surface: _paperHi,
        onSurface: _ink,
        secondary: _inkMuted,
        onSecondary: _paperHi,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: _paper,
        foregroundColor: _ink,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        titleTextStyle: TextStyle(
          fontFamily: 'Courier New',
          fontSize: 17,
          fontWeight: FontWeight.w600,
          color: _ink,
          letterSpacing: 0.6,
        ),
      ),
      cardTheme: CardThemeData(
        color: _paperHi,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(kAppRadius),
        ),
      ),
      snackBarTheme: SnackBarThemeData(
        backgroundColor: _ink,
        contentTextStyle: const TextStyle(
          fontFamily: 'Courier New',
          color: _paperHi,
          fontSize: 13,
        ),
        behavior: SnackBarBehavior.fixed,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(kAppRadius),
        ),
      ),
      progressIndicatorTheme: const ProgressIndicatorThemeData(
        color: _ink,
        linearTrackColor: Color(0xFFD4CEC3),
      ),
      textTheme: const TextTheme(
        bodyLarge: TextStyle(color: _ink, fontSize: 14, height: 1.35),
        bodyMedium: TextStyle(color: _ink, fontSize: 13, height: 1.35),
        bodySmall: TextStyle(color: _inkMuted, fontSize: 12, height: 1.3),
        titleMedium: TextStyle(
          color: _ink,
          fontSize: 14,
          fontWeight: FontWeight.w600,
          letterSpacing: 0.4,
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: _ink,
          backgroundColor: _paperHi,
          side: const BorderSide(color: _ink, width: 1),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          minimumSize: const Size(88, 40),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(kAppRadius),
          ),
          textStyle: const TextStyle(
            fontFamily: 'Courier New',
            fontSize: 13,
            letterSpacing: 0.3,
          ),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: _ink,
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
          textStyle: const TextStyle(fontFamily: 'Courier New', fontSize: 13),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(kAppRadius),
          ),
        ),
      ),
    );

    return MaterialApp(title: '图片转 PDF', theme: base, home: const HomePage());
  }
}
