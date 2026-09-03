"""Coordinate and quaternion helpers for the VRX ROS boundary.

VRX publishes the station-keeping goal as ``geographic_msgs/GeoPoseStamped``
in WGS84 latitude/longitude, while the WAM-V odometry is local ENU metres.
These functions keep that conversion explicit and dependency-light.
"""

import math


WGS84_SEMI_MAJOR_M = 6378137.0
WGS84_FLATTENING = 1.0 / 298.257223563


def _ecef(latitude_deg, longitude_deg, altitude_m=0.0):
    latitude = math.radians(float(latitude_deg))
    longitude = math.radians(float(longitude_deg))
    sin_lat = math.sin(latitude)
    cos_lat = math.cos(latitude)
    radius = WGS84_SEMI_MAJOR_M / math.sqrt(
        1.0 - (2.0 * WGS84_FLATTENING - WGS84_FLATTENING ** 2) * sin_lat ** 2
    )
    return (
        (radius + altitude_m) * cos_lat * math.cos(longitude),
        (radius + altitude_m) * cos_lat * math.sin(longitude),
        (radius * (1.0 - WGS84_FLATTENING) ** 2 + altitude_m) * sin_lat,
    )


def wgs84_to_local_enu(latitude_deg, longitude_deg, datum_latitude_deg, datum_longitude_deg):
    """Convert WGS84 latitude/longitude to the VRX local ENU XY frame."""

    latitude = math.radians(float(datum_latitude_deg))
    longitude = math.radians(float(datum_longitude_deg))
    origin = _ecef(datum_latitude_deg, datum_longitude_deg)
    point = _ecef(latitude_deg, longitude_deg)
    dx, dy, dz = (point[i] - origin[i] for i in range(3))
    east = -math.sin(longitude) * dx + math.cos(longitude) * dy
    north = (
        -math.sin(latitude) * math.cos(longitude) * dx
        - math.sin(latitude) * math.sin(longitude) * dy
        + math.cos(latitude) * dz
    )
    return east, north


def quaternion_to_yaw(x, y, z, w):
    """Return the ENU yaw represented by a ROS quaternion."""

    return math.atan2(2.0 * (float(w) * float(z) + float(x) * float(y)), 1.0 - 2.0 * (float(y) ** 2 + float(z) ** 2))

