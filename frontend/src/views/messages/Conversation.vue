<template>
  <div class="messages d-flex flex-column">
    <v-toolbar flat rounded="lg">
      <v-btn
        icon
        v-if="$vuetify.breakpoint.smAndDown"
        @click="$router.push({ name: 'messages' })"
      >
        <v-icon>mdi-arrow-left</v-icon>
      </v-btn>

      <v-toolbar-title>
        Conversation {{ $route.params.conversationId }}
      </v-toolbar-title>
    </v-toolbar>

    <transition-group
      name="scroll-y-reverse-transition"
      tag="div"
      class="message-container px-4 d-flex flex-column-reverse align-start"
    >
      <div
        v-for="message in messages"
        :key="message.id"
        class="message grey lighten-3 px-4 py-2 mb-2 rounded-xl"
        :class="message.pos"
      >
        <span>{{ message.text }}</span>
      </div>
    </transition-group>

    <form
      @submit.prevent="sendMessage"
      class="d-flex flex-row align-center pa-3"
    >
      <v-text-field
        v-model="message"
        ref="message"
        background-color="grey lighten-3"
        flat
        hide-details
        rounded
        solo
        placeholder="Type a message..."
      ></v-text-field>

      <v-btn color="primary" icon class="ml-3" type="submit">
        <v-icon>mdi-send</v-icon>
      </v-btn>
    </form>
  </div>
</template>

<script>
let id = 6

export default {
  name: "Messages",
  mounted() {
    // TODO: doesnt' work
    this.$refs.message.$el.focus()
  },
  methods: {
    sendMessage() {
      this.messages.unshift({
        text: this.message,
        pos: "right",
        id
      });
      id++;
      this.message = ""
    }
  },
  data: () => ({
    message: "",

    messages: [
      {
        text: "Love u",
        pos: "right",
        id: 5
      },
      {
        text: "Ok do good work lol",
        pos: "left",
        id: 4
      },
      {
        text: "Nothing my shift is starting",
        pos: "right",
        id: 3
      },
      {
        text: "What's up",
        pos: "left",
        id: 2
      },
      {
        text: "Hi",
        pos: "right",
        id: 1
      },
      {
        text: "Hello!",
        pos: "left",
        id: 0
      },
    ],
  }),
};
</script>

<style lang="scss" scoped>
.messages {
  height: 100%;
}

.message-container {
  height: 100%;
  overflow-y: auto;
}

.message {
  transition: all 0.2s;
}
.message.left {
  align-self: flex-start;
}
.message.right {
  align-self: flex-end;
}

.message-enter-active,
.message-leave-active {
  transition: all 0.2s;
}
.message-enter,
.message-leave-to {
  opacity: 0;
  transform: translateY(30px);
}
.message-move {
  transition: transform 0.2s;
}
</style>