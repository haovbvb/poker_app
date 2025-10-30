import 'package:flutter/material.dart';
import 'package:merchant_app/l10n/app_localizations.dart';

class WorkTab extends StatelessWidget {
  const WorkTab({super.key});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Text(l10n.workInProgress, textAlign: TextAlign.center),
      ),
    );
  }
}
