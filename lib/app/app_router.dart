import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:merchant_app/app/root_tab_scaffold.dart';
import 'package:merchant_app/core/utils/logger.dart';
import 'package:merchant_app/features/login/models/auth_state.dart';
import 'package:merchant_app/features/login/presentation/bootstrap_page.dart';
import 'package:merchant_app/features/login/presentation/login_page.dart';
import 'package:merchant_app/features/login/providers/auth_controller.dart';

class AppRouter {
  AppRouter._();

  static final GlobalKey<NavigatorState> navigatorKey =
      GlobalKey<NavigatorState>();

  static const String homePath = '/home';
  static const String loginPath = '/login';
  static const String splashPath = '/splash';

  static final GoRouter router = GoRouter(
    navigatorKey: navigatorKey,
    initialLocation: splashPath,
    routes: [
      GoRoute(
        path: splashPath,
        name: 'splash',
        builder: (context, state) => const BootstrapPage(),
      ),
      GoRoute(
        path: loginPath,
        name: 'login',
        builder: (context, state) => const LoginPage(),
      ),
      GoRoute(
        path: homePath,
        name: 'home',
        builder: (context, state) => const RootTabScaffold(),
      ),
    ],
    redirect: (context, state) {
      final ref = ProviderScope.containerOf(context, listen: false);
      final authState = ref.read(authNotifierProvider);
      // logI(
      //   '[AppRouter] redirect stateXXX=${authState.token} location=${state.matchedLocation}',
      // );
      final splash = state.matchedLocation == splashPath;
      final loggingIn = state.matchedLocation == loginPath;

      if (splash) {
        // Splash 页面自己决定后续跳转。
        return null;
      }

      if (!authState.isAuthenticated && !loggingIn) {
        return splashPath;
      }

      if (authState.isAuthenticated && loggingIn) {
        return homePath;
      }

      return null;
    },
    refreshListenable: _GoRouterRefreshNotifier(authNotifierProvider),
  );

  static void goHome() => router.go(homePath);

  static void goLogin() => router.go(loginPath);
  static void goSplash() => router.go(splashPath);
}

class _GoRouterRefreshNotifier extends ChangeNotifier {
  _GoRouterRefreshNotifier(this._provider);

  final NotifierProvider<AuthNotifier, AuthState> _provider;
  ProviderSubscription<AuthState>? _subscription;

  void _ensureSubscribed(BuildContext context) {
    if (_subscription != null) {
      return;
    }
    final container = ProviderScope.containerOf(context, listen: false);
    _subscription = container.listen<AuthState>(
      _provider,
      (_, __) => notifyListeners(),
      fireImmediately: true,
    );
  }

  void _subscribeIfNeeded() {
    final context = AppRouter.navigatorKey.currentContext;
    if (context == null) {
      WidgetsBinding.instance.addPostFrameCallback((_) => _subscribeIfNeeded());
      return;
    }
    _ensureSubscribed(context);
  }

  @override
  void dispose() {
    _subscription?.close();
    super.dispose();
  }

  @override
  void addListener(VoidCallback listener) {
    super.addListener(listener);
    _subscribeIfNeeded();
  }

  @override
  void removeListener(VoidCallback listener) {
    super.removeListener(listener);
    if (!hasListeners) {
      _subscription?.close();
      _subscription = null;
    }
  }
}
