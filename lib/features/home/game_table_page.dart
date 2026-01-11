import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:poker_app/app/app_router.dart';
import 'package:poker_app/core/utils/toast.dart';
import 'package:poker_app/features/home/poker_ws_client.dart';
import 'package:poker_app/network/api_path.dart';
import 'package:poker_app/network/api_service.dart';

class GameTablePage extends ConsumerStatefulWidget {
  const GameTablePage({
    super.key,
    required this.tableId,
    this.autoPlay = false,
  });

  final String tableId;
  final bool autoPlay;

  @override
  ConsumerState<GameTablePage> createState() => _GameTablePageState();
}

class _GameTablePageState extends ConsumerState<GameTablePage> {
  final _scaffoldKey = GlobalKey<ScaffoldState>();
  final _api = ApiService();
  PokerTableSnapshot? _snapshot;
  bool _loading = false;
  String? _error;

  PokerWsClient? _ws;
  StreamSubscription<Map<String, dynamic>>? _wsSub;
  bool _wsConnecting = false;
  bool _wsConnected = false;
  int _lastSeq = 0;
  PokerActionRequest? _actionRequest;
  Timer? _refreshDebounce;
  Timer? _reconnectTimer;

  int? _lastAutoActionToken;

  bool _autoSeatInProgress = false;
  int _autoSeatLastAttemptMs = 0;

  Future<void> _standUp() async {
    setState(() => _loading = true);
    try {
      await _api.post<void>(
        ApiPath.v1PokerTableSpectate(widget.tableId),
        parser: (_) {},
        toastOnBusinessError: true,
      );
      showToast('已站起');
      await _refresh();
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _changeTable() async {
    const fallbackMaxChips = 1000000;
    final snap = _snapshot;

    // 尽量用你当前买入/桌子上限来选择同档位桌。
    final youId = snap?.youUserId;
    final memberBuyin = snap?.members
        .where((m) => youId != null && m.userId == youId)
        .map((m) => m.buyin)
        .cast<int?>()
        .firstOrNull;
    final maxChips = (memberBuyin != null && memberBuyin > 0)
        ? memberBuyin
        : (snap?.config.maxBuyin ?? fallbackMaxChips);

    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      // 先断开当前桌连接并离桌。
      await _wsSub?.cancel();
      _wsSub = null;
      await _ws?.disconnect();
      _ws?.dispose();
      _ws = null;
      await _api.post<void>(
        ApiPath.v1PokerTableLeave(widget.tableId),
        parser: (_) {},
        toastOnBusinessError: false,
      );

      // 快速开始：自动买入/坐下/补 1 个机器人，确保能开局。
      final resp = await _api.post<Map<String, dynamic>>(
        ApiPath.v1PokerTablesQuickStart,
        data: {
          'max_chips': maxChips,
          'auto_buyin': maxChips,
          'auto_seat': true,
          'fill_bots': 1,
        },
        parser: (json) => Map<String, dynamic>.from(json as Map),
      );

      final tableId = resp.result?['table_id'] as String?;
      if (!resp.isSuccess || tableId == null || tableId.isEmpty) {
        showToast(resp.message.isNotEmpty ? resp.message : '未获取到新牌桌');
        return;
      }

      // 换桌：替换当前路由，避免堆栈越来越深。
      final path = '/poker/$tableId${widget.autoPlay ? '?auto=1' : ''}';
      AppRouter.router.go(path);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  void initState() {
    super.initState();
    _joinAndLoad();
  }

  @override
  void dispose() {
    _reconnectTimer?.cancel();
    _refreshDebounce?.cancel();
    _wsSub?.cancel();
    _ws?.dispose();
    super.dispose();
  }

  Future<void> _joinAndLoad() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      await _api.post<void>(
        ApiPath.v1PokerTableJoin(widget.tableId),
        parser: (_) {},
      );
      final snap = await _fetchSnapshot();
      if (!mounted) return;
      setState(() {
        _snapshot = snap;
        _lastSeq = snap.table.seq ?? 0;
      });
      unawaited(_maybeAutoSeat(snapshot: snap));
      await _connectWs();
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  Future<void> _maybeAutoSeat({PokerTableSnapshot? snapshot}) async {
    final snap = snapshot ?? _snapshot;
    if (snap == null) return;

    if (_autoSeatInProgress) return;
    final now = DateTime.now().millisecondsSinceEpoch;
    if (now - _autoSeatLastAttemptMs < 1500) return;

    final youId = snap.youUserId;
    if (youId == null) return;

    final member = snap.members
        .where((m) => m.userId == youId)
        .cast<PokerMember?>()
        .firstOrNull;
    if (member == null) return;

    // 已经有座位了就不做任何事。
    if (member.seatNo != null) return;
    if (snap.seats.any((s) => s.userId == youId)) return;

    // 未买入不能坐下（后端会拒绝）。
    if (member.buyin <= 0) return;

    final maxPlayers = snap.table.maxPlayers ?? 9;
    final occupied = snap.seats.map((s) => s.seatNo).toSet();
    final candidates = <int>[];
    for (var i = 1; i <= maxPlayers; i++) {
      if (!occupied.contains(i)) candidates.add(i);
    }
    if (candidates.isEmpty) return;

    _autoSeatInProgress = true;
    _autoSeatLastAttemptMs = now;

    try {
      for (final seatNo in candidates) {
        try {
          await _api.post<void>(
            ApiPath.v1PokerTableSeat(widget.tableId),
            data: {'seat_no': seatNo},
            parser: (_) {},
            // 自动坐下时不要频繁 toast 业务错误；失败会尝试下一个座位。
            toastOnBusinessError: false,
          );

          // 成功后拉一次快照刷新 UI。
          final next = await _fetchSnapshot();
          if (!mounted) return;
          setState(() {
            _snapshot = next;
            _lastSeq = next.table.seq ?? _lastSeq;
          });
          showToast('已自动坐下（座位 $seatNo）');
          return;
        } catch (_) {
          // try next seat
        }
      }
    } finally {
      _autoSeatInProgress = false;
    }
  }

  Future<void> _connectWs() async {
    if (_wsConnecting) return;
    _wsConnecting = true;

    try {
      await _wsSub?.cancel();
      _ws?.dispose();

      final client = PokerWsClient(
        baseUrl: ApiPath.proBaseUrl,
        tableId: widget.tableId,
      );
      _ws = client;

      final lastSeq = _lastSeq > 0 ? _lastSeq : (_snapshot?.table.seq ?? 0);

      await client.connect(lastSeq: lastSeq);
      if (!mounted) return;
      setState(() => _wsConnected = true);

      _wsSub = client.messages.listen(_onWsMessage);
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _wsConnected = false;
      });
      _scheduleReconnect();
    } finally {
      _wsConnecting = false;
    }
  }

  void _scheduleReconnect() {
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(const Duration(seconds: 2), () {
      if (!mounted) return;
      _connectWs();
    });
  }

  void _onWsMessage(Map<String, dynamic> msg) {
    final type = (msg['type'] ?? '').toString();
    if (type == 'PONG') return;

    if (type == 'CLOSED') {
      if (!mounted) return;
      setState(() => _wsConnected = false);
      _scheduleReconnect();
      return;
    }

    final seqRaw = msg['seq'];
    if (seqRaw is num) {
      final seq = seqRaw.toInt();
      if (seq > _lastSeq) _lastSeq = seq;
    }

    if (type == 'ERROR') {
      final payload = msg['payload'];
      final message = payload is Map ? (payload['msg']?.toString() ?? '') : '';
      if (message.isNotEmpty) {
        showToast(message);
      }
      return;
    }

    if (type == 'TABLE_SNAPSHOT') {
      final payload = msg['payload'];
      if (payload is Map) {
        try {
          final snap = PokerTableSnapshot.fromJson(
            Map<String, dynamic>.from(payload),
          );
          if (!mounted) return;
          setState(() {
            _snapshot = snap;
            _error = null;
          });
          unawaited(_maybeAutoSeat(snapshot: snap));
        } catch (_) {
          // ignore parse errors
        }
      }
      return;
    }

    if (type == 'ACTION_REQUESTED') {
      final payload = msg['payload'];
      if (payload is Map) {
        final req = PokerActionRequest.fromJson(
          Map<String, dynamic>.from(payload),
        );
        if (!mounted) return;

        setState(() => _actionRequest = req);

        // 自动托管：收到轮到自己行动时，自动 check/call。
        if (widget.autoPlay) {
          final youUserId = _snapshot?.youUserId;
          if (youUserId != null && req.userId == youUserId) {
            if (_lastAutoActionToken != req.actionToken) {
              _lastAutoActionToken = req.actionToken;
              // 轻微延迟，避免与 UI setState/WS 状态竞争。
              Timer(const Duration(milliseconds: 120), () {
                if (!mounted) return;
                if (_actionRequest?.actionToken != req.actionToken) return;
                _sendAction(req.toCall > 0 ? 'call' : 'check');
              });
            }
          }
        }
      }
      return;
    }

    if (type == 'STREET_DEALT') {
      final payload = msg['payload'];
      if (payload is Map) {
        final boardRaw = payload['board'];
        final street = payload['street']?.toString();
        if (boardRaw is List && street != null) {
          final cards = boardRaw.map((e) => e.toString()).toList();
          if (!mounted) return;
          setState(() {
            final snap = _snapshot;
            final hand = snap?.hand;
            if (snap != null && hand != null) {
              final updatedHand = PokerHandInfo(
                handId: hand.handId,
                street: street,
                pot: hand.pot,
                currentBet: hand.currentBet,
                minRaiseTo: hand.minRaiseTo,
                actingSeat: hand.actingSeat,
                actionDeadlineMs: hand.actionDeadlineMs,
                players: hand.players,
                board: cards,
              );
              _snapshot = PokerTableSnapshot(
                table: snap.table,
                config: snap.config,
                seats: snap.seats,
                members: snap.members,
                hand: updatedHand,
                youUserId: snap.youUserId,
                youHoleCards: snap.youHoleCards,
              );
            }
          });
        }
      }
      // 同步一次快照，确保 pot/actingSeat 等也更新。
      _refreshDebounce?.cancel();
      _refreshDebounce = Timer(const Duration(milliseconds: 200), () {
        if (!mounted) return;
        _refresh();
      });
      return;
    }

    // 其他事件先走「轻量同步」：去拉一次快照（带 debounce，避免刷屏）。
    _refreshDebounce?.cancel();
    _refreshDebounce = Timer(const Duration(milliseconds: 300), () {
      if (!mounted) return;
      _refresh();
    });
  }

  Future<void> _refresh() async {
    setState(() => _loading = true);
    try {
      final snap = await _fetchSnapshot();
      if (!mounted) return;
      setState(() {
        _snapshot = snap;
        _lastSeq = snap.table.seq ?? _lastSeq;
      });
      unawaited(_maybeAutoSeat(snapshot: snap));
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  Future<PokerTableSnapshot> _fetchSnapshot() async {
    final resp = await _api.get<PokerTableSnapshot>(
      ApiPath.v1PokerTableSnapshot(widget.tableId),
      parser: (json) =>
          PokerTableSnapshot.fromJson(Map<String, dynamic>.from(json as Map)),
    );
    if (!resp.isSuccess || resp.result == null) {
      throw Exception(resp.message.isNotEmpty ? resp.message : '获取牌桌失败');
    }
    return resp.result!;
  }

  Future<void> _leaveTable() async {
    setState(() => _loading = true);
    try {
      await _wsSub?.cancel();
      _wsSub = null;
      await _ws?.disconnect();
      _ws?.dispose();
      _ws = null;
      await _api.post<void>(
        ApiPath.v1PokerTableLeave(widget.tableId),
        parser: (_) {},
        toastOnBusinessError: true,
      );
      showToast('已离开牌桌');
      if (!mounted) return;
      AppRouter.goHome();
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final snapshot = _snapshot;

    final actionReq = _actionRequest;
    final youUserId = snapshot?.youUserId;
    final yourSeatNoFromSeats = snapshot?.seats
        .where((s) => youUserId != null && s.userId == youUserId)
        .map((s) => s.seatNo)
        .cast<int?>()
        .firstOrNull;
    final yourSeatNoFromMembers = snapshot?.members
        .where((m) => youUserId != null && m.userId == youUserId)
        .map((m) => m.seatNo)
        .cast<int?>()
        .firstOrNull;
    final yourSeatNo = yourSeatNoFromSeats ?? yourSeatNoFromMembers;
    final isSeated = yourSeatNo != null;
    // 动作栏显示以服务端 ACTION_REQUESTED 为准：
    // 有时快照里的 actingSeat 更新会有一点延迟，直接依赖它会导致按钮不出现。
    final showActions =
        snapshot != null &&
        actionReq != null &&
        youUserId != null &&
        actionReq.userId == youUserId &&
        actionReq.actionToken > 0 &&
        // seat 信息以现有数据为准；如果本地还没同步到 seat，也不要因此隐藏按钮。
        (yourSeatNo == null || actionReq.seatNo == yourSeatNo);

    final canAct = !_loading && _wsConnected;

    return Scaffold(
      key: _scaffoldKey,
      drawer: Drawer(
        child: SafeArea(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
                child: Text(
                  '牌桌 ${widget.tableId}',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ),
              const Divider(height: 1),
              ListTile(
                leading: const Icon(Icons.home_outlined),
                title: const Text('返回大厅'),
                onTap: _loading
                    ? null
                    : () {
                        Navigator.of(context).pop();
                        _leaveTable();
                      },
              ),
              ListTile(
                leading: Icon(isSeated ? Icons.logout : Icons.event_seat),
                title: Text(isSeated ? '站起' : '坐下'),
                onTap: _loading
                    ? null
                    : () {
                        Navigator.of(context).pop();
                        if (isSeated) {
                          _standUp();
                          return;
                        }
                        final buyin =
                            snapshot?.members
                                .where(
                                  (m) =>
                                      youUserId != null &&
                                      m.userId == youUserId,
                                )
                                .map((m) => m.buyin)
                                .cast<int?>()
                                .firstOrNull ??
                            0;
                        if (buyin <= 0) {
                          showToast('请先买入');
                          return;
                        }
                        _showSeat();
                      },
              ),
              ListTile(
                leading: const Icon(Icons.swap_horiz),
                title: const Text('换桌'),
                onTap: _loading
                    ? null
                    : () {
                        Navigator.of(context).pop();
                        _changeTable();
                      },
              ),
              const Spacer(),
            ],
          ),
        ),
      ),
      appBar: AppBar(
        automaticallyImplyLeading: false,
        leading: IconButton(
          icon: const Icon(Icons.menu),
          onPressed: () => _scaffoldKey.currentState?.openDrawer(),
        ),
        title: Text('牌桌 ${widget.tableId}'),
        backgroundColor: const Color(0xFF0F2942),
      ),
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Color(0xFF1A4D6F), Color(0xFF0F2942)],
          ),
        ),
        child: Column(
          children: [
            Expanded(
              child: _loading && snapshot == null
                  ? const Center(child: CircularProgressIndicator())
                  : _error != null
                  ? _ErrorView(message: _error!, onRetry: _joinAndLoad)
                  : snapshot == null
                  ? const Center(child: Text('暂无数据'))
                  : _TableContent(
                      snapshot: snapshot,
                      onRefresh: _refresh,
                      onLeave: _leaveTable,
                      loading: _loading,
                      onBuyIn: _loading ? null : _showBuyIn,
                      onSeat: _loading ? null : _showSeat,
                    ),
            ),
            if (showActions)
              _ActionBar(
                request: actionReq,
                onFold: canAct ? () => _sendAction('fold') : null,
                onCheckOrCall: canAct
                    ? () => _sendAction(actionReq.toCall > 0 ? 'call' : 'check')
                    : null,
                onRaise: canAct ? _showRaise : null,
              ),
          ],
        ),
      ),
    );
  }

  Future<void> _showBuyIn() async {
    final snapshot = _snapshot;
    if (snapshot == null) return;

    final controller = TextEditingController();
    final amount = await showModalBottomSheet<int>(
      context: context,
      isScrollControlled: true,
      builder: (ctx) {
        final bottom = MediaQuery.of(ctx).viewInsets.bottom;
        return Padding(
          padding: EdgeInsets.only(
            left: 16,
            right: 16,
            top: 16,
            bottom: bottom + 16,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                '买入筹码（${snapshot.config.minBuyin}~${snapshot.config.maxBuyin}）',
              ),
              const SizedBox(height: 12),
              TextField(
                controller: controller,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(hintText: '输入买入金额'),
              ),
              const SizedBox(height: 12),
              ElevatedButton(
                onPressed: () {
                  final v = int.tryParse(controller.text.trim());
                  Navigator.of(ctx).pop(v);
                },
                child: const Text('确认买入'),
              ),
            ],
          ),
        );
      },
    );

    if (amount == null) return;
    setState(() => _loading = true);
    try {
      await _api.post<void>(
        ApiPath.v1PokerTableBuyIn(widget.tableId),
        data: {'amount': amount},
        parser: (_) {},
        toastOnBusinessError: true,
      );
      showToast('买入成功');
      await _refresh();
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _showSeat() async {
    final snapshot = _snapshot;
    if (snapshot == null) return;
    final max = snapshot.table.maxPlayers ?? 9;
    final seatNo = await showDialog<int>(
      context: context,
      builder: (ctx) {
        return AlertDialog(
          title: const Text('选择座位'),
          content: SizedBox(
            width: double.maxFinite,
            child: Wrap(
              spacing: 8,
              runSpacing: 8,
              children: List.generate(max, (i) => i + 1)
                  .map(
                    (s) => OutlinedButton(
                      onPressed: () => Navigator.of(ctx).pop(s),
                      child: Text('$s'),
                    ),
                  )
                  .toList(),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(),
              child: const Text('取消'),
            ),
          ],
        );
      },
    );

    if (seatNo == null) return;
    setState(() => _loading = true);
    try {
      await _api.post<void>(
        ApiPath.v1PokerTableSeat(widget.tableId),
        data: {'seat_no': seatNo},
        parser: (_) {},
        toastOnBusinessError: true,
      );
      showToast('坐下成功');
      await _refresh();
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _sendAction(String action, {int? amount}) {
    final req = _actionRequest;
    final ws = _ws;
    if (req == null) return;
    if (!_wsConnected || ws == null) {
      showToast('网络未连接，无法操作');
      return;
    }

    // 先隐藏动作栏，避免重复点击（后续会收到快照/事件刷新）。
    if (mounted) {
      setState(() => _actionRequest = null);
    }

    ws.sendAction(actionToken: req.actionToken, action: action, amount: amount);
  }

  Future<void> _showRaise() async {
    final req = _actionRequest;
    if (req == null) return;
    if (!_wsConnected || _ws == null) {
      showToast('网络未连接，无法操作');
      return;
    }
    final controller = TextEditingController(text: req.minRaiseTo.toString());

    final amount = await showModalBottomSheet<int>(
      context: context,
      isScrollControlled: true,
      builder: (ctx) {
        final bottom = MediaQuery.of(ctx).viewInsets.bottom;
        return Padding(
          padding: EdgeInsets.only(
            left: 16,
            right: 16,
            top: 16,
            bottom: bottom + 16,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text('加注到（最小 ${req.minRaiseTo}）'),
              const SizedBox(height: 12),
              TextField(
                controller: controller,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(hintText: '输入 raise_to 金额'),
              ),
              const SizedBox(height: 12),
              ElevatedButton(
                onPressed: () {
                  final v = int.tryParse(controller.text.trim());
                  Navigator.of(ctx).pop(v);
                },
                child: const Text('确认加注'),
              ),
            ],
          ),
        );
      },
    );

    if (amount == null) return;
    if (amount < req.minRaiseTo) {
      showToast('加注金额不能小于最小加注');
      return;
    }
    _sendAction('raise_to', amount: amount);
  }
}

class _TableContent extends StatelessWidget {
  const _TableContent({
    required this.snapshot,
    required this.onRefresh,
    required this.onLeave,
    required this.loading,
    required this.onBuyIn,
    required this.onSeat,
  });

  final PokerTableSnapshot snapshot;
  final VoidCallback onRefresh;
  final VoidCallback onLeave;
  final bool loading;
  final VoidCallback? onBuyIn;
  final VoidCallback? onSeat;

  @override
  Widget build(BuildContext context) {
    final seats = snapshot.seats;
    final config = snapshot.config;
    final actingSeat = snapshot.hand?.actingSeat;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              _Chip('盲注 ${config.sb}/${config.bb}'),
              const SizedBox(width: 12),
              _Chip('最低买入 ${config.minBuyin}'),
              const SizedBox(width: 12),
              _Chip('最高买入 ${config.maxBuyin}'),
              const Spacer(),
              if (snapshot.hand != null)
                _Chip('当前阶段 ${snapshot.hand!.street ?? '-'}'),
            ],
          ),
          const SizedBox(height: 16),
          _TableCanvas(snapshot: snapshot),
          const SizedBox(height: 16),
          if (snapshot.youHoleCards != null &&
              snapshot.youHoleCards!.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Row(
                children: [
                  const _Chip('你的手牌'),
                  const SizedBox(width: 12),
                  ...snapshot.youHoleCards!.map(
                    (c) => Container(
                      margin: const EdgeInsets.only(right: 8),
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 10,
                      ),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        c,
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Colors.black87,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          Wrap(
            spacing: 12,
            runSpacing: 12,
            children: seats
                .map(
                  (s) => _SeatCard(
                    seat: s,
                    isYou:
                        snapshot.youUserId != null &&
                        s.userId == snapshot.youUserId,
                    isActing: actingSeat != null && s.seatNo == actingSeat,
                  ),
                )
                .toList(),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: ElevatedButton(
                  onPressed: onBuyIn,
                  child: const Text('买入'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: OutlinedButton(
                  onPressed: onSeat,
                  child: const Text('坐下'),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: loading ? null : onRefresh,
                  icon: const Icon(Icons.refresh),
                  label: const Text('刷新牌桌'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: loading ? null : onLeave,
                  icon: const Icon(Icons.logout),
                  label: const Text('离开牌桌'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _TableCanvas extends StatelessWidget {
  const _TableCanvas({required this.snapshot});

  final PokerTableSnapshot snapshot;

  @override
  Widget build(BuildContext context) {
    final hand = snapshot.hand;
    final pot = hand?.pot ?? 0;
    final community = hand?.board ?? const <String>[];
    final actingSeat = hand?.actingSeat;
    final street = hand?.street;

    return Center(
      child: Container(
        width: double.infinity,
        constraints: const BoxConstraints(maxWidth: 920, minHeight: 320),
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          gradient: const RadialGradient(
            radius: 1.2,
            colors: [Color(0xFF1D6A90), Color(0xFF0C1F33)],
          ),
          borderRadius: BorderRadius.circular(240),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.35),
              blurRadius: 18,
              offset: const Offset(0, 8),
            ),
          ],
          border: Border.all(
            color: Colors.black.withValues(alpha: 0.5),
            width: 4,
          ),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            AnimatedSwitcher(
              duration: const Duration(milliseconds: 250),
              child: Text(
                '底池: $pot',
                key: ValueKey(pot),
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 20,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
            const SizedBox(height: 12),
            if (hand == null)
              const Text(
                '等待开局（至少需要 2 名玩家坐下）',
                style: TextStyle(color: Colors.white70),
              )
            else if (community.isEmpty)
              Text(
                street == 'PREFLOP' ? '等待翻牌（请完成下注）' : '等待发牌...',
                style: const TextStyle(color: Colors.white70),
              )
            else
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: community
                    .map(
                      (card) => Container(
                        margin: const EdgeInsets.symmetric(horizontal: 6),
                        padding: const EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 10,
                        ),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          card,
                          style: const TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                            color: Colors.black87,
                          ),
                        ),
                      ),
                    )
                    .toList(),
              ),
            if (actingSeat != null) ...[
              const SizedBox(height: 12),
              Text(
                '行动位: 座位 $actingSeat',
                style: const TextStyle(color: Colors.white70),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _SeatCard extends StatelessWidget {
  const _SeatCard({
    required this.seat,
    required this.isYou,
    required this.isActing,
  });

  final PokerSeat seat;
  final bool isYou;
  final bool isActing;

  @override
  Widget build(BuildContext context) {
    final subtitle = seat.status.isEmpty ? '等待' : seat.status;

    return Container(
      width: 160,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.black.withValues(alpha: 0.25),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isActing
              ? const Color(0xFF9AD6FF)
              : (isYou ? const Color(0xFFFFD54F) : Colors.white24),
          width: (isYou || isActing) ? 2 : 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(
                '座位 ${seat.seatNo}',
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const Spacer(),
              if (isYou)
                const Icon(Icons.star, color: Color(0xFFFFD54F), size: 16),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            seat.username ?? '空位',
            style: const TextStyle(
              color: Colors.white,
              fontSize: 16,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 4),
          Text(subtitle, style: const TextStyle(color: Colors.white70)),
          const SizedBox(height: 6),
          Text(
            '${seat.stack} 筹码',
            style: const TextStyle(color: Color(0xFF9AD6FF)),
          ),
        ],
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  const _Chip(this.text);

  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: Colors.black.withValues(alpha: 0.3),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white24),
      ),
      child: Text(text, style: const TextStyle(color: Colors.white)),
    );
  }
}

class _ErrorView extends StatelessWidget {
  const _ErrorView({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              message,
              style: const TextStyle(color: Colors.white),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 12),
            ElevatedButton(onPressed: onRetry, child: const Text('重试')),
          ],
        ),
      ),
    );
  }
}

class PokerTableSnapshot {
  PokerTableSnapshot({
    required this.table,
    required this.config,
    required this.seats,
    required this.members,
    this.hand,
    this.youUserId,
    this.youHoleCards,
  });

  final PokerTableInfo table;
  final PokerTableConfig config;
  final List<PokerSeat> seats;
  final List<PokerMember> members;
  final PokerHandInfo? hand;
  final int? youUserId;
  final List<String>? youHoleCards;

  factory PokerTableSnapshot.fromJson(Map<String, dynamic> json) {
    final table = PokerTableInfo.fromJson(
      Map<String, dynamic>.from(json['table'] as Map? ?? {}),
    );
    final config = PokerTableConfig.fromJson(
      Map<String, dynamic>.from(json['config'] as Map? ?? {}),
    );
    final seatsJson = json['seats'] as List? ?? [];
    final seats = seatsJson
        .map((e) => PokerSeat.fromJson(Map<String, dynamic>.from(e as Map)))
        .toList();
    final membersJson = json['members'] as List? ?? [];
    final members = membersJson
        .map((e) => PokerMember.fromJson(Map<String, dynamic>.from(e as Map)))
        .toList();
    final handJson = json['hand'] as Map?;
    final you = json['you'] as Map?;
    final hole = you == null ? null : you['hole_cards'];
    final holeCards = hole is List
        ? hole.map((e) => e.toString()).toList()
        : null;

    return PokerTableSnapshot(
      table: table,
      config: config,
      seats: seats,
      members: members,
      hand: handJson == null
          ? null
          : PokerHandInfo.fromJson(Map<String, dynamic>.from(handJson)),
      youUserId: you == null ? null : you['user_id'] as int?,
      youHoleCards: holeCards,
    );
  }
}

class PokerMember {
  PokerMember({
    required this.userId,
    required this.username,
    required this.status,
    required this.buyin,
    required this.seatNo,
  });

  final int userId;
  final String? username;
  final String status;
  final int buyin;
  final int? seatNo;

  factory PokerMember.fromJson(Map<String, dynamic> json) {
    return PokerMember(
      userId: (json['user_id'] as num?)?.toInt() ?? 0,
      username: json['username'] as String?,
      status: json['status'] as String? ?? '',
      buyin: (json['buyin'] as num?)?.toInt() ?? 0,
      seatNo: (json['seat_no'] as num?)?.toInt(),
    );
  }
}

class PokerTableInfo {
  PokerTableInfo({required this.tableId, this.name, this.maxPlayers, this.seq});

  final String tableId;
  final String? name;
  final int? maxPlayers;
  final int? seq;

  factory PokerTableInfo.fromJson(Map<String, dynamic> json) {
    return PokerTableInfo(
      tableId: (json['table_id'] ?? '') as String,
      name: json['name'] as String?,
      maxPlayers: (json['max_players'] as num?)?.toInt(),
      seq: (json['seq'] as num?)?.toInt(),
    );
  }
}

class PokerTableConfig {
  PokerTableConfig({
    required this.sb,
    required this.bb,
    required this.ante,
    required this.minBuyin,
    required this.maxBuyin,
    required this.straddle,
  });

  final int sb;
  final int bb;
  final int ante;
  final int minBuyin;
  final int maxBuyin;
  final bool straddle;

  factory PokerTableConfig.fromJson(Map<String, dynamic> json) {
    return PokerTableConfig(
      sb: (json['sb'] as num?)?.toInt() ?? 1,
      bb: (json['bb'] as num?)?.toInt() ?? 2,
      ante: (json['ante'] as num?)?.toInt() ?? 0,
      minBuyin: (json['min_buyin'] as num?)?.toInt() ?? 40,
      maxBuyin: (json['max_buyin'] as num?)?.toInt() ?? 200,
      straddle: json['straddle'] as bool? ?? false,
    );
  }
}

class PokerSeat {
  PokerSeat({
    required this.seatNo,
    required this.userId,
    required this.username,
    required this.stack,
    required this.status,
  });

  final int seatNo;
  final int? userId;
  final String? username;
  final int stack;
  final String status;

  factory PokerSeat.fromJson(Map<String, dynamic> json) {
    return PokerSeat(
      seatNo: (json['seat_no'] as num?)?.toInt() ?? 0,
      userId: (json['user_id'] as num?)?.toInt(),
      username: json['username'] as String?,
      stack: (json['stack'] as num?)?.toInt() ?? 0,
      status: json['status'] as String? ?? '',
    );
  }
}

class PokerHandInfo {
  PokerHandInfo({
    this.handId,
    this.street,
    this.pot,
    this.currentBet,
    this.minRaiseTo,
    this.actingSeat,
    this.actionDeadlineMs,
    this.players,
    this.board,
  });

  final String? handId;
  final String? street;
  final int? pot;
  final int? currentBet;
  final int? minRaiseTo;
  final int? actingSeat;
  final int? actionDeadlineMs;
  final Map<String, dynamic>? players;
  final List<String>? board;

  factory PokerHandInfo.fromJson(Map<String, dynamic> json) {
    final boardRaw = json['board'] as List?;

    return PokerHandInfo(
      handId: json['hand_id'] as String?,
      street: json['street'] as String?,
      pot: (json['pot'] as num?)?.toInt(),
      currentBet: (json['current_bet'] as num?)?.toInt(),
      minRaiseTo: (json['min_raise_to'] as num?)?.toInt(),
      actingSeat: (json['acting_seat'] as num?)?.toInt(),
      actionDeadlineMs: (json['action_deadline_ms'] as num?)?.toInt(),
      players: json['players'] is Map
          ? Map<String, dynamic>.from(json['players'] as Map)
          : null,
      board: boardRaw?.map((e) => e.toString()).toList(),
    );
  }
}

class PokerActionRequest {
  PokerActionRequest({
    required this.handId,
    required this.seatNo,
    required this.userId,
    required this.actionToken,
    required this.toCall,
    required this.currentBet,
    required this.minRaiseTo,
    required this.deadlineMs,
    required this.street,
  });

  final String? handId;
  final int seatNo;
  final int userId;
  final int actionToken;
  final int toCall;
  final int currentBet;
  final int minRaiseTo;
  final int? deadlineMs;
  final String? street;

  factory PokerActionRequest.fromJson(Map<String, dynamic> json) {
    return PokerActionRequest(
      handId: json['hand_id'] as String?,
      seatNo: (json['seat_no'] as num?)?.toInt() ?? 0,
      userId: (json['user_id'] as num?)?.toInt() ?? 0,
      actionToken: (json['action_token'] as num?)?.toInt() ?? 0,
      toCall: (json['to_call'] as num?)?.toInt() ?? 0,
      currentBet: (json['current_bet'] as num?)?.toInt() ?? 0,
      minRaiseTo: (json['min_raise_to'] as num?)?.toInt() ?? 0,
      deadlineMs: (json['deadline_ms'] as num?)?.toInt(),
      street: json['street'] as String?,
    );
  }
}

class _ActionBar extends StatelessWidget {
  const _ActionBar({
    required this.request,
    required this.onFold,
    required this.onCheckOrCall,
    required this.onRaise,
  });

  final PokerActionRequest request;
  final VoidCallback? onFold;
  final VoidCallback? onCheckOrCall;
  final VoidCallback? onRaise;

  @override
  Widget build(BuildContext context) {
    final canCall = request.toCall > 0;
    final checkOrCallLabel = canCall ? '跟注 ${request.toCall}' : '过牌';

    return SafeArea(
      top: false,
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.black.withValues(alpha: 0.25),
          border: const Border(top: BorderSide(color: Colors.white24)),
        ),
        child: Row(
          children: [
            Expanded(
              child: OutlinedButton(onPressed: onFold, child: const Text('弃牌')),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: ElevatedButton(
                onPressed: onCheckOrCall,
                child: Text(checkOrCallLabel),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: ElevatedButton(
                onPressed: onRaise,
                child: const Text('加注'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

extension _IterableFirstOrNull<T> on Iterable<T> {
  T? get firstOrNull => isEmpty ? null : first;
}
