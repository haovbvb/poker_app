import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import 'styles/typography.dart';

class BaseTheme {
  // Brand colors
  static const Color primaryColor = Color(0xFF56B327); // 主色
  static const Color hiveBrown = Color(0xFF8D6E63); // 辅助色
  static const Color energyOrange = Color(0xFF56B327); // 点缀色
  static const Color paperIvory = Color(0xFFFFFFFF); // 背景
  static const Color textDark = Color(0xFF333333); // 文字

  static ThemeData lightTheme({TargetPlatform? platform}) {
    final base = ThemeData.light();
    final pf = platform ?? defaultTargetPlatform;
    final isIOS = pf == TargetPlatform.iOS || pf == TargetPlatform.macOS;
    final adjustedTextTheme = AppTypography.buildBase(
      base.textTheme,
      isIOS: isIOS,
    ).apply(bodyColor: textDark, displayColor: textDark);

    return base.copyWith(
      colorScheme: base.colorScheme.copyWith(
        primary: primaryColor,
        secondary: energyOrange,
        surface: Colors.white,
      ),
      primaryColor: primaryColor,
      scaffoldBackgroundColor: paperIvory,
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.white,
        foregroundColor: textDark,
        elevation: 0.0,
        centerTitle: true,
        surfaceTintColor: Colors.transparent,
        scrolledUnderElevation: 0,
      ),
      floatingActionButtonTheme: const FloatingActionButtonThemeData(
        backgroundColor: primaryColor,
        foregroundColor: Colors.white,
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        selectedItemColor: energyOrange,
        unselectedItemColor: Colors.grey,
        showUnselectedLabels: true,
        backgroundColor: Colors.white,
        elevation: 8,
      ),
      textTheme: adjustedTextTheme,
    );
  }

  static ThemeData darkTheme({TargetPlatform? platform}) {
    final base = ThemeData.dark();
    final pf = platform ?? defaultTargetPlatform;
    final isIOS = pf == TargetPlatform.iOS || pf == TargetPlatform.macOS;
    final adjusted = AppTypography.buildBase(
      base.textTheme,
      isIOS: isIOS,
    ).apply(bodyColor: Colors.white, displayColor: Colors.white);
    return base.copyWith(
      colorScheme: base.colorScheme.copyWith(
        primary: primaryColor,
        secondary: energyOrange,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.black,
        foregroundColor: Colors.white,
        elevation: 0,
        centerTitle: true,
        surfaceTintColor: Colors.transparent,
        scrolledUnderElevation: 0,
      ),
      floatingActionButtonTheme: const FloatingActionButtonThemeData(
        backgroundColor: primaryColor,
        foregroundColor: Colors.black,
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        selectedItemColor: primaryColor,
        unselectedItemColor: Colors.grey,
        showUnselectedLabels: true,
      ),
      textTheme: adjusted,
    );
  }
}
