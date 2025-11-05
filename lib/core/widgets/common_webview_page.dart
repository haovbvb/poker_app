import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

/// Generic WebView page with optional actions and progress indicator.
class CommonWebViewPage extends StatefulWidget {
  const CommonWebViewPage({
    super.key,
    required this.initialUrl,
    this.title,
    this.javascriptMode = JavaScriptMode.unrestricted,
    this.onProgressChanged,
    this.onPageFinished,
    this.onWebResourceError,
    this.onNavigationRequest,
    this.actionsBuilder,
    this.showProgressBar = true,
  });

  final String initialUrl;
  final String? title;
  final JavaScriptMode javascriptMode;
  final ValueChanged<int>? onProgressChanged;
  final ValueChanged<String>? onPageFinished;
  final ValueChanged<WebResourceError>? onWebResourceError;
  final NavigationDecision Function(NavigationRequest request)?
  onNavigationRequest;
  final List<Widget> Function(WebViewController controller)? actionsBuilder;
  final bool showProgressBar;

  @override
  State<CommonWebViewPage> createState() => _CommonWebViewPageState();
}

class _CommonWebViewPageState extends State<CommonWebViewPage> {
  late final WebViewController _controller;
  double _progress = 0;
  String? _pageTitle;

  @override
  void initState() {
    super.initState();
    _controller = WebViewController()
      ..setJavaScriptMode(widget.javascriptMode)
      ..setNavigationDelegate(
        NavigationDelegate(
          onProgress: (value) {
            setState(() => _progress = value / 100);
            widget.onProgressChanged?.call(value);
          },
          onPageFinished: (url) {
            widget.onPageFinished?.call(url);
            if (widget.title == null) {
              _updatePageTitle();
            }
          },
          onWebResourceError: widget.onWebResourceError,
          onNavigationRequest: widget.onNavigationRequest,
        ),
      )
      ..loadRequest(Uri.parse(widget.initialUrl));
    if (widget.title == null) {
      _updatePageTitle();
    }
  }

  Future<void> _updatePageTitle() async {
    final title = await _controller.getTitle();
    if (!mounted) {
      return;
    }
    final trimmed = title?.trim();
    if (trimmed != null && trimmed.isNotEmpty && trimmed != _pageTitle) {
      setState(() => _pageTitle = trimmed);
    }
  }

  @override
  Widget build(BuildContext context) {
    final actions =
        widget.actionsBuilder?.call(_controller) ??
        <Widget>[
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => _controller.reload(),
          ),
        ];

    final resolvedTitle = widget.title ?? _pageTitle ?? '';

    return Scaffold(
      appBar: AppBar(
        title: resolvedTitle.isNotEmpty ? Text(resolvedTitle) : null,
        actions: actions,
        bottom: widget.showProgressBar && _progress < 1
            ? PreferredSize(
                preferredSize: const Size.fromHeight(2),
                child: LinearProgressIndicator(value: _progress),
              )
            : null,
      ),
      body: WebViewWidget(controller: _controller),
    );
  }
}
