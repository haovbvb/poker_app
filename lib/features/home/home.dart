import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:poker_app/app/styles/colors.dart';
import 'package:poker_app/app/root_tab_scaffold.dart';
import 'package:poker_app/core/utils/context_extensions.dart';

enum _LobbyTier { normal, vip }

class _PokerTableInfo {
  const _PokerTableInfo({
    required this.tableNo,
    required this.buyInRange,
    required this.blinds,
    required this.feePerHand,
    required this.tier,
  });

  final int tableNo;
  final String buyInRange;
  final String blinds;
  final String feePerHand;
  final _LobbyTier tier;
}

const _tables = <_PokerTableInfo>[
  _PokerTableInfo(
    tableNo: 1,
    buyInRange: '150K / 750K',
    blinds: '2.5K / 5K',
    feePerHand: '1.5K',
    tier: _LobbyTier.normal,
  ),
  _PokerTableInfo(
    tableNo: 2,
    buyInRange: '300K / 1.5M',
    blinds: '5K / 10K',
    feePerHand: '3K',
    tier: _LobbyTier.normal,
  ),
  _PokerTableInfo(
    tableNo: 3,
    buyInRange: '1.5M / 7.5M',
    blinds: '25K / 50K',
    feePerHand: '15K',
    tier: _LobbyTier.normal,
  ),
  _PokerTableInfo(
    tableNo: 4,
    buyInRange: '6M / 30M',
    blinds: '100K / 200K',
    feePerHand: '60K',
    tier: _LobbyTier.normal,
  ),
  _PokerTableInfo(
    tableNo: 5,
    buyInRange: '30M / 150M',
    blinds: '500K / 1M',
    feePerHand: '300K',
    tier: _LobbyTier.vip,
  ),
  _PokerTableInfo(
    tableNo: 6,
    buyInRange: '150M / 750M',
    blinds: '2.5M / 5M',
    feePerHand: '1.5M',
    tier: _LobbyTier.vip,
  ),
  _PokerTableInfo(
    tableNo: 7,
    buyInRange: '600M / 3B',
    blinds: '10M / 20M',
    feePerHand: '6M',
    tier: _LobbyTier.vip,
  ),
  _PokerTableInfo(
    tableNo: 8,
    buyInRange: '3B / 15B',
    blinds: '50M / 100M',
    feePerHand: '30M',
    tier: _LobbyTier.vip,
  ),
];

final _lobbyTierProvider = NotifierProvider<_LobbyTierNotifier, _LobbyTier>(
  _LobbyTierNotifier.new,
);

class _LobbyTierNotifier extends Notifier<_LobbyTier> {
  @override
  _LobbyTier build() => _LobbyTier.normal;

  void setTier(_LobbyTier value) => state = value;
}

class HomeTab extends ConsumerWidget {
  const HomeTab({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tier = ref.watch(_lobbyTierProvider);
    final visibleTables = _tables
        .where((t) => t.tier == tier)
        .toList(growable: false);

    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              SizedBox(
                width: 240,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text(
                      '大厅',
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        color: AppColors.black09Text,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 12),
                    _TierButton(
                      title: '常规桌',
                      subtitle: '无需订阅',
                      selected: tier == _LobbyTier.normal,
                      onTap: () => ref
                          .read(_lobbyTierProvider.notifier)
                          .setTier(_LobbyTier.normal),
                    ),
                    const SizedBox(height: 12),
                    _TierButton(
                      title: '高级桌',
                      subtitle: '需要订阅',
                      selected: tier == _LobbyTier.vip,
                      onTap: () => ref
                          .read(_lobbyTierProvider.notifier)
                          .setTier(_LobbyTier.vip),
                    ),
                    const Spacer(),
                    FilledButton(
                      onPressed: () =>
                          ref.read(bottomNavIndexProvider.notifier).setIndex(1),
                      child: const Text('进入游戏主页'),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      context.l10n.homeTitle,
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: AppColors.black05Text,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 16),
              Expanded(child: _TableList(tables: visibleTables)),
            ],
          ),
        ),
      ),
    );
  }
}

class _TierButton extends StatelessWidget {
  const _TierButton({
    required this.title,
    required this.subtitle,
    required this.selected,
    required this.onTap,
  });

  final String title;
  final String subtitle;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return InkWell(
      borderRadius: BorderRadius.circular(16),
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: selected
              ? AppColors.primaryColor.withValues(alpha: 0.08)
              : null,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: selected
                ? AppColors.primaryColor.withValues(alpha: 0.25)
                : Colors.black.withValues(alpha: 0.06),
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: theme.textTheme.titleMedium?.copyWith(
                color: AppColors.black09Text,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              subtitle,
              style: theme.textTheme.bodySmall?.copyWith(
                color: AppColors.black05Text,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _TableList extends StatelessWidget {
  const _TableList({required this.tables});

  final List<_PokerTableInfo> tables;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.black.withValues(alpha: 0.06)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 10),
            child: Row(
              children: [
                Text(
                  '牌桌列表',
                  style: theme.textTheme.titleMedium?.copyWith(
                    color: AppColors.black09Text,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const Spacer(),
                Text(
                  '点击进入（占位）',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: AppColors.black05Text,
                  ),
                ),
              ],
            ),
          ),
          const Divider(height: 1),
          Expanded(
            child: ListView.separated(
              padding: const EdgeInsets.all(16),
              itemBuilder: (context, index) => _TableCard(info: tables[index]),
              separatorBuilder: (_, __) => const SizedBox(height: 12),
              itemCount: tables.length,
            ),
          ),
        ],
      ),
    );
  }
}

class _TableCard extends StatelessWidget {
  const _TableCard({required this.info});

  final _PokerTableInfo info;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return InkWell(
      onTap: () {},
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: Colors.black.withValues(alpha: 0.06)),
        ),
        child: Row(
          children: [
            Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                color: AppColors.primaryColor.withValues(alpha: 0.08),
                borderRadius: BorderRadius.circular(12),
              ),
              alignment: Alignment.center,
              child: Text(
                '${info.tableNo}',
                style: theme.textTheme.titleMedium?.copyWith(
                  color: AppColors.primaryColor,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '买入：${info.buyInRange}',
                    style: theme.textTheme.titleSmall?.copyWith(
                      color: AppColors.black09Text,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    '盲注：${info.blinds}    每局固定消耗：${info.feePerHand}',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: AppColors.black06Text,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 12),
            Text(
              info.tier == _LobbyTier.vip ? 'VIP' : '常规',
              style: theme.textTheme.labelMedium?.copyWith(
                color: info.tier == _LobbyTier.vip
                    ? Colors.orange.shade800
                    : AppColors.black06Text,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
