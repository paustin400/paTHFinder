class PathfinderApp {
  constructor() {
    // Configuration settings
    this.CONFIG = {
      MAX_RETRY_ATTEMPTS: 3,
      RETRY_DELAY: 1000,
      ERROR_DISPLAY_DURATION: 5000,
      API_TIMEOUT: 10000,
      DEFAULT_LOCATION: { lat: 39.8283, lng: -98.5795 },
      DEFAULT_ZOOM: 4,
      MAP_STYLES: [
        {
          featureType: "poi.business",
          stylers: [{ visibility: "off" }]
        },
        {
          featureType: "transit",
          elementType: "labels.icon",
          stylers: [{ visibility: "off" }]
        }
      ]
    };

    // Check if map element exists
    this.mapRequired = !!document.getElementById('map');

    // State tracking
    this.initialized = false;
    this.mapInitialized = false;

    // Map components
    this.map = null;
    this.circle = null;
    this.markers = [];
    this.directionsService = null;
    this.directionsRenderer = null;
    this.geocoder = null;
    this.placesService = null;
    this.searchBox = null;

    // Application state: global selected location for search
    this.selectedLat = null;
    this.selectedLng = null;
    this.searchInProgress = false;
    this.currentRoute = null;
    this.currentInfoWindow = null;

    // Bind methods to preserve context
    this.init = this.init.bind(this);
    this.initializeMap = this.initializeMap.bind(this);
    this.initializeServices = this.initializeServices.bind(this);
  }

  async init() {
    if (this.initialized) return;
    try {
      this.showLoading();
      this.initialized = true;
      const mapElement = document.getElementById('map');
      if (!mapElement) {
        // No map required; simply hide the loading overlay.
        this.hideLoading();
        return;
      }
      // Map initialization will be triggered by the Google Maps API callback.
    } catch (error) {
      console.error('Initialization error:', error);
      this.showError('Failed to initialize application. Please refresh the page.');
      this.hideLoading();
    }
  }

  async initializeMap() {
    if (this.mapInitialized) return;
    try {
      const mapElement = document.getElementById('map');
      if (!mapElement) {
        throw new Error('Map element not found');
      }

      // Create the map instance
      this.map = new google.maps.Map(mapElement, {
        center: this.CONFIG.DEFAULT_LOCATION,
        zoom: this.CONFIG.DEFAULT_ZOOM,
        styles: this.CONFIG.MAP_STYLES,
        mapTypeControl: true,
        mapTypeControlOptions: {
          style: google.maps.MapTypeControlStyle.HORIZONTAL_BAR,
          position: google.maps.ControlPosition.TOP_RIGHT
        },
        fullscreenControl: true,
        streetViewControl: true,
        zoomControl: true
      });

      // Initialize all Google Maps services
      await this.initializeServices();

      // Set up UI event listeners
      this.setupEventListeners();

      this.mapInitialized = true;

      // Attempt to acquire the initial location
      await this.tryGetInitialLocation();

      // Check for a route detail page (if route data exists)
      const routeData = document.getElementById('route-data');
      if (routeData) {
        const route = JSON.parse(routeData.dataset.route);
        const aiAnalysis = JSON.parse(routeData.dataset.aiAnalysis || '{}');
        await this.displayRoute(route);
        if (Object.keys(aiAnalysis).length > 0) {
          await this.displayAIAnalysis(aiAnalysis);
        }
      }

      this.hideLoading();
      return this.map;
    } catch (error) {
      console.error('Map initialization error:', error);
      this.showError('Failed to initialize map. Please refresh the page.');
      this.hideLoading();
      throw error;
    }
  }

  async initializeServices() {
    // Initialize Google Maps services
    this.geocoder = new google.maps.Geocoder();
    this.placesService = new google.maps.places.PlacesService(this.map);
    this.directionsService = new google.maps.DirectionsService();
    this.directionsRenderer = new google.maps.DirectionsRenderer({
      map: this.map,
      suppressMarkers: true
    });

    // Initialize the search box if available (this may be overridden by autocomplete in search.js)
    const input = document.getElementById('location-input');
    if (input) {
      this.searchBox = new google.maps.places.SearchBox(input);
      // Do not push the input into map controls since we want it in the sidebar.
      this.map.addListener('bounds_changed', () => {
        this.searchBox.setBounds(this.map.getBounds());
      });
      this.searchBox.addListener('places_changed', () => {
        const places = this.searchBox.getPlaces();
        if (places.length === 0) return;
        const place = places[0];
        if (!place.geometry || !place.geometry.location) return;
        this.handleLocationSelect(place.geometry.location);
      });
    }
  }

  setupEventListeners() {
    // Search button event listener
    const searchButton = document.getElementById('search-routes');
    if (searchButton) {
      searchButton.addEventListener('click', () => this.handleSearch());
    }
    // Current location button event listener
    const locationButton = document.getElementById('current-location');
    if (locationButton) {
      locationButton.addEventListener('click', () => this.getCurrentLocation());
    }
    // Proximity slider event listener
    const proximitySlider = document.getElementById('proximity');
    const proximityValue = document.getElementById('proximity-value');
    if (proximitySlider && proximityValue) {
      proximitySlider.addEventListener('input', (e) => {
        const value = e.target.value;
        proximityValue.textContent = `${value} km`;
        if (this.selectedLat && this.selectedLng) {
          this.updateCircle();
        }
      });
    }
    // Sidebar container: set up toggle and draggable behavior
    const container = document.getElementById('sidebar-container');
    if (container) {
      const toggleIcon = container.querySelector('.sidebar-toggle');
      const sidebar = container.querySelector('#sidebar');
      if (toggleIcon && sidebar) {
        // Toggle open/close: clicking the icon will toggle the container's "closed" class.
        toggleIcon.addEventListener('click', (e) => {
          // Only toggle if not dragging.
          if (!container.classList.contains('dragging')) {
            container.classList.toggle('closed');
          }
          e.stopPropagation();
        });
        // Draggable behavior for the entire container (both horizontally and vertically)
        let isDragging = false;
        let offsetX = 0;
        let offsetY = 0;

        toggleIcon.addEventListener('mousedown', (e) => {
          isDragging = true;
          container.classList.add('dragging');
          offsetX = e.clientX - container.offsetLeft;
          offsetY = e.clientY - container.offsetTop;
          e.preventDefault();
        });

        document.addEventListener('mousemove', (e) => {
          if (isDragging) {
            container.style.left = (e.clientX - offsetX) + 'px';
            container.style.top = (e.clientY - offsetY) + 'px';
          }
        });

        document.addEventListener('mouseup', () => {
          if (isDragging) {
            isDragging = false;
            container.classList.remove('dragging');
          }
        });
      }
    }
  }

  async tryGetInitialLocation() {
    if (navigator.geolocation) {
      try {
        const position = await new Promise((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject);
        });
        const userLocation = {
          lat: position.coords.latitude,
          lng: position.coords.longitude
        };
        this.map.setCenter(userLocation);
        this.map.setZoom(12);
        this.handleLocationSelect(new google.maps.LatLng(userLocation.lat, userLocation.lng));
      } catch (error) {
        console.warn('Could not get user location:', error);
        // Fall back to default location/zoom if necessary.
      }
    }
  }

  async getCurrentLocation() {
    if (!navigator.geolocation) {
      this.showError('Geolocation is not supported by your browser');
      return;
    }
    try {
      const position = await new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject);
      });
      const location = new google.maps.LatLng(
        position.coords.latitude,
        position.coords.longitude
      );
      this.handleLocationSelect(location);
    } catch (error) {
      this.showError('Could not get your location. Please enter it manually.');
    }
  }

  handleLocationSelect(location) {
    this.selectedLat = location.lat();
    this.selectedLng = location.lng();
    this.map.setCenter(location);
    this.map.setZoom(14);
    this.updateCircle();
    // Reverse geocode to update the location input
    this.geocoder.geocode({ location: location }, (results, status) => {
      if (status === 'OK' && results[0]) {
        const input = document.getElementById('location-input');
        if (input) {
          input.value = results[0].formatted_address;
        }
      }
    });
  }

  updateCircle() {
    const radius = Number(document.getElementById('proximity').value) * 1000; // in meters
    const center = new google.maps.LatLng(this.selectedLat, this.selectedLng);
    if (this.circle) {
      this.circle.setMap(null);
    }
    this.circle = new google.maps.Circle({
      map: this.map,
      center: center,
      radius: radius,
      fillColor: '#4285F4',
      fillOpacity: 0.2,
      strokeColor: '#4285F4',
      strokeWeight: 2
    });
  }

  async handleSearch() {
    if (this.searchInProgress) return;
    if (!this.selectedLat || !this.selectedLng) {
      this.showError('Please select a starting location first');
      return;
    }
    try {
      this.searchInProgress = true;
      this.showLoading();
      const searchParams = this.getSearchParams();
      const routes = await this.searchRoutes(searchParams);
      if (!routes || routes.length === 0) {
        this.showMessage('No routes found matching your criteria');
        return;
      }
      this.displayRoutes(routes);
    } catch (error) {
      console.error('Search error:', error);
      this.showError('Failed to search routes. Please try again.');
    } finally {
      this.searchInProgress = false;
      this.hideLoading();
    }
  }

  getSearchParams() {
    const params = new URLSearchParams();
    // Append location, proximity, route type, elevation preference, and sidewalks requirement.
    params.append('latitude', this.selectedLat.toString());
    params.append('longitude', this.selectedLng.toString());
    const proximity = document.getElementById('proximity').value;
    params.append('max_distance', proximity);
    const routeType = document.querySelector('input[name="route_type"]:checked').value;
    params.append('route_type', routeType);
    const elevation = document.querySelector('input[name="elevation"]:checked').value;
    params.append('elevation_preference', elevation);
    const requireSidewalks = document.getElementById('require_sidewalks').checked;
    params.append('require_sidewalks', requireSidewalks.toString());
    return params;
  }

  async searchRoutes(params) {
    const response = await fetch(`/api/routes/search?${params.toString()}`);
    if (!response.ok) {
      throw new Error('Failed to fetch routes');
    }
    return await response.json();
  }

  displayRoutes(routes) {
    this.clearMap();
    routes.forEach((route, index) => {
      const marker = new google.maps.Marker({
        position: { lat: route.latitude, lng: route.longitude },
        map: this.map,
        title: route.name,
        label: (index + 1).toString()
      });
      marker.addListener('click', () => {
        this.showRouteDetails(route);
      });
      this.markers.push(marker);
    });
    // Fit map bounds to include all markers.
    const bounds = new google.maps.LatLngBounds();
    this.markers.forEach(marker => bounds.extend(marker.getPosition()));
    this.map.fitBounds(bounds);
  }

  clearMap() {
    this.markers.forEach(marker => marker.setMap(null));
    this.markers = [];
    if (this.directionsRenderer) {
      this.directionsRenderer.setDirections({ routes: [] });
    }
  }

  showLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
      overlay.style.display = 'flex';
      overlay.classList.add('active');
    }
  }

  hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
      overlay.classList.remove('active');
      setTimeout(() => {
        overlay.style.display = 'none';
      }, 300);
    }
  }

  showError(message) {
    this.showMessage(message, 'error');
  }

  showMessage(message, type = 'info') {
    const container = document.getElementById('message-container');
    if (!container) return;
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.textContent = message;
    container.appendChild(messageDiv);
    setTimeout(() => {
      messageDiv.classList.add('fade-out');
      setTimeout(() => messageDiv.remove(), 300);
    }, this.CONFIG.ERROR_DISPLAY_DURATION);
  }

  async displayRoute(route) {
    try {
      this.clearMap();
      if (!route || !route.latitude || !route.longitude) {
        console.error('Invalid route data');
        return;
      }
      const routeLocation = {
        lat: parseFloat(route.latitude),
        lng: parseFloat(route.longitude)
      };
      this.map.setCenter(routeLocation);
      this.map.setZoom(15);
      const marker = new google.maps.Marker({
        position: routeLocation,
        map: this.map,
        title: route.name
      });
      this.markers.push(marker);
      if (route.path) {
        try {
          const path = JSON.parse(route.path);
          const routePath = new google.maps.Polyline({
            path: path,
            geodesic: true,
            strokeColor: '#4285F4',
            strokeOpacity: 1.0,
            strokeWeight: 3
          });
          routePath.setMap(this.map);
        } catch (e) {
          console.error('Error parsing route path:', e);
        }
      }
      this.currentRoute = route;
    } catch (error) {
      console.error('Error displaying route:', error);
      this.showError('Failed to display route on map');
    }
  }

  async displayAIAnalysis(analysis) {
    try {
      if (!analysis || !this.currentRoute) return;
      if (this.currentInfoWindow) {
        this.currentInfoWindow.close();
      }
      const infoContent = `
        <div class="route-info-window">
          <h3>${this.currentRoute.name}</h3>
          <div class="ai-stats">
            <p><strong>Match Score:</strong> ${(analysis.quality_score * 100).toFixed(1)}%</p>
            <p><strong>Difficulty:</strong> ${analysis.difficulty_score ? this.getDifficultyLabel(analysis.difficulty_score) : 'N/A'}</p>
            ${analysis.route_type ? `<p><strong>Type:</strong> ${analysis.route_type}</p>` : ''}
          </div>
          ${analysis.route_features ? `
            <div class="route-features">
              <strong>Features:</strong>
              <ul>
                ${analysis.route_features.map(feature => `<li>${feature}</li>`).join('')}
              </ul>
            </div>
          ` : ''}
        </div>
      `;
      if (this.markers.length > 0) {
        this.currentInfoWindow = new google.maps.InfoWindow({
          content: infoContent
        });
        this.currentInfoWindow.open(this.map, this.markers[0]);
        this.markers[0].addListener('click', () => {
          if (this.currentInfoWindow) {
            this.currentInfoWindow.open(this.map, this.markers[0]);
          }
        });
      }
      this.updateMapStylesForAnalysis(analysis);
    } catch (error) {
      console.error('Error displaying AI analysis:', error);
    }
  }

  getDifficultyLabel(score) {
    if (score < 0.3) return 'Easy';
    if (score < 0.6) return 'Moderate';
    if (score < 0.8) return 'Challenging';
    return 'Very Challenging';
  }

  updateMapStylesForAnalysis(analysis) {
    const styles = [...this.CONFIG.MAP_STYLES];
    if (analysis.route_type === 'trail') {
      styles.push({
        featureType: 'landscape.natural',
        stylers: [{ visibility: 'on', weight: 2 }]
      });
    }
    this.map.setOptions({ styles });
  }

  showRouteDetails(route) {
    window.location.href = `/route/${route.id}`;
  }
}

let pathfinderApp = null;

function initMap() {
  if (!pathfinderApp) {
    pathfinderApp = new PathfinderApp();
    window.pathfinder = pathfinderApp;
  }
  pathfinderApp.initializeMap().catch(console.error);
}

document.addEventListener('DOMContentLoaded', () => {
  pathfinderApp = new PathfinderApp();
  window.pathfinder = pathfinderApp;
  pathfinderApp.init().catch(console.error);
});
