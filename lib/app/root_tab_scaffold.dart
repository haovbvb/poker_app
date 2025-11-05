import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:merchant_app/features/home/home.dart';
import 'package:merchant_app/features/me/me.dart';
import 'package:merchant_app/features/work/work.dart';
import 'package:merchant_app/l10n/app_localizations.dart';

final bottomNavIndexProvider = NotifierProvider<_BottomNavIndexNotifier, int>(
  _BottomNavIndexNotifier.new,
);

class RootTabScaffold extends ConsumerWidget {
  const RootTabScaffold({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context)!;
    final currentIndex = ref.watch(bottomNavIndexProvider);
    final tabs = <_TabConfig>[
      _TabConfig(
        title: l10n.homeTitle,
        label: l10n.tabHome,
        iconAsset: 'assets/images/tab_1.png',
        activeIconAsset: 'assets/images/tab_1_selected.png',
        body: const HomeTab(),
      ),
      _TabConfig(
        title: l10n.workTitle,
        label: l10n.tabWork,
        iconAsset: 'assets/images/tab_2.png',
        activeIconAsset: 'assets/images/tab_2_selected.png',
        body: const WorkTab(),
      ),
      _TabConfig(
        title: '',
        label: l10n.tabMe,
        iconAsset: 'assets/images/tab_3.png',
        activeIconAsset: 'assets/images/tab_3_selected.png',
        body: const ProfileTab(),
      ),
    ];

    return Scaffold(
      // appBar: AppBar(title: Text(tabs[currentIndex].title)),
      body: IndexedStack(
        index: currentIndex,
        children: tabs.map((tab) => tab.body).toList(growable: false),
      ),
      bottomNavigationBar: Theme(
        data: Theme.of(context).copyWith(
          splashFactory: NoSplash.splashFactory,
          highlightColor: Colors.transparent,
        ),
        child: BottomNavigationBar(
          currentIndex: currentIndex,
          onTap: (index) =>
              ref.read(bottomNavIndexProvider.notifier).setIndex(index),
          type: BottomNavigationBarType.fixed,
          items: tabs
              .map(
                (tab) => BottomNavigationBarItem(
                  icon: Image.asset(tab.iconAsset),
                  activeIcon: Image.asset(tab.activeIconAsset ?? tab.iconAsset),
                  label: tab.label,
                ),
              )
              .toList(growable: false),
        ),
      ),
    );
  }
}

class _BottomNavIndexNotifier extends Notifier<int> {
  @override
  int build() => 0;

  void setIndex(int value) => state = value;
}

class _TabConfig {
  const _TabConfig({
    required this.title,
    required this.label,
    required this.iconAsset,
    this.activeIconAsset,
    required this.body,
  });

  final String title;
  final String label;
  final String iconAsset;
  final String? activeIconAsset;
  final Widget body;
}
