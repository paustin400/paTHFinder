// static/app.js

class PathfinderApp {
    constructor() {
        this.map = null;
        this.circle = null;
        this.geocoder = null;
        this.directionsService = null;
        this.directionsRenderer = null;
        this.selectedLat = null;
        this.selectedLng = null;
        this.searchInProgress = false;
        this.currentRoute = null;
        this.markers = [];
    }

    async init() {
        try {
            // Initialize Google Maps components
            const initialLocation = { lat: 40.7128, lng: -74.0060 };
            this.map = new google.maps.Map(document.getElementById('map'), {
                center: initialLocation,
                zoom: 12,
                styles: this.getMapStyles()
            });

            this.directionsService = new google.maps.DirectionsService();
            this.directionsRenderer = new google.maps.DirectionsRenderer({
                map: this.map,
                suppressMarkers: true
            });

            this.geocoder = new google.maps.Geocoder();
            this.setupAutocomplete();
            this.setupCircle(initialLocation);
            this.setupEventListeners();

        } catch (error) {
            console.error('Error initializing map:', error);
            this.showError('Failed to initialize map. Please refresh the page.');
        }
    }

    setupAutocomplete() {
        const autocomplete = new google.maps.places.Autocomplete(
            document.getElementById('location'),
            { types: ['geocode'] }
        );

        autocomplete.addListener('place_changed', () => {
            const place = autocomplete.getPlace();
            if (place.geometry) {
                this.handlePlaceSelection(place.geometry.location);
            } else {
                this.showError('Please select a location from the dropdown.');
            }
        });
    }

    setupCircle(center) {
        this.circle = new google.maps.Circle({
            map: this.map,
            radius: 10000,
            fillColor: '#4285F4',
            strokeColor: '#4285F4',
            strokeOpacity: 0.8,
            fillOpacity: 0.3,
            strokeWeight: 2
        });
        this.circle.setCenter(center);
    }

    setupEventListeners() {
        // Form submission
        const searchForm = document.querySelector('form');
        if (searchForm) {
            searchForm.addEventListener('submit', (e) => this.handleSearch(e));
        }

        // Proximity slider
        const proximitySlider = document.getElementById('proximity');
        if (proximitySlider) {
            proximitySlider.addEventListener('input', (e) => this.handleProximityChange(e));
        }

        // Current location button
        const locationButton = document.getElementById('current-location');
        if (locationButton) {
            locationButton.addEventListener('click', () => this.getCurrentLocation());
        }
    }

    async handleSearch(event) {
        event.preventDefault();
        if (this.searchInProgress) return;

        try {
            this.searchInProgress = true;
            this.showLoading();

            if (!this.selectedLat || !this.selectedLng) {
                throw new Error('Please select a valid location first');
            }

            const formData = new FormData(event.target);
            const searchParams = new URLSearchParams({
                latitude: this.selectedLat,
                longitude: this.selectedLng,
                max_distance: formData.get('proximity'),
                route_type: formData.get('route_type'),
                elevation_preference: formData.get('elevation_preference')
            });

            const response = await fetch(`/api/routes/search?${searchParams}`);
            if (!response.ok) {
                throw new Error('Failed to fetch routes');
            }

            const routes = await response.json();
            if (routes.length === 0) {
                this.showMessage('No routes found matching your criteria.');
                return;
            }

            this.displayRoutes(routes);
            window.location.href = '/search-results';

        } catch (error) {
            console.error('Search error:', error);
            this.showError(error.message);
        } finally {
            this.searchInProgress = false;
            this.hideLoading();
        }
    }

    async displayRoutes(routes) {
        this.clearMap();
        routes.forEach(route => this.displayRoute(route));
        this.updateRoutesList(routes);
    }

    displayRoute(route) {
        try {
            const waypoints = this.generateWaypoints(route);
            const request = {
                origin: { lat: route.latitude, lng: route.longitude },
                destination: { lat: route.latitude, lng: route.longitude },
                waypoints: waypoints,
                travelMode: 'WALKING'
            };

            this.directionsService.route(request, (result, status) => {
                if (status === 'OK') {
                    this.directionsRenderer.setDirections(result);
                    this.addRouteMarker(route);
                }
            });
        } catch (error) {
            console.error('Error displaying route:', error);
        }
    }

    generateWaypoints(route) {
        const numPoints = 8;
        const radius = route.distance * 1000 / (2 * Math.PI);
        return Array.from({ length: numPoints }, (_, i) => {
            const angle = (2 * Math.PI * i) / numPoints;
            const lat = route.latitude + (radius * Math.cos(angle)) / 111111;
            const lng = route.longitude + (radius * Math.sin(angle)) / (111111 * Math.cos(route.latitude * Math.PI / 180));
            return {
                location: new google.maps.LatLng(lat, lng),
                stopover: false
            };
        });
    }

    updateRoutesList(routes) {
        const routesList = document.getElementById('routes-list');
        if (!routesList) return;

        routesList.innerHTML = routes.map(route => this.createRouteElement(route)).join('');
    }

    createRouteElement(route) {
        return `
            <div class="route-item" onclick="pathfinder.showRouteDetails(${route.id})">
                <h3>${this.escapeHtml(route.name)}</h3>
                <div class="route-details">
                    <div class="detail-item">
                        <span class="icon">📏</span>
                        ${route.distance.toFixed(1)} km
                    </div>
                    ${route.elevation_gain ? `
                        <div class="detail-item">
                            <span class="icon">⛰️</span>
                            ${route.elevation_gain.toFixed(1)}m gain
                        </div>
                    ` : ''}
                    ${route.quality_score ? `
                        <div class="detail-item">
                            <span class="icon">📊</span>
                            ${(route.quality_score * 100).toFixed(1)}% match
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    // Utility methods
    showLoading() {
        const searchButton = document.querySelector('button[type="submit"]');
        if (searchButton) {
            searchButton.disabled = true;
            searchButton.innerHTML = '<span class="spinner"></span> Searching...';
        }
    }

    hideLoading() {
        const searchButton = document.querySelector('button[type="submit"]');
        if (searchButton) {
            searchButton.disabled = false;
            searchButton.innerHTML = 'Search';
        }
    }

    showError(message) {
        const errorDiv = document.getElementById('error-message') || this.createErrorElement();
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    }

    showMessage(message) {
        const messageDiv = document.getElementById('message') || this.createMessageElement();
        messageDiv.textContent = message;
        messageDiv.style.display = 'block';
        setTimeout(() => {
            messageDiv.style.display = 'none';
        }, 3000);
    }

    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    getMapStyles() {
        return [
            {
                featureType: "poi.business",
                stylers: [{ visibility: "off" }]
            },
            {
                featureType: "transit",
                elementType: "labels.icon",
                stylers: [{ visibility: "off" }]
            }
        ];
    }
}

// Initialize the app
const pathfinder = new PathfinderApp();
window.initMap = () => pathfinder.init();