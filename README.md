# merchant_app

A new Flutter project.

## Getting Started

This project is a starting point for a Flutter application.

A few resources to get you started if this is your first Flutter project:

- [Lab: Write your first Flutter app](https://docs.flutter.dev/get-started/codelab)
- [Cookbook: Useful Flutter samples](https://docs.flutter.dev/cookbook)

For help getting started with Flutter development, view the
[online documentation](https://docs.flutter.dev/), which offers tutorials,
samples, guidance on mobile development, and a full API reference.

## 目录结构总览

``

lib/
 ├── main.dart
 ├── app/
 │    ├── app.dart              # App 根组件（MaterialApp / router）
 │    ├── router.dart           # 路由定义 (go_router / auto_route)
 │    ├── theme.dart            # 全局主题、颜色、字体
 │    └── localization.dart     # 国际化支持
 │
 ├── core/                      # 核心通用模块（不依赖具体业务）
 │    ├── constants/            # 常量、枚举、AppConfig
 │    ├── utils/                # 工具函数（日期、格式化、加密等）
 │    ├── services/             # 系统服务（网络、存储、日志等）
 │    ├── error/                # 全局异常处理、自定义错误类型
 │    └── widgets/              # 全局通用组件（如 AppButton、LoadingView）
 │
 ├── data/                      # 数据访问层（数据库、本地缓存、远程接口）
 │    ├── db/                   # Drift/SQLite 数据库定义、DAO
 │    ├── models/               # 数据模型（如 User、Message）
 │    ├── repositories/         # 仓库层（封装本地/远程数据访问逻辑）
 │    └── network/              # 网络请求封装（Dio/Supabase/Http）
 │
 ├── features/                  # 按功能模块划分业务（推荐）
 │    ├── auth/                 # 登录注册模块
 │    │    ├── data/            # 模块专属数据（可选）
 │    │    ├── providers/       # Riverpod 状态提供器
 │    │    ├── views/           # 页面（LoginPage / RegisterPage）
 │    │    └── widgets/         # 模块专属小组件
 │    │
 │    ├── chat/
 │    ├── settings/
 │    └── stats/
 │
 ├── l10n/                      # Flutter 本地化（由 flutter gen-l10n 生成）
 │    └── app_en.arb
 │    └── app_zh.arb
 │
 ├── gen/                       # 自动生成代码（如 json_serializable / drift）
 │    └── drift_database.g.dart
 │
 └── bootstrap.dart              # 程序启动入口，负责初始化（DB、依赖注入、日志等）


``