import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:poker_app/app/app_router.dart';
import 'package:poker_app/features/login/providers/auth_controller.dart';

class SettingsDialog extends ConsumerWidget {
  const SettingsDialog({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final size = MediaQuery.sizeOf(context);
    final dialogWidth = size.width * 0.78;
    final dialogHeight = size.height * 0.72;

    return Dialog(
      insetPadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      backgroundColor: Colors.transparent,
      elevation: 0,
      child: ConstrainedBox(
        constraints: BoxConstraints(
          maxWidth: dialogWidth.clamp(320, 980),
          maxHeight: dialogHeight.clamp(260, 720),
        ),
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(6),
            border: Border.all(
              color: Colors.white.withValues(alpha: 0.25),
              width: 1,
            ),
            gradient: const LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [Color(0xFF1A4D6F), Color(0xFF0F2942)],
            ),
          ),
          child: Column(
            children: [
              // Header
              Container(
                height: 56,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                decoration: BoxDecoration(
                  borderRadius: const BorderRadius.only(
                    topLeft: Radius.circular(6),
                    topRight: Radius.circular(6),
                  ),
                  color: Colors.black.withValues(alpha: 0.25),
                ),
                child: Row(
                  children: [
                    const Spacer(),
                    const Text(
                      '设置',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const Spacer(),
                    IconButton(
                      onPressed: () => Navigator.of(context).pop(),
                      icon: const Icon(Icons.close, color: Colors.white),
                      splashRadius: 20,
                    ),
                  ],
                ),
              ),

              Expanded(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(24, 18, 24, 12),
                  child: Row(
                    children: [
                      // Left column
                      Expanded(
                        child: SingleChildScrollView(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const _SettingsRow(
                                label: '［音乐］',
                                trailing: _CheckBadge(checked: true),
                              ),
                              const SizedBox(height: 18),
                              const _SettingsRow(
                                label: '［音效］',
                                trailing: _CheckBadge(checked: true),
                              ),
                              const SizedBox(height: 18),
                              _GoldButton(text: '联系客服', onPressed: () {}),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(width: 20),
                      // Right column
                      Expanded(
                        child: SingleChildScrollView(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const _SettingsRow(
                                label: '［语言选择］',
                                trailing: _DropdownBadge(text: '中文'),
                              ),
                              const SizedBox(height: 14),
                              const SizedBox(height: 16),
                              Align(
                                alignment: Alignment.centerRight,
                                child: _OutlineButton(
                                  text: '退出登录',
                                  onPressed: () async {
                                    final notifier = ref.read(
                                      authNotifierProvider.notifier,
                                    );
                                    await notifier.clearSession();
                                    if (context.mounted) {
                                      Navigator.of(context).pop();
                                    }
                                    AppRouter.goLogin();
                                  },
                                ),
                              ),
                              const SizedBox(height: 16),
                              Align(
                                alignment: Alignment.centerRight,
                                child: _GoldButton(
                                  text: '公平性认证',
                                  onPressed: () {},
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),

              // Footer
              Container(
                height: 56,
                padding: const EdgeInsets.symmetric(horizontal: 20),
                decoration: BoxDecoration(
                  color: Colors.black.withValues(alpha: 0.18),
                  borderRadius: const BorderRadius.only(
                    bottomLeft: Radius.circular(6),
                    bottomRight: Radius.circular(6),
                  ),
                ),
                child: Row(
                  children: [
                    _FooterLink(text: '用户协议', onTap: () {}),
                    const Spacer(),
                    _FooterLink(text: '隐私政策', onTap: () {}),
                    const Spacer(),
                    _FooterLink(text: '删除账号', onTap: () {}),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _SettingsRow extends StatelessWidget {
  const _SettingsRow({required this.label, required this.trailing});

  final String label;
  final Widget trailing;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Text(
          label,
          style: const TextStyle(
            color: Color(0xFFB9D7FF),
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
        const Spacer(),
        trailing,
      ],
    );
  }
}

class _CheckBadge extends StatelessWidget {
  const _CheckBadge({required this.checked});

  final bool checked;

  @override
  Widget build(BuildContext context) {
    final bg = checked ? const Color(0xFF10B259) : const Color(0xFF3A4A5C);
    final icon = checked ? Icons.check : Icons.check;
    final iconColor = checked ? Colors.white : Colors.white54;
    return Container(
      width: 20,
      height: 20,
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Icon(icon, color: iconColor, size: 14),
    );
  }
}

class _ArrowBadge extends StatelessWidget {
  const _ArrowBadge({required this.expanded});

  final bool expanded;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 42,
      height: 42,
      decoration: BoxDecoration(
        color: const Color(0xFF3A4A5C),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Icon(
        expanded ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down,
        color: Colors.white54,
        size: 30,
      ),
    );
  }
}

class _DropdownBadge extends StatelessWidget {
  const _DropdownBadge({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          text,
          style: const TextStyle(
            color: Color(0xFFB9D7FF),
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(width: 10),
        const _ArrowBadge(expanded: true),
      ],
    );
  }
}

class _OutlineButton extends StatelessWidget {
  const _OutlineButton({required this.text, required this.onPressed});

  final String text;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 220,
      height: 36,
      child: OutlinedButton(
        onPressed: onPressed,
        style: OutlinedButton.styleFrom(
          foregroundColor: Colors.white,
          side: BorderSide(
            color: Colors.white.withValues(alpha: 0.25),
            width: 1,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(18),
          ),
          backgroundColor: Colors.black.withValues(alpha: 0.2),
        ),
        child: Text(
          text,
          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w400),
        ),
      ),
    );
  }
}

class _GoldButton extends StatelessWidget {
  const _GoldButton({required this.text, required this.onPressed});

  final String text;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 240,
      height: 40,
      child: ElevatedButton(
        onPressed: onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFFD8C06A),
          foregroundColor: Colors.black,
          elevation: 0,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
        ),
        child: Text(
          text,
          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
        ),
      ),
    );
  }
}

class _FooterLink extends StatelessWidget {
  const _FooterLink({required this.text, required this.onTap});

  final String text;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Text(
        text,
        style: const TextStyle(
          color: Color(0xFFB9D7FF),
          fontSize: 16,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}
