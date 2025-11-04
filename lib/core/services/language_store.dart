class LanguageStore {
  LanguageStore._();

  static final LanguageStore instance = LanguageStore._();

  String _languageCode = 'en';

  String get languageCode => _languageCode;

  void update(String code) {
    _languageCode = code.isNotEmpty ? code : 'en';
  }
}
