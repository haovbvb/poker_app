import 'package:flutter/material.dart';
import 'package:merchant_app/core/utils/context_extensions.dart';

class AboutPage extends StatelessWidget {
  const AboutPage({super.key});

  static const String _appVersion = '1.0.0+1';
  static const String _supportEmail = 'support@example.com';

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(context.l10n.profileAbout)),
      body: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          Text(context.l10n.appTitle, style: theme.textTheme.headlineSmall),
          const SizedBox(height: 12),
          Text('Version $_appVersion', style: theme.textTheme.bodyMedium),
          const SizedBox(height: 24),
          Card(
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
            ),
            child: ListTile(
              leading: const Icon(Icons.help_outline),
              title: const Text('Support'),
              subtitle: Text(_supportEmail),
            ),
          ),
        ],
      ),
    );
  }
}
