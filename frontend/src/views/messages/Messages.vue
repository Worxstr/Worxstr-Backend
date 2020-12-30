<template>
  <v-container class="messages fill-height align-start d-flex flex-row pa-md-2 pa-0">
    <v-card
      v-if="$route.name == 'messages' || $vuetify.breakpoint.mdAndUp"
      class="mr-md-4"
      :width="$route.name == 'conversation' ? '30%' : '100%'"
      :max-width="$vuetify.breakpoint.mdAndUp ? '350px' : '100%'"
      :rounded="$vuetify.breakpoint.mdAndUp ? 'lg' : '0'"
    >
      <Conversations />
    </v-card>

    <v-card
      v-if="$route.name == 'conversation'"
      class="flex-grow-1 fill-height"
      :rounded="$vuetify.breakpoint.mdAndUp ? 'lg' : '0'"
    >
      <router-view />
    </v-card>
  </v-container>
</template>

<script>
import Conversations from "./Conversations";

export default {
  name: "Messages",
  components: { Conversations },
};
</script>