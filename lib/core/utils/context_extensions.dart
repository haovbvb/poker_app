import 'package:flutter/widgets.dart';
import 'package:poker_app/l10n/app_localizations.dart';

extension LocalizationBuildContextX on BuildContext {
  AppLocalizations get l10n => AppLocalizations.of(this)!;
}
