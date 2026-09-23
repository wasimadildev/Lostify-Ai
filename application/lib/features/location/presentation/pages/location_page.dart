import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/design_system/app_colors.dart';
import '../../../../core/design_system/app_radius.dart';
import '../../../../core/design_system/app_spacing.dart';
import '../../../../core/widgets/lostify_button.dart';
import '../../../../core/widgets/lostify_card.dart';

class LocationPage extends StatefulWidget {
  const LocationPage({super.key});

  @override
  State<LocationPage> createState() => _LocationPageState();
}

class _LocationPageState extends State<LocationPage> {
  _LocationOption? _selectedLocation;
  bool _loadingLocation = false;
  String? _locationError;

  final _locations = const [
    _LocationOption(
      title: 'Shifa Tameer-e-Millat University',
      subtitle: 'Islamabad, Pakistan',
      detail: 'Main gate · 15 Aug 2026, 10:30 AM',
    ),
    _LocationOption(
      title: 'F-10 Park',
      subtitle: 'Islamabad, Pakistan',
      detail: 'Jogging track · 14 Aug 2026, 5:45 PM',
    ),
  ];

  Future<void> _useCurrentLocation() async {
    setState(() {
      _loadingLocation = true;
      _locationError = null;
    });
    await Future<void>.delayed(const Duration(milliseconds: 800));
    if (!mounted) return;
    setState(() {
      _selectedLocation = _locations.first;
      _loadingLocation = false;
    });
  }

  Future<void> _chooseOnMap() async {
    final selected = await showModalBottomSheet<_LocationOption>(
      context: context,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(AppSpacing.lg, 0, AppSpacing.lg, AppSpacing.lg),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Choose a nearby place', style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: AppSpacing.sm),
              ..._locations.map(
                (location) => ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.place_outlined, color: AppColors.primary),
                  title: Text(location.title),
                  subtitle: Text(location.subtitle),
                  onTap: () => Navigator.of(context).pop(location),
                ),
              ),
            ],
          ),
        ),
      ),
    );
    if (selected != null && mounted) setState(() => _selectedLocation = selected);
  }

  void _continue() {
    if (_selectedLocation == null) {
      setState(() => _locationError = 'Choose a location to continue.');
      return;
    }
    context.push('/report/processing');
  }

  @override
  Widget build(BuildContext context) {
    final selected = _selectedLocation;
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(onPressed: () => context.pop(), icon: const Icon(Icons.arrow_back_rounded)),
        title: const Text('Choose location'),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: AppSpacing.lg),
            child: Center(child: Text('2 of 2', style: Theme.of(context).textTheme.labelMedium)),
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.fromLTRB(AppSpacing.lg, AppSpacing.sm, AppSpacing.lg, AppSpacing.xxl),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Where did it happen?', style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: AppSpacing.xs),
            Text(
              'Use the map or pick a familiar place nearby.',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: AppColors.textSecondary),
            ),
            const SizedBox(height: AppSpacing.lg),
            Expanded(
              child: LostifyCard(
                padding: EdgeInsets.zero,
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(AppRadius.l),
                  child: Stack(
                    children: [
                      Positioned.fill(child: CustomPaint(painter: _MapPainter())),
                      Center(
                        child: Container(
                          width: 56,
                          height: 56,
                          decoration: BoxDecoration(
                            color: AppColors.primary,
                            shape: BoxShape.circle,
                            boxShadow: [
                              BoxShadow(color: AppColors.primary.withValues(alpha: 0.3), blurRadius: 18, offset: const Offset(0, 8)),
                            ],
                          ),
                          child: const Icon(Icons.location_on_rounded, color: Colors.white, size: 28),
                        ),
                      ),
                      if (selected != null)
                        Positioned(
                          left: AppSpacing.md,
                          right: AppSpacing.md,
                          bottom: AppSpacing.md,
                          child: LostifyCard(
                            padding: const EdgeInsets.all(AppSpacing.md),
                            child: Row(
                              children: [
                                const Icon(Icons.check_circle_rounded, color: AppColors.success),
                                const SizedBox(width: AppSpacing.sm),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(selected.title, style: Theme.of(context).textTheme.titleSmall),
                                      Text(selected.subtitle, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppColors.textSecondary)),
                                    ],
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
            ),
            const SizedBox(height: AppSpacing.lg),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _loadingLocation ? null : _useCurrentLocation,
                    icon: _loadingLocation
                        ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                        : const Icon(Icons.my_location_rounded),
                    label: Text(_loadingLocation ? 'Locating...' : 'Current location'),
                  ),
                ),
                const SizedBox(width: AppSpacing.sm),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _chooseOnMap,
                    icon: const Icon(Icons.map_outlined),
                    label: const Text('Choose on map'),
                  ),
                ),
              ],
            ),
            if (_locationError != null) ...[
              const SizedBox(height: AppSpacing.sm),
              Text(_locationError!, style: const TextStyle(color: AppColors.error)),
            ],
            const SizedBox(height: AppSpacing.lg),
            LostifyButton(onPressed: _continue, label: 'Find matches', width: double.infinity),
          ],
        ),
      ),
    );
  }
}

class _LocationOption {
  const _LocationOption({required this.title, required this.subtitle, required this.detail});

  final String title;
  final String subtitle;
  final String detail;
}

class _MapPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final blockPaint = Paint()..color = const Color(0xFFBFD8FF).withValues(alpha: 0.5);
    for (var index = 0; index < 12; index++) {
      final rect = Rect.fromLTWH(20 + index * 26, 30 + (index % 3) * 25, 70, 40);
      canvas.drawRect(rect, blockPaint);
    }
    final roadPaint = Paint()
      ..color = const Color(0xFF8AD6B4).withValues(alpha: 0.38)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 14;
    final road = Path()
      ..moveTo(0, size.height * 0.75)
      ..lineTo(size.width * 0.2, size.height * 0.7)
      ..lineTo(size.width * 0.36, size.height * 0.82)
      ..lineTo(size.width * 0.62, size.height * 0.66)
      ..lineTo(size.width * 0.84, size.height * 0.78)
      ..lineTo(size.width, size.height * 0.7);
    canvas.drawPath(road, roadPaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
