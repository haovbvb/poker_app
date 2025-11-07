import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:merchant_app/core/utils/context_extensions.dart';

class WorkTab extends ConsumerWidget {
  const WorkTab({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = context.l10n;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Text(l10n.workInProgress, textAlign: TextAlign.center),
      ),
    );
  }
}


