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

  @override
  String get profileMessage => 'Message';

  @override
  String get profileChangePassword => 'Change Password';

  @override
  String get profileLanguage => 'Language';

  @override
  String get profileUserAgreement => 'User Agreement';

  @override
  String get profileAbout => 'About';

  @override
  String get login => 'Sign In';

  @override
  String get loginHint => 'Enter your username and password to continue.';

  @override
  String get nameLabel => 'Username';

  @override
  String get nameRequired => 'Username is required';

  @override
  String get passwordLabel => 'Password';

  @override
  String get passwordRequired => 'Password is required';

  @override
  String get passwordTooShort => 'Password must be at least 6 characters';
}
