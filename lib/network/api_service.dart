import 'api_client.dart';
import 'api_path.dart';
import 'base_response.dart';

class ApiService {
  final _client = ApiClient();

  Future<BaseResponse<List<dynamic>>> getPosts() async {
    final response = await _client.get(ApiPath.posts);
    return BaseResponse.fromJson(
      {
        'code': 200,
        'message': 'ok',
        'data': response.data,
      },
      (data) => List<dynamic>.from(data),
    );
  }

  Future<BaseResponse<Map<String, dynamic>>> createPost(Map<String, dynamic> data) async {
    final response = await _client.post(ApiPath.posts, data: data);
    return BaseResponse.fromJson(
      {
        'code': 200,
        'message': 'ok',
        'data': response.data,
      },
      (data) => Map<String, dynamic>.from(data),
    );
  }
}
