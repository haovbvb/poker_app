import 'package:flutter/material.dart';
import 'package:merchant_app/core/utils/context_extensions.dart';

class WorkTab extends StatefulWidget {
  const WorkTab({super.key});

  @override
  State<WorkTab> createState() => _WorkTabState();
}

class _WorkTabState extends State<WorkTab> {
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Text(context.l10n.workInProgress, textAlign: TextAlign.center),
      ),
    );
  }
}
