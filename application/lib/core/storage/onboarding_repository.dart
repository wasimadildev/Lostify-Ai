import 'package:shared_preferences/shared_preferences.dart';

abstract interface class OnboardingRepository {
  Future<bool> hasCompletedOnboarding();

  Future<void> markOnboardingCompleted();
}

class SharedPreferencesOnboardingRepository implements OnboardingRepository {
  static const _completionKey = 'onboarding_completed';

  @override
  Future<bool> hasCompletedOnboarding() async {
    final preferences = await SharedPreferences.getInstance();
    return preferences.getBool(_completionKey) ?? false;
  }

  @override
  Future<void> markOnboardingCompleted() async {
    final preferences = await SharedPreferences.getInstance();
    await preferences.setBool(_completionKey, true);
  }
}