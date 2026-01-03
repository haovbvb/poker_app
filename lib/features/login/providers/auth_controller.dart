import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:poker_app/app/app_router.dart';
import 'package:poker_app/core/constants/storage_keys.dart';
import 'package:poker_app/core/utils/logger.dart';
import 'package:poker_app/core/utils/toast.dart';
import 'package:poker_app/features/login/models/auth_result.dart';
import 'package:poker_app/features/login/models/auth_session.dart';
import 'package:poker_app/features/login/models/user_state.dart';
import 'package:poker_app/network/network.dart';
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
      final response = await _apiService.post<AuthResult>(
        ApiPath.login,
        data: {'username': name, 'password': password},
        parser: _parseAuthResult,
      );

      if (!response.isSuccess) {
        return;
      }

      final authResult = response.result;
      if (authResult == null || authResult.accessToken.isEmpty) {
        showToast('缺少 access_token');
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
    _apiClient.setAuthToken(result.accessToken);
    await _persistSession(result);
    AuthSession.instance.update(result);
    state = UserState(token: result.accessToken, user: result);
  }

  Future<void> clearSession() async {
    await _clearPersistedSession();
    _apiClient.clearAuthToken();
    AuthSession.instance.clear();
    state = const UserState();
  }

  Future<String?> loadTokenFromStorage() async {
    return _readToken();
  }

  Future<String?> loadRefreshTokenFromStorage() async {
    return _readRefreshToken();
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

  Future<void> _persistSession(AuthResult session) async {
    try {
      final prefs = await SharedPreferences.getInstance();

      final okAccess = await prefs.setString(
        StorageKeys.authToken,
        session.accessToken,
      );
      if (!okAccess) {
        logW('[AuthNotifier] Failed to persist access token');
      }

      if (session.refreshToken.isNotEmpty) {
        final okRefresh = await prefs.setString(
          StorageKeys.refreshToken,
          session.refreshToken,
        );
        if (!okRefresh) {
          logW('[AuthNotifier] Failed to persist refresh token');
        }
      }

      logI('[AuthNotifier] Session 持久化完成');
    } catch (error, stackTrace) {
      logE('[AuthNotifier] Error persisting session', error, stackTrace);
    }
  }

  Future<String?> _readToken() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString(StorageKeys.authToken);
    return token;
  }

  Future<String?> _readRefreshToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(StorageKeys.refreshToken);
  }

  Future<void> _clearPersistedSession() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(StorageKeys.authToken);
      await prefs.remove(StorageKeys.refreshToken);
    } catch (error, stackTrace) {
      logE('[AuthNotifier] Error clearing session', error, stackTrace);
    }
  }
}
