<template>
  <v-container
    class="sign-in fill-height d-flex flex-column justify-center align-center"
  >
    <v-card>
      <v-card-title>Sign in</v-card-title>

      <v-card-text>
        <v-text-field label="Email" type="email"/>
        <v-text-field label="Password" type="password"/>
      </v-card-text>

      <v-card-actions>
				<v-spacer></v-spacer>
        <v-btn text color="primary">Sign in</v-btn>
      </v-card-actions>
    </v-card>
  </v-container>
</template>
