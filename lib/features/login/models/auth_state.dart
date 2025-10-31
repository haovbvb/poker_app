class AuthState {
  const AuthState({this.token, this.errorMessage, this.isLoading = false});

  final String? token;
  final String? errorMessage;
  final bool isLoading;

  bool get isAuthenticated => token != null && token!.isNotEmpty;

  AuthState copyWith({
    String? token,
    bool updateToken = false,
    String? errorMessage,
    bool updateError = false,
    bool? isLoading,
  }) {
    return AuthState(
      token: updateToken ? token : (token ?? this.token),
      errorMessage: updateError ? errorMessage : this.errorMessage,
      isLoading: isLoading ?? this.isLoading,
    );
  }

  AuthState clearError() => copyWith(errorMessage: null, updateError: true);

  static AuthState initialLoading() => const AuthState(isLoading: true);
}
