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
    </v-card>
  </v-container>
</template>

<script>
export default {
  name: "signIn",
  data: () => ({
    email: "",
    password: "",
  }),
  methods: {
    signIn() {
      this.$store.dispatch("signIn", {
        email: this.email,
        password: this.password,
      });
    },
  },
}
</script>
