import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/design_system/app_colors.dart';
import '../../../../core/design_system/app_radius.dart';
import '../../../../core/design_system/app_spacing.dart';
import '../../../../core/widgets/lostify_button.dart';
import '../../../../core/widgets/lostify_text_field.dart';

class ReportPage extends StatefulWidget {
  const ReportPage({super.key});

  @override
  State<ReportPage> createState() => _ReportPageState();
}

class _ReportPageState extends State<ReportPage> {
  final _formKey = GlobalKey<FormState>();
  final _titleController = TextEditingController();
  final _descriptionController = TextEditingController();
  String _reportType = 'Lost';
  String _category = 'Item';
  bool _loading = false;
  final List<String> _photos = [
    'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=900&q=80',
  ];

  @override
  void dispose() {
    _titleController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  Future<void> _continue() async {
    if (!(_formKey.currentState?.validate() ?? false) || _photos.isEmpty) {
      if (_photos.isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Add at least one photo to continue.')),
        );
      }
      return;
    }
    setState(() => _loading = true);
    await Future<void>.delayed(const Duration(milliseconds: 350));
    if (!mounted) return;
    context.push('/report/location');
  }

  void _addPhoto() {
    const samplePhotos = [
      'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=900&q=80',
      'https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=900&q=80',
    ];
    if (_photos.length >= 3) return;
    setState(() => _photos.add(samplePhotos[_photos.length % samplePhotos.length]));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(onPressed: () => context.pop(), icon: const Icon(Icons.arrow_back_rounded)),
        title: const Text('Create a report'),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: AppSpacing.lg),
            child: Center(child: Text('1 of 2', style: Theme.of(context).textTheme.labelMedium)),
          ),
        ],
      ),
      body: Form(
        key: _formKey,
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(AppSpacing.lg, AppSpacing.sm, AppSpacing.lg, AppSpacing.xxl),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('What happened?', style: Theme.of(context).textTheme.headlineSmall),
              const SizedBox(height: AppSpacing.xs),
              Text(
                'A few clear details help Lostify find the strongest matches.',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: AppColors.textSecondary),
              ),
              const SizedBox(height: AppSpacing.xxl),
              Text('Report type', style: Theme.of(context).textTheme.labelLarge),
              const SizedBox(height: AppSpacing.sm),
              SegmentedButton<String>(
                segments: const [
                  ButtonSegment(value: 'Lost', label: Text('I lost something'), icon: Icon(Icons.search_off_rounded)),
                  ButtonSegment(value: 'Found', label: Text('I found something'), icon: Icon(Icons.check_circle_outline_rounded)),
                ],
                selected: {_reportType},
                onSelectionChanged: (selection) => setState(() => _reportType = selection.first),
              ),
              const SizedBox(height: AppSpacing.xxl),
              Text('Photos', style: Theme.of(context).textTheme.labelLarge),
              const SizedBox(height: AppSpacing.xs),
              Text('Add up to three clear photos.', style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppColors.textSecondary)),
              const SizedBox(height: AppSpacing.sm),
              SizedBox(
                height: 104,
                child: ListView.separated(
                  scrollDirection: Axis.horizontal,
                  itemCount: _photos.length + 1,
                  separatorBuilder: (_, index) => const SizedBox(width: AppSpacing.sm),
                  itemBuilder: (context, index) {
                    if (index == _photos.length) {
                      return InkWell(
                        onTap: _addPhoto,
                        borderRadius: BorderRadius.circular(AppRadius.l),
                        child: Container(
                          width: 104,
                          decoration: BoxDecoration(
                            color: AppColors.surface,
                            borderRadius: BorderRadius.circular(AppRadius.l),
                            border: Border.all(color: AppColors.borderStrong),
                          ),
                          child: const Icon(Icons.add_photo_alternate_outlined, color: AppColors.primary),
                        ),
                      );
                    }
                    return _PhotoTile(
                      url: _photos[index],
                      onRemove: () => setState(() => _photos.removeAt(index)),
                    );
                  },
                ),
              ),
              const SizedBox(height: AppSpacing.xxl),
              LostifyTextField(
                label: 'Title',
                hintText: 'Black Nike backpack',
                controller: _titleController,
                validator: (value) => value == null || value.trim().length < 3 ? 'Add a short title' : null,
              ),
              const SizedBox(height: AppSpacing.lg),
              LostifyTextField(
                label: 'Description',
                hintText: 'What makes this item recognisable?',
                controller: _descriptionController,
                validator: (value) => value == null || value.trim().length < 10 ? 'Add a few more details' : null,
              ),
              const SizedBox(height: AppSpacing.lg),
              Text('Category', style: Theme.of(context).textTheme.labelLarge),
              const SizedBox(height: AppSpacing.sm),
              Wrap(
                spacing: AppSpacing.sm,
                runSpacing: AppSpacing.sm,
                children: ['Item', 'Pet', 'Person'].map((category) {
                  final selected = category == _category;
                  return ChoiceChip(
                    label: Text(category),
                    selected: selected,
                    onSelected: (_) => setState(() => _category = category),
                    selectedColor: AppColors.primary,
                    labelStyle: TextStyle(color: selected ? Colors.white : AppColors.textPrimary),
                  );
                }).toList(),
              ),
              const SizedBox(height: AppSpacing.xxxl),
              LostifyButton(
                onPressed: _continue,
                label: 'Continue to location',
                loading: _loading,
                width: double.infinity,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _PhotoTile extends StatelessWidget {
  const _PhotoTile({required this.url, required this.onRemove});

  final String url;
  final VoidCallback onRemove;

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        ClipRRect(
          borderRadius: BorderRadius.circular(AppRadius.l),
          child: Image.network(
            url,
            width: 104,
            height: 104,
            fit: BoxFit.cover,
            errorBuilder: (context, error, stackTrace) => Container(
              width: 104,
              height: 104,
              color: AppColors.surfaceVariant,
              child: const Icon(Icons.image_not_supported_outlined),
            ),
          ),
        ),
        Positioned(
          top: AppSpacing.xs,
          right: AppSpacing.xs,
          child: IconButton(
            onPressed: onRemove,
            icon: const Icon(Icons.close_rounded, size: 16),
            style: IconButton.styleFrom(
              backgroundColor: Colors.black.withValues(alpha: 0.58),
              foregroundColor: Colors.white,
              minimumSize: const Size(28, 28),
              padding: EdgeInsets.zero,
            ),
            tooltip: 'Remove photo',
          ),
        ),
      ],
    );
  }
}
