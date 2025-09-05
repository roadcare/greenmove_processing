
import { lineString } from '@turf/helpers';
import simplify from '@turf/simplify';
import { Feature, LineString } from 'geojson';
function tripDetailToLineString(detailTrip: TripDetailDto[]): Feature<LineString> {
  const coordinates = detailTrip
    .filter(
      (point) =>
        point.lat !== undefined &&
        point.long !== undefined &&
        !isNaN(point.lat) &&
        !isNaN(point.long),
    )
    .map((point) => [point.long, point.lat]);

  return lineString(coordinates);
}
function coordinatesToTripDetail(
  coordinates: number[][],
  originalPoints: TripDetailDto[],
): TripDetailDto[] {
  return coordinates.map(([long, lat]) => {
    // Tìm điểm gốc gần nhất
    const nearestPoint = originalPoints.reduce((nearest, current) => {
      const nearestDistance = Math.sqrt(
        Math.pow(nearest.lat - lat, 2) + Math.pow(nearest.long - long, 2),
      );
      const currentDistance = Math.sqrt(
        Math.pow(current.lat - lat, 2) + Math.pow(current.long - long, 2),
      );
      return currentDistance < nearestDistance ? current : nearest;
    });

    return {
      ...nearestPoint,
      lat: lat,
      long: long,
    };
  });
}
async simplifyDetailTrip(
    detailTrip: TripDetailDto[],
    tolerance: number = 0.0005,
    highQuality: boolean = true,
  ): Promise<TripDetailDto[]> {
    try {
      // Kiểm tra đầu vào
      if (!detailTrip || detailTrip.length === 0) {
        return [];
      }

      // Nếu chỉ có 1 hoặc 2 điểm, không cần simplify
      if (detailTrip.length <= 2) {
        return detailTrip;
      }

      // Sắp xếp các điểm theo thời gian nếu có timestamp
      const sortedTrip = [...detailTrip].sort((a, b) => {
        if (a.timestamp && b.timestamp) {
          return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
        }
        if (a.time && b.time) {
          return a.time - b.time;
        }
        return 0;
      });

      // Lọc ra các điểm có tọa độ hợp lệ
      const validPoints = sortedTrip.filter(
        (point) =>
          point.lat !== undefined &&
          point.long !== undefined &&
          !isNaN(point.lat) &&
          !isNaN(point.long) &&
          point.lat >= -90 &&
          point.lat <= 90 &&
          point.long >= -180 &&
          point.long <= 180,
      );

      if (validPoints.length <= 2) {
        return validPoints;
      }

      // Convert sang GeoJSON LineString sử dụng helper function
      const line = this.tripDetailToLineString(validPoints);

      // Sử dụng turf.js để simplify
      const simplifiedLine = simplify(line, {
        tolerance: tolerance,
        highQuality: highQuality,
      });

      // Convert ngược về TripDetailDto[] sử dụng helper function
      const simplifiedCoordinates = simplifiedLine.geometry.coordinates;
      const simplifiedPoints = this.coordinatesToTripDetail(
        simplifiedCoordinates,
        validPoints,
      );

      // Đảm bảo điểm đầu và cuối được giữ lại
      if (simplifiedPoints.length > 0) {
        simplifiedPoints[0] = { ...validPoints[0] };
        simplifiedPoints[simplifiedPoints.length - 1] = {
          ...validPoints[validPoints.length - 1],
        };
      }

      return simplifiedPoints;
    } catch (error) {
      console.error('Error in simplifyDetailTrip:', error);
      // Trả về dữ liệu gốc nếu có lỗi
      return detailTrip;
    }
  }