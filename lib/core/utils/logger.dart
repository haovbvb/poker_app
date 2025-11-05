import 'package:flutter/foundation.dart';

enum LogLevel { info, warn, error }

const int _maxChunkLength = 800;

String _ts() {
  final now = DateTime.now();
  String two(int n) => n.toString().padLeft(2, '0');
  String three(int n) => n.toString().padLeft(3, '0');
  return '${two(now.hour)}:${two(now.minute)}:${two(now.second)}.${three(now.millisecond)}';
}

void _printInChunks(String message) {
  if (message.isEmpty) {
    debugPrint(message);
    return;
  }

  var start = 0;
  final length = message.length;
  while (start < length) {
    final end = (start + _maxChunkLength) < length
        ? start + _maxChunkLength
        : length;
    debugPrint(message.substring(start, end));
    start = end;
  }
}

void _log(LogLevel level, String msg) {
  final lv = switch (level) {
    LogLevel.info => 'ℹ️',
    LogLevel.warn => '⚠️',
    LogLevel.error => '⛔',
  };
  _printInChunks('[$lv ${_ts()}] $msg');
}

void log(String msg) => _log(LogLevel.info, msg);
void logI(String msg) => _log(LogLevel.info, msg);
void logW(String msg) => _log(LogLevel.warn, msg);
void logE(String msg, [Object? err, StackTrace? st]) {
  _log(LogLevel.error, msg);
  if (err != null) _printInChunks('  error: $err');
  if (st != null) _printInChunks('  stack: $st');
}
