import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:poker_app/app/app_router.dart';
import 'package:poker_app/core/utils/toast.dart';
import 'package:poker_app/features/home/settings_dialog.dart';
import 'package:poker_app/network/api_path.dart';
import 'package:poker_app/network/api_service.dart';

class HomeTab extends ConsumerWidget {
  const HomeTab({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Color(0xFF1A4D6F), Color(0xFF0F2942)],
          ),
        ),
        child: SafeArea(
          child: Column(
            children: [
              // 顶部筹码显示
              Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: 24,
                  vertical: 16,
                ),
                child: Row(
                  children: [
                    // 用户头像
                    Container(
                      width: 56,
                      height: 56,
                      decoration: BoxDecoration(
                        color: const Color(0xFFE67E22),
                        borderRadius: BorderRadius.circular(28),
                        border: Border.all(color: Colors.white, width: 2),
                      ),
                      child: const Icon(
                        Icons.person,
                        color: Colors.white,
                        size: 32,
                      ),
                    ),
                    const SizedBox(width: 12),
                    const Text(
                      'Page',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 20,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    const Spacer(),
                    // 筹码显示
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 20,
                        vertical: 10,
                      ),
                      decoration: BoxDecoration(
                        color: Colors.black.withValues(alpha: 0.3),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: const Row(
                        children: [
                          Text(
                            '123.23M',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 18,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          SizedBox(width: 12),
                          Icon(
                            Icons.add_circle_outline,
                            color: Colors.white,
                            size: 24,
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              // 中间卡片区域
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: Row(
                    children: [
                      // 公告卡片
                      Expanded(
                        child: _PokerCard(
                          title: '公告',
                          gradient: const LinearGradient(
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                            colors: [Color(0xFF1A4D6F), Color(0xFF0F2942)],
                          ),
                          imagePath: 'assets/images/chips_stack.png',
                          onTap: () {},
                        ),
                      ),
                      const SizedBox(width: 12),
                      // 高级桌卡片
                      Expanded(
                        child: _PokerCard(
                          title: '高级桌',
                          gradient: const LinearGradient(
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                            colors: [Color(0xFF2B5B7F), Color(0xFF1A4D6F)],
                          ),
                          imagePath: 'assets/images/premium_table.png',
                          onTap: () {},
                        ),
                      ),
                      const SizedBox(width: 12),
                      // VIP桌卡片
                      Expanded(
                        child: _PokerCard(
                          title: 'VIP-桌',
                          gradient: const LinearGradient(
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                            colors: [Color(0xFF3A6B8F), Color(0xFF2B5B7F)],
                          ),
                          imagePath: 'assets/images/vip_table.png',
                          onTap: () {},
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              // 底部导航栏
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 24,
                  vertical: 16,
                ),
                decoration: BoxDecoration(
                  color: Colors.black.withValues(alpha: 0.3),
                ),
                child: Row(
                  children: [
                    _BottomNavIcon(
                      icon: Icons.shopping_bag_outlined,
                      label: 'SHOP',
                      onTap: () {},
                    ),
                    const SizedBox(width: 32),
                    _BottomNavIcon(
                      icon: Icons.chat_bubble_outline,
                      label: '',
                      onTap: () {},
                    ),
                    const SizedBox(width: 32),
                    _BottomNavIcon(
                      icon: Icons.settings_outlined,
                      label: '',
                      onTap: () {
                        showDialog<void>(
                          context: context,
                          barrierDismissible: true,
                          builder: (_) => const SettingsDialog(),
                        );
                      },
                    ),
                    const Spacer(),
                    // 快速开始按钮
                    ElevatedButton(
                      onPressed: () => _onQuickStart(context),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFFFFEB3B),
                        foregroundColor: Colors.black,
                        padding: const EdgeInsets.symmetric(
                          horizontal: 48,
                          vertical: 16,
                        ),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8),
                        ),
                        elevation: 0,
                      ),
                      child: const Text(
                        '快速开始',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _PokerCard extends StatelessWidget {
  const _PokerCard({
    required this.title,
    required this.gradient,
    required this.imagePath,
    required this.onTap,
  });

  final String title;
  final Gradient gradient;
  final String imagePath;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        decoration: BoxDecoration(
          gradient: gradient,
          borderRadius: BorderRadius.circular(12),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.3),
              blurRadius: 8,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Stack(
          children: [
            // 背景图片（占位）
            Positioned.fill(
              child: ClipRRect(
                borderRadius: BorderRadius.circular(12),
                child: Image.asset(
                  imagePath,
                  fit: BoxFit.cover,
                  errorBuilder: (_, __, ___) => Container(
                    decoration: BoxDecoration(gradient: gradient),
                    child: const Center(
                      child: Icon(
                        Icons.casino,
                        color: Colors.white54,
                        size: 64,
                      ),
                    ),
                  ),
                ),
              ),
            ),
            // 标题
            Positioned(
              top: 16,
              left: 16,
              child: Text(
                title,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 24,
                  fontWeight: FontWeight.w600,
                  shadows: [Shadow(color: Colors.black54, blurRadius: 4)],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _BottomNavIcon extends StatelessWidget {
  const _BottomNavIcon({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Padding(
        padding: const EdgeInsets.all(8),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, color: Colors.white, size: 28),
            if (label.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(
                label,
                style: const TextStyle(color: Colors.white, fontSize: 12),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

Future<void> _onQuickStart(BuildContext context) async {
  const defaultBuyIn = 1000000;
  final api = ApiService();

  try {
    final resp = await api.post<Map<String, dynamic>>(
      ApiPath.v1PokerTablesQuickStart,
      data: {'max_chips': defaultBuyIn},
      parser: (json) => Map<String, dynamic>.from(json as Map),
    );

    final tableId = resp.result?['table_id'] as String?;
    if (!resp.isSuccess || tableId == null || tableId.isEmpty) {
      showToast(resp.message.isNotEmpty ? resp.message : '未获取到牌桌');
      return;
    }

    AppRouter.pushGame(tableId);
  } catch (e) {
    showToast('快速开始失败: $e');
  }
}
