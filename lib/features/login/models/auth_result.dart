class AuthResult {
  const AuthResult({
    required this.token,
    this.name,
    this.agentName,
    this.role,
    this.raw,
  });

  final String token;
  final String? name;
  final String? agentName;
  final int? role;
  final Map<String, dynamic>? raw;

  factory AuthResult.fromJson(Map<String, dynamic> json) {
    return AuthResult(
      token: json['token']?.toString() ?? '',
      name: json['name']?.toString(),
      agentName: json['agentName']?.toString(),
      role: json['role'] is int
          ? json['role'] as int
          : int.tryParse(json['role']?.toString() ?? ''),
      raw: json,
    );
  }
}
