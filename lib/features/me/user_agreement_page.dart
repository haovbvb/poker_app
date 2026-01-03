import 'package:flutter/material.dart';
import 'package:poker_app/core/widgets/common_webview_page.dart';

class UserAgreementPage extends StatelessWidget {
  const UserAgreementPage({super.key});

  static const String agreementUrl = 'https://book.flutterchina.club/';

  @override
  Widget build(BuildContext context) {
    return CommonWebViewPage(
      initialUrl: agreementUrl,
    );
  }
}
