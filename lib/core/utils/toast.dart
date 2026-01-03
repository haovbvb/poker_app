import 'dart:async';

import 'package:flutter/material.dart';
import 'package:poker_app/app/app_router.dart';

/// 简易 Toast 封装，支持重复调用时覆盖上一个提示。
class Toast {
  Toast._();

  static OverlayEntry? _currentEntry;
  static Timer? _dismissTimer;

  /// 展示一个新的 toast，如果已有 toast 会先移除旧的。
  static void show(
    String message, {
    Duration duration = const Duration(seconds: 2),
  }) {
    _dismiss();

    final navigatorState = AppRouter.navigatorKey.currentState;
    final context =
        navigatorState?.context ?? AppRouter.navigatorKey.currentContext;
    if (context == null) {
      return;
    }

    final overlay =
        navigatorState?.overlay ?? Overlay.of(context, rootOverlay: true);

    _currentEntry = OverlayEntry(
      builder: (ctx) => Positioned.fill(
        child: IgnorePointer(
          ignoring: true,
          child: SafeArea(
            child: Center(
              child: Material(
                color: Colors.transparent,
                child: Container(
                  margin: const EdgeInsets.symmetric(horizontal: 24),
                  padding: const EdgeInsets.symmetric(
                    horizontal: 14,
                    vertical: 12,
                  ),
                  decoration: BoxDecoration(
                    color: Colors.black.withValues(alpha: 0.85),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    message,
                    textAlign: TextAlign.center,
                    style: const TextStyle(color: Colors.white),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );

    overlay.insert(_currentEntry!);
    _dismissTimer = Timer(duration, _dismiss);
  }

  /// 手动关闭当前 toast。
  static void dismiss() => _dismiss();

  static void _dismiss() {
    _dismissTimer?.cancel();
    _dismissTimer = null;
    _currentEntry?.remove();
    _currentEntry = null;
  }
}

/// 为兼容旧调用保留的方法，后续可逐步迁移到 `Toast.show`。
void showToast(
  String message, {
  Duration duration = const Duration(seconds: 2),
}) {
  Toast.show(message, duration: duration);
}
