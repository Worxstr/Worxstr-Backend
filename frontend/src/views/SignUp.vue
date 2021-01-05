<template>
  <v-container
    class="sign-in fill-height d-flex flex-column justify-center align-center"
  >
    <v-card>
      <form @submit.prevent="signUp">
        <v-card-title>Sign up</v-card-title>

        <v-card-text>
          <v-text-field label="First name" v-model="form.first_name" />
          <v-text-field label="Last name" v-model="form.last_name" />
          <v-text-field label="Email" type="email" v-model="form.email" />
          <v-text-field label="Phone" type="phone" v-model="form.phone" />
          <v-text-field
            label="Password"
            type="password"
            v-model="form.password"
          />
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text color="primary" type="submit">Sign up</v-btn>
        </v-card-actions>
      </form>

      <v-fade-transition>
        <v-overlay absolute opacity="0.2" v-if="loading">
          <v-progress-circular indeterminate />
        </v-overlay>
      </v-fade-transition>
    </v-card>
  </v-container>
</template>

<script>
export default {
  name: "signUp",
  data: () => ({
    form: {
      'first_name': "",
      'last_name': "",
      'phone': "",
      'email': "",
      'password': "",
    },
    loading: false,
  }),
  methods: {
    async signUp() {
      this.loading = true;
      await this.$store.dispatch("signUp", this.form);
      this.loading = false;
    },
  },
};
</script>
