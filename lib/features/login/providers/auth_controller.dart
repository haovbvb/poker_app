import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:merchant_app/app/app_router.dart';
import 'package:merchant_app/core/constants/storage_keys.dart';
import 'package:merchant_app/core/utils/hash_utils.dart';
import 'package:merchant_app/core/utils/logger.dart';
import 'package:merchant_app/core/utils/toast.dart';
import 'package:merchant_app/features/login/models/auth_result.dart';
import 'package:merchant_app/features/login/models/auth_session.dart';
import 'package:merchant_app/features/login/models/user_state.dart';
import 'package:merchant_app/network/network.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// 对外暴露登录状态，供 UI 订阅的 Riverpod Notifier。
final authNotifierProvider = NotifierProvider<AuthNotifier, UserState>(
  AuthNotifier.new,
);

/// 管理登录、登出流程的状态机，并负责恢复持久化的 token。
class AuthNotifier extends Notifier<UserState> {
  final ApiService _apiService = ApiService();
  final ApiClient _apiClient = ApiClient();

  @override
  UserState build() {
    return const UserState();
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
    _apiClient.setAuthToken(result.token);
    await _persistToken(result.token);
    AuthSession.instance.update(result);
    state = UserState(token: result.token, user: result);
  }

  Future<void> clearSession() async {
    await _clearToken();
    _apiClient.clearAuthToken();
    AuthSession.instance.clear();
    state = const UserState();
  }

  Future<String?> loadTokenFromStorage() async {
    return _readToken();
  }

  void setToken(String token) {
    _apiClient.setAuthToken(token);
    state = state.copyWith(token: token);
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
    try {
      final prefs = await SharedPreferences.getInstance();
      final ok = await prefs.setString(StorageKeys.authToken, token);
      if (!ok) {
        logW('[AuthNotifier] Failed to persist token');
      } else {
        logI('[AuthNotifier] Token 更新成功！');
      }
    } catch (error, stackTrace) {
      logE('[AuthNotifier] Error persisting token', error, stackTrace);
    }
  }

  Future<String?> _readToken() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString(StorageKeys.authToken);
    return token;
  }

  Future<void> _clearToken() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(StorageKeys.authToken);
    } catch (error, stackTrace) {
      logE('[AuthNotifier] Error clearing token', error, stackTrace);
    }
  }
}
