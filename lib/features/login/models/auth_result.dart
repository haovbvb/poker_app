class AuthResult {
  const AuthResult({
    required this.accessToken,
    required this.refreshToken,
    required this.username,
    required this.tier,
    required this.tokenType,
    required this.expiresIn,
    required this.raw,
  });

  final String accessToken;
  final String refreshToken;
  final String username;
  final String tier;
  final String tokenType;
  final int expiresIn;
  final Map<String, dynamic> raw;

  factory AuthResult.fromJson(Map<String, dynamic> json) {
    final accessToken =
        (json['access_token'] ?? json['accessToken'])?.toString() ?? '';
    final refreshToken =
        (json['refresh_token'] ?? json['refreshToken'])?.toString() ?? '';
    final username = (json['username'] ?? json['userName'])?.toString() ?? '';
    final tier = (json['tier'] ?? json['level'] ?? '')?.toString() ?? '';
    final tokenType =
        (json['token_type'] ?? json['tokenType'] ?? '')?.toString() ?? '';
    final expiresIn = json['expires_in'] is int
        ? json['expires_in'] as int
        : int.tryParse(json['expires_in']?.toString() ?? '') ??
              (json['expiresIn'] is int
                  ? json['expiresIn'] as int
                  : int.tryParse(json['expiresIn']?.toString() ?? '') ?? 0);

    return AuthResult(
      accessToken: accessToken,
      refreshToken: refreshToken,
      username: username,
      tier: tier,
      tokenType: tokenType,
      expiresIn: expiresIn,
      raw: json,
    );
  }
}
