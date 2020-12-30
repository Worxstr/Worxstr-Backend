<template>
  <v-container class="availability d-flex flex-column align-center">
    <v-card class="pa-4">
      <div v-for="(day, index) in availability" :key="index">
        <p class="text-subtitle-2">{{index | capitalize}}</p>
        <div class="d-flex flex-row">
          <v-text-field
            v-model="availability[index].startTime"
            label="Start time"
            type="time"
          ></v-text-field>

          <v-spacer class="mx-3"></v-spacer>

          <v-text-field
            v-model="availability[index].endTime"
            label="End time"
            type="time"
          ></v-text-field>
        </div>
      </div>
    </v-card>
  </v-container>
</template>

<script>
export default {
  name: "Availability",
  data: () => ({
    menu: false,
    availability: {
      monday: {
        startTime: '09:00',
        endTime: '17:00',
      },
      tuesday: {
        startTime: '09:00',
        endTime: '17:00',
      },
      wednesday: {
        startTime: '09:00',
        endTime: '17:00',
      },
      thursday: {
        startTime: '09:00',
        endTime: '17:00',
      },
      friday: {
        startTime: '09:00',
        endTime: '17:00',
      },
      saturday: {
        startTime: null,
        endTime: null,
      },
      sunday: {
        startTime: null,
        endTime: null,
      },
    },
  }),
};
</script>