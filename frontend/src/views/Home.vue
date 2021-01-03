<template>
  <v-container class="home fill-height d-flex flex-column justify-center align-center">
    <h2 class="text-h2 font-weight-bold mb-2">Worxstr</h2>
    <p class="text-subtitle-2">Uhhhh idk what else to put here</p>

    <v-btn v-if="authenticatedUser" @click="signOut" color="primary">Sign out</v-btn>
    <v-btn v-else :to="{name: 'signIn'}" color="primary">Sign in</v-btn>

    <div style="height: 160px;display: block"></div>
  </v-container>
</template>

<script>
import { mapState, mapActions } from 'vuex'

export default {
  name: 'home',
  computed: {
    ...mapState(['authenticatedUser'])
  },
  methods: {
    ...mapActions(['signOut'])
  }
}
</script>