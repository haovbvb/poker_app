import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:merchant_app/app/app_router.dart';
import 'package:merchant_app/core/utils/context_extensions.dart';
import 'package:merchant_app/features/login/models/auth_session.dart';
import 'package:merchant_app/features/login/providers/auth_controller.dart';

class ProfileTab extends ConsumerWidget {
  const ProfileTab({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    ref.watch(authNotifierProvider);
    final session = AuthSession.instance.current;
    final rawName = session != null ? session.name.trim() : '';
    final rawPhone = session != null ? session.phone.trim() : '';
    final name = rawName.isNotEmpty ? rawName : context.l10n.tabMe;
    final phone = rawPhone.isNotEmpty ? rawPhone : context.l10n.profileGreeting;
    final avatarUrl = session?.avatar.trim();

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        scrolledUnderElevation: 0,
        surfaceTintColor: Colors.transparent,
        title: Text(context.l10n.tabMe),
        actions: [
          TextButton(
            onPressed: () async {
              await ref.read(authNotifierProvider.notifier).logout();
            },
            child: Text(context.l10n.logout),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(24, 8, 24, 24),
        children: [
          _ProfileHeader(name: name, subtitle: phone, avatarUrl: avatarUrl),
          const SizedBox(height: 24),
          _ProfileSection(
            title: 'General',
            items: [
              _SectionItem(
                label: context.l10n.profileMessage,
                icon: Icons.mail_outline,
                onTap: () {
                  AppRouter.router.push(AppRouter.messagePath);
                },
              ),
              _SectionItem(
                label: context.l10n.profileChangePassword,
                icon: Icons.lock_reset,
                onTap: () {},
              ),
            ],
          ),
          const SizedBox(height: 16),
          _ProfileSection(
            title: 'Settings',
            items: [
              _SectionItem(
                label: context.l10n.profileLanguage,
                icon: Icons.language,
                onTap: () {
                  AppRouter.router.push(AppRouter.languagePath);
                },
              ),
              _SectionItem(
                label: context.l10n.profileUserAgreement,
                icon: Icons.description,
                onTap: () {
                  AppRouter.router.push(AppRouter.userAgreementPath);
                },
              ),
              _SectionItem(
                label: context.l10n.profileAbout,
                icon: Icons.info_outline,
                onTap: () {
                  AppRouter.router.push(AppRouter.aboutPath);
                },
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _ProfileHeader extends StatelessWidget {
  const _ProfileHeader({
    required this.name,
    required this.subtitle,
    this.avatarUrl,
  });

  final String name;
  final String subtitle;
  final String? avatarUrl;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        children: [
          _Avatar(avatarUrl: avatarUrl, displayName: name),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(name, style: theme.textTheme.titleMedium),
                const SizedBox(height: 4),
                Text(
                  subtitle,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: theme.textTheme.bodyMedium?.color?.withOpacity(0.7),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _Avatar extends StatelessWidget {
  const _Avatar({required this.avatarUrl, required this.displayName});

  final String? avatarUrl;
  final String displayName;

  @override
  Widget build(BuildContext context) {
    final sanitized = displayName.trim();
    final initials = sanitized.isNotEmpty
        ? sanitized.substring(0, 1).toUpperCase()
        : '?';
    if (avatarUrl != null && avatarUrl!.isNotEmpty) {
      return CircleAvatar(
        radius: 32,
        backgroundImage: NetworkImage(avatarUrl!),
        onBackgroundImageError: (_, __) {},
      );
    }
    return CircleAvatar(
      radius: 32,
      child: Text(initials, style: Theme.of(context).textTheme.titleMedium),
    );
  }
}

class _ProfileSection extends StatelessWidget {
  const _ProfileSection({required this.title, required this.items});

  final String title;
  final List<_SectionItem> items;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: theme.textTheme.titleSmall?.copyWith(
            color: theme.textTheme.titleSmall?.color?.withOpacity(0.7),
            letterSpacing: 0.2,
          ),
        ),
        const SizedBox(height: 12),
        Card(
          margin: EdgeInsets.zero,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          child: Column(
            children: [
              for (var i = 0; i < items.length; i++) ...[
                _ProfileTile(item: items[i]),
                if (i != items.length - 1)
                  const Divider(height: 1, indent: 16, endIndent: 16),
              ],
            ],
          ),
        ),
      ],
    );
  }
}

class _SectionItem {
  const _SectionItem({required this.label, required this.icon, this.onTap});

  final String label;
  final IconData icon;
  final VoidCallback? onTap;
}

class _ProfileTile extends StatelessWidget {
  const _ProfileTile({required this.item});

  final _SectionItem item;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return ListTile(
      leading: Icon(item.icon, color: theme.colorScheme.primary),
      title: Text(item.label),
      trailing: const Icon(Icons.chevron_right),
      onTap: item.onTap,
    );
  }
}
