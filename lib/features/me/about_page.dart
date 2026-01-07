import 'package:flutter/material.dart';

class AboutPage extends StatelessWidget {
  const AboutPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0D1B2A),
      body: SafeArea(
        child: Column(
          children: [
            // 顶部栏
            Padding(
              padding: const EdgeInsets.symmetric(
                horizontal: 16.0,
                vertical: 8,
              ),
              child: Row(
                children: [
                  IconButton(
                    icon: const Icon(Icons.arrow_back_ios, color: Colors.white),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
            ),

            // 中间 Logo 与标题
            const SizedBox(height: 40),
            Center(
              child: Column(
                children: [
                  // Logo
                  Container(
                    width: 80,
                    height: 80,
                    decoration: const BoxDecoration(
                      shape: BoxShape.circle,
                      color: Colors.transparent,
                    ),
                    child: const Icon(
                      Icons.info_outline,
                      color: Colors.white,
                      size: 56,
                    ),
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'TINBOT',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 22,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 1.2,
                    ),
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    'Version 2.0.0',
                    style: TextStyle(color: Colors.white70, fontSize: 14),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 40),

            // 更新记录区域
            Expanded(
              child: Container(
                decoration: const BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.only(
                    topLeft: Radius.circular(24),
                    topRight: Radius.circular(24),
                  ),
                ),
                child: ListView(
                  padding: const EdgeInsets.symmetric(
                    vertical: 16,
                    horizontal: 20,
                  ),
                  children: const [
                    VersionTile(
                      version: 'V2.0.0',
                      date: '2023-10-08',
                      description:
                          'The door of warehouse No. 5 cannot be closed, and there are no parts and cannot be repaired...',
                      isLatest: true,
                    ),
                    SizedBox(height: 16),
                    VersionTile(
                      version: 'V1.9.8',
                      date: '2023-09-06',
                      description: 'Fine-tune user experience',
                    ),
                    SizedBox(height: 16),
                    VersionTile(
                      version: 'V1.9.7',
                      date: '2023-08-04',
                      description: 'Fine-tune user experience',
                    ),
                    SizedBox(height: 16),
                    VersionTile(
                      version: 'V1.0.0',
                      date: '2023-09-03',
                      description: 'Optimize map UI',
                      isCritical: true,
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class VersionTile extends StatelessWidget {
  final String version;
  final String date;
  final String description;
  final bool isLatest;
  final bool isCritical;

  const VersionTile({
    super.key,
    required this.version,
    required this.date,
    required this.description,
    this.isLatest = false,
    this.isCritical = false,
  });

  @override
  Widget build(BuildContext context) {
    final color = isLatest
        ? Colors.red
        : isCritical
        ? Colors.red
        : Colors.green;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(Icons.circle, size: 10, color: color),
            const SizedBox(width: 8),
            Text(
              version,
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
            ),
            const Spacer(),
            Text(
              date,
              style: const TextStyle(color: Colors.grey, fontSize: 13),
            ),
          ],
        ),
        const SizedBox(height: 6),
        Text(
          description,
          style: const TextStyle(color: Colors.grey, fontSize: 14, height: 1.4),
        ),
      ],
    );
  }
}
