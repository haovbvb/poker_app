import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:merchant_app/core/services/language_store.dart';
import 'package:shared_preferences/shared_preferences.dart';

final languageNotifierProvider = NotifierProvider<LanguageNotifier, Locale>(
  LanguageNotifier.new,
);

class LanguageNotifier extends Notifier<Locale> {
  static const _storageKey = 'app_language_code';

  @override
  Locale build() {
    final fallback = _resolvePlatformLocale();
    LanguageStore.instance.update(fallback.languageCode);
    _loadPersistedLanguage();
    return fallback;
  }

  Future<void> setLocale(Locale locale) async {
    if (state == locale) {
      return;
    }
    state = locale;
    LanguageStore.instance.update(locale.languageCode);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_storageKey, locale.languageCode);
  }

  Future<void> _loadPersistedLanguage() async {
    final prefs = await SharedPreferences.getInstance();
    final storedCode = prefs.getString(_storageKey);
    if (storedCode == null) {
      return;
    }
    final locale = _resolveLocale(storedCode);
    if (locale != state) {
      state = locale;
      LanguageStore.instance.update(locale.languageCode);
    }
  }

  Locale _resolvePlatformLocale() {
    final platformLocale = WidgetsBinding.instance.platformDispatcher.locale;
    return _resolveLocale(platformLocale.languageCode);
  }

  Locale _resolveLocale(String? languageCode) {
    if (languageCode != null && languageCode.toLowerCase().startsWith('zh')) {
      return const Locale('zh');
    }
    return const Locale('en');
  }
}
