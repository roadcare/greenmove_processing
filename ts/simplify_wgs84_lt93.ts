import { lineString } from '@turf/helpers';
import simplify from '@turf/simplify';
import { Feature, LineString } from 'geojson';
import proj4 from 'proj4';

// Define Lambert 93 (RGF93 / Lambert-93) projection - EPSG:2154
proj4.defs('EPSG:2154', '+proj=lcc +lat_1=49 +lat_2=44 +lat_0=46.5 +lon_0=3 +x_0=700000 +y_0=6600000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs');

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

// Helper function to transform coordinates from WGS84 to Lambert 93
function transformToLambert93(geojsonLine: Feature<LineString>): Feature<LineString> {
  const coordinates = geojsonLine.geometry.coordinates.map(coord => {
    // Transform from WGS84 [lon, lat] to Lambert 93 [x, y]
    return proj4('EPSG:4326', 'EPSG:2154', coord);
  });
  
  return {
    type: 'Feature',
    geometry: {
      type: 'LineString',
      coordinates: coordinates
    },
    properties: geojsonLine.properties || {}
  };
}

// Helper function to transform coordinates from Lambert 93 back to WGS84
function transformToWGS84(lambertLine: Feature<LineString>): Feature<LineString> {
  const coordinates = lambertLine.geometry.coordinates.map(coord => {
    // Transform from Lambert 93 [x, y] back to WGS84 [lon, lat]
    return proj4('EPSG:2154', 'EPSG:4326', coord);
  });
  
  return {
    type: 'Feature',
    geometry: {
      type: 'LineString',
      coordinates: coordinates
    },
    properties: lambertLine.properties || {}
  };
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
    tolerance: number = 10, // Changed default to 10 meters instead of 0.0005 degrees
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

      // Transform from WGS84 to Lambert 93 for meter-based operations
      const lambertLine = transformToLambert93(line);

      // Sử dụng turf.js để simplify trong hệ tọa độ Lambert 93
      const simplifiedLambertLine = simplify(lambertLine, {
        tolerance: tolerance, // tolerance is now correctly applied in meters
        highQuality: highQuality,
      });

      // Transform back to WGS84 for final result
      const simplifiedLine = transformToWGS84(simplifiedLambertLine);

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