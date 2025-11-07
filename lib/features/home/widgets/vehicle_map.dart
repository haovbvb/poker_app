import 'package:apple_maps_flutter/apple_maps_flutter.dart' as amaps;
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart' as gmaps;

/// 展示车辆所在位置的地图：Android 使用 Google Maps，iOS 使用 Apple Maps。
class VehicleMap extends StatelessWidget {
  const VehicleMap({
    super.key,
    this.latitude = 22.543099,
    this.longitude = 114.057868,
  });

  final double latitude;
  final double longitude;

  @override
  Widget build(BuildContext context) {
    if (kIsWeb) {
      return const Center(child: Text('Web 平台暂不支持地图展示'));
    }

    final platform = defaultTargetPlatform;
    if (platform == TargetPlatform.android) {
      return _AndroidVehicleMap(position: gmaps.LatLng(latitude, longitude));
    }

    if (platform == TargetPlatform.iOS) {
      return _IosVehicleMap(position: amaps.LatLng(latitude, longitude));
    }

    return const Center(child: Text('当前平台暂不支持地图展示'));
  }
}

class _AndroidVehicleMap extends StatelessWidget {
  const _AndroidVehicleMap({required this.position});

  final gmaps.LatLng position;
  static const double _defaultZoom = 14;

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(16),
      child: gmaps.GoogleMap(
        initialCameraPosition: gmaps.CameraPosition(
          target: position,
          zoom: _defaultZoom,
        ),
        myLocationButtonEnabled: false,
        mapToolbarEnabled: false,
        compassEnabled: false,
        zoomControlsEnabled: false,
      ),
    );
  }
}

class _IosVehicleMap extends StatelessWidget {
  const _IosVehicleMap({required this.position});

  final amaps.LatLng position;
  static const double _defaultZoom = 14;

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(16),
      child: amaps.AppleMap(
        initialCameraPosition: amaps.CameraPosition(
          target: position,
          zoom: _defaultZoom,
        ),
        compassEnabled: false,
        myLocationButtonEnabled: false,
        mapType: amaps.MapType.standard,
      ),
    );
  }
}
