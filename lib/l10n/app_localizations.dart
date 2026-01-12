import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_zh.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale) : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations? of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations);
  }

  static const LocalizationsDelegate<AppLocalizations> delegate = _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates = <LocalizationsDelegate<dynamic>>[
    delegate,
    GlobalMaterialLocalizations.delegate,
    GlobalCupertinoLocalizations.delegate,
    GlobalWidgetsLocalizations.delegate,
  ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('zh')
  ];

  /// No description provided for @appTitle.
  ///
  /// In en, this message translates to:
  /// **'Merchant'**
  String get appTitle;

  /// No description provided for @welcomeMessage.
  ///
  /// In en, this message translates to:
  /// **'Welcome to Merchant!'**
  String get welcomeMessage;

  /// No description provided for @logout.
  ///
  /// In en, this message translates to:
  /// **'Logout'**
  String get logout;

  /// Label for the home tab in the bottom navigation bar.
  ///
  /// In en, this message translates to:
  /// **'Home'**
  String get tabHome;

  /// Label for the work tab in the bottom navigation bar.
  ///
  /// In en, this message translates to:
  /// **'Work'**
  String get tabWork;

  /// Label for the profile tab in the bottom navigation bar.
  ///
  /// In en, this message translates to:
  /// **'Me'**
  String get tabMe;

  /// Title displayed in the app bar when the home tab is active.
  ///
  /// In en, this message translates to:
  /// **'Overview'**
  String get homeTitle;

  /// Title displayed in the app bar when the work tab is active.
  ///
  /// In en, this message translates to:
  /// **'Workbench'**
  String get workTitle;

  /// Title displayed in the app bar when the profile tab is active.
  ///
  /// In en, this message translates to:
  /// **'Profile'**
  String get meTitle;

  /// Placeholder text for the work tab body.
  ///
  /// In en, this message translates to:
  /// **'Your workbench content will appear here soon.'**
  String get workInProgress;

  /// Helper text in the profile tab.
  ///
  /// In en, this message translates to:
  /// **'Manage your personal settings here.'**
  String get profileGreeting;

  /// No description provided for @login.
  ///
  /// In en, this message translates to:
  /// **'Sign In'**
  String get login;

  /// No description provided for @loginHint.
  ///
  /// In en, this message translates to:
  /// **'Enter your username and password to continue.'**
  String get loginHint;

  /// No description provided for @nameLabel.
  ///
  /// In en, this message translates to:
  /// **'Username'**
  String get nameLabel;

  /// No description provided for @nameRequired.
  ///
  /// In en, this message translates to:
  /// **'Username is required'**
  String get nameRequired;

  /// No description provided for @passwordLabel.
  ///
  /// In en, this message translates to:
  /// **'Password'**
  String get passwordLabel;

  /// No description provided for @passwordRequired.
  ///
  /// In en, this message translates to:
  /// **'Password is required'**
  String get passwordRequired;

  /// No description provided for @passwordTooShort.
  ///
  /// In en, this message translates to:
  /// **'Password must be at least 6 characters'**
  String get passwordTooShort;

  /// Menu label for viewing messages in the profile tab.
  ///
  /// In en, this message translates to:
  /// **'Message'**
  String get profileMessage;

  /// Menu label for changing the account password.
  ///
  /// In en, this message translates to:
  /// **'Change Password'**
  String get profileChangePassword;

  /// Menu label for selecting the application language.
  ///
  /// In en, this message translates to:
  /// **'Language'**
  String get profileLanguage;

  /// Menu label for viewing the user agreement.
  ///
  /// In en, this message translates to:
  /// **'User Agreement'**
  String get profileUserAgreement;

  /// Menu label for viewing information about the application.
  ///
  /// In en, this message translates to:
  /// **'About'**
  String get profileAbout;

  /// Common: cancel
  ///
  /// In en, this message translates to:
  /// **'Cancel'**
  String get commonCancel;

  /// Common: retry
  ///
  /// In en, this message translates to:
  /// **'Retry'**
  String get commonRetry;

  /// Poker table page title
  ///
  /// In en, this message translates to:
  /// **'Table {tableId}'**
  String pokerTableTitle(String tableId);

  /// Drawer item: back to lobby
  ///
  /// In en, this message translates to:
  /// **'Back to Lobby'**
  String get pokerBackToLobby;

  /// Drawer item: stand up
  ///
  /// In en, this message translates to:
  /// **'Stand Up'**
  String get pokerStandUp;

  /// Drawer item: sit down
  ///
  /// In en, this message translates to:
  /// **'Sit Down'**
  String get pokerSitDown;

  /// Drawer item: change table
  ///
  /// In en, this message translates to:
  /// **'Change Table'**
  String get pokerChangeTable;

  /// Poker table page empty state
  ///
  /// In en, this message translates to:
  /// **'No data'**
  String get pokerNoData;

  /// Toast: stand up success
  ///
  /// In en, this message translates to:
  /// **'Stood up'**
  String get pokerStandUpDone;

  /// Toast: buy-in required
  ///
  /// In en, this message translates to:
  /// **'Please buy in first'**
  String get pokerPleaseBuyInFirst;

  /// Change table: no new table returned
  ///
  /// In en, this message translates to:
  /// **'Failed to get a new table'**
  String get pokerChangeTableNoNewTable;

  /// Toast: auto seat success
  ///
  /// In en, this message translates to:
  /// **'Auto seated (Seat {seatNo})'**
  String pokerAutoSeated(int seatNo);

  /// Default error when fetching table snapshot
  ///
  /// In en, this message translates to:
  /// **'Failed to fetch table'**
  String get pokerFetchTableFailed;

  /// Toast: left table
  ///
  /// In en, this message translates to:
  /// **'Left the table'**
  String get pokerLeftTable;

  /// Button: buy in
  ///
  /// In en, this message translates to:
  /// **'Buy In'**
  String get pokerBuyIn;

  /// Button: refresh table
  ///
  /// In en, this message translates to:
  /// **'Refresh'**
  String get pokerRefreshTable;

  /// Button: leave table
  ///
  /// In en, this message translates to:
  /// **'Leave'**
  String get pokerLeaveTable;

  /// Buy-in sheet title
  ///
  /// In en, this message translates to:
  /// **'Buy-in chips ({minBuyin}~{maxBuyin})'**
  String pokerBuyInChipsRange(int minBuyin, int maxBuyin);

  /// Buy-in amount input hint
  ///
  /// In en, this message translates to:
  /// **'Enter buy-in amount'**
  String get pokerBuyInAmountHint;

  /// Confirm buy-in button
  ///
  /// In en, this message translates to:
  /// **'Confirm Buy-in'**
  String get pokerConfirmBuyIn;

  /// Toast: buy-in success
  ///
  /// In en, this message translates to:
  /// **'Buy-in successful'**
  String get pokerBuyInSuccess;

  /// Seat selection dialog title
  ///
  /// In en, this message translates to:
  /// **'Select seat'**
  String get pokerSelectSeat;

  /// Toast: sit down success
  ///
  /// In en, this message translates to:
  /// **'Seated'**
  String get pokerSitDownSuccess;

  /// Toast when websocket is not connected
  ///
  /// In en, this message translates to:
  /// **'Not connected. Unable to act.'**
  String get pokerNetworkNotConnected;

  /// Raise sheet title
  ///
  /// In en, this message translates to:
  /// **'Raise to (min {minRaiseTo})'**
  String pokerRaiseToMin(int minRaiseTo);

  /// Raise amount input hint
  ///
  /// In en, this message translates to:
  /// **'Enter raise_to amount'**
  String get pokerRaiseToHint;

  /// Confirm raise button
  ///
  /// In en, this message translates to:
  /// **'Confirm Raise'**
  String get pokerConfirmRaise;

  /// Toast when raise is below minimum
  ///
  /// In en, this message translates to:
  /// **'Raise amount must be at least the minimum'**
  String get pokerRaiseAmountTooSmall;

  /// Blinds label
  ///
  /// In en, this message translates to:
  /// **'Blinds {sb}/{bb}'**
  String pokerBlind(int sb, int bb);

  /// Min buy-in label
  ///
  /// In en, this message translates to:
  /// **'Min buy-in {minBuyin}'**
  String pokerMinBuyIn(int minBuyin);

  /// Max buy-in label
  ///
  /// In en, this message translates to:
  /// **'Max buy-in {maxBuyin}'**
  String pokerMaxBuyIn(int maxBuyin);

  /// Current street label
  ///
  /// In en, this message translates to:
  /// **'Street {street}'**
  String pokerCurrentStreet(String street);

  /// Your hole cards label
  ///
  /// In en, this message translates to:
  /// **'Your cards'**
  String get pokerYourHoleCards;

  /// Pot display
  ///
  /// In en, this message translates to:
  /// **'Pot: {pot}'**
  String pokerPot(int pot);

  /// Waiting for game start
  ///
  /// In en, this message translates to:
  /// **'Waiting to start (at least 2 players seated)'**
  String get pokerWaitingForStart;

  /// Waiting for flop
  ///
  /// In en, this message translates to:
  /// **'Waiting for flop (finish betting)'**
  String get pokerWaitingForFlop;

  /// Waiting for dealing
  ///
  /// In en, this message translates to:
  /// **'Waiting for dealing...'**
  String get pokerWaitingForDeal;

  /// Acting seat display
  ///
  /// In en, this message translates to:
  /// **'Acting: Seat {seatNo}'**
  String pokerActingSeat(int seatNo);

  /// Seat status: waiting
  ///
  /// In en, this message translates to:
  /// **'Waiting'**
  String get pokerWaiting;

  /// Seat number display
  ///
  /// In en, this message translates to:
  /// **'Seat {seatNo}'**
  String pokerSeatNo(int seatNo);

  /// Empty seat label
  ///
  /// In en, this message translates to:
  /// **'Empty'**
  String get pokerEmptySeat;

  /// Chip count display
  ///
  /// In en, this message translates to:
  /// **'{stack} chips'**
  String pokerChipCount(int stack);

  /// Call button label
  ///
  /// In en, this message translates to:
  /// **'Call {toCall}'**
  String pokerCallAmount(int toCall);

  /// Check button label
  ///
  /// In en, this message translates to:
  /// **'Check'**
  String get pokerCheck;

  /// Fold button label
  ///
  /// In en, this message translates to:
  /// **'Fold'**
  String get pokerFold;

  /// Raise button label
  ///
  /// In en, this message translates to:
  /// **'Raise'**
  String get pokerRaise;
}

class _AppLocalizationsDelegate extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) => <String>['en', 'zh'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {


  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en': return AppLocalizationsEn();
    case 'zh': return AppLocalizationsZh();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.'
  );
}
