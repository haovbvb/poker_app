import 'package:merchant_app/features/login/models/auth_result.dart';

import 'api_client.dart';
import 'api_path.dart';
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
  }) async {
    final response = await _client.get(path, params: queryParameters);
    final payload = response.data;

    if (payload is Map<String, dynamic> && payload.containsKey('code')) {
      return BaseResponse.fromJson(payload, parser);
    }

    return BaseResponse.fromJson({
      'code': response.statusCode ?? 0,
      'msg': response.statusMessage ?? '',
      'result': payload,
    }, parser);
  }

  Future<BaseResponse<T>> post<T>(
    String path, {
    dynamic data,
    required T Function(dynamic json) parser,
  }) async {
    final response = await _client.post(path, data: data);
    final payload = response.data;

    if (payload is Map<String, dynamic> && payload.containsKey('code')) {
      return BaseResponse.fromJson(payload, parser);
    }

    return BaseResponse.fromJson({
      'code': response.statusCode ?? 0,
      'msg': response.statusMessage ?? '',
      'result': payload,
    }, parser);
  }
}
