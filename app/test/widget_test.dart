import 'package:flutter_test/flutter_test.dart';

import 'package:image_to_pdf/main.dart';

void main() {
  testWidgets('App loads', (WidgetTester tester) async {
    await tester.pumpWidget(const ImageToPdfApp());
    expect(find.text('图片 → PDF'), findsOneWidget);
  });
}
