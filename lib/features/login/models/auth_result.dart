class AuthResult {
  const AuthResult({
    required this.token,
    required this.name,
    required this.phone,
    required this.avatar,
    required this.role,
    required this.agentNo,
    required this.agentName,
    required this.shopNo,
    required this.shopName,
    required this.appRole,
    required this.managerFlag,
    required this.ops,
    required this.tenantName,
    required this.emailCode,
    required this.tenantId,
    required this.currencyUnit,
    required this.platform,
    required this.areaCode,
    required this.cityCode,
    required this.cardNum,
    required this.serviceType,
    required this.apiKey,
    required this.raw,
  });

  final String token;
  final String name;
  final String phone;
  final String avatar;
  final int role;
  final String agentNo;
  final String agentName;
  final String shopNo;
  final String shopName;
  final String appRole;
  final bool managerFlag;
  final List<AuthOperation> ops;
  final String tenantName;
  final String emailCode;
  final String tenantId;
  final String currencyUnit;
  final int platform;
  final String areaCode;
  final String cityCode;
  final String cardNum;
  final String serviceType;
  final String apiKey;
  final Map<String, dynamic> raw;

  factory AuthResult.fromJson(Map<String, dynamic> json) {
    final opsJson = json['ops'] as List?;
    return AuthResult(
      token: json['token']?.toString() ?? '',
      name: json['name']?.toString() ?? '',
      phone: json['phone']?.toString() ?? '',
      avatar: json['avatar']?.toString() ?? '',
      role: json['role'] is int
          ? json['role'] as int
          : int.tryParse(json['role']?.toString() ?? '') ?? 0,
      agentNo: json['agentNo']?.toString() ?? '',
      agentName: json['agentName']?.toString() ?? '',
      shopNo: json['shopNo']?.toString() ?? '',
      shopName: json['shopName']?.toString() ?? '',
      appRole: json['appRole']?.toString() ?? '',
      managerFlag: json['managerFlag'] is bool
          ? json['managerFlag'] as bool
          : json['managerFlag'] == 'true',
      ops: opsJson == null
          ? const <AuthOperation>[]
          : opsJson
                .whereType<Map>()
                .map(
                  (item) => AuthOperation.fromJson(
                    item is Map<String, dynamic>
                        ? item
                        : Map<String, dynamic>.from(item),
                  ),
                )
                .toList(growable: false),
      tenantName: json['tenantName']?.toString() ?? '',
      emailCode: json['emailCode']?.toString() ?? '',
      tenantId: json['tenantId']?.toString() ?? '',
      currencyUnit: json['currencyUnit']?.toString() ?? '',
      platform: json['platform'] is int
          ? json['platform'] as int
          : int.tryParse(json['platform']?.toString() ?? '') ?? 0,
      areaCode: json['areaCode']?.toString() ?? '',
      cityCode: json['cityCode']?.toString() ?? '',
      cardNum: json['cardNum']?.toString() ?? '',
      serviceType: json['serviceType']?.toString() ?? '',
      apiKey: json['apiKey']?.toString() ?? '',
      raw: json,
    );
  }
}

class AuthOperation {
  const AuthOperation({
    required this.code,
    required this.dictionaryCode,
    required this.id,
    required this.isOwn,
    required this.name,
    required this.platform,
  });

  final String code;
  final String dictionaryCode;
  final String id;
  final int isOwn;
  final String name;
  final int platform;

  factory AuthOperation.fromJson(Map<String, dynamic> json) {
    return AuthOperation(
      code: json['code']?.toString() ?? '',
      dictionaryCode: json['dictionaryCode']?.toString() ?? '',
      id: json['id']?.toString() ?? '',
      isOwn: json['isOwn'] is int
          ? json['isOwn'] as int
          : int.tryParse(json['isOwn']?.toString() ?? '') ?? 0,
      name: json['name']?.toString() ?? '',
      platform: json['platform'] is int
          ? json['platform'] as int
          : int.tryParse(json['platform']?.toString() ?? '') ?? 0,
    );
  }
}
