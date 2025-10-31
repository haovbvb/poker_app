import 'package:flutter/material.dart';
import 'package:merchant_app/core/utils/context_extensions.dart';

class HomeTab extends StatefulWidget {
  const HomeTab({super.key});

  @override
  State<HomeTab> createState() => _HomeTabState();
}

class _HomeTabState extends State<HomeTab> {
  @override
  Widget build(BuildContext context) {
    
    final theme = Theme.of(context);

    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            context.l10n.welcomeMessage,
            style: theme.textTheme.headlineSmall,
          ),
          const SizedBox(height: 12),
          Text(context.l10n.appTitle, style: theme.textTheme.bodyLarge),
        ],
      ),
    );
  }
}
