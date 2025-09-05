/**
 * Calculate distance between two GPS points using Haversine formula
 * @param {number} lat1 - Latitude of point 1
 * @param {number} lon1 - Longitude of point 1
 * @param {number} lat2 - Latitude of point 2
 * @param {number} lon2 - Longitude of point 2
 * @returns {number} Distance in kilometers
 */
function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Earth's radius in kilometers
    const dLat = toRadians(lat2 - lat1);
    const dLon = toRadians(lon2 - lon1);
    
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
              Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) *
              Math.sin(dLon / 2) * Math.sin(dLon / 2);
    
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    const distance = R * c;
    
    return distance;
}

/**
 * Convert degrees to radians
 * @param {number} degrees
 * @returns {number} Radians
 */
function toRadians(degrees) {
    return degrees * (Math.PI / 180);
}

/**
 * Calculate speed between two GPS points
 * @param {number} longitude1 - Longitude of point 1
 * @param {number} latitude1 - Latitude of point 1
 * @param {number} longitude2 - Longitude of point 2
 * @param {number} latitude2 - Latitude of point 2
 * @param {number|Date} timestamp1 - Timestamp of point 1 (milliseconds or Date object)
 * @param {number|Date} timestamp2 - Timestamp of point 2 (milliseconds or Date object)
 * @returns {number} Speed in km/h
 */
function calculateSpeed(longitude1, latitude1, longitude2, latitude2, timestamp1, timestamp2) {
    // Calculate distance between points
    const distance = calculateDistance(latitude1, longitude1, latitude2, longitude2);
    
    // Convert timestamps to milliseconds if they're Date objects
    const time1 = timestamp1 instanceof Date ? timestamp1.getTime() : timestamp1;
    const time2 = timestamp2 instanceof Date ? timestamp2.getTime() : timestamp2;
    
    // Calculate time difference in hours
    const timeDiffMs = Math.abs(time2 - time1);
    const timeDiffHours = timeDiffMs / (1000 * 60 * 60);
    
    // Avoid division by zero
    if (timeDiffHours === 0) {
        return 0;
    }
    
    // Calculate speed in km/h
    const speed = distance / timeDiffHours;
    
    return speed;
}

/**
 * Calculate speed with additional validation and formatting
 * @param {Object} point1 - First point {longitude, latitude, timestamp}
 * @param {Object} point2 - Second point {longitude, latitude, timestamp}
 * @param {number} precision - Number of decimal places (default: 2)
 * @returns {Object} Result object with speed, distance, and time difference
 */
function calculateSpeedDetailed(point1, point2, precision = 2) {
    const { longitude: lon1, latitude: lat1, timestamp: ts1 } = point1;
    const { longitude: lon2, latitude: lat2, timestamp: ts2 } = point2;
    
    // Validate coordinates
    if (!isValidCoordinate(lat1, lon1) || !isValidCoordinate(lat2, lon2)) {
        throw new Error('Invalid GPS coordinates');
    }
    
    // Calculate distance and time difference
    const distance = calculateDistance(lat1, lon1, lat2, lon2);
    const time1 = ts1 instanceof Date ? ts1.getTime() : ts1;
    const time2 = ts2 instanceof Date ? ts2.getTime() : ts2;
    const timeDiffMs = Math.abs(time2 - time1);
    const timeDiffHours = timeDiffMs / (1000 * 60 * 60);
    const timeDiffSeconds = timeDiffMs / 1000;
    
    // Calculate speed
    const speed = timeDiffHours === 0 ? 0 : distance / timeDiffHours;
    
    return {
        speed: parseFloat(speed.toFixed(precision)),
        distance: parseFloat(distance.toFixed(precision + 1)),
        timeDifferenceSeconds: timeDiffSeconds,
        timeDifferenceHours: parseFloat(timeDiffHours.toFixed(4))
    };
}

/**
 * Validate GPS coordinates
 * @param {number} lat - Latitude
 * @param {number} lon - Longitude
 * @returns {boolean} True if coordinates are valid
 */
function isValidCoordinate(lat, lon) {
    return typeof lat === 'number' && typeof lon === 'number' &&
           lat >= -90 && lat <= 90 &&
           lon >= -180 && lon <= 180;
}

// Example usage:

// Example 1: Simple speed calculation
const speed1 = calculateSpeed(
    2.3522, 48.8566,  // Point 1: Longitude, Latitude (Paris)
    2.3488, 48.8530,  // Point 2: Longitude, Latitude (Near Paris)
    1693920000000,    // Timestamp 1 (milliseconds)
    1693920120000     // Timestamp 2 (milliseconds) - 2 minutes later
);
console.log(`Speed: ${speed1.toFixed(2)} km/h`);

// Example 2: Using Date objects
const date1 = new Date('2023-09-05T10:00:00Z');
const date2 = new Date('2023-09-05T10:02:00Z');
const speed2 = calculateSpeed(2.3522, 48.8566, 2.3488, 48.8530, date1, date2);
console.log(`Speed with dates: ${speed2.toFixed(2)} km/h`);

// Example 3: Detailed calculation with validation
try {
    const point1 = { longitude: 2.3522, latitude: 48.8566, timestamp: Date.now() };
    const point2 = { longitude: 2.3488, latitude: 48.8530, timestamp: Date.now() + 120000 }; // 2 minutes later
    
    const result = calculateSpeedDetailed(point1, point2);
    console.log('Detailed result:', result);
} catch (error) {
    console.error('Error:', error.message);
}

// Example 4: Processing trip data from your database format
function calculateTripSegmentSpeed(tripDetail1, tripDetail2) {
    return calculateSpeedDetailed(
        {
            longitude: tripDetail1.long,
            latitude: tripDetail1.lat,
            timestamp: new Date(tripDetail1.timestamp)
        },
        {
            longitude: tripDetail2.long,
            latitude: tripDetail2.lat,
            timestamp: new Date(tripDetail2.timestamp)
        }
    );
}

// Export functions for use in other modules
module.exports = {
    calculateDistance,
    calculateSpeed,
    calculateSpeedDetailed,
    isValidCoordinate
};