abstract interface class AuthenticationRepository {
  Future<void> signInWithEmail({required String email, required String password});

  Future<void> signInWithPhone({required String phone, required String password});

  Future<void> signInWithProvider(String provider);

  Future<void> signUp({required String email, required String password});
}