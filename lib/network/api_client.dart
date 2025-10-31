import 'package:dio/dio.dart';
import 'package:merchant_app/core/utils/logger.dart';

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
          logI(_logTag, buffer.toString());
          if (_authToken != null && _authToken!.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $_authToken';
          } else {
            options.headers.remove('Authorization');
          }
          return handler.next(options);
        },
        onResponse: (response, handler) {
          final buffer = StringBuffer(
            '✅ status=${response.statusCode} path=${response.realUri.path}',
          );
          if (response.data != null) {
            buffer.write(' data=${response.data}');
          }
          logI(_logTag, buffer.toString());
          return handler.next(response);
        },
        onError: (DioException e, handler) {
          logE(
            _logTag,
            '❌ Dio error for ${e.requestOptions.uri}',
            e,
            e.stackTrace,
          );
          return handler.reject(e);
        },
      ),
    );
  }

  // 通用请求封装
  Future<Response> get(String path, {Map<String, dynamic>? params}) async {
    try {
      return await dio.get(path, queryParameters: params);
    } catch (e) {
      throw NetworkExceptions.fromDioException(e);
    }
  }

  Future<Response> post(String path, {dynamic data}) async {
    try {
      return await dio.post(path, data: data);
    } catch (e) {
      throw NetworkExceptions.fromDioException(e);
    }
  }

  void setAuthToken(String? token) {
    _authToken = token;
    if (token != null && token.isNotEmpty) {
      logI(_logTag, '🔐 Token attached');
    } else {
      logI(_logTag, '🔓 Token cleared');
    }
  }

  void clearAuthToken() => setAuthToken(null);
}
