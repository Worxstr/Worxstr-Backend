<template>
  <v-app class="d-flex flex-column fill-height">
    <v-app-bar
      color="white"
      class="flex-grow-0"
      elevate-on-scroll
      scroll-target="#scroll-target"
    >
      <v-container class="py-0 fill-height">
        <router-link to="/" style="text-decoration: none">
          <v-avatar class="mr-10" color="grey darken-1" size="32">
            <span class="white--text">W</span>
          </v-avatar>
        </router-link>

        <div class="d-flex flex-row" v-if="!$vuetify.breakpoint.smAndDown">
          <v-btn
            v-for="link in links"
            :key="link"
            text
            :to="{ name: link.label }"
            active-class="primary--text"
            >{{ link.label }}</v-btn
          >
        </div>

        <v-spacer />

        <div v-if="authenticatedUser">
          <v-menu v-model="menu" :close-on-content-click="false" bottom left>
            <template v-slot:activator="{ on, attrs }">
              <v-btn icon>
                <v-icon v-bind="attrs" v-on="on">mdi-bell-outline</v-icon>
              </v-btn>
            </template>

            <v-card>
              <v-list two-line>
                <v-list-item-group>
                  <template v-for="(item, index) in notifs">
                    <v-list-item :key="item.title">
                      <template v-slot:default>
                        <v-list-item-content>
                          <v-list-item-title
                            v-text="item.title"
                          ></v-list-item-title>

                          <v-list-item-subtitle
                            class="text--primary"
                            v-text="item.headline"
                          ></v-list-item-subtitle>

                          <v-list-item-subtitle
                            v-text="item.subtitle"
                          ></v-list-item-subtitle>
                        </v-list-item-content>

                        <v-list-item-action>
                          <v-list-item-action-text
                            v-text="item.action"
                          ></v-list-item-action-text>

                          <v-icon color="yellow darken-3"> mdi-star </v-icon>
                        </v-list-item-action>
                      </template>
                    </v-list-item>

                    <v-divider
                      v-if="index < notifs.length - 1"
                      :key="index"
                    ></v-divider>
                  </template>
                </v-list-item-group>
              </v-list>
            </v-card>
          </v-menu>

          <v-btn icon @click="signOut">
            <v-icon>mdi-logout-variant</v-icon>
          </v-btn>
        </div>

        <div v-else>
          <v-btn text :to="{ name: 'signIn' }" active-class="primary--text"
            >Sign in</v-btn
          >
        </div>
      </v-container>
    </v-app-bar>

    <v-main
      id="scroll-target"
      class="grey lighten-3 d-flex flex-column fill-height"
    >
      <v-container fluid class="pa-0 fill-height align-start">
        <transition appear name="slide-y-transition" mode="out-in">
          <router-view />
        </transition>
      </v-container>
    </v-main>

    <transition name="slide-fade">
      <v-bottom-navigation
        v-model="value"
        :input-value="active"
        v-if="
          $vuetify.breakpoint.smAndDown &&
          authenticatedUser &&
          $route.name != 'home' &&
          $route.name != 'conversation'
        "
        color="indigo"
        grow
      >
        <v-btn
          v-for="(link, index) in links"
          :key="index"
          :value="link.label"
          :to="{ name: link.label }"
        >
          <span>{{ link.label | capitalize }}</span>

          <v-icon>{{ link.icon }}</v-icon>
        </v-btn>
      </v-bottom-navigation>
    </transition>
  </v-app>
</template>

<script lang="ts">
import Vue from "vue";
import { mapState } from "vuex";

export default Vue.extend({
  name: "App",
  methods: {
    signOut() {
      this.authenticatedUser = false;
      this.$router.push("/");
    },
  },
  computed: {
    ...mapState(["showBottomNav"]),
  },
  data: () => ({
    authenticatedUser: true,
    links: [
      {
        icon: "mdi-clock-outline",
        label: "clock",
      },
      {
        icon: "mdi-calendar-check",
        label: "availability",
      },
      {
        icon: "mdi-calendar-multiselect",
        label: "schedule",
      },
      {
        icon: "mdi-message-text-outline",
        label: "messages",
      },
    ],
    menu: false,
    notifs: [
      {
        action: "15 min",
        headline: "Brunch this weekend?",
        subtitle: `I'll be in your neighborhood doing errands this weekend.`,
        title: "Ali Connors",
      },
      {
        action: "2 hr",
        headline: "Summer BBQ",
        subtitle: `Wish I could come, but I'm out of town this weekend.`,
        title: "me, Scrott, Jennifer",
      },
      {
        action: "6 hr",
        headline: "Oui oui",
        subtitle: "Do you have Paris recommendations? Have you ever been?",
        title: "Sandra Adams",
      },
      {
        action: "12 hr",
        headline: "Birthday gift",
        subtitle:
          "Have any ideas about what we should get Heidi for her birthday?",
        title: "Trevor Hansen",
      },
      {
        action: "18hr",
        headline: "Recipe to try",
        subtitle:
          "We should eat this: Grate, Squash, Corn, and tomatillo Tacos.",
        title: "Britta Holt",
      },
    ],
  }),
});
</script>

<style scoped lang="scss">
.v-bottom-navigation {
  transform: initial !important;
  height: 56px !important;
}
.slide-fade-enter-active, .slide-fade-leave-active {
  transition: all 0.2s ease !important;
}
.slide-fade-enter, .slide-fade-leave-to {
  transform: translateY(100%) !important;
  height: 0 !important;
  opacity: 0;
}

main {
  flex: 1 !important;
  overflow: auto;
}
.v-main__wrap {
  height: 100%;
}
.v-app-bar {
  z-index: 1;
}
</style>