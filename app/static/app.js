let map, circle, geocoder;

/**
 * Initializes the map, autocomplete, and proximity circle.
 */
function initMap() {
    const initialLocation = { lat: 40.7128, lng: -74.0060 }; // Default to NYC

    // Initialize the map centered at the initial location
    map = new google.maps.Map(document.getElementById('map'), {
        center: initialLocation,
        zoom: 12
    });

    // Initialize geocoder and autocomplete
    geocoder = new google.maps.Geocoder();
    const autocomplete = new google.maps.places.Autocomplete(document.getElementById('location'));

    // Create a circle representing proximity
    circle = new google.maps.Circle({
        map: map,
        radius: 10000, // Default 10 km
        fillColor: '#AA0000',
        strokeColor: '#AA0000',
        strokeOpacity: 0.6,
        fillOpacity: 0.3
    });
    circle.setCenter(initialLocation);

    // Update map and circle when location changes
    autocomplete.addListener('place_changed', () => {
        const place = autocomplete.getPlace();
        if (place.geometry) {
            const location = place.geometry.location;
            map.setCenter(location);
            circle.setCenter(location);
        } else {
            alert("Location not found.");
        }
    });

    // Update circle radius based on proximity slider
    document.getElementById('proximity').addEventListener('input', function () {
        const proximity = parseFloat(this.value);
        circle.setRadius(proximity * 1000); // Convert km to meters
        document.getElementById('proximity-value').innerText = proximity;
    });
}

/**
 * Gets the user's current location.
 */
function getCurrentLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition((position) => {
            const { latitude: lat, longitude: lng } = position.coords;
            document.getElementById('location').value = `${lat}, ${lng}`;
            const userLocation = { lat, lng };
            map.setCenter(userLocation);
            circle.setCenter(userLocation);
        }, () => alert('Unable to fetch your location.'));
    } else {
        alert('Geolocation not supported by your browser.');
    }
}

// Toggle sidebar visibility
document.getElementById('toggle-btn').addEventListener('click', () => {
    document.getElementById('sidebar').classList.toggle('show');
});

// Update distance value dynamically
function updateDistanceValue(value) {
    document.getElementById('distance-value').innerText = value;
}

window.initMap = initMap;
