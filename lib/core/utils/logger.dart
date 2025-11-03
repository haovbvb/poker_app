import 'package:flutter/foundation.dart';

enum LogLevel { info, warn, error }

String _ts() {
  final now = DateTime.now();
  String two(int n) => n.toString().padLeft(2, '0');
  String three(int n) => n.toString().padLeft(3, '0');
  return '${two(now.hour)}:${two(now.minute)}:${two(now.second)}.${three(now.millisecond)}';
}

void _log(LogLevel level, String msg) {
  final lv = switch (level) {
    LogLevel.info => 'I',
    LogLevel.warn => 'W',
    LogLevel.error => 'E',
  };
  debugPrint('[$lv ${_ts()}] $msg');
}

void logI(String msg) => _log(LogLevel.info, msg);
void logW(String msg) => _log(LogLevel.warn, msg);
void logE(String msg, [Object? err, StackTrace? st]) {
  _log(LogLevel.error, msg);
  if (err != null) debugPrint('  error: $err');
  if (st != null) debugPrint('  stack: $st');
}
