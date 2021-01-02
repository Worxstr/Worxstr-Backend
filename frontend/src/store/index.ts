import Vue from 'vue'
import Vuex from 'vuex'
import axios from 'axios'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    clock: {
      history: {}
    }
  },
  mutations: {
    SET_CLOCK_HISTORY(state, data) {
      state.clock.history = {
        ...state.clock.history,
        ...data.reduce((obj, item) => {
          obj[item.id] = item
          return obj
        }, {})
      }
    }
  },
  actions: {
    async getClockHistory({ commit }, { limit, offset }) {
      const { data } = await axios.get('http://localhost:5000/api/clock/history', {
        params: {
          limit,
          offset
        }
      })
      commit('SET_CLOCK_HISTORY', data.history)
    }
  },
  getters: {
    // TODO: Transform this and add labels, separated by day of week
    clockHistory: state => state.clock.history
  },
  modules: {
  }
})
