class SearchPageHandler {
  constructor() {
    this.map = window.pathfinder.map;
    this.autocomplete = null;
  }

  init() {
    // Use the global PathfinderApp instance for the map
    this.map = window.pathfinder.map;
    this.setupAutocomplete();
  }

  setupAutocomplete() {
    const searchInput = document.getElementById('location-input');
    if (searchInput && google.maps.places) {
      this.autocomplete = new google.maps.places.Autocomplete(searchInput);
      this.autocomplete.bindTo('bounds', this.map);
      this.autocomplete.addListener('place_changed', () => {
        const place = this.autocomplete.getPlace();
        if (!place.geometry) {
          window.pathfinder.showError('No details available for this location');
          return;
        }
        // Delegate location selection to the global PathfinderApp instance
        window.pathfinder.handleLocationSelect(place.geometry.location);
      });
    }
  }
}

document.addEventListener('DOMContentLoaded', function () {
  const checkPathfinder = setInterval(() => {
    if (window.pathfinder && window.pathfinder.map) {
      clearInterval(checkPathfinder);
      const searchHandler = new SearchPageHandler();
      searchHandler.init();
    }
  }, 100);
});
