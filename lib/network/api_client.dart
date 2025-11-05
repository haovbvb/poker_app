import 'dart:async';

import 'package:dio/dio.dart';
import 'package:merchant_app/core/constants/storage_keys.dart';
import 'package:merchant_app/core/services/language_store.dart';
import 'package:merchant_app/core/utils/hud.dart';
import 'package:merchant_app/core/utils/logger.dart';
import 'package:merchant_app/core/utils/toast.dart';
import 'package:merchant_app/network/api_path.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'network_exceptions.dart';

const _logTag = 'ApiClient';

enum ApiEnvironment { production, testing }

class ApiClient {
  static final ApiClient _instance = ApiClient._internal();
  factory ApiClient() => _instance;
  late Dio dio;
  String? _authToken;
  ApiEnvironment _environment = ApiEnvironment.production;

  static const Map<ApiEnvironment, String> _envBaseUrls = {
    ApiEnvironment.production: ApiPath.proBaseUrl,
    ApiEnvironment.testing: ApiPath.testBaseUrl,
  };

  ApiClient._internal() {
    dio = Dio(
      BaseOptions(
        baseUrl: _resolveBaseUrl(),
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(seconds: 30),
        headers: {'Content-Type': 'application/json'},
      ),
    );

    unawaited(_restoreToken());

    // ✅ 添加拦截器
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          final buffer = StringBuffer('➡️ ${options.method} ${options.uri}');
          if (options.queryParameters.isNotEmpty) {
            buffer.write(' query=${options.queryParameters}');
          }
          if (options.data != null) {
            buffer.write(' body=${options.data}');
          }

          final showHud = options.extra['showHud'] as bool? ?? true;
          if (showHud) {
            Hud.show();
            options.extra['_hudShown'] = true;
          }

          final acceptLanguage = LanguageStore.instance.languageCode;
          options.headers['Accept-Language'] = acceptLanguage;

          if (_authToken != null && _authToken!.isNotEmpty) {
            options.headers['AccessToken'] = _authToken;
          } else {
            options.headers.remove('AccessToken');
          }

          if (options.headers.isNotEmpty) {
            buffer.write(' headers=${options.headers}');
          }

          logI('[$_logTag] ${buffer.toString()}');
          return handler.next(options);
        },
        onResponse: (response, handler) {
          final buffer = StringBuffer(
            '✅ status=${response.statusCode} path=${response.realUri.path}',
          );
          if (response.data != null) {
            buffer.write(' data=${response.data}');
          }
          logI('[$_logTag] ${buffer.toString()}');

          if (response.requestOptions.extra['_hudShown'] == true) {
            Hud.dismiss();
            response.requestOptions.extra.remove('_hudShown');
          }

          return handler.next(response);
        },
        onError: (DioException e, handler) {
          if (e.requestOptions.extra['_hudShown'] == true) {
            Hud.dismiss();
            e.requestOptions.extra.remove('_hudShown');
          }

          logE(
            '[$_logTag] ❌ Dio error for ${e.requestOptions.uri}',
            e,
            e.stackTrace,
          );

          final notifyOnError =
              e.requestOptions.extra['notifyOnError'] as bool? ?? true;
          if (notifyOnError) {
            final exception = NetworkExceptions.fromDioException(e);
            showToast(exception.message);
          }

          return handler.reject(e);
        },
      ),
    );
  }

  ApiEnvironment get environment => _environment;

  String get baseUrl => _resolveBaseUrl();

  void setEnvironment(ApiEnvironment environment) {
    if (_environment == environment) {
      return;
    }
    _environment = environment;
    final resolved = _resolveBaseUrl();
    dio.options.baseUrl = resolved;
    logI('[$_logTag] 🔁 Switched API environment to $environment ($resolved)');
  }

  // 通用请求封装
  Future<Response> get(
    String path, {
    Map<String, dynamic>? params,
    bool showHud = true,
    bool notifyOnError = true,
  }) async {
    try {
      return await dio.get(
        path,
        queryParameters: params,
        options: Options(
          extra: {'showHud': showHud, 'notifyOnError': notifyOnError},
        ),
      );
    } catch (e) {
      throw NetworkExceptions.fromDioException(e);
    }
  }

  Future<Response> post(
    String path, {
    dynamic data,
    bool showHud = true,
    bool notifyOnError = true,
  }) async {
    try {
      return await dio.post(
        path,
        data: data,
        options: Options(
          extra: {'showHud': showHud, 'notifyOnError': notifyOnError},
        ),
      );
    } catch (e) {
      throw NetworkExceptions.fromDioException(e);
    }
  }

  void setAuthToken(String? token) {
    _authToken = token;
    if (token != null && token.isNotEmpty) {
      logI('[$_logTag] 🔐 Token attached');
    } else {
      logI('[$_logTag] 🔓 Token cleared');
    }
  }

  Future<void> _restoreToken() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString(StorageKeys.authToken);
      if (token != null && token.isNotEmpty) {
        _authToken = token;
        logI('[$_logTag] 🔁 Restored persisted token');
      }
    } catch (error) {
      logW('[$_logTag] ⚠️ Failed to restore token: $error');
    }
  }

  void clearAuthToken() => setAuthToken(null);

  String _resolveBaseUrl() {
    return _envBaseUrls[_environment]!;
  }
}
