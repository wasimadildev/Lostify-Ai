import 'dart:async';

import '../domain/authentication_repository.dart';

class MockAuthenticationRepository implements AuthenticationRepository {
  const MockAuthenticationRepository();

  @override
  Future<void> signInWithEmail({required String email, required String password}) {
    return _completeRequest(email.contains('@') && password.length >= 6);
  }

  @override
  Future<void> signInWithPhone({required String phone, required String password}) {
    return _completeRequest(phone.replaceAll(RegExp(r'\D'), '').length >= 7 && password.length >= 6);
  }

  @override
  Future<void> signInWithProvider(String provider) {
    return _completeRequest(provider.isNotEmpty);
  }

  @override
  Future<void> signUp({required String email, required String password}) {
    return _completeRequest(email.contains('@') && password.length >= 6);
  }

  Future<void> _completeRequest(bool isValid) async {
    await Future<void>.delayed(const Duration(milliseconds: 700));
    if (!isValid) {
      throw const AuthenticationException('We could not verify those details. Please try again.');
    }
  }
}

class AuthenticationException implements Exception {
  const AuthenticationException(this.message);

  final String message;

  @override
  String toString() => message;
}