<template>
  <v-container
    class="clock d-flex flex-column flex-md-row-reverse justify-md-center align-md-start"
  >
    <div
      class="mx-15 d-flex align-center align-md-start flex-column justify-center"
      style="margin-top: 20vh; margin-bottom: 15vh; top: 60px; position: sticky"
    >
      <h6 class="text-h6">Your shift ends at</h6>
      <h3 class="text-h3 py-2 font-weight-bold">
        {{
          nextEvent.timestamp
            .toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
            .replace(/^0(?:0:0?)?/, "")
        }}
      </h3>
      <p class="text-subtitle-2 text-center text-md-left">
        <countdown :end-time="nextEvent.timestamp">
          <template v-slot:process="props">
            <span>
              That's in
              <span v-if="props.timeObj.d != 0"
                >{{ props.timeObj.d }} days,
              </span>
              <span v-if="props.timeObj.h != 0"
                >{{ props.timeObj.h }} hours,
              </span>
              <span v-if="props.timeObj.m != 0"
                >{{ props.timeObj.m }} minutes,
              </span>
              {{ props.timeObj.s }} seconds.
            </span>
          </template>
          <template v-slot:finish>
            <span>That's right now!</span>
          </template>
        </countdown>
      </p>

      <div class="d-flex flex-row">
        <v-expand-x-transition>
          <div v-if="!this.break" class="py-2">
            <v-btn
              raised
              :color="clocked ? 'pink' : 'green'"
              @click="toggleClock()"
              class="pa-6 mr-2"
              width="130px"
              dark
              style="transition: background-color 0.3s"
            >
              Clock {{ clocked ? "out" : "in" }}
            </v-btn>
          </div>
        </v-expand-x-transition>

        <v-expand-x-transition>
          <div v-if="clocked" class="py-2">
            <v-btn
              raised
              :color="this.break ? 'green' : 'amber'"
              @click="toggleBreak()"
              class="pa-6"
              width="130px"
              dark
              style="transition: background-color 0.3s"
            >
              {{ this.break ? "End" : "Start" }} break
            </v-btn>
          </div>
        </v-expand-x-transition>
      </div>
    </div>

    <v-card
      class="align-self-center"
      width="100%"
      max-width="500px"
      rounded="lg"
    >
      <v-card-title class="ma-1">Your history</v-card-title>

      <v-timeline align-top dense>
        <transition-group name="scroll-y-transition">
          <div v-for="event in history" :key="event.id || event.time || event.label">
            <v-timeline-item v-if="event.label" hide-dot>
              <span>{{ event.label }}</span>
            </v-timeline-item>

            <v-timeline-item v-else :color="event.color" small>
              <v-row class="pt-1">
                <v-col cols="3">
                  <strong>{{ event.time }}</strong>
                </v-col>
                <v-col>
                  <strong>{{ event.message }}</strong>
                  <div class="caption">{{ event.description }}</div>
                </v-col>
              </v-row>
            </v-timeline-item>
          </div>
        </transition-group>
      </v-timeline>

      <v-card-actions class="d-flex justify-center">
        <v-btn text color="primary">
          <v-icon right dark> mdi-arrow-down </v-icon>
          Load more
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-container>
</template>

<script>
import Vue from "vue"
import vueAwesomeCountdown from "vue-awesome-countdown"

Vue.use(vueAwesomeCountdown, "vac")

const shiftBegin = new Date()
// shiftBegin.setDate(shiftBegin.getDate() + 1) // Add a day
shiftBegin.setHours(9)
shiftBegin.setMinutes(0)
shiftBegin.setSeconds(0)

const shiftEnd = shiftBegin
shiftEnd.setHours(17)

let id = 0

export default {
  name: "Clock",
  data: () => ({
    nextEvent: {
      timestamp: shiftEnd,
      type: "shift_end",
    },
    clocked: true,
    break: false,
    history: [
      {
        label: "Today",
      },
      {
        time: "9:01 am",
        message: "Clocked in",
        color: "green",
        description: "1 min late",
      },
      {
        label: "Yesterday",
      },
      {
        time: "4:55 pm",
        message: "Clocked out",
        color: "pink",
        description: "5 mins left",
      },
      {
        time: "1:06 pm",
        message: "Finished break",
        color: "green",
        description: "2 mins left",
      },
      {
        time: "2:45 pm",
        message: "Started break",
        color: "amber",
        description: "30 mins available",
      },
      {
        time: "9:02 am",
        message: "Clocked in",
        color: "green",
        description: "Caption",
      },
      {
        label: "Thursday",
      },
      {
        time: "4:58 pm",
        message: "Clocked out",
        color: "pink",
        description: "2 mins left",
      },
      {
        time: "1:06 pm",
        message: "Finished break",
        color: "green",
        description: "2 mins left",
      },
      {
        time: "2:45 pm",
        message: "Started break",
        color: "amber",
        description: "30 mins available",
      },
      {
        time: "9:02 am",
        message: "Clocked in",
        color: "green",
        description: "Caption",
      },
    ],
  }),
  methods: {
    toggleClock() {
      this.history.splice(1, 0, {
        time: new Date()
          .toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
          .replace(/^0(?:0:0?)?/, ""),
        message: `Clocked ${this.clocked ? "out" : "in"}`,
        color: this.clocked ? "pink" : "green",
        description: "Blah",
        id
      })
      id++
      this.clocked = !this.clocked
    },
    toggleBreak() {
      this.history.splice(1, 0, {
        time: new Date()
          .toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
          .replace(/^0(?:0:0?)?/, ""),
        message: `${this.break ? "Finished" : "Started"} break`,
        color: this.break ? "green" : "amber",
        description: "Blah",
        id
      })
      id++
      this.break = !this.break
    },
  },
};
</script>
