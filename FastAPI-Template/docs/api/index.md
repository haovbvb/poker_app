# API 文档

## 概述

这里是 FastAPI 后端模板的完整 API 文档。所有 API 都遵循 RESTful 设计原则，使用 JSON 格式进行数据交换。

## 认证

大部分 API 需要 JWT 认证。请先通过登录接口获取访问令牌，然后在请求头中包含：

```
Authorization: Bearer <your-access-token>
```

## 响应格式

所有 API 响应都遵循统一的格式：

### 成功响应

```json
{
  "code": 200,
  "msg": "OK",
  "data": {}
}
```

### 分页响应

```json
{
  "code": 200,
  "msg": "OK",
  "data": [],
  "total": 123,
  "page": 1,
  "page_size": 20
}
```

### 错误响应

```json
{
  "code": 400,
  "msg": "Bad Request",
  "data": null,
  "error_key": "poker.invalid_limit",
  "error_params": null
}
```

### 错误码说明

| 错误码 | 说明           |
| ------ | -------------- |
| 200    | 成功           |
| 400    | 请求参数错误   |
| 401    | 未认证         |
| 403    | 无权限         |
| 404    | 资源不存在     |
| 422    | 参数验证失败   |
| 429    | 请求过于频繁   |
| 500    | 服务器内部错误 |

## API 模块

- [认证授权](base.md) - 用户登录、token 刷新等
- [用户管理](users.md) - 用户 CRUD 操作
- [角色管理](role.md) - 角色权限管理
- [菜单管理](menu.md) - 系统菜单配置
- [文件管理](files.md) - 文件上传下载
- [部门管理](dept.md) - 组织架构管理
- [API 权限](api.md) - API 权限控制
- [审计日志](auditlog.md) - 操作日志记录
- [Poker 德州牌桌](poker.md) - 牌桌 REST + WebSocket 事件流
- [牌谱与成长统计](analysis.md) - 牌谱上传、成长数据统计（全量 + 近30日）

## 在线测试

启动服务后，您可以通过以下地址访问交互式 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 请求限制

- 文件上传大小限制：10MB
- 登录尝试限制：5 次/分钟
- Token 刷新限制：10 次/分钟
- API 请求频率：根据具体接口而定

## 健康检查

- **健康状态**: `GET /api/v1/base/health`
- **版本信息**: `GET /api/v1/base/version`
