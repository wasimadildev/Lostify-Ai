import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/design_system/app_colors.dart';
import '../../../../core/design_system/app_radius.dart';
import '../../../../core/design_system/app_spacing.dart';
import '../../../../core/widgets/lostify_button.dart';
import '../../../../core/widgets/lostify_text_field.dart';
import '../../data/mock_authentication_repository.dart';
import '../../domain/authentication_repository.dart';

class LoginPage extends StatefulWidget {
  const LoginPage({super.key, this.repository = const MockAuthenticationRepository()});

  final AuthenticationRepository repository;

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> with SingleTickerProviderStateMixin {
  late final TabController _tabController;
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _phoneController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _obscurePassword = true;
  bool _loading = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this)
      ..addListener(() {
        if (!_tabController.indexIsChanging && mounted) {
          setState(() => _errorMessage = null);
        }
      });
  }

  @override
  void dispose() {
    _tabController.dispose();
    _emailController.dispose();
    _phoneController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _signIn() async {
    FocusManager.instance.primaryFocus?.unfocus();
    if (!(_formKey.currentState?.validate() ?? false)) return;
    setState(() {
      _loading = true;
      _errorMessage = null;
    });

    try {
      if (_tabController.index == 0) {
        await widget.repository.signInWithEmail(
          email: _emailController.text.trim(),
          password: _passwordController.text,
        );
      } else {
        await widget.repository.signInWithPhone(
          phone: _phoneController.text.trim(),
          password: _passwordController.text,
        );
      }
      if (!mounted) return;
      context.go('/home');
    } on AuthenticationException catch (error) {
      if (mounted) setState(() => _errorMessage = error.message);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _socialSignIn(String provider) async {
    setState(() {
      _loading = true;
      _errorMessage = null;
    });
    try {
      await widget.repository.signInWithProvider(provider);
      if (!mounted) return;
      context.go('/home');
    } on AuthenticationException catch (error) {
      if (mounted) setState(() => _errorMessage = error.message);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  String? _emailValidator(String? value) {
    if (value == null || value.trim().isEmpty) return 'Enter your email address';
    if (!RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch(value.trim())) {
      return 'Enter a valid email address';
    }
    return null;
  }

  String? _phoneValidator(String? value) {
    if (value == null || value.trim().isEmpty) return 'Enter your phone number';
    if (value.replaceAll(RegExp(r'\D'), '').length < 7) return 'Enter a valid phone number';
    return null;
  }

  String? _passwordValidator(String? value) {
    if (value == null || value.isEmpty) return 'Enter your password';
    if (value.length < 6) return 'Use at least 6 characters';
    return null;
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
                Text('Welcome back', style: Theme.of(context).textTheme.headlineMedium),
                const SizedBox(height: AppSpacing.sm),
                Text(
                  'Find your way back to what matters.',
                  style: Theme.of(context).textTheme.bodyLarge?.copyWith(color: AppColors.textSecondary),
                ),
                const SizedBox(height: AppSpacing.xxl),
                Container(
                  padding: const EdgeInsets.all(AppSpacing.xs),
                  decoration: BoxDecoration(
                    color: AppColors.surface,
                    borderRadius: BorderRadius.circular(AppRadius.xl),
                    border: Border.all(color: AppColors.border),
                  ),
                  child: TabBar(
                    controller: _tabController,
                    dividerColor: Colors.transparent,
                    indicator: BoxDecoration(
                      color: AppColors.primary,
                      borderRadius: BorderRadius.circular(AppRadius.l),
                    ),
                    indicatorSize: TabBarIndicatorSize.tab,
                    labelColor: Colors.white,
                    unselectedLabelColor: AppColors.textSecondary,
                    tabs: const [Tab(text: 'Email'), Tab(text: 'Phone')],
                  ),
                ),
                const SizedBox(height: AppSpacing.xxl),
                AnimatedBuilder(
                  animation: _tabController,
                  builder: (context, child) => _AuthenticationFields(
                    isPhone: _tabController.index == 1,
                    emailController: _emailController,
                    phoneController: _phoneController,
                    passwordController: _passwordController,
                    obscurePassword: _obscurePassword,
                    onTogglePassword: () => setState(() => _obscurePassword = !_obscurePassword),
                    emailValidator: _emailValidator,
                    phoneValidator: _phoneValidator,
                    passwordValidator: _passwordValidator,
                  ),
                ),
                Align(
                  alignment: Alignment.centerRight,
                  child: TextButton(
                    onPressed: _loading
                        ? null
                        : () => ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(content: Text('Password reset is available in the next release.')),
                            ),
                    child: const Text('Forgot password?'),
                  ),
                ),
                if (_errorMessage != null) ...[
                  const SizedBox(height: AppSpacing.sm),
                  _ErrorBanner(message: _errorMessage!),
                ],
                const SizedBox(height: AppSpacing.lg),
                LostifyButton(
                  onPressed: _signIn,
                  label: 'Sign in',
                  loading: _loading,
                  width: double.infinity,
                ),
                const SizedBox(height: AppSpacing.xxl),
                Row(
                  children: [
                    const Expanded(child: Divider()),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md),
                      child: Text('or continue with', style: Theme.of(context).textTheme.labelMedium),
                    ),
                    const Expanded(child: Divider()),
                  ],
                ),
                const SizedBox(height: AppSpacing.lg),
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: _loading ? null : () => _socialSignIn('Google'),
                        icon: const Icon(Icons.g_mobiledata_rounded, size: 28),
                        label: const Text('Google'),
                      ),
                    ),
                    const SizedBox(width: AppSpacing.md),
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: _loading ? null : () => _socialSignIn('Facebook'),
                        icon: const Icon(Icons.facebook_rounded, size: 22),
                        label: const Text('Facebook'),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: AppSpacing.xxl),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text('New to Lostify?', style: Theme.of(context).textTheme.bodyMedium),
                    TextButton(
                      onPressed: _loading ? null : () => context.push('/signup'),
                      child: const Text('Create account'),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _AuthenticationFields extends StatelessWidget {
  const _AuthenticationFields({
    required this.isPhone,
    required this.emailController,
    required this.phoneController,
    required this.passwordController,
    required this.obscurePassword,
    required this.onTogglePassword,
    required this.emailValidator,
    required this.phoneValidator,
    required this.passwordValidator,
  });

  final bool isPhone;
  final TextEditingController emailController;
  final TextEditingController phoneController;
  final TextEditingController passwordController;
  final bool obscurePassword;
  final VoidCallback onTogglePassword;
  final String? Function(String?) emailValidator;
  final String? Function(String?) phoneValidator;
  final String? Function(String?) passwordValidator;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        LostifyTextField(
          label: isPhone ? 'Phone number' : 'Email address',
          hintText: isPhone ? '+1 555 000 0000' : 'you@example.com',
          controller: isPhone ? phoneController : emailController,
          keyboardType: isPhone ? TextInputType.phone : TextInputType.emailAddress,
          prefixIcon: isPhone ? Icons.phone_outlined : Icons.email_outlined,
          validator: isPhone ? phoneValidator : emailValidator,
        ),
        const SizedBox(height: AppSpacing.lg),
        LostifyTextField(
          label: 'Password',
          hintText: 'At least 6 characters',
          controller: passwordController,
          obscureText: obscurePassword,
          prefixIcon: Icons.lock_outline_rounded,
          validator: passwordValidator,
          suffixIcon: IconButton(
            onPressed: onTogglePassword,
            icon: Icon(
              obscurePassword ? Icons.visibility_rounded : Icons.visibility_off_rounded,
              color: AppColors.textSecondary,
            ),
            tooltip: obscurePassword ? 'Show password' : 'Hide password',
          ),
        ),
      ],
    );
  }
}

class _ErrorBanner extends StatelessWidget {
  const _ErrorBanner({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: AppColors.error.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(AppRadius.m),
        border: Border.all(color: AppColors.error.withValues(alpha: 0.24)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.info_outline_rounded, color: AppColors.error),
          const SizedBox(width: AppSpacing.sm),
          Expanded(
            child: Text(message, style: const TextStyle(color: AppColors.error)),
          ),
        ],
      ),
    );
  }
}
