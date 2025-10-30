import 'package:dio/dio.dart';
import 'network_exceptions.dart';

class ApiClient {
  static final ApiClient _instance = ApiClient._internal();
  factory ApiClient() => _instance;
  late Dio dio;

  ApiClient._internal() {
    dio = Dio(BaseOptions(
      baseUrl: 'https://jsonplaceholder.typicode.com', // 🔧 修改为你的域名
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 10),
      headers: {'Content-Type': 'application/json'},
    ));

    // ✅ 添加拦截器
    dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) {
        print('➡️ [${options.method}] ${options.uri}');
        // 可自动添加 token
        // options.headers['Authorization'] = 'Bearer your_token';
        return handler.next(options);
      },
      onResponse: (response, handler) {
        print('✅ 响应状态: ${response.statusCode}');
        return handler.next(response);
      },
      onError: (DioException e, handler) {
        print('❌ Dio Error: ${e.message}');
        return handler.reject(e);
      },
    ));
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
}
