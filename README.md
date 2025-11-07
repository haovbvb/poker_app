# merchant_app

Flutter 商户侧应用，整合 Riverpod 状态管理、Dio 网络封装以及多语言支持，提供登录、首页、工作台与“我的”等核心模块。
通用 UI 组件库 jui, 参考文档: https://www.yuque.com/jui_flutter/kb/howistv001f1ghp9

## 环境要求

- Flutter 3.24+（Dart 3.9+）
- Xcode 15 / Android Studio（编译 iOS/Android）
- 已配置好基础 Flutter 开发环境（`flutter doctor` 通过）

## 快速开始

```bash
# 安装依赖
flutter pub get

# 运行 iOS 模拟器示例
flutter run -d "iPhone 16 Plus"

# 或指定 Android 设备
flutter run -d <device-id>
```

首次登录前，请向后端申请可用的账号密码。密码会在客户端侧通过 MD5（32 位小写）处理后再发送。

## 主要特性

- **Riverpod Notifier**：驱动全局登录状态、底部导航索引等。
- **Dio 封装**：统一 Accept-Language、AccessToken 头部，自动弹出 HUD、Toast 处理错误。
- **GoRouter**：控制登录态路由跳转，支持启动时刷新 token。
- **多语言**：`flutter gen-l10n` 生成中英文文案，网络请求携带当前语言。
- **自定义底部导航**：资产化图标，选中态与未选中态分离，支持多倍图资源。

## 目录结构

```
lib/
 ├── main.dart                   # 应用入口
 ├── app/
 │    ├── app.dart               # 顶层 MaterialApp（含 Riverpod）
 │    ├── router.dart            # GoRouter 路由表
 │    └── theme.dart             # 全局主题与颜色
 │
 ├── core/                       # 通用工具与常量
 │    ├── constants/             # 常量（StorageKeys 等）
 │    ├── utils/                 # HUD、日志、加密、Toast
 │    └── widgets/               # 全局可复用组件
 │
 ├── data/                       # 网络层（Dio 封装、请求路径）
 │    └── network/
 │         ├── api_client.dart   # Dio 单例、拦截器
 │         ├── api_service.dart  # GET/POST 封装
 │         ├── api_path.dart     # 后端接口常量
 │         └── base_response.dart# 通用响应解析
 │
 ├── features/                   # 按业务划分模块
 │    ├── login/                 # 登录与鉴权
 │    │    ├── models/           # AuthState / AuthResult / AuthSession
 │    │    └── providers/        # AuthNotifier
 │    ├── home/
 │    ├── work/
 │    └── me/
 │
 ├── l10n/                       # 多语言资源与生成代码
 └── test/                       # Widget / 单元测试样例
```

## 鉴权流程

1. 登录请求成功后，`AuthNotifier` 会：
   - 通过 `AuthResult` 解析完整用户信息；
   - 调用 `AuthSession` 单例缓存会话；
   - 持久化刷新后的 token 并跳转首页。
2. 应用启动时若检测到本地 token，会调用 `/admin/sys/account/refreshToken` 接口刷新，成功则继续保留登录态，失败则清空会话并返回登录页。
3. 登出接口成功后会清除本地 token、Session，并导航回登录页。

## 资源管理

- 底部标签栏图标位于 `assets/images/`，支持 `2.0x/`、`3.0x/` 变体。
- 如需新增图片，请同步更新 `pubspec.yaml` 的 `assets` 配置后执行 `flutter pub get`。

## 开发建议

- 新增接口：在 `api_path.dart` 定义路径 -> 在 `ApiService` 调用 -> 根据需要新增模型。
- 新增功能模块：在 `features/` 下建立子目录，包含 `models/providers/views/widgets` 等子结构。
- 若需调试网络，请关注控制台输出（`ApiClient` 已内置请求/响应日志）。

## 常用命令

```bash
# 代码格式化
flutter format lib test

# 运行测试
flutter test

# 生成多语言文件
flutter gen-l10n
```

---

欢迎根据业务需求扩展 README，补充 API 文档、设计稿链接或迭代计划。若发现文档与实现不一致，请优先以代码为准并提更新。
