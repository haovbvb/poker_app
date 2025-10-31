import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:merchant_app/app/app_router.dart';
import 'package:merchant_app/core/constants/storage_keys.dart';
import 'package:merchant_app/core/utils/hash_utils.dart';
import 'package:merchant_app/core/utils/toast.dart';
import 'package:merchant_app/features/login/models/auth_result.dart';
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
    _bootstrap();
    return AuthState.initialLoading();
  }

  /// 执行登录流程，并在成功后保存 token。
  Future<void> login({required String name, required String password}) async {
    state = state.copyWith(
      isLoading: true,
      updateError: true,
      errorMessage: null,
    );
    try {
      final hashedPassword = HashUtils.md5Lower32(password);
      final response = await _apiService.post<AuthResult>(
        ApiPath.login,
        data: {'name': name, 'password': hashedPassword},
        parser: _parseAuthResult,
      );

      if (!response.isSuccess) {
        final message = response.message.isNotEmpty ? response.message : '请求失败';
        showToast(message);
        state = state.copyWith(
          isLoading: false,
          updateError: true,
          errorMessage: message,
        );
        return;
      }

      final token = response.data?.token ?? '';
      if (token.isEmpty) {
        throw NetworkExceptions('缺少 token');
      }

      await _persistToken(token);

      state = state.copyWith(
        updateToken: true,
        token: token,
        isLoading: false,
        updateError: true,
        errorMessage: null,
      );
      Future.microtask(AppRouter.goHome);
    } catch (e) {
      final message = e is NetworkExceptions ? e.message : e.toString();
      showToast(message);
      state = state.copyWith(
        isLoading: false,
        updateError: true,
        errorMessage: message,
      );
    }
  }

  /// 清除 token 并重置为未登录状态。
  Future<void> logout() async {
    await _clearToken();
    state = state.copyWith(
      updateToken: true,
      token: null,
      isLoading: false,
      updateError: true,
      errorMessage: null,
    );
    Future.microtask(AppRouter.goLogin);
  }

  /// 启动时尝试恢复本地 token，提升冷启动体验。
  Future<void> _bootstrap() async {
    try {
      final token = await _readToken();
      state = state.copyWith(
        updateToken: true,
        token: token,
        isLoading: false,
        updateError: true,
        errorMessage: null,
      );
      if (token != null && token.isNotEmpty) {
        Future.microtask(AppRouter.goHome);
      } else {
        Future.microtask(AppRouter.goLogin);
      }
    } catch (e) {
      final message = e is NetworkExceptions ? e.message : e.toString();
      state = state.copyWith(
        isLoading: false,
        updateError: true,
        errorMessage: message,
      );
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
  }
}
