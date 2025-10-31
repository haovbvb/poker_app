import 'dart:convert';

import 'package:crypto/crypto.dart';

/// 提供常用的哈希算法工具。
class HashUtils {
  const HashUtils._();

  /// 计算字符串的 MD5（32 位小写）。
  static String md5Lower32(String input) {
    final bytes = utf8.encode(input);
    final digest = md5.convert(bytes);
    return digest.toString();
  }
}
