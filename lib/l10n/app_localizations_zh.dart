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

  @override
  String get profileMessage => '消息';

  @override
  String get profileChangePassword => '修改密码';

  @override
  String get profileLanguage => '语言';

  @override
  String get profileUserAgreement => '用户协议';

  @override
  String get profileAbout => '关于';

  @override
  String get commonCancel => '取消';

  @override
  String get commonRetry => '重试';

  @override
  String pokerTableTitle(String tableId) {
    return '牌桌 $tableId';
  }

  @override
  String get pokerBackToLobby => '返回大厅';

  @override
  String get pokerStandUp => '站起';

  @override
  String get pokerSitDown => '坐下';

  @override
  String get pokerChangeTable => '换桌';

  @override
  String get pokerNoData => '暂无数据';

  @override
  String get pokerStandUpDone => '已站起';

  @override
  String get pokerPleaseBuyInFirst => '请先买入';

  @override
  String get pokerChangeTableNoNewTable => '未获取到新牌桌';

  @override
  String pokerAutoSeated(int seatNo) {
    return '已自动坐下（座位 $seatNo）';
  }

  @override
  String get pokerFetchTableFailed => '获取牌桌失败';

  @override
  String get pokerLeftTable => '已离开牌桌';

  @override
  String get pokerBuyIn => '买入';

  @override
  String get pokerRefreshTable => '刷新牌桌';

  @override
  String get pokerLeaveTable => '离开牌桌';

  @override
  String pokerBuyInChipsRange(int minBuyin, int maxBuyin) {
    return '买入筹码（$minBuyin~$maxBuyin）';
  }

  @override
  String get pokerBuyInAmountHint => '输入买入金额';

  @override
  String get pokerConfirmBuyIn => '确认买入';

  @override
  String get pokerBuyInSuccess => '买入成功';

  @override
  String get pokerSelectSeat => '选择座位';

  @override
  String get pokerSitDownSuccess => '坐下成功';

  @override
  String get pokerNetworkNotConnected => '网络未连接，无法操作';

  @override
  String pokerRaiseToMin(int minRaiseTo) {
    return '加注到（最小 $minRaiseTo）';
  }

  @override
  String get pokerRaiseToHint => '输入 raise_to 金额';

  @override
  String get pokerConfirmRaise => '确认加注';

  @override
  String get pokerRaiseAmountTooSmall => '加注金额不能小于最小加注';

  @override
  String pokerBlind(int sb, int bb) {
    return '盲注 $sb/$bb';
  }

  @override
  String pokerMinBuyIn(int minBuyin) {
    return '最低买入 $minBuyin';
  }

  @override
  String pokerMaxBuyIn(int maxBuyin) {
    return '最高买入 $maxBuyin';
  }

  @override
  String pokerCurrentStreet(String street) {
    return '当前阶段 $street';
  }

  @override
  String get pokerYourHoleCards => '你的手牌';

  @override
  String pokerPot(int pot) {
    return '底池: $pot';
  }

  @override
  String get pokerWaitingForStart => '等待开局（至少需要 2 名玩家坐下）';

  @override
  String get pokerWaitingForFlop => '等待翻牌（请完成下注）';

  @override
  String get pokerWaitingForDeal => '等待发牌...';

  @override
  String pokerActingSeat(int seatNo) {
    return '行动位: 座位 $seatNo';
  }

  @override
  String get pokerWaiting => '等待';

  @override
  String pokerSeatNo(int seatNo) {
    return '座位 $seatNo';
  }

  @override
  String get pokerEmptySeat => '空位';

  @override
  String pokerChipCount(int stack) {
    return '$stack 筹码';
  }

  @override
  String pokerCallAmount(int toCall) {
    return '跟注 $toCall';
  }

  @override
  String get pokerCheck => '过牌';

  @override
  String get pokerFold => '弃牌';

  @override
  String get pokerRaise => '加注';
}
