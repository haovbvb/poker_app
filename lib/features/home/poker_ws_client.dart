import 'dart:async';
import 'dart:convert';

import 'package:poker_app/core/constants/storage_keys.dart';
import 'package:poker_app/network/api_path.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:web_socket_channel/io.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

class PokerWsClient {
  PokerWsClient({required this.baseUrl, required this.tableId});

  final String baseUrl;
  final String tableId;

  WebSocketChannel? _channel;
  StreamSubscription? _sub;
  Timer? _pingTimer;

  final _messages = StreamController<Map<String, dynamic>>.broadcast();
  Stream<Map<String, dynamic>> get messages => _messages.stream;

  bool get isConnected => _channel != null;

  Future<void> connect({required int lastSeq}) async {
    await disconnect();

    final headers = await _buildHeaders();
    final uri = _wsUri(baseUrl, tableId, lastSeq: lastSeq);

    final ch = IOWebSocketChannel.connect(
      uri,
      headers: headers,
      pingInterval: null, // 我们走业务 PING/PONG
    );

    _channel = ch;

    _sub = ch.stream.listen(
      (event) {
        final parsed = _parseEvent(event);
        if (parsed != null) {
          _messages.add(parsed);
        }
      },
      onError: (Object err, StackTrace st) {
        _messages.add({
          'type': 'CLIENT_ERROR',
          'payload': {'message': err.toString()},
        });
      },
      onDone: () {
        _messages.add({'type': 'CLOSED'});
      },
      cancelOnError: false,
    );

    // 服务端支持 query 里的 last_seq；同时也支持 RESUME 消息，这里双保险。
    send({'type': 'RESUME', 'last_seq': lastSeq});

    _pingTimer = Timer.periodic(const Duration(seconds: 15), (_) {
      send({'type': 'PING'});
    });
  }

  Future<void> disconnect() async {
    _pingTimer?.cancel();
    _pingTimer = null;

    await _sub?.cancel();
    _sub = null;

    await _channel?.sink.close();
    _channel = null;
  }

  void dispose() {
    unawaited(disconnect());
    unawaited(_messages.close());
  }

  void send(Map<String, dynamic> message) {
    final ch = _channel;
    if (ch == null) return;

    try {
      ch.sink.add(jsonEncode(message));
    } catch (_) {
      // ignore
    }
  }

  void sendAction({
    required int actionToken,
    required String action,
    int? amount,
    String? clientActionId,
  }) {
    final msg = <String, dynamic>{
      'type': 'ACTION',
      'action_token': actionToken,
      'action': action,
      'client_action_id':
          clientActionId ?? DateTime.now().microsecondsSinceEpoch.toString(),
    };
    if (amount != null) msg['amount'] = amount;
    send(msg);
  }

  Map<String, dynamic>? _parseEvent(Object? event) {
    if (event == null) return null;

    if (event is String) {
      final trimmed = event.trim();
      if (trimmed.isEmpty) return null;

      if (trimmed == 'PONG') {
        return {'type': 'PONG'};
      }

      try {
        final decoded = jsonDecode(trimmed);
        if (decoded is Map) {
          return Map<String, dynamic>.from(decoded);
        }
      } catch (_) {
        return {
          'type': 'TEXT',
          'payload': {'text': trimmed},
        };
      }
    }

    return {'type': 'BINARY'};
  }

  Uri _wsUri(String baseUrl, String tableId, {required int lastSeq}) {
    final httpUri = Uri.parse(baseUrl);
    final scheme = httpUri.scheme == 'https' ? 'wss' : 'ws';

    // baseUrl 可能包含 path，这里只替换 path 到 ws endpoint。
    return httpUri.replace(
      scheme: scheme,
      path: ApiPath.v1PokerTableWs(tableId),
      queryParameters: lastSeq > 0
          ? {'last_seq': lastSeq.toString()}
          : const {},
    );
  }

  Future<Map<String, dynamic>> _buildHeaders() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString(StorageKeys.authToken) ?? '';
    if (token.isEmpty) return const {};

    return {'Authorization': 'Bearer $token'};
  }
}
