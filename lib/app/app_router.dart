import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:poker_app/core/widgets/common_webview_page.dart';
import 'package:poker_app/features/home/home.dart';
import 'package:poker_app/features/home/game_table_page.dart';
import 'package:poker_app/features/login/models/user_state.dart';
import 'package:poker_app/features/login/presentation/bootstrap_page.dart';
import 'package:poker_app/features/login/presentation/login_page.dart';
import 'package:poker_app/features/login/providers/auth_controller.dart';
import 'package:poker_app/features/me/about_page.dart';
import 'package:poker_app/features/me/language.dart';
import 'package:poker_app/features/me/message.dart';

class AppRouter {
  AppRouter._();

  static final GlobalKey<NavigatorState> navigatorKey =
      GlobalKey<NavigatorState>();

  static const String homePath = '/home';
  static const String loginPath = '/login';
  static const String splashPath = '/splash';
  static const String gamePath = '/poker/:tableId';
  static const String userAgreementPath = '/profile/user-agreement';
  static const String aboutPath = '/profile/about';
  static const String messagePath = '/profile/messages';
  static const String languagePath = '/profile/language';

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
        builder: (context, state) =>
            HomeTab(key: ValueKey(state.uri.toString())),
      ),
      GoRoute(
        path: gamePath,
        name: 'poker_game',
        builder: (context, state) {
          final tableId = state.pathParameters['tableId'];
          if (tableId == null) {
            return const Scaffold(body: Center(child: Text('缺少牌桌ID')));
          }
          final auto = state.uri.queryParameters['auto'];
          final autoPlay = auto == '1' || auto == 'true';
          return GameTablePage(tableId: tableId, autoPlay: autoPlay);
        },
      ),
      GoRoute(
        path: userAgreementPath,
        name: 'user_agreement',
        builder: (context, state) => const CommonWebViewPage(
          initialUrl: 'https://book.flutterchina.club/',
        ),
      ),
      GoRoute(
        path: aboutPath,
        name: 'about',
        builder: (context, state) => const AboutPage(),
      ),
      GoRoute(
        path: messagePath,
        name: 'messages',
        builder: (context, state) => const MessagePage(),
      ),
      GoRoute(
        path: languagePath,
        name: 'language',
        builder: (context, state) => const LanguageSelectionPage(),
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

  static void goHome({bool refresh = false}) {
    if (!refresh) {
      router.go(homePath);
      return;
    }
    final ts = DateTime.now().millisecondsSinceEpoch;
    router.go('$homePath?r=$ts');
  }

  static void goLogin() => router.go(loginPath);
  static void goSplash() => router.go(splashPath);
  static void pushGame(String tableId, {bool autoPlay = false}) =>
      router.push('/poker/$tableId${autoPlay ? '?auto=1' : ''}');
}

class _GoRouterRefreshNotifier extends ChangeNotifier {
  _GoRouterRefreshNotifier(this._provider);

  final NotifierProvider<AuthNotifier, UserState> _provider;
  ProviderSubscription<UserState>? _subscription;

  void _ensureSubscribed(BuildContext context) {
    if (_subscription != null) {
      return;
    }
    final container = ProviderScope.containerOf(context, listen: false);
    _subscription = container.listen<UserState>(
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
