class ApiPath {
  static const String proBaseUrl =
      'http://localhost:8000';
  static const String testBaseUrl =
      'http://localhost:8000';

  static const String posts = '/posts';

  // FastAPI OpenAPI (/api/v1)
  static const String _v1 = '/api/v1';

  // 基础模块
  static const String login = '$_v1/base/access_token';
  static const String refreshToken = '$_v1/base/refresh_token';
  static const String user = '$_v1/base/userinfo';
  static const String logout = '$_v1/base/logout';
  static const String v1Health = '$_v1/base/health';
  static const String v1Version = '$_v1/base/version';

  // Analysis
  static const String v1HandsUpload = '$_v1/hands/upload';
  static const String v1Hands = '$_v1/hands';
  static const String v1GrowthStats = '$_v1/growth/stats';

  // 用户模块
  static const String v1UsersList = '$_v1/users/list';
  static const String v1UsersGet = '$_v1/users/get';
  static const String v1UsersCreate = '$_v1/users/create';
  static const String v1UsersUpdate = '$_v1/users/update';
  static const String v1UsersDelete = '$_v1/users/delete';
  static const String v1UsersResetPassword = '$_v1/users/reset_password';

  // 消息模块
  static const String v1MessagesList = '$_v1/messages/list';
  static const String v1MessagesUnreadCount = '$_v1/messages/unread_count';
  static String v1MessagesRead(int messageId) =>
      '$_v1/messages/$messageId/read';
  static const String v1MessagesReadAll = '$_v1/messages/read_all';
  static String v1MessagesDelete(int messageId) => '$_v1/messages/$messageId';
  static const String v1MessagesCreate = '$_v1/messages/create';

  // 上传文件
  static const String v1FilesUpload = '$_v1/files/upload';

  // 扑克桌模块
  static const String v1PokerTablesList = '$_v1/poker/tables/list';
  static const String v1PokerLobbyLevels = '$_v1/poker/tables/lobby_levels';
  static const String v1PokerTablesCreate = '$_v1/poker/tables/create';
  static const String v1PokerTablesQuickStart = '$_v1/poker/tables/quick_start';
  static String v1PokerTableConfig(String tableId) =>
      '$_v1/poker/tables/$tableId/config';
  static String v1PokerTableSnapshot(String tableId) =>
      '$_v1/poker/tables/$tableId';
  static String v1PokerTableEvents(String tableId) =>
      '$_v1/poker/tables/$tableId/events';
  static String v1PokerTableJoin(String tableId) =>
      '$_v1/poker/tables/$tableId/join';
  static String v1PokerTableLeave(String tableId) =>
      '$_v1/poker/tables/$tableId/leave';
  static String v1PokerTableBuyIn(String tableId) =>
      '$_v1/poker/tables/$tableId/buyin';
  static String v1PokerTableSeat(String tableId) =>
      '$_v1/poker/tables/$tableId/seat';
  static String v1PokerTableSpectate(String tableId) =>
      '$_v1/poker/tables/$tableId/spectate';
  static String v1PokerTableSitout(String tableId) =>
      '$_v1/poker/tables/$tableId/sitout';

    static String v1PokerTableWs(String tableId) => '$_v1/poker/tables/$tableId/ws';

  // 订阅模块
  static const String v1SubscriptionsVerify = '$_v1/subscriptions/verify';
  static const String v1SubscriptionsMe = '$_v1/subscriptions/me';
  static const String v1SubscriptionsWebhooksApple =
      '$_v1/subscriptions/webhooks/apple';
  static const String v1SubscriptionsWebhooksGoogle =
      '$_v1/subscriptions/webhooks/google';

  // 每日奖励
  static const String v1RewardsDaily = '$_v1/rewards/daily';
  static const String v1RewardsDailyClaim = '$_v1/rewards/daily/claim';

  // 破产救济
  static const String v1WelfareBankruptcyStatus =
      '$_v1/welfare/bankruptcy/status';
  static const String v1WelfareBankruptcyClaim =
      '$_v1/welfare/bankruptcy/claim';
}
