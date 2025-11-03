import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:merchant_app/app/app_router.dart';
import 'package:merchant_app/core/constants/storage_keys.dart';
import 'package:merchant_app/core/utils/hash_utils.dart';
import 'package:merchant_app/core/utils/toast.dart';
import 'package:merchant_app/features/login/models/auth_result.dart';
import 'package:merchant_app/features/login/models/auth_session.dart';
import 'package:merchant_app/features/login/models/auth_state.dart';
import 'package:merchant_app/network/api_client.dart';
import 'package:merchant_app/network/api_path.dart';
import 'package:merchant_app/network/api_service.dart';
import 'package:merchant_app/network/network_exceptions.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// 对外暴露登录状态，供 UI 订阅的 Riverpod Notifier。
final authNotifierProvider = NotifierProvider<AuthNotifier, AuthState>(
  AuthNotifier.new,
);

/// 管理登录、登出流程的状态机，并负责恢复持久化的 token。
class AuthNotifier extends Notifier<AuthState> {
  final ApiService _apiService = ApiService();

  @override
  AuthState build() {
    return AuthState();
  }

  /// 执行登录流程，并在成功后保存 token。
  Future<void> login({required String name, required String password}) async {
    try {
      final hashedPassword = HashUtils.md5Lower32(password);
      final response = await _apiService.post<AuthResult>(
        ApiPath.login,
        data: {'name': name, 'password': hashedPassword},
        parser: _parseAuthResult,
      );

      if (!response.isSuccess) {
        return;
      }

      final authResult = response.result;
      if (authResult == null || authResult.token.isEmpty) {
        showToast('缺少 token');
        return;
      }

      await updateSession(authResult);
      Future.microtask(AppRouter.goHome);
    } catch (e) {
      // 全局已处理提示，这里仅确保状态不变。
    }
  }

  /// 清除 token 并重置为未登录状态。
  Future<void> logout() async {
    try {
      final response = await _apiService.post<AuthResult>(
        ApiPath.logout,
        parser: _parseAuthResult,
      );

      if (!response.isSuccess) {
        return;
      }

      await clearSession();
      Future.microtask(AppRouter.goLogin);
    } catch (_) {
      // 全局已处理提示。
    }
  }

  Future<void> updateSession(AuthResult result) async {
    AuthSession.instance.update(result);
    await _persistToken(result.token);
    state = AuthState(token: result.token);
  }

  Future<void> clearSession() async {
    await _clearToken();
    state = const AuthState();
  }

  Future<String?> loadTokenFromStorage() async {
    return _readToken();
  }

  void setToken(String token) {
    state = AuthState(token: token);
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

  Future<void> _persistToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(StorageKeys.authToken, token);
    ApiClient().setAuthToken(token);
  }

  Future<String?> _readToken() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString(StorageKeys.authToken);
    ApiClient().setAuthToken(token);
    return token;
  }

  Future<void> _clearToken() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(StorageKeys.authToken);
    ApiClient().clearAuthToken();
    AuthSession.instance.clear();
  }
}
