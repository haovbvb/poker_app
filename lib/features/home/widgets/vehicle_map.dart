import 'package:flutter/material.dart';

/// 车辆位置展示组件（地图功能已移除）。
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
    // 保留参数以避免上层调用改动；但不再渲染地图。
    // kIsWeb / defaultTargetPlatform 仍可用于上层逻辑判断，这里不区分平台。
    return const SizedBox.shrink();
  }
}
