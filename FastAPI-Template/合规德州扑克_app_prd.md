# 合规德州扑克 App（订阅制）PRD + 技术任务拆解

> 文档状态：可执行草案（建议评审后固化）
>
> 版本：v0.1（2025-12-26）

> 产品目标：
> 在**不涉及真钱、不抽水、不做代理**的前提下，打造一款
> **德州扑克 × 竞技 × 成长 × 订阅制** 的长期可运营产品。

---

## 一、产品概述

### 1.0 范围说明（MVP）

- **MVP 必做**：快速桌（普通/VIP）、虚拟筹码（不可交易）、订阅会员等级（普通+4 档）、基础数据面板、简版复盘、断线重连、破产救济
- **MVP 明确不做/不支持**：真钱、提现、筹码交易、玩家间转账、抽水/代理、博彩/赔率玩法

### 1.1 产品定位

- 类型：竞技类棋牌（德州扑克 NLH）
- 核心卖点：公平竞技 + 技能成长 + 数据分析
- 商业模式：订阅制 + 虚拟商品
- 合规原则：虚拟筹码仅用于游戏，不可交易、不可兑换

### 1.2 目标用户

- 德州扑克新手（学习 / 娱乐）
- 中级玩家（提升胜率、数据复盘）
- 重度玩家（排位、赛事、分析工具）

---

## 二、核心功能 PRD（MVP）

### 2.0 术语与口径（必须统一）

- **钱包筹码上限**：用户“账户钱包”可持有筹码最大值，用于限制发放/买入等入口。
- **订阅有效**：服务端判定为准（订阅快照 `status == active` 且未过期）。
- **会员等级**：普通/Pro/Gold/Diamond/SVIP，为服务端根据订阅快照计算出的“当前有效最高档”。
- **VIP 桌**：需要达到最低会员等级才能进入（建议默认：Pro 起）。
- **筹码单位**：文档中的 `M/B` 为数量级缩写，`1M = 1,000,000`，`1B = 1,000,000,000`；服务端统一用“整数筹码（chips）”存储与计算。

### 2.1 游戏系统

#### 2.1.1 快速桌（必做）

- 玩法：NLH 6-max
- 桌级： 普通 / VIP
- 匹配规则：
  - 注册会员仅进入普通桌
  - 按筹码区间 + 等级匹配

#### 2.1.2 按筹码区间分配桌
| 桌号 | 买入 | 盲注 | 每局固定消耗（服务费/固定前注，照此扣减） |
| ---- | -------- | ---- | ---- |
| 1 | 150K/750K      | 2.5K/5K   | 1.5K |
| 2 | 300K/1.5M     | 5K/10K    | 3K |
| 3 | 1.5M/7.5M     | 25K/50K   | 15K |
| 4 | 6M/30M      | 100K/200K | 60K |
| 5 | 30M/150M     | 500K/1M   | 300K |
| 6 | 150M/750M      | 2.5M/5M   | 1.5M |
| 7 | 600M/3B      | 10M/20M   | 6M |
| 8 | 3B/15B     | 50M/100M  | 30M |

> “每局固定消耗”作为固定服务费/前注，每手开始即从在座玩家中按规则扣减，用于控制筹码流速；单位与买入一致（chips）。



**验收标准**

- 3 秒内完成匹配
- 支持断线重连

---

### 2.2 虚拟筹码系统

#### 2.2.1 筹码规则

- 仅用于入场与下注
- 不支持玩家间转移
- 有等级上限与衰减

**规则口径（建议补齐）**

- “等级上限”具体指：
  - A）钱包筹码上限（见订阅表格）
  - B）单次领取上限（若需要）
  - C）单日净增上限（MVP 可先不做，后续迭代）

#### 2.2.2 每日奖励

```
奖励 = Base × 等级倍率 × 衰减系数
```

**触发（B 手动领取）**：客户端在奖励入口展示“今日可领/已领”，用户点击后发起领取；同一自然日（按服务器时区）最多领取一次。

**接口（与当前后端实现对齐）**

- `GET /api/v1/rewards/daily`：获取今日状态（含 `can_claim`、`wallet_cap`、`wallet_chips`、`next_reset_at`）
- `POST /api/v1/rewards/daily/claim`：领取每日奖励（返回 `wallet_before`、`wallet_after`、`reward_awarded`）

**验收标准**

- 同一自然日（按服务器时区）只触发一次
- 发放后钱包筹码不得超过“钱包筹码上限”（超过则截断到上限）

---

### 2.3 订阅系统（核心营收）

#### 2.3.1 等级设计

> 登录态用户会员等级：普通（免费）+ Pro / Gold / Diamond / SVIP（付费 4 档）。

| 等级    | 月费 | 权益             | 每日奖励 | 用户账户钱包筹码上限 |
| ------- | ---- | ---------------- | -------- | -------------------- |
| 普通    | ¥0   | AI 分析 + 复盘   | 10M      | 30M                 |
| Pro     | ¥68  | AI 分析 + VIP 桌 | 50M      | 200M                 |
| Gold    | ¥128 | AI 分析 + VIP 桌 | 125M     | 560M                 |
| Diamond | ¥308 | 深度分析         | 310M     | 1.55B                |
| SVIP    | ¥668 | 深度分析         | 730M     | 3.5B                 |

**数据口径（与后端实现对齐）**

- 后端不在用户表存 `vip_level`；会员等级由订阅快照推导。
- 相关表与字段：
  - `subscription_snapshot`：`user_id`、`product_id`、`status`、`expires_at`、`platform`
  - `subscription_fact`：`user_id`、`product_id`、`status`、`expires_at`、`event_time`（事实流水/审计）
- 推导规则：取该用户所有 `subscription_snapshot` 中 `status == active` 的记录，用 `product_id` 映射到档位，取最高档作为最终等级；无有效订阅则为 `normal`。
- `product_id -> 档位`：优先使用配置映射 `SUBSCRIPTION_PRODUCT_TIER_MAP`，否则按 `product_id` 是否包含 `pro/gold/diamond/svip` 做兜底推断。

#### 2.3.2 订阅触发点

- 筹码不足
- 尝试进入高等级桌
- 查看 AI 复盘时

**后端自动触发接口（建议落点）**

- 进入牌桌/快速开始：当目标桌为 VIP 桌且用户等级不足时，返回“需要升级订阅”
  - `POST /api/v1/poker/tables/quick_start`
  - `POST /api/v1/poker/tables/{table_id}/join`
- 买入/带入筹码：当买入金额超过当前会员的“钱包筹码上限”或桌级要求时，返回“需要升级订阅”
  - `POST /api/v1/poker/tables/{table_id}/buyin`
- AI 复盘/深度分析：在复盘/分析接口进行权限校验（当前代码库暂无对应 API，后续新增时对齐）

**接口返回口径（建议统一）**

- 等级不足：HTTP 403，`error_key = subscription.tier_insufficient`
- 钱包上限不足：HTTP 403，`error_key = subscription.wallet_cap_exceeded`

**错误返回结构（建议统一）**

等级不足示例：

```json
{
  "code": 403,
  "msg": "需要 pro 及以上订阅（当前 normal），原因：vip_table",
  "error_key": "subscription.tier_insufficient",
  "error_params": {"required": "pro", "current": "normal", "reason": "vip_table"}
}
```

钱包上限不足示例：

```json
{
  "code": 403,
  "msg": "当前订阅(normal)钱包筹码上限为 30000000，请求 50000000，请升级订阅",
  "error_key": "subscription.wallet_cap_exceeded",
  "error_params": {"current": "normal", "cap": 30000000, "requested": 50000000}
}
```

**验收标准**

- 登录返回 token 响应内包含 `tier`（normal/pro/gold/diamond/svip），与服务端实时推导一致
- 重复验单/重复回调不造成重复入库（幂等）

---

### 2.4 成长与数据系统

#### 2.4.1 基础数据（MVP）

- VPIP
- PFR
- AF
- 3-bet
- WT
- 总手牌
- 平均每手赢取
- 最大 POT 赢取

**指标定义（建议写清，避免口径分叉）**

- VPIP：翻牌前“自愿投入”（call/raise，不含强制盲注）的手数 / 发到手牌总手数
- PFR：翻牌前加注（raise/raise_to）的手数 / 发到手牌总手数
- 3-bet：翻牌前再加注（re-raise）的手数 / 发到手牌总手数（MVP 先按手数口径，后续可升级为机会口径）
- AF（Aggression Factor）：翻牌后（FLOP+TURN+RIVER）(Bet+Raise) / Call（若 Call=0，则按 Bet+Raise 处理）
- WT（Went To Showdown / WTSD）：打到摊牌的手数 / 看过翻牌（VPIP 且未在翻牌前结束）的手数
- 平均每手赢取：净赢筹码总和 / 发到手牌总手数（净赢可为负）
- 最大 POT 赢取：单手结算中获得的最大底池金额

#### 2.4.2 进阶数据(30日)
- 入池率
- 胜率
- 入池胜率
- 总局数

**近30日指标定义（建议）**

- 入池率：近30日 VPIP
- 胜率：近30日赢下手牌的手数 / 发到手牌总手数
- 入池胜率：近30日 VPIP 且赢下手牌的手数 / VPIP 手数
- 总局数：近30日发到手牌总手数

**数据口径（建议补齐）**

- 统计窗口：全部 + 近 30 天（MVP）
- 样本下限：局数 < N 时提示“样本不足”（N 待确认）

#### 2.4.3 简版复盘

- 显示关键决策点
- 标记：Good / Bad / Mistake

---

### 2.5 破产保护

- 触发条件：筹码 < 5M
- 每日最多 2 次救济
- 连续 3 天触发 → 订阅引导

**接口 + 数据结构 + 幂等口径 + 计数口径（建议补齐）**

- 接口
  - `GET /api/v1/welfare/bankruptcy/status`：返回今日剩余次数、是否符合领取条件、下一次重置时间
  - `POST /api/v1/welfare/bankruptcy/claim`：发放救济（建议支持 `client_request_id` 幂等）
- 幂等口径
  - 客户端每次点击领取生成 `client_request_id`（UUID）并随请求提交；服务端以 `(user_id, client_request_id)` 去重，重复请求返回同一结果
- 计数口径
  - “每日最多 2 次”按服务器时区自然日统计
  - “连续 3 天触发”按服务器时区自然日连续计（建议定义为：连续3天都发生过救济领取）
- 数据结构（建议落库）
  - `bankruptcy_relief_claim`：`user_id`、`claim_date`（服务器时区日期）、`client_request_id`、`wallet_before`、`wallet_after`、`relief_awarded`、`created_at`

**验收标准**

- 救济次数按自然日重置
- 救济发放后不超过钱包筹码上限

---

## 三、非功能需求

### 3.1 公平性

- RNG 可审计
- 所有发牌与结算有 Hand ID

**手牌事件流最小集合（建议对齐 WS/HTTP 回放）**

- `HAND_STARTED`：新一手开始（`hand_id/button_seat/sb_seat/bb_seat`）
- `BLINDS_POSTED`：盲注/前注/straddle 入池（含 `pot`）
- `HOLE_CARDS_DEALT`：私牌下发（仅本人可见 `cards`，其他人只见 `count`）
- `ACTION_REQUESTED`：轮到某玩家行动（含 `action_token/to_call/min_raise_to/deadline_ms/street`）
- `ACTION_TAKEN`：玩家已行动（含 `client_action_id/contributed/pot`）
- `STREET_DEALT`：发公共牌（FLOP/TURN/RIVER，含 `board`）
- `SHOWDOWN`：摊牌结算（含 `side_pots/payouts`）
- `HAND_SEED_REVEALED`：种子揭示用于审计（`server_seed_hash/server_seed/deck_hash`）
- `HAND_ENDED`：手牌结束（弃牌结束时含 `winner_seat`；摊牌结束时含 `payouts`）

### 3.2 合规

- UI 不出现“赢钱”文案
- 明示：No Real Money

**合规文案建议（MVP）**

- 登录页/订阅页/大厅页显著位置展示：
  - “虚拟筹码仅用于游戏，不可交易、不可提现”
  - “No Real Money / No Cash-out”

### 3.3 风控

- 行为监控
- 筹码异常检测
- 软惩罚优先

---

## 四、关键流程（用于产品/研发对齐）

### 4.1 登录态等级展示

- 登录成功后返回 `tier` 字段（字符串：normal/pro/gold/diamond/svip）
- 客户端展示“会员等级”以该字段为准；若需要更实时，可调用“我的订阅快照”接口拉取

### 4.2 订阅验单 / 回调更新

- 客户端购买完成后调用“订阅验单”接口写入事实表并更新快照
- 平台回调到服务端 webhook 时，服务端写入事实表并更新快照

### 4.3 VIP 桌准入

- 入口：快速开始 / 进入牌桌 / 买入
- 服务端校验：
  - 若桌级要求 > 用户有效等级 → 返回等级不足错误
  - 若买入/带入导致超过钱包上限 → 返回钱包上限错误

---

## 五、接口与数据（面向后端实现/联调）

### 5.1 已有接口（当前仓库）

> 说明：以下为“当前代码仓库已实现并可联调”的接口清单（按模块分组）。

**登录/会话（JWT）**

- `POST /api/v1/base/access_token`：登录获取 token（返回包含 `tier`）
- `POST /api/v1/base/refresh_token`：刷新 token
- `POST /api/v1/base/logout`：退出登录（可选传入 refresh_token 做撤销）
- `GET /api/v1/base/userinfo`：查看用户信息（返回包含 `tier`）
- `GET /api/v1/base/health`：健康检查
- `GET /api/v1/base/version`：版本信息

**订阅（IAP 验单 / Webhook）**

- `GET /api/v1/subscriptions/me`：获取我的订阅快照列表
- `POST /api/v1/subscriptions/verify`：订阅验单并更新快照（幂等）
- `POST /api/v1/subscriptions/webhooks/apple`：Apple 回调入口（支持 `X-Webhook-Secret`）
- `POST /api/v1/subscriptions/webhooks/google`：Google 回调入口（支持 `X-Webhook-Secret`）

**德州扑克（牌桌 / 匹配 / 事件 / WebSocket）**

- `GET /api/v1/poker/tables/lobby_levels`：大厅桌档位（按筹码区间 + 是否 VIP）
- `POST /api/v1/poker/tables/quick_start`：快速开始（按 `max_chips` 匹配/创建桌）
- `GET /api/v1/poker/tables/list`：牌桌列表
- `POST /api/v1/poker/tables/create`：创建牌桌（当前实现：需登录；实际线上建议仅管理端开放）
- `GET /api/v1/poker/tables/{table_id}/config`：牌桌规则配置
- `GET /api/v1/poker/tables/{table_id}`：牌桌快照（含你自己的私牌）
- `GET /api/v1/poker/tables/{table_id}/events?since_seq=0&limit=200`：事件增量回放（HTTP 断线补偿）
- `POST /api/v1/poker/tables/{table_id}/join`：进入牌桌（默认观战）
- `POST /api/v1/poker/tables/{table_id}/leave`：离开牌桌
- `POST /api/v1/poker/tables/{table_id}/buyin`：买入/带入筹码（含钱包 cap + VIP 等级校验）
- `POST /api/v1/poker/tables/{table_id}/seat`：坐下
- `POST /api/v1/poker/tables/{table_id}/spectate`：切换观战
- `POST /api/v1/poker/tables/{table_id}/sitout`：坐出
- `WS /api/v1/poker/tables/{table_id}/ws`：牌桌实时事件（支持 RESUME 补发）

**每日奖励**

- `GET /api/v1/rewards/daily`：每日奖励状态（返回 `wallet_chips/wallet_cap/can_claim/next_reset_at`）
- `POST /api/v1/rewards/daily/claim`：领取每日奖励（返回 `wallet_before/after`）

**破产救济**

- `GET /api/v1/welfare/bankruptcy/status`：破产救济状态（含 `consecutive_claim_days/should_prompt_subscribe`）
- `POST /api/v1/welfare/bankruptcy/claim`：领取破产救济（要求 `client_request_id` 幂等）

**牌谱与成长数据（Analysis/Growth）**

- `POST /api/v1/hands/upload`：上传牌谱（存储 + 基础解析）
- `GET /api/v1/hands`：获取我的牌谱列表
- `GET /api/v1/growth/stats`：成长数据统计（全量 + 近30日）

**系统通知/公告（消息）**

- `GET /api/v1/messages/list`：消息列表（支持 `unread_only/type/page/page_size`）
- `GET /api/v1/messages/unread_count`：未读数量
- `POST /api/v1/messages/{message_id}/read`：标记已读
- `POST /api/v1/messages/read_all`：全部标记已读
- `DELETE /api/v1/messages/{message_id}`：删除/隐藏消息
- `POST /api/v1/messages/create`：新增消息（后台权限）

`POST /api/v1/hands/upload` 请求示例（JSON）：

```json
{
  "platform": "PokerStars",
  "raw_content": "PokerStars Hand #1234567890:  Hold'em No Limit ($0.05/$0.10 USD) - 2025/12/29 20:00:00 ET\nTable 'Alpha' 6-max Seat #1 is the button\nSeat 1: Hero ($10 in chips)\nSeat 2: Villain1 ($10 in chips)\nSeat 3: Villain2 ($10 in chips)\nHero: posts small blind $0.05\nVillain1: posts big blind $0.10\n*** HOLE CARDS ***\nDealt to Hero [As Kd]\nVillain2: folds\nHero: raises $0.20 to $0.25\nVillain1: calls $0.15\n*** FLOP *** [Ah 7c 2d]\nHero: bets $0.35\nVillain1: calls $0.35\n*** TURN *** [Ah 7c 2d] [9s]\nHero: bets $0.90\nVillain1: folds\nUncalled bet ($0.90) returned to Hero\nHero collected $1.20 from pot\n*** SUMMARY ***\nTotal pot $1.20 | Rake $0.00\nSeat 1: Hero collected ($1.20)\n"
}
```

### 5.2 建议新增/补齐（与 PRD 对齐）

> 目标：达到“可上线”的最小标准（用户能注册/登录、能稳定玩牌、筹码闭环正确、订阅闭环正确、可运营可追溯）。

**P0（上线阻断，必须补齐）**

1) **账号注册/找回/合规注销**（当前仓库缺失注册与用户侧密码管理接口）

- `POST /api/v1/base/register`
  - 入参：`username/email/password`（具体字段与校验规则需定稿）
  - 出参：`user_id/username` + 初始 `tier=normal` + token（可选）
- `POST /api/v1/base/update_password`（用户侧修改密码，需登录）
- `POST /api/v1/base/request_password_reset` + `POST /api/v1/base/confirm_password_reset`（若上线范围包含找回密码）
- `POST /api/v1/base/delete_account`（合规：账号注销/删除请求；最小实现可“软删除 + 冷静期 + 审计”）

2) **钱包（筹码）闭环与账本**（当前实现仅有“上限校验 + 发放”，缺少“买入扣款/离桌结算/明细”）

- `GET /api/v1/wallet/me`
  - 出参：`wallet_chips/wallet_cap/tier/server_time`（大厅/个人中心展示用）
- `GET /api/v1/wallet/ledger`（可选但强烈建议：上线后排查纠纷/风控必备）
  - 出参：分页列表：`type(delta, before, after, ref_id, created_at)`
- **德州买入/离桌与钱包对账口径（必须落地）**
  - `POST /api/v1/poker/tables/{table_id}/buyin`：需要将 `amount` 从 `user_wallet.chips` 扣减（不足则 403/400），并写入账本
  - `POST /api/v1/poker/tables/{table_id}/leave`：需要将玩家在桌面剩余 `stack` 自动结算回 `user_wallet.chips`（并写入账本），否则玩家会“离桌丢筹码”
  - `POST /api/v1/poker/tables/{table_id}/spectate`：若从 seated → spectator，也需要明确是否触发结算（建议：触发）

3) **断线重连协议定稿（客户端可实现）**（代码已实现，但 PRD 需要补齐“联调口径”）

- WS 建议口径（当前实现已支持）：
  - `PING` → `PONG`
  - `RESUME {last_seq}`：服务端补发 `seq > last_seq` 的事件；若无事件则返回 `TABLE_SNAPSHOT`
  - `ACTION {action_token, action, amount?, client_action_id?}`：出错返回 `type=ERROR`（不强制断开）
- HTTP 补偿：`GET /api/v1/poker/tables/{table_id}/events?since_seq=...`

4) **公平性/可审计事件字段对齐**（代码已实现 commit-reveal，但 PRD 事件集合需与实现一致）

- 建议在“手牌事件流最小集合”中明确以下事件与字段：
  - `HAND_SEED_COMMIT {hand_id, algo_version, server_seed_hash}`
  - `HAND_DECK_COMMIT {hand_id, deck_hash, used_player_ids}`
  - `HAND_SEED_REVEALED {hand_id, algo_version, server_seed_hash, server_seed, deck_hash}`
  - `HOLE_CARDS_DEALT` 为私有事件：本人 `cards`，他人只见 `count`

5) **复盘/分析（与订阅权益匹配）**（PRD 宣称“AI 分析/复盘/深度分析”，但目前仅有上传牌谱与成长统计）

- 最小可上线方案二选一：
  - A）若上线必须包含 AI/复盘：补齐接口与权限门槛（并在服务端做限流/排队）
  - B）若上线不包含 AI：需要下调 PRD/订阅权益文案，避免“宣传与能力不一致”

若选 A，建议接口：

- `POST /api/v1/analysis/review`：简版复盘（Pro+ 或普通也可，按产品表定）
  - 入参：`hand_id` 或 `raw_content`（二选一）
  - 出参：关键节点列表（street、action、建议、标签 Good/Bad/Mistake）
- `POST /api/v1/analysis/deep`：深度分析（Diamond/SVIP）
- `GET /api/v1/analysis/jobs/{job_id}`：异步任务结果（避免移动端超时）

**P1（强烈建议，接近上线必做/运营必备）**

1) **举报/封禁/风控最小闭环**（当前缺失相关接口）

- `POST /api/v1/moderation/report`：举报玩家（原因、证据、table_id/hand_id 可选）
- `POST /api/v1/moderation/block` / `DELETE /api/v1/moderation/block`：拉黑（可选）
- 管理端：`POST /api/v1/moderation/ban` / `POST /api/v1/moderation/unban`：封禁/解封（含时长与理由）

2) **运营配置下发（避免每次改档位都发版）**

- `GET /api/v1/config/runtime`：下发 lobby 档位、订阅权益文案开关、活动开关、时区等（MVP 可只返回 lobby_levels + tiers 配置）

3) **关键链路审计与追踪**

- 最小要求：登录、验单、入桌、买入、离桌结算、每日奖励、救济，均写可查询的审计/账本（至少数据库留痕）

---

## 六、验收清单（MVP 最小可验收集）

- 快速桌：匹配 < 3 秒；断线可重连；VIP 桌等级不足可正确拦截
- 筹码：不可转账；每日手动领取一次（按服务器时区自然日）；不超过钱包上限
- 订阅：验单写入事实表+快照表；重复请求幂等；登录返回 `tier` 与快照一致
- 风控/日志：关键动作（登录、验单、入桌、买入、救济）可追踪（至少有 audit log 或等价日志）

---

## 七、技术任务拆解（建议）

### 7.1 后端

- 会员等级：确认 `SUBSCRIPTION_PRODUCT_TIER_MAP` 的商品映射（iOS/Android 各 product_id）
- 桌准入：在 `quick_start/join/buyin` 等入口统一做等级与钱包上限校验，并统一错误码
- 日奖励：每日手动领取（app 端拉取状态 + 点击领取）；服务端按自然日幂等与上限截断
- 破产救济：新增救济接口与次数限制逻辑
- 指标与复盘：确定 MVP 数据表/聚合口径（若暂不做落库，至少先定接口契约）

### 7.2 客户端

- 展示：登录后展示会员等级（来自 token 的 `tier`）；订阅页展示权益与当前状态
- 购买：成功后调用验单接口；支持“恢复购买”流程（iOS/Android 各自机制）

### 7.3 测试

- 订阅：active/expired 的边界时间；重复验单/重复回调幂等
- 桌准入：不同 tier 进入普通/VIP 的矩阵用例
- 钱包上限：每日奖励/救济/买入 三类入口的上限截断与拒绝用例


## 八、系统通知/运营公告

- 触发条件：重要版本更新、系统维护、活动公告等
- 发送渠道：应用内通知、电子邮件（可选）
- 内容模板：预定义模板支持动态内容插入

## 九、牌号
牌面表示法采用两字符表示法：
- 第一字符表示牌的点数，取值范围为：2,3,4,5,6,7,8,9,T,J,Q,K,A
- 第二字符表示牌的花色，取值范围为：S,H,D,C
其中：
S = Spades（黑桃 ♠）
H = Hearts（红桃 ♥）
D = Diamonds（方块 ♦）
C = Clubs（梅花 ♣）