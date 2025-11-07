import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:merchant_app/app/app_router.dart';
import 'package:merchant_app/app/styles/colors.dart';
import 'package:merchant_app/core/utils/context_extensions.dart';
import 'package:merchant_app/features/login/providers/auth_controller.dart';

class LoginPage extends ConsumerStatefulWidget {
  const LoginPage({super.key});

  @override
  ConsumerState<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends ConsumerState<LoginPage> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _obscurePassword = true;
  bool _isSubmitting = false;
  bool _agreedToTerms = false;

  @override
  void dispose() {
    _nameController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    ref.watch(authNotifierProvider);

    return Scaffold(
      backgroundColor: Colors.white,
      body: GestureDetector(
        onTap: () => FocusScope.of(context).unfocus(),
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const SizedBox(height: 60),
                  Center(
                    child: Container(
                      width: 80,
                      height: 80,
                      decoration: BoxDecoration(
                        color: Colors.white,
                        shape: BoxShape.circle,
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(0.06),
                            blurRadius: 12,
                            offset: const Offset(0, 4),
                          ),
                        ],
                      ),
                      child: Image.asset(
                        'assets/images/logo.png',
                        fit: BoxFit.contain,
                        errorBuilder: (_, __, ___) => Icon(
                          Icons.eco,
                          color: AppColors.primaryColor,
                          size: 48,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),
                  Text(
                    'TINBOT Merchant',
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                      color: AppColors.black09Text,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 0.5,
                    ),
                  ),
                  const SizedBox(height: 60),
                  _AccountField(controller: _nameController),
                  const SizedBox(height: 24),
                  _PasswordField(
                    controller: _passwordController,
                    obscurePassword: _obscurePassword,
                    onToggleVisibility: () => setState(() {
                      _obscurePassword = !_obscurePassword;
                    }),
                  ),
                  const SizedBox(height: 32),
                  _LoginButton(
                    isSubmitting: _isSubmitting,
                    agreedToTerms: _agreedToTerms,
                    onPressed: _onSubmit,
                  ),
                  const SizedBox(height: 20),
                  _TermsCheckbox(
                    agreed: _agreedToTerms,
                    onChanged: (value) => setState(() {
                      _agreedToTerms = value ?? false;
                    }),
                  ),
                  const SizedBox(height: 24),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _onSubmit() async {
    if (!_agreedToTerms) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please agree to the terms first')),
      );
      return;
    }
    if (!_formKey.currentState!.validate()) {
      return;
    }

    final name = _nameController.text.trim();
    final password = _passwordController.text.trim();
    final notifier = ref.read(authNotifierProvider.notifier);

    setState(() => _isSubmitting = true);
    try {
      await notifier.login(name: name, password: password);
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }
}

class _AccountField extends StatelessWidget {
  const _AccountField({required this.controller});

  final TextEditingController controller;

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      controller: controller,
      keyboardType: TextInputType.emailAddress,
      style: TextStyle(color: AppColors.black09Text, fontSize: 16),
      decoration: InputDecoration(
        hintText: 'Please enter account',
        hintStyle: TextStyle(color: AppColors.black04Text, fontSize: 16),
        prefixIcon: Icon(
          Icons.person_outline,
          color: AppColors.black05Text,
          size: 22,
        ),
        border: UnderlineInputBorder(
          borderSide: BorderSide(color: AppColors.black02Text),
        ),
        enabledBorder: UnderlineInputBorder(
          borderSide: BorderSide(color: AppColors.black02Text),
        ),
        focusedBorder: UnderlineInputBorder(
          borderSide: BorderSide(color: AppColors.primaryColor, width: 1.5),
        ),
        contentPadding: const EdgeInsets.symmetric(vertical: 16),
      ),
      validator: (value) {
        if (value == null || value.isEmpty) {
          return 'Account is required';
        }
        return null;
      },
    );
  }
}

class _PasswordField extends StatelessWidget {
  const _PasswordField({
    required this.controller,
    required this.obscurePassword,
    required this.onToggleVisibility,
  });

  final TextEditingController controller;
  final bool obscurePassword;
  final VoidCallback onToggleVisibility;

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      controller: controller,
      obscureText: obscurePassword,
      style: TextStyle(color: AppColors.black09Text, fontSize: 16),
      decoration: InputDecoration(
        hintText: 'Please enter password',
        hintStyle: TextStyle(color: AppColors.black04Text, fontSize: 16),
        prefixIcon: Icon(
          Icons.lock_outline,
          color: AppColors.black05Text,
          size: 22,
        ),
        suffixIcon: IconButton(
          icon: Icon(
            obscurePassword
                ? Icons.visibility_off_outlined
                : Icons.visibility_outlined,
            color: AppColors.black04Text,
            size: 22,
          ),
          onPressed: onToggleVisibility,
        ),
        border: UnderlineInputBorder(
          borderSide: BorderSide(color: AppColors.black02Text),
        ),
        enabledBorder: UnderlineInputBorder(
          borderSide: BorderSide(color: AppColors.black02Text),
        ),
        focusedBorder: UnderlineInputBorder(
          borderSide: BorderSide(color: AppColors.primaryColor, width: 1.5),
        ),
        contentPadding: const EdgeInsets.symmetric(vertical: 16),
      ),
      validator: (value) {
        if (value == null || value.isEmpty) {
          return 'Password is required';
        }
        if (value.length < 6) {
          return 'Password must be at least 6 characters';
        }
        return null;
      },
    );
  }
}

class _LoginButton extends StatelessWidget {
  const _LoginButton({
    required this.isSubmitting,
    required this.agreedToTerms,
    required this.onPressed,
  });

  final bool isSubmitting;
  final bool agreedToTerms;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    final isActive = agreedToTerms && !isSubmitting;
    return SizedBox(
      height: 52,
      child: ElevatedButton(
        onPressed: isActive ? onPressed : null,
        style: ElevatedButton.styleFrom(
          backgroundColor: isActive
              ? AppColors.primaryColor
              : AppColors.primaryColor.withOpacity(0.4),
          foregroundColor: Colors.white,
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(26),
          ),
          disabledBackgroundColor: AppColors.primaryColor.withOpacity(0.4),
          disabledForegroundColor: Colors.white,
        ),
        child: isSubmitting
            ? const SizedBox(
                width: 24,
                height: 24,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                ),
              )
            : Text(
                agreedToTerms ? 'Confirm' : 'Log In',
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 0.5,
                ),
              ),
      ),
    );
  }
}

class _TermsCheckbox extends StatelessWidget {
  const _TermsCheckbox({required this.agreed, required this.onChanged});

  final bool agreed;
  final ValueChanged<bool?> onChanged;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        SizedBox(
          width: 24,
          height: 24,
          child: Checkbox(
            value: agreed,
            onChanged: onChanged,
            activeColor: AppColors.primaryColor,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(4),
            ),
            side: BorderSide(
              color: agreed ? AppColors.primaryColor : AppColors.black03Text,
              width: 1.5,
            ),
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: RichText(
            text: TextSpan(
              style: TextStyle(
                color: AppColors.black06Text,
                fontSize: 14,
                height: 1.4,
              ),
              children: [
                const TextSpan(text: 'I have read, and agree to '),
                TextSpan(
                  text: 'User Agreement',
                  style: const TextStyle(
                    color: Colors.blue,
                    decoration: TextDecoration.none,
                  ),
                  recognizer: TapGestureRecognizer()
                    ..onTap = () {
                      AppRouter.router.push(AppRouter.userAgreementPath);
                    },
                ),
                const TextSpan(text: ' and '),
                TextSpan(
                  text: 'Privacy Policy',
                  style: const TextStyle(
                    color: Colors.blue,
                    decoration: TextDecoration.none,
                  ),
                  recognizer: TapGestureRecognizer()
                    ..onTap = () {
                      // Navigate to privacy policy
                    },
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
