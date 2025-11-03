class AuthState {
  const AuthState({this.token});

  final String? token;

  bool get isAuthenticated => token != null && token!.isNotEmpty;
}
