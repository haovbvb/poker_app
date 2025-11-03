import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:merchant_app/app/app_router.dart';
import 'package:merchant_app/core/utils/context_extensions.dart';
import 'package:merchant_app/core/utils/logger.dart';
import 'package:merchant_app/features/login/models/auth_result.dart';
import 'package:merchant_app/features/login/models/auth_session.dart';
import 'package:merchant_app/features/login/providers/auth_controller.dart';
import 'package:merchant_app/network/api_path.dart';
import 'package:merchant_app/network/api_service.dart';
import 'package:merchant_app/network/network_exceptions.dart';

class HomeTab extends ConsumerStatefulWidget {
  const HomeTab({super.key});

  @override
  ConsumerState<HomeTab> createState() => _HomeTabState();
}

class _HomeTabState extends ConsumerState<HomeTab> {
  final ApiService _apiService = ApiService();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _refreshToken());
  }

  Future<void> _refreshToken() async {
    try {
      final response = await _apiService.post<AuthResult>(
        ApiPath.refreshToken,
        parser: _parseAuthResult,
        showHud: false,
        notifyOnError: false,
        toastOnBusinessError: false,
      );

      if (!mounted) {
        return;
      }

      if (response.isSuccess && response.result != null) {
        await ref
            .read(authNotifierProvider.notifier)
            .updateSession(response.result!);
      } else {
        await ref.read(authNotifierProvider.notifier).clearSession();
        AppRouter.goLogin();
      }
    } catch (_) {
      if (!mounted) {
        return;
      }
      await ref.read(authNotifierProvider.notifier).clearSession();
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
    final theme = Theme.of(context);
    final userInfo = AuthSession.instance.current;
    var name = userInfo?.name ?? '';
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            name,
            style: theme.textTheme.headlineSmall,
          ),
          const SizedBox(height: 12),
          Text(context.l10n.appTitle, style: theme.textTheme.bodyLarge),
        ],
      ),
    );
  }
}
