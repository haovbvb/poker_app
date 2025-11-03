import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:merchant_app/app/app_router.dart';
import 'package:merchant_app/features/login/providers/auth_controller.dart';

/// 启动引导页：判断登录态后跳转 Home 或 Login。
class BootstrapPage extends ConsumerStatefulWidget {
  const BootstrapPage({super.key});

  @override
  ConsumerState<BootstrapPage> createState() => _BootstrapPageState();
}

class _BootstrapPageState extends ConsumerState<BootstrapPage> {
  bool _checking = true;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _bootstrap());
  }

  Future<void> _bootstrap() async {
    final notifier = ref.read(authNotifierProvider.notifier);
    try {
      final token = await notifier.loadTokenFromStorage();
      if (!mounted) {
        return;
      }

      if (token != null && token.isNotEmpty) {
        notifier.setToken(token);
        AppRouter.goHome();
      } else {
        await notifier.clearSession();
        AppRouter.goLogin();
      }
    } catch (_) {
      if (!mounted) {
        return;
      }
      await notifier.clearSession();
      AppRouter.goLogin();
    } finally {
      if (mounted) {
        setState(() => _checking = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: _checking
            ? const CircularProgressIndicator.adaptive()
            : const SizedBox.shrink(),
      ),
    );
  }
}
