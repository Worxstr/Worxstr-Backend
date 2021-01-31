# Vuetify Google Autocomplete

A Vuetify ready Vue.js (2.x) autosuggest component for the Google Maps Places API.

[![Build Status](https://travis-ci.org/MadimetjaShika/vuetify-google-autocomplete.svg?branch=dev)](https://travis-ci.org/MadimetjaShika/vuetify-google-autocomplete)

## Versions

Latest Beta: 2.0.0-beta.8

Latest Stable: 2.0.1

See [releases](https://github.com/MadimetjaShika/vuetify-google-autocomplete/releases) for details.

## Thanks

Huge thanks and credit goes to [@olefirenko](https://github.com/olefirenko) and contributors for creating [Vue Google Autocomplete](https://github.com/olefirenko/vue-google-autocomplete) from which this Vuetify ready version was inspired.

## Demo

Live Interactive demo: [madimetjashika.github.io/vuetify-google-autocomplete](https://madimetjashika.github.io/vuetify-google-autocomplete/)

## Installation

The easiest way to use Vuetify Google Autocomplete is to install it from **npm** or **yarn**.

```sh
npm i vuetify-google-autocomplete
```

Or

```sh
yarn add vuetify-google-autocomplete
```

### For version >= 2.0.0-alpha.2

Within your main.js or Vue entry point, import and initialise the component.

```javascript
import Vue from 'vue';
import VuetifyGoogleAutocomplete from 'vuetify-google-autocomplete';

Vue.use(VuetifyGoogleAutocomplete, {
  apiKey: '...', // Can also be an object. E.g, for Google Maps Premium API, pass `{ client: <YOUR-CLIENT-ID> }`
  version: '...', // Optional
  language: '...', // Optional
  installComponents: true, // Optional (default: true) - false, if you want to locally install components
  vueGoogleMapsCompatibility: false, // Optional (default: false) - true, requires vue2-google-maps to be configured see https://github.com/xkjyeah/vue-google-maps
});
```

For use with `vue2-google-maps`
```javascript
import Vue from 'vue';
import * as VueGoogleMaps from 'vue2-google-maps';
import VuetifyGoogleAutocomplete from 'vuetify-google-autocomplete';

// @see https://www.npmjs.com/package/vue2-google-maps
Vue.use(VueGoogleMaps, {
    load: {
        key: 'xxxxxxxxs',
        // This is required to use the Autocomplete plugin
        libraries: 'places', // 'places,drawing,visualization'
    },
});

Vue.use(VuetifyGoogleAutocomplete, {
    /*
      not used as loaded with component
      apiKey: key,
    */
    vueGoogleMapsCompatibility: true,
});


```
### For version <= 1.1.0

This component uses Google Maps Places API to get geo suggests for autocompletion, so you have to include the Google Maps Places API in the `<head>` of your HTML:

```html
<!DOCTYPE html>
  <html>
  <head>
    …
    <script src="https://maps.googleapis.com/maps/api/js?key=YOUR_API_KEY_HERE&libraries=places"></script>
  </head>
  <body>
    …
  </body>
</html>
```

To obtain API key please visit the [Google Developer Console](https://console.developers.google.com). The API's that you have to enable in your Google API Manager Dashboard are [Google Maps Geocoding API](https://developers.google.com/maps/documentation/geocoding/start), [Google Places API Web Service](https://developers.google.com/places/web-service/) and [Google Maps Javascript API](https://developers.google.com/maps/documentation/javascript/).

## Usage and API

### For version >= 2.0.0-alpha.1

Simply start using the component in your HTML.

```html
<vuetify-google-autocomplete
    id="map"
    append-icon="search"
    v-bind:disabled="true"
    placeholder="Start typing"
    v-on:placechanged="getAddressData"
>
</vuetify-google-autocomplete>
```

### For version <= 1.1.0

The Vuetify Google Autocomplete works out of the box by just including it.

```js
import VuetifyGoogleAutocomplete from 'vuetify-google-autocomplete'

```

In your template you can use this syntax:

```html
<vuetify-google-autocomplete
    id="map"
    append-icon="search"
    v-bind:disabled="true"
    classname="form-control"
    placeholder="Start typing"
    v-on:placechanged="getAddressData"
>
</vuetify-google-autocomplete>
```

### Properties

**Please refer to the following for a list of all the properties supported by this library:**

*  [Vuetify text fields](https://vuetifyjs.com/en/components/text-fields), for all vuetify props supported.
*  [Props API Docs](https://madimetjashika.github.io/vuetify-google-autocomplete/docs/module-vuetify-google-autocomplete.props.html) or [JSDOCS.md file](https://github.com/MadimetjaShika/vuetify-google-autocomplete/blob/dev/JSDOCS.md), for living code documentation on props defined in this library.

### Events
The component emits the following events, which you can listen in your application:

#### placechanged
Gets triggered when the address data got obtained. This data is available on the returned objects:
* `street_number`, `route`, `locality`, `administrative_area_level_1`, `country`, `postal_code`, `latitude`, `longitude`.
* `place` - [PlaceResult object](https://developers.google.com/maps/documentation/javascript/reference#PlaceResult) is available as second parameter.

#### no-results-found
Gets triggered when a user entered the name of a Place that was not suggested and pressed the Enter key, or the Place Details request failed.

Pleae refer to [Vuetify text field events](https://vuetifyjs.com/en/components/text-fields) for all vuetify supported events.

### Exposed component functions

These functions are accessible by setting "ref" on the component ([Refs documentation](https://vuejs.org/v2/guide/components.html#Child-Component-Refs)). See example below how to use these functions.

#### clear()

Call to clear the value of the user input.

#### focus()

Call focus to focus on the element

#### blur()

Call blur to blur (unfocus) the element

#### update(value)

Call to update the user input with a new value


### Example

Please note that you need to provide the method that will listen (`v-on:placechanged`) to for an event when the address data is obtained. In the example below, the method is ``getAddressData``.

```html
<template>
    <div>
        <h2>Your Address</h2>
        <vuetify-google-autocomplete
            ref="address"
            id="map"
            classname="form-control"
            placeholder="Please type your address"
            v-on:placechanged="getAddressData"
            country="sg"
        >
        </vuetify-google-autocomplete>
    </div>
</template>

<script>
    export default {
        data: function () {
            return {
              address: ''
            }
        },
        mounted() {
            // To demonstrate functionality of exposed component functions
            // Here we make focus on the user input
            this.$refs.address.focus();
        },
        methods: {
            /**
            * When the location found
            * @param {Object} addressData Data of the found location
            * @param {Object} placeResultData PlaceResult object
            * @param {String} id Input container ID
            */
            getAddressData: function (addressData, placeResultData, id) {
                this.address = addressData;
            }
        }
    }
</script>
```

### Exposed component slots

The slots available are proxied [`v-text-field`](https://vuetifyjs.com/en/components/text-fields/) slots.

#### append

Adds an item inside the input and after input content. (Note in underlying `v-text-field` this slot overrides `append-icon` prop.)

#### append-outer

Adds an item inside the input and after input content. (Note in underlying `v-text-field` this slot overrides `append-outer-icon` prop.)

#### label

Replaces the default label

#### prepend

Adds an item outside the input and before input content. (Note in underlying `v-text-field` this slot overrides `prepend-icon` prop.)

#### prepend-inner

Adds an item inside the input and before input content.  (Note in underlying `v-text-field` this slot overrides `prepend-inner-icon` prop.)

#### progress

Slot for custom progress linear (displayed when **loading** prop is not equal to Boolean False)

### Example

Use slots as you would any other component. Example below uses `append` which uses a component rather than the `append-icon`
props (note: this defers slot behaviour back to the `v-text-field` implementation).

```html
<template>
    <div>
        <h2>Your Address</h2>
        <vuetify-google-autocomplete
            ref="address"
            id="map"
            classname="form-control"
            placeholder="Please type your address"
            v-on:placechanged="getAddressData"
            country="sg"
        >
            <template #append>
                <!-- my fancy component rather than a simple icon -->
                <my-btn/>
            </template>
        </vuetify-google-autocomplete>
    </div>
</template>
```

## Contributing

Let's make this an awesome vuetify component! Collaborations and contributions are welcome!

[code of conduct]: https://thoughtbot.com/open-source-code-of-conduct

### Contribution Guidlines

Have a read through the [Contributor Code of Conduct](https://github.com/MadimetjaShika/vuetify-google-autocomplete/blob/master/CODE_OF_CONDUCT.md). Pretty standard, nothing hectic.

Fork, then clone the repo:

    git clone git@github.com:your-username/vuetify-google-autocomplete.git

Install dependencies with **npm**

    npm install

   or **yarn**

    yarn


Make your changes, and observe them at dev-time by running

    npm run dev

and going to the displayed URL to see your changes.

Then, ensure tests are written for your changes. Ensure that your changes pass all the tests:

    npm run test

Ensure that your changes are documented via JSDocs standard, then run

    npm run docs

to update the JSDocs.

If relevant, please ensure that you update the README and demo/example accordingly.

Push to your fork and [submit a pull request](https://github.com/MadimetjaShika/vuetify-google-autocomplete/compare/).

If all is well, your changes will be merged timeously!

Feel free to also post issues for bug fixes or enhancements or anything.

### Roadmap

I'm planning on updating this library to support the most latest version of vuetify during the month of December 2019. This would include potentially having this library as a vue cli 3.* supported plugin.

If you've got any requests, please post them via issues and i'll look into them.

PS - I am looking for people to help me maintain this library. The demand has grown since creation and unfortunately i'm unable to support it regularly at an acceptable rate. If you're keen, please drop me a mail me at madi@mjshika.xyz.
