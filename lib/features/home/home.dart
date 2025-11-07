import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:merchant_app/app/styles/colors.dart';
import 'package:merchant_app/core/utils/context_extensions.dart';
import 'package:merchant_app/features/home/widgets/vehicle_map.dart';

class _VehicleInfo {
  const _VehicleInfo({
    required this.serialNumber,
    required this.bindingId,
    required this.address,
    required this.distance,
    required this.imageAsset,
    this.requiresMaintenance = false,
  });

  final String serialNumber;
  final String bindingId;
  final String address;
  final String distance;
  final String imageAsset;
  final bool requiresMaintenance;
}

const _mockVehicles = <_VehicleInfo>[
  _VehicleInfo(
    serialNumber: 'AS101FD23300018',
    bindingId: '1003504591',
    address: 'China 6, Panyu District CN Guangdong Province',
    distance: '200m',
    imageAsset: 'assets/images/scooter_green.png',
    requiresMaintenance: true,
  ),
  _VehicleInfo(
    serialNumber: 'AS101FD23300018',
    bindingId: '1003504591',
    address: 'China 6, Panyu District CN Guangdong Province',
    distance: '450m',
    imageAsset: 'assets/images/scooter_white.png',
  ),
  _VehicleInfo(
    serialNumber: 'AS101FD23300018',
    bindingId: '1003504591',
    address: 'China 6, Panyu District CN Guangdong Province',
    distance: '781m',
    imageAsset: 'assets/images/scooter_yellow.png',
  ),
  _VehicleInfo(
    serialNumber: 'AS101FD23300018',
    bindingId: '1003504591',
    address: 'China 6, Panyu District CN Guangdong Province',
    distance: '1.4km',
    imageAsset: 'assets/images/scooter_green.png',
    requiresMaintenance: true,
  ),
  _VehicleInfo(
    serialNumber: 'AS101FD23300018',
    bindingId: '1003504591',
    address: 'China 6, Panyu District CN Guangdong Province',
    distance: '1.9km',
    imageAsset: 'assets/images/scooter_white.png',
  ),
];

class HomeTab extends ConsumerWidget {
  const HomeTab({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = context.l10n;

    return Scaffold(
      backgroundColor: Colors.white,
      body: Stack(
        children: [
          const Positioned.fill(child: VehicleMap()),
          _HomeOverlays(title: l10n.homeTitle),
          const _VehicleDraggableSheet(vehicles: _mockVehicles),
        ],
      ),
    );
  }
}

class _HomeOverlays extends StatelessWidget {
  const _HomeOverlays({required this.title});

  final String title;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              title,
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                color: AppColors.black09Text,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: Container(
                    height: 44,
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(22),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withOpacity(0.04),
                          blurRadius: 10,
                          offset: const Offset(0, 4),
                        ),
                      ],
                    ),
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    alignment: Alignment.centerLeft,
                    child: Row(
                      children: [
                        Icon(
                          Icons.search,
                          color: AppColors.black04Text,
                          size: 20,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          'Search for bound vehicles',
                          style: Theme.of(context).textTheme.bodyMedium
                              ?.copyWith(color: AppColors.black05Text),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                DecoratedBox(
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(16),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.04),
                        blurRadius: 10,
                        offset: const Offset(0, 4),
                      ),
                    ],
                  ),
                  child: IconButton(
                    icon: const Icon(Icons.filter_alt_outlined),
                    color: AppColors.black07Text,
                    onPressed: () {},
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _VehicleDraggableSheet extends StatelessWidget {
  const _VehicleDraggableSheet({required this.vehicles});

  final List<_VehicleInfo> vehicles;

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      initialChildSize: 0.35,
      minChildSize: 0.2,
      maxChildSize: 0.85,
      builder: (context, controller) {
        return Align(
          alignment: Alignment.bottomCenter,
          child: Container(
            decoration: const BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.only(
                topLeft: Radius.circular(28),
                topRight: Radius.circular(28),
              ),
              boxShadow: [
                BoxShadow(
                  color: Color(0x1F000000),
                  blurRadius: 14,
                  offset: Offset(0, -4),
                ),
              ],
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const SizedBox(height: 8),
                Container(
                  width: 48,
                  height: 4,
                  decoration: BoxDecoration(
                    color: Colors.black.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
                const SizedBox(height: 12),
                Expanded(
                  child: ListView.separated(
                    controller: controller,
                    padding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 8,
                    ),
                    itemBuilder: (context, index) {
                      final vehicle = vehicles[index % vehicles.length];
                      return _VehicleCard(info: vehicle);
                    },
                    separatorBuilder: (_, __) => const SizedBox(height: 12),
                    itemCount: vehicles.length,
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _VehicleCard extends StatelessWidget {
  const _VehicleCard({required this.info});

  final _VehicleInfo info;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.black.withOpacity(0.05)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 12,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _VehicleImage(asset: info.imageAsset),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'SN: ${info.serialNumber}',
                      style: theme.textTheme.titleMedium?.copyWith(
                        color: AppColors.black09Text,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        if (info.requiresMaintenance)
                          const _StatusChip(
                            label: 'To be maintained',
                            borderColor: AppColors.danger,
                            textColor: AppColors.danger,
                          ),
                        if (info.requiresMaintenance) const SizedBox(width: 8),
                        _StatusChip(
                          label: 'Binding ID: ${info.bindingId}',
                          borderColor: AppColors.black02Text,
                          textColor: AppColors.black06Text,
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Icon(Icons.location_on, size: 18, color: AppColors.black04Text),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  info.address,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: AppColors.black06Text,
                    height: 1.3,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Icon(
                Icons.campaign_outlined,
                size: 18,
                color: AppColors.black04Text,
              ),
              const SizedBox(width: 4),
              Text(
                info.distance,
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: AppColors.black06Text,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _VehicleImage extends StatelessWidget {
  const _VehicleImage({required this.asset});

  final String asset;

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(16),
      child: Container(
        width: 72,
        height: 72,
        color: Colors.white,
        child: Image.asset(
          asset,
          fit: BoxFit.cover,
          errorBuilder: (_, __, ___) {
            return Container(
              color: Colors.grey.shade200,
              child: const Icon(
                Icons.electric_scooter,
                size: 36,
                color: Colors.grey,
              ),
            );
          },
        ),
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({
    required this.label,
    required this.borderColor,
    required this.textColor,
  });

  final String label;
  final Color borderColor;
  final Color textColor;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: borderColor.withOpacity(0.08),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: borderColor.withOpacity(0.5)),
      ),
      child: Text(
        label,
        style: Theme.of(context).textTheme.labelMedium?.copyWith(
          color: textColor,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }
}
