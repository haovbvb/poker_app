import 'package:dio/dio.dart';

class NetworkExceptions implements Exception {
  final String message;
  NetworkExceptions(this.message);

  static NetworkExceptions fromDioException(dynamic error) {
    if (error is DioException) {
      switch (error.type) {
        case DioExceptionType.connectionTimeout:
          return NetworkExceptions("连接超时");
        case DioExceptionType.receiveTimeout:
          return NetworkExceptions("响应超时");
        case DioExceptionType.sendTimeout:
          return NetworkExceptions("请求超时");
        case DioExceptionType.badResponse:
          return NetworkExceptions("服务器返回错误: ${error.response?.statusCode}");
        case DioExceptionType.cancel:
          return NetworkExceptions("请求已取消");
        case DioExceptionType.unknown:
          return NetworkExceptions("未知错误: ${error.message}");
        default:
          return NetworkExceptions("网络错误");
      }
    } else {
      return NetworkExceptions("未知错误: $error");
    }
  }

  @override
  String toString() => message;
}
