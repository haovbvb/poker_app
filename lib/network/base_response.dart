class BaseResponse<T> {
  final int code;
  final String message;
  final T? result;

  BaseResponse({required this.code, required this.message, this.result});

  factory BaseResponse.fromJson(
    Map<String, dynamic> json,
    T Function(dynamic) fromJsonT,
  ) {
    final rawCode = json['code'] ?? json['status'] ?? json['statusCode'] ?? 0;
    final resolvedCode = rawCode is int
        ? rawCode
        : int.tryParse(rawCode.toString()) ?? 0;

    final resolvedMessage =
        (json['message'] ?? json['msg'] ?? json['error'] ?? '').toString();
    final rawData = json.containsKey('result') ? json['result'] : json['data'];

    return BaseResponse(
      code: resolvedCode,
      message: resolvedMessage,
      result: rawData != null ? fromJsonT(rawData) : null,
    );
  }

  bool get isSuccess => code == 0 || code == 1000;
}
