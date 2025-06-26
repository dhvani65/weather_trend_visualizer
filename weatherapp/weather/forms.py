import pdb

import requests
from django import forms

GEO_API_KEY = '6d809f54ba214dff9c2ab5b9b699facc'
GEO_API_URL = 'https://api.opencagedata.com/geocode/v1/json'


class LocationForm(forms.Form):
    state = forms.CharField(max_length=50)
    country = forms.CharField(max_length=50)

    def clean(self):
        cleaned_data = super().clean()
        state = cleaned_data.get('state')
        country = cleaned_data.get('country')

        if not state or not country:
            return

        try:
            response = requests.get(GEO_API_URL, params={
                "q": f"{state}, {country}",
                "key": GEO_API_KEY
            }, timeout=10)
            # pdb; pdb.set_trace()
        except requests.RequestException:
            raise forms.ValidationError("Network error while checking location.")

        if response.status_code != 200:
            raise forms.ValidationError("Failed to retrieve location data.")

        try:
            data = response.json()
        except Exception:
            raise forms.ValidationError("Invalid response from geolocation service.")

        if not data.get('results'):
            raise forms.ValidationError("Location not found.")

        result = data['results'][0]
        components = result.get('components', {})

        # Reject if city, town, or village is present
        if any(k in components for k in ['city', 'town', 'village']):
            raise forms.ValidationError("Only state names are allowed, not cities or towns.")

        matched_state = components.get('state', '').strip().lower()
        matched_country = components.get('country', '').strip().lower()

        if not matched_state or not matched_country:
            raise forms.ValidationError("The state and country are mismatched.")

        # Normalize input
        input_state = state.strip().lower()
        input_country = country.strip().lower()

        # Match country
        if matched_country != input_country:
            raise forms.ValidationError(f"The state '{state}' does not belong to the country '{country}'.")

        # Don't fail on minor state spelling differences (like accents or suffixes)
        if input_state not in matched_state:
            raise forms.ValidationError(
                f"'{state}' was not recognized as a valid state in '{country}'. Did you mean '{matched_state.title()}'?"
            )

        # Save for use in view
        self.cleaned_data['latitude'] = result['geometry']['lat']
        self.cleaned_data['longitude'] = result['geometry']['lng']

