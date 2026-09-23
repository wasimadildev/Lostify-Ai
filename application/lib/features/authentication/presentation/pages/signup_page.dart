import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/design_system/app_colors.dart';
import '../../../../core/design_system/app_spacing.dart';
import '../../../../core/widgets/lostify_button.dart';
import '../../../../core/widgets/lostify_text_field.dart';
import '../../data/mock_authentication_repository.dart';
import '../../domain/authentication_repository.dart';

class SignupPage extends StatefulWidget {
  const SignupPage({super.key, this.repository = const MockAuthenticationRepository()});

  final AuthenticationRepository repository;

  @override
  State<SignupPage> createState() => _SignupPageState();
}

class _SignupPageState extends State<SignupPage> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  bool _obscurePassword = true;
  bool _obscureConfirmation = true;
  bool _loading = false;
  String? _errorMessage;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  String? _emailValidator(String? value) {
    if (value == null || value.trim().isEmpty) return 'Enter your email address';
    if (!RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch(value.trim())) return 'Enter a valid email address';
    return null;
  }

  String? _passwordValidator(String? value) {
    if (value == null || value.isEmpty) return 'Create a password';
    if (value.length < 6) return 'Use at least 6 characters';
    return null;
  }

  String? _confirmationValidator(String? value) {
    if (value != _passwordController.text) return 'Passwords do not match';
    return null;
  }

  Future<void> _createAccount() async {
    FocusManager.instance.primaryFocus?.unfocus();
    if (!(_formKey.currentState?.validate() ?? false)) return;
    setState(() {
      _loading = true;
      _errorMessage = null;
    });
    try {
      await widget.repository.signUp(
        email: _emailController.text.trim(),
        password: _passwordController.text,
      );
      if (!mounted) return;
      context.go('/home');
    } on AuthenticationException catch (error) {
      if (mounted) setState(() => _errorMessage = error.message);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(AppSpacing.lg, AppSpacing.sm, AppSpacing.lg, AppSpacing.lg),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                IconButton(
                  onPressed: _loading ? null : () => context.pop(),
                  icon: const Icon(Icons.arrow_back_ios_new_rounded),
                  style: IconButton.styleFrom(
                    backgroundColor: AppColors.surface,
                    side: const BorderSide(color: AppColors.border),
                  ),
                ),
                const SizedBox(height: AppSpacing.xxl),
                Text('Create your account', style: Theme.of(context).textTheme.headlineMedium),
                const SizedBox(height: AppSpacing.sm),
                Text(
                  'Join a community built to help things find their way home.',
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(color: AppColors.textSecondary),
                ),
                const SizedBox(height: AppSpacing.xxxl),
                LostifyTextField(
                  label: 'Email address',
                  hintText: 'you@example.com',
                  controller: _emailController,
                  keyboardType: TextInputType.emailAddress,
                  prefixIcon: Icons.email_outlined,
                  validator: _emailValidator,
                ),
                const SizedBox(height: AppSpacing.lg),
                LostifyTextField(
                  label: 'Password',
                  hintText: 'At least 6 characters',
                  controller: _passwordController,
                  obscureText: _obscurePassword,
                  prefixIcon: Icons.lock_outline_rounded,
                  validator: _passwordValidator,
                  suffixIcon: IconButton(
                    onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                    icon: Icon(
                      _obscurePassword ? Icons.visibility_rounded : Icons.visibility_off_rounded,
                      color: AppColors.textSecondary,
                    ),
                  ),
                ),
                const SizedBox(height: AppSpacing.lg),
                LostifyTextField(
                  label: 'Confirm password',
                  hintText: 'Repeat your password',
                  controller: _confirmPasswordController,
                  obscureText: _obscureConfirmation,
                  prefixIcon: Icons.verified_user_outlined,
                  validator: _confirmationValidator,
                  suffixIcon: IconButton(
                    onPressed: () => setState(() => _obscureConfirmation = !_obscureConfirmation),
                    icon: Icon(
                      _obscureConfirmation ? Icons.visibility_rounded : Icons.visibility_off_rounded,
                      color: AppColors.textSecondary,
                    ),
                  ),
                ),
                if (_errorMessage != null) ...[
                  const SizedBox(height: AppSpacing.lg),
                  Text(_errorMessage!, style: const TextStyle(color: AppColors.error)),
                ],
                const SizedBox(height: AppSpacing.xxxl),
                LostifyButton(
                  onPressed: _createAccount,
                  label: 'Create account',
                  loading: _loading,
                  width: double.infinity,
                ),
                const SizedBox(height: AppSpacing.lg),
                Center(
                  child: TextButton(
                    onPressed: _loading ? null : () => context.pop(),
                    child: const Text('Already have an account? Sign in'),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
