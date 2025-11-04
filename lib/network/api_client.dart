import 'package:dio/dio.dart';
import 'package:merchant_app/core/services/language_store.dart';
import 'package:merchant_app/core/utils/hud.dart';
import 'package:merchant_app/core/utils/logger.dart';
import 'package:merchant_app/core/utils/toast.dart';

import 'network_exceptions.dart';

const _logTag = 'ApiClient';

class ApiClient {
  static final ApiClient _instance = ApiClient._internal();
  factory ApiClient() => _instance;
  late Dio dio;
  String? _authToken;

  ApiClient._internal() {
    dio = Dio(
      BaseOptions(
        baseUrl: 'https://t-kora-admin-app.esquare-global.com', // 🔧 修改为你的域名
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(seconds: 30),
        headers: {'Content-Type': 'application/json'},
      ),
    );

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
          buffer
            // ..write(' token=${_authToken ?? ''}')
            ..write(' acceptLanguage=$acceptLanguage');

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

  void clearAuthToken() => setAuthToken(null);
}
