import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:poker_app/core/utils/context_extensions.dart';
import 'package:poker_app/features/me/providers/language_notifier.dart';

class LanguageSelectionPage extends ConsumerWidget {
  const LanguageSelectionPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final currentLocale = ref.watch(languageNotifierProvider);
    final theme = Theme.of(context);
    final options = _buildOptions(context);

    return Scaffold(
      appBar: AppBar(title: Text(context.l10n.tabMe)),
      body: RadioGroup<Locale>(
        groupValue: currentLocale,
        onChanged: (value) {
          if (value == null) {
            return;
          }
          _onSelect(ref, value, context);
        },
        child: ListView.separated(
          itemBuilder: (context, index) {
            final option = options[index];
            final isSelected = option.locale == currentLocale;
            return ListTile(
              leading: Icon(option.icon, color: theme.colorScheme.primary),
              title: Text(option.title),
              subtitle: Text(option.subtitle),
              trailing: Radio<Locale>(value: option.locale),
              onTap: () => _onSelect(ref, option.locale, context),
              selected: isSelected,
            );
          },
          separatorBuilder: (_, __) => const Divider(height: 1),
          itemCount: options.length,
        ),
      ),
    );
  }

  void _onSelect(WidgetRef ref, Locale locale, BuildContext context) {
    ref.read(languageNotifierProvider.notifier).setLocale(locale);
    Navigator.of(context).pop();
  }

  List<_LanguageOption> _buildOptions(BuildContext context) => [
    _LanguageOption(
      locale: const Locale('en'),
      title: 'English',
      subtitle: 'English (US)',
      icon: Icons.language,
    ),
    _LanguageOption(
      locale: const Locale('zh'),
      title: '简体中文',
      subtitle: 'Chinese (Simplified)',
      icon: Icons.translate,
    ),
  ];
}

class _LanguageOption {
  const _LanguageOption({
    required this.locale,
    required this.title,
    required this.subtitle,
    required this.icon,
  });

  final Locale locale;
  final String title;
  final String subtitle;
  final IconData icon;
}
