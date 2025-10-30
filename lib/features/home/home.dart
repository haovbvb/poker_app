import 'package:flutter/material.dart';
import 'package:merchant_app/l10n/app_localizations.dart';

class HomeTab extends StatelessWidget {
  const HomeTab({super.key});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);

    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(l10n.welcomeMessage, style: theme.textTheme.headlineSmall),
          const SizedBox(height: 12),
          Text(l10n.appTitle, style: theme.textTheme.bodyLarge),
        ],
      ),
    );
  }
}
