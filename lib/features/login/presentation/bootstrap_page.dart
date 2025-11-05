import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:merchant_app/app/app_router.dart';
import 'package:merchant_app/core/utils/logger.dart';
import 'package:merchant_app/features/login/models/auth_result.dart';
import 'package:merchant_app/features/login/providers/auth_controller.dart';
import 'package:merchant_app/network/network.dart';

/// 启动引导页：判断登录态后跳转 Home 或 Login。
class BootstrapPage extends ConsumerStatefulWidget {
  const BootstrapPage({super.key});

  @override
  ConsumerState<BootstrapPage> createState() => _BootstrapPageState();
}

class _BootstrapPageState extends ConsumerState<BootstrapPage> {
  bool _checking = true;
  final ApiService _apiService = ApiService();
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
        _refreshToken();
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

  Future<void> _refreshToken() async {
    final notifier = ref.read(authNotifierProvider.notifier);
    try {
      final response = await _apiService.post<AuthResult>(
        ApiPath.refreshToken,
        parser: _parseAuthResult,
        showHud: false,
        notifyOnError: false,
        toastOnBusinessError: false,
      );

      if (response.isSuccess && response.result != null) {
        await notifier.updateSession(response.result!);
      } else {
        await notifier.clearSession();
        AppRouter.goLogin();
      }
    } catch (_) {
      await notifier.clearSession();
      AppRouter.goLogin();
    }
  }

  AuthResult _parseAuthResult(dynamic data) {
    if (data is Map<String, dynamic>) {
      return AuthResult.fromJson(data);
    }
    if (data is Map) {
      return AuthResult.fromJson(Map<String, dynamic>.from(data));
    }
    throw NetworkExceptions('响应格式错误');
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
