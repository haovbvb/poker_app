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
  String get commonCancel => 'Cancel';

  @override
  String get commonRetry => 'Retry';

  @override
  String pokerTableTitle(String tableId) {
    return 'Table $tableId';
  }

  @override
  String get pokerBackToLobby => 'Back to Lobby';

  @override
  String get pokerStandUp => 'Stand Up';

  @override
  String get pokerSitDown => 'Sit Down';

  @override
  String get pokerChangeTable => 'Change Table';

  @override
  String get pokerNoData => 'No data';

  @override
  String get pokerStandUpDone => 'Stood up';

  @override
  String get pokerPleaseBuyInFirst => 'Please buy in first';

  @override
  String get pokerChangeTableNoNewTable => 'Failed to get a new table';

  @override
  String pokerAutoSeated(int seatNo) {
    return 'Auto seated (Seat $seatNo)';
  }

  @override
  String get pokerFetchTableFailed => 'Failed to fetch table';

  @override
  String get pokerLeftTable => 'Left the table';

  @override
  String get pokerBuyIn => 'Buy In';

  @override
  String get pokerRefreshTable => 'Refresh';

  @override
  String get pokerLeaveTable => 'Leave';

  @override
  String pokerBuyInChipsRange(int minBuyin, int maxBuyin) {
    return 'Buy-in chips ($minBuyin~$maxBuyin)';
  }

  @override
  String get pokerBuyInAmountHint => 'Enter buy-in amount';

  @override
  String get pokerConfirmBuyIn => 'Confirm Buy-in';

  @override
  String get pokerBuyInSuccess => 'Buy-in successful';

  @override
  String get pokerSelectSeat => 'Select seat';

  @override
  String get pokerSitDownSuccess => 'Seated';

  @override
  String get pokerNetworkNotConnected => 'Not connected. Unable to act.';

  @override
  String pokerRaiseToMin(int minRaiseTo) {
    return 'Raise to (min $minRaiseTo)';
  }

  @override
  String get pokerRaiseToHint => 'Enter raise_to amount';

  @override
  String get pokerConfirmRaise => 'Confirm Raise';

  @override
  String get pokerRaiseAmountTooSmall => 'Raise amount must be at least the minimum';

  @override
  String pokerBlind(int sb, int bb) {
    return 'Blinds $sb/$bb';
  }

  @override
  String pokerMinBuyIn(int minBuyin) {
    return 'Min buy-in $minBuyin';
  }

  @override
  String pokerMaxBuyIn(int maxBuyin) {
    return 'Max buy-in $maxBuyin';
  }

  @override
  String pokerCurrentStreet(String street) {
    return 'Street $street';
  }

  @override
  String get pokerYourHoleCards => 'Your cards';

  @override
  String pokerPot(int pot) {
    return 'Pot: $pot';
  }

  @override
  String get pokerWaitingForStart => 'Waiting to start (at least 2 players seated)';

  @override
  String get pokerWaitingForFlop => 'Waiting for flop (finish betting)';

  @override
  String get pokerWaitingForDeal => 'Waiting for dealing...';

  @override
  String pokerActingSeat(int seatNo) {
    return 'Acting: Seat $seatNo';
  }

  @override
  String get pokerWaiting => 'Waiting';

  @override
  String pokerSeatNo(int seatNo) {
    return 'Seat $seatNo';
  }

  @override
  String get pokerEmptySeat => 'Empty';

  @override
  String pokerChipCount(int stack) {
    return '$stack chips';
  }

  @override
  String pokerCallAmount(int toCall) {
    return 'Call $toCall';
  }

  @override
  String get pokerCheck => 'Check';

  @override
  String get pokerFold => 'Fold';

  @override
  String get pokerRaise => 'Raise';
}
