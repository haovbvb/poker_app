import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:merchant_app/app/root_tab_scaffold.dart';
import 'package:merchant_app/features/login/presentation/login_page.dart';

class AppRouter {
  AppRouter._();

  static final GlobalKey<NavigatorState> navigatorKey =
      GlobalKey<NavigatorState>();

  static const String homePath = '/home';
  static const String loginPath = '/login';

  static final GoRouter router = GoRouter(
    navigatorKey: navigatorKey,
    initialLocation: loginPath,
    routes: [
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
  );

  static void goHome() => router.go(homePath);

  static void goLogin() => router.go(loginPath);
}
