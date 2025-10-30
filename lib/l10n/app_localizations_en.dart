// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'Merchant';

  @override
  String get welcomeMessage => 'Welcome to Merchant!';

  @override
  String get logout => 'Logout';

  @override
  String get tabHome => 'Home';

  @override
  String get tabWork => 'Work';

  @override
  String get tabMe => 'Me';

  @override
  String get homeTitle => 'Overview';

  @override
  String get workTitle => 'Workbench';

  @override
  String get meTitle => 'Profile';

  @override
  String get workInProgress => 'Your workbench content will appear here soon.';

  @override
  String get profileGreeting => 'Manage your personal settings here.';
}
