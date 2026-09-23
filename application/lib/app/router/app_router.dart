import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../shell/app_shell.dart';
import '../../features/ai_processing/presentation/pages/ai_processing_page.dart';
import '../../features/authentication/presentation/pages/login_page.dart';
import '../../features/authentication/presentation/pages/signup_page.dart';
import '../../features/chat/presentation/pages/chat_page.dart';
import '../../features/communities/presentation/pages/communities_page.dart';
import '../../features/communities/presentation/pages/community_details_page.dart';
import '../../features/communities/presentation/pages/community_post_page.dart';
import '../../features/home/presentation/pages/home_page.dart';
import '../../features/location/presentation/pages/location_page.dart';
import '../../features/matches/presentation/pages/matches_page.dart';
import '../../features/onboarding/presentation/pages/onboarding_page.dart';
import '../../features/reports/presentation/pages/report_details_page.dart';
import '../../features/reports/presentation/pages/report_page.dart';
import '../../features/shell/presentation/pages/shell_placeholder_page.dart';
import '../../features/splash/presentation/pages/splash_page.dart';

final appRouter = GoRouter(
  initialLocation: '/splash',
  routes: [
    GoRoute(path: '/splash', builder: (context, state) => const SplashPage()),
    GoRoute(path: '/onboarding', builder: (context, state) => const OnboardingPage()),
    GoRoute(path: '/login', builder: (context, state) => const LoginPage()),
    GoRoute(path: '/signup', builder: (context, state) => const SignupPage()),
    StatefulShellRoute.indexedStack(
      builder: (context, state, navigationShell) => LostifyAppShell(
        navigationShell: navigationShell,
      ),
      branches: [
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/home',
              builder: (context, state) => const HomePage(),
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/search',
              builder: (context, state) => const ShellPlaceholderPage(
                title: 'Search',
                icon: Icons.search_rounded,
              ),
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/create',
              builder: (context, state) => const ShellPlaceholderPage(
                title: 'Create',
                icon: Icons.add_circle_outline_rounded,
              ),
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/alerts',
              builder: (context, state) => const ShellPlaceholderPage(
                title: 'Alerts',
                icon: Icons.notifications_none_rounded,
              ),
            ),
          ],
        ),
        StatefulShellBranch(
          routes: [
            GoRoute(
              path: '/profile',
              builder: (context, state) => const ShellPlaceholderPage(
                title: 'Profile',
                icon: Icons.person_outline_rounded,
              ),
            ),
          ],
        ),
      ],
    ),
    GoRoute(path: '/report', builder: (context, state) => const ReportPage()),
    GoRoute(path: '/report/location', builder: (context, state) => const LocationPage()),
    GoRoute(path: '/report/processing', builder: (context, state) => const AiProcessingPage()),
    GoRoute(path: '/report/matches', builder: (context, state) => const MatchesPage()),
    GoRoute(path: '/report/details', builder: (context, state) => const ReportDetailsPage()),
    GoRoute(path: '/chat', builder: (context, state) => const ChatPage()),
    GoRoute(path: '/communities', builder: (context, state) => const CommunitiesPage()),
    GoRoute(
      path: '/community/:id',
      builder: (context, state) => CommunityDetailsPage(
        communityId: state.pathParameters['id'] ?? 'islamabad',
      ),
    ),
    GoRoute(
      path: '/community/:communityId/post/new',
      builder: (context, state) => CommunityPostPage(
        communityId: state.pathParameters['communityId'] ?? 'islamabad',
        postId: 'new',
      ),
    ),
    GoRoute(
      path: '/community/:communityId/post/:postId',
      builder: (context, state) => CommunityPostPage(
        communityId: state.pathParameters['communityId'] ?? 'islamabad',
        postId: state.pathParameters['postId'] ?? 'wallet',
      ),
    ),
    GoRoute(
      path: '/settings',
      builder: (context, state) => const ShellPlaceholderPage(
        title: 'Settings',
        icon: Icons.settings_outlined,
      ),
    ),
  ],
);
