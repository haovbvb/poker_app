import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:merchant_app/app/theme.dart';

import 'features/home/home.dart';
import 'features/me/me.dart';
import 'features/work/work.dart';
import 'l10n/app_localizations.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const ProviderScope(child: MerchantApp()));
}

final _lightThemeProvider = Provider<ThemeData>(
  (ref) => BaseTheme.lightTheme(),
);
final _darkThemeProvider = Provider<ThemeData>((ref) => BaseTheme.darkTheme());
final _themeModeProvider = NotifierProvider<_ThemeModeNotifier, ThemeMode>(
  _ThemeModeNotifier.new,
);
final _bottomNavIndexProvider = NotifierProvider<_BottomNavIndexNotifier, int>(
  _BottomNavIndexNotifier.new,
);

class MerchantApp extends ConsumerWidget {
  const MerchantApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      onGenerateTitle: (ctx) => AppLocalizations.of(ctx)!.appTitle,
      theme: ref.watch(_lightThemeProvider),
      darkTheme: ref.watch(_darkThemeProvider),
      themeMode: ref.watch(_themeModeProvider),
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      home: const _RootTabScaffold(),
    );
  }
}

class _RootTabScaffold extends ConsumerWidget {
  const _RootTabScaffold();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context)!;
    final currentIndex = ref.watch(_bottomNavIndexProvider);
    final tabs = <_TabConfig>[
      _TabConfig(
        title: l10n.homeTitle,
        label: l10n.tabHome,
        icon: Icons.home_outlined,
        activeIcon: Icons.home,
        body: const HomeTab(),
      ),
      _TabConfig(
        title: l10n.workTitle,
        label: l10n.tabWork,
        icon: Icons.work_outline,
        activeIcon: Icons.work,
        body: const WorkTab(),
      ),
      _TabConfig(
        title: l10n.meTitle,
        label: l10n.tabMe,
        icon: Icons.person_outline,
        activeIcon: Icons.person,
        body: const ProfileTab(),
      ),
    ];

    return Scaffold(
      appBar: AppBar(title: Text(tabs[currentIndex].title)),
      body: IndexedStack(
        index: currentIndex,
        children: tabs.map((tab) => tab.body).toList(growable: false),
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: currentIndex,
        onTap: (index) =>
            ref.read(_bottomNavIndexProvider.notifier).setIndex(index),
        type: BottomNavigationBarType.fixed,
        items: tabs
            .map(
              (tab) => BottomNavigationBarItem(
                icon: Icon(tab.icon),
                activeIcon: Icon(tab.activeIcon),
                label: tab.label,
              ),
            )
            .toList(growable: false),
      ),
    );
  }
}

class _BottomNavIndexNotifier extends Notifier<int> {
  @override
  int build() => 0;

  void setIndex(int value) => state = value;
}

class _ThemeModeNotifier extends Notifier<ThemeMode> {
  @override
  ThemeMode build() => ThemeMode.system;

  void setThemeMode(ThemeMode mode) => state = mode;
}

class _TabConfig {
  const _TabConfig({
    required this.title,
    required this.label,
    required this.icon,
    required this.activeIcon,
    required this.body,
  });

  final String title;
  final String label;
  final IconData icon;
  final IconData activeIcon;
  final Widget body;
}
