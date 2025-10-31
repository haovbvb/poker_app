// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Chinese (`zh`).
class AppLocalizationsZh extends AppLocalizations {
  AppLocalizationsZh([String locale = 'zh']) : super(locale);

  @override
  String get appTitle => '商家端';

  @override
  String get welcomeMessage => '欢迎使用商家端！';

  @override
  String get logout => '退出登录';

  @override
  String get tabHome => '首页';

  @override
  String get tabWork => '工作台';

  @override
  String get tabMe => '我的';

  @override
  String get homeTitle => '概览';

  @override
  String get workTitle => '工作台';

  @override
  String get meTitle => '个人中心';

  @override
  String get workInProgress => '工作台内容即将上线，敬请期待。';

  @override
  String get profileGreeting => '在这里管理你的个人信息。';

  @override
  String get login => '登录';

  @override
  String get loginHint => '请输入用户名和密码继续。';

  @override
  String get nameLabel => '用户名';

  @override
  String get nameRequired => '请输入用户名';

  @override
  String get passwordLabel => '密码';

  @override
  String get passwordRequired => '请输入密码';

  @override
  String get passwordTooShort => '密码长度至少 6 位';
}
