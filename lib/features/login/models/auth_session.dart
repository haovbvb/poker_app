import 'auth_result.dart';

/// Singleton holder for the authenticated user info.
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
