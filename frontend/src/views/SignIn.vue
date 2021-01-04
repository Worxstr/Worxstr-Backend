<template>
  <v-container
    class="sign-in fill-height d-flex flex-column justify-center align-center"
  >
    <v-card>
      <form @submit.prevent="signIn">
        <v-card-title>Sign in</v-card-title>

        <v-card-text>
          <v-text-field label="Email" type="email" v-model="email" />
          <v-text-field label="Password" type="password" v-model="password" />
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text color="primary" type="submit">Sign in</v-btn>
        </v-card-actions>
      </form>
      <v-fade-transition>
        <v-overlay absolute opacity="0.2" v-if="loading">
          <v-progress-circular indeterminate/>
        </v-overlay>
      </v-fade-transition>
    </v-card>
  </v-container>
</template>

<script>
export default {
  name: "signIn",
  data: () => ({
    email: "",
    password: "",
    loading: false,
  }),
  methods: {
    async signIn() {
      this.loading = true
      await this.$store.dispatch("signIn", {
        email: this.email,
        password: this.password,
      })
      console.log('test')
      this.loading = false
    },
  },
};
</script>
