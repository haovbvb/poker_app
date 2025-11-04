import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:merchant_app/core/utils/context_extensions.dart';
import 'package:pull_to_refresh/pull_to_refresh.dart';

class MessagePage extends StatefulWidget {
  const MessagePage({super.key});

  @override
  State<MessagePage> createState() => _MessagePageState();
}

class _MessagePageState extends State<MessagePage> {
  final DateFormat _timeFormatter = DateFormat('yyyy-MM-dd HH:mm');
  final List<_MessageItem> _items = List<_MessageItem>.from(_seedMessages);
  late final RefreshController _refreshController;

  @override
  void initState() {
    super.initState();
    _refreshController = RefreshController(initialRefresh: false);
  }

  Future<void> _refreshMessages() async {
    await Future<void>.delayed(const Duration(milliseconds: 600));
    setState(() {
      _items.insert(
        0,
        _MessageItem(
          icon: Icons.notifications_active_outlined,
          title: 'System Update',
          content:
              'A new version of the app is available. Update now to enjoy the latest features.',
          time: DateTime.now(),
        ),
      );
    });
    _refreshController.refreshCompleted();
  }

  @override
  void dispose() {
    _refreshController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(context.l10n.profileMessage)),
      body: SmartRefresher(
        controller: _refreshController,
        enablePullDown: true,
        header: const WaterDropHeader(),
        onRefresh: _refreshMessages,
        child: ListView.separated(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          itemBuilder: (context, index) {
            final item = _items[index];
            return _MessageTile(
              icon: item.icon,
              title: item.title,
              content: item.content,
              time: _timeFormatter.format(item.time),
              theme: theme,
            );
          },
          separatorBuilder: (_, __) => const SizedBox(height: 12),
          itemCount: _items.length,
        ),
      ),
    );
  }
}

class _MessageTile extends StatelessWidget {
  const _MessageTile({
    required this.icon,
    required this.title,
    required this.content,
    required this.time,
    required this.theme,
  });

  final IconData icon;
  final String title;
  final String content;
  final String time;
  final ThemeData theme;

  @override
  Widget build(BuildContext context) {
    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      elevation: 0,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            CircleAvatar(
              radius: 24,
              backgroundColor: theme.colorScheme.primaryContainer,
              child: Icon(icon, color: theme.colorScheme.primary),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: Text(title, style: theme.textTheme.titleMedium),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        time,
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: theme.textTheme.bodySmall?.color?.withOpacity(
                            0.6,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(content, style: theme.textTheme.bodyMedium),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _MessageItem {
  const _MessageItem({
    required this.icon,
    required this.title,
    required this.content,
    required this.time,
  });

  final IconData icon;
  final String title;
  final String content;
  final DateTime time;
}

final List<_MessageItem> _seedMessages = <_MessageItem>[
  _MessageItem(
    icon: Icons.notifications_none_outlined,
    title: 'Settlement Reminder',
    content:
        'Your settlement for October 2025 has been processed successfully. Check your account for details.',
    time: DateTime(2025, 11, 3, 18, 20),
  ),
  _MessageItem(
    icon: Icons.event_available_outlined,
    title: 'Holiday Notice',
    content:
        'Our service hours will adjust during the upcoming holiday. Please review the updated schedule.',
    time: DateTime(2025, 11, 2, 9, 45),
  ),
  _MessageItem(
    icon: Icons.security_outlined,
    title: 'Security Alert',
    content:
        'A login attempt was detected from a new device. If this was not you, please reset your password immediately.',
    time: DateTime(2025, 10, 30, 21, 10),
  ),
];
