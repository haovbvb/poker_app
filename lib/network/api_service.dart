import 'dart:async';

import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:poker_app/app/app_router.dart';
import 'package:poker_app/core/utils/toast.dart';
import 'package:poker_app/features/login/providers/auth_controller.dart';

import 'api_client.dart';
import 'base_response.dart';

// 调用示例:
// final apiService = ApiService();
// final posts = await apiService.get<List<dynamic>>(
//   ApiPath.posts,
//   parser: (data) => List<dynamic>.from(data as Iterable),
// );
// final created = await apiService.post<Map<String, dynamic>>(
//   ApiPath.posts,
//   data: {'title': 'foo', 'body': 'bar'},
//   parser: (data) => Map<String, dynamic>.from(data as Map),
// );

class ApiService {
  final _client = ApiClient();

  Future<BaseResponse<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    required T Function(dynamic json) parser,
    bool showHud = true,
    bool notifyOnError = true,
    bool toastOnBusinessError = true,
  }) async {
    final response = await _client.get(
      path,
      params: queryParameters,
      showHud: showHud,
      notifyOnError: notifyOnError,
    );
    final payload = response.data;

    if (payload is Map<String, dynamic> && payload.containsKey('code')) {
      final result = BaseResponse.fromJson(payload, parser);
      await _handleBusinessError(result, toastOnBusinessError && notifyOnError);
      return result;
    }

    final result = BaseResponse.fromJson({
      'code': response.statusCode ?? 0,
      'msg': response.statusMessage ?? '',
      'result': payload,
    }, parser);
    await _handleBusinessError(result, toastOnBusinessError && notifyOnError);
    return result;
  }

  Future<BaseResponse<T>> post<T>(
    String path, {
    dynamic data,
    required T Function(dynamic json) parser,
    bool showHud = true,
    bool notifyOnError = true,
    bool toastOnBusinessError = true,
  }) async {
    final response = await _client.post(
      path,
      data: data,
      showHud: showHud,
      notifyOnError: notifyOnError,
    );
    final payload = response.data;

    if (payload is Map<String, dynamic> && payload.containsKey('code')) {
      final result = BaseResponse.fromJson(payload, parser);
      await _handleBusinessError(result, toastOnBusinessError && notifyOnError);
      return result;
    }

    final result = BaseResponse.fromJson({
      'code': response.statusCode ?? 0,
      'msg': response.statusMessage ?? '',
      'result': payload,
    }, parser);
    await _handleBusinessError(result, toastOnBusinessError && notifyOnError);
    return result;
  }

  Future<void> _handleBusinessError<T>(
    BaseResponse<T> response,
    bool shouldToast,
  ) async {
    if (response.code == 1001) {
      final message = response.message.isNotEmpty ? response.message : '登录已过期';
      showToast(message);

      await _forceLogout();
      return;
    }

    if (shouldToast && !response.isSuccess) {
      final message = response.message.isNotEmpty ? response.message : '请求失败';
      showToast(message);
    }
  }

  Future<void> _forceLogout() async {
    final context = AppRouter.navigatorKey.currentContext;
    if (context == null) {
      WidgetsBinding.instance.addPostFrameCallback((_) => _forceLogout());
      return;
    }

    final container = ProviderScope.containerOf(context, listen: false);
    await container.read(authNotifierProvider.notifier).clearSession();
    Future.microtask(AppRouter.goLogin);
  }
}
