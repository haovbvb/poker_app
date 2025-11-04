import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:merchant_app/core/utils/context_extensions.dart';
import 'package:merchant_app/features/login/providers/auth_controller.dart';

class HomeTab extends ConsumerWidget {
  const HomeTab({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final user = ref.watch(authNotifierProvider).user;
    final name = (user?.name ?? '').trim();

    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            name.isNotEmpty ? name : context.l10n.tabMe,
            style: theme.textTheme.headlineSmall,
          ),
          const SizedBox(height: 12),
          Text(context.l10n.appTitle, style: theme.textTheme.bodyLarge),
        ],
      ),
    );
  }
}
