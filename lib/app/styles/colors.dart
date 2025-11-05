import 'package:flutter/material.dart';

/// 颜色令牌：中性色、语义色、分割线与文本对比色工具
class AppColors {
  // 中性文本
  static const Color black09Text = Color(0xE6000000); // 黑 0.9
  static const Color black08Text = Color(0xCC000000); // 黑 0.8
  static const Color black07Text = Color(0xB3000000); // 黑 0.7
  static const Color black05Text = Color(0x7F000000); // 黑 0.5
  static const Color black06Text = Color(0x99000000); // 黑 0.6
  static const Color black04Text = Color(0x66000000); // 黑 0.4
  static const Color black03Text = Color(0x4D000000); // 黑 0.3
  static const Color black02Text = Color(0x33000000); // 黑 0.2
  static const Color black025Text = Color(0x40000000); // 黑 0.2.5

  static const Color white09Text = Color(0xE6FFFFFF); // 白 0.9

  static const Color primaryColor = Color(0xFF56B327); // 主色
  static const Color secondaryColor = Color(0xFFFA4332); // 次要色

  // 分隔/卡片背景（通过透明度控制层级）
  static Color divider = Colors.black.withValues(alpha: 0.06);
  static Color cardBg = Colors.white;
  static Color greyBg = Color(0xFFF6F8FC);

  // 语义色
  static const Color success = Color(0xFF22C55E);
  static const Color warning = Color(0xFFF59E0B);
  static const Color danger = Color(0xFFEF4444);

  // 根据背景自动选择对比文本（简化：亮背景用深字，暗背景用白字）
  static Color onColor(Color bg) {
    final l = bg.computeLuminance();
    return l > 0.5 ? const Color(0xFF111827) : Colors.white;
  }
}
