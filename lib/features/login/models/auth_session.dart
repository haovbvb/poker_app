import 'auth_result.dart';

/// Holds the current authenticated user info for quick access across the app.
class AuthSession {
  AuthSession._();

  static final AuthSession instance = AuthSession._();

  AuthResult? _current;

  AuthResult? get current => _current;

  void update(AuthResult result) {
    _current = result;
  }

  void clear() {
    _current = null;
  }
}
