import 'package:flutter_test/flutter_test.dart';

import 'package:lostify_ai/app/app.dart';

void main() {
  testWidgets('Lostify app loads splash screen', (WidgetTester tester) async {
    await tester.pumpWidget(const LostifyApp());

    expect(find.text('Lostify AI'), findsOneWidget);
    expect(find.text('AI-Powered Search.\nFaster Recovery.'), findsOneWidget);
  });
}
