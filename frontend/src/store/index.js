import Vue from 'vue'
import Vuex from 'vuex'
import axios from 'axios'
import router from '../router'

import { normalizeRelations, resolveRelations } from '../plugins/helpers'

Vue.use(Vuex)

axios.defaults.withCredentials = true

const baseUrl = 'http://localhost:5000/api'

const store = new Vuex.Store({
  state: {
    snackbar: {
      show: false,
      text: 'Test',
      timeout: 5000
    },
    authenticatedUser: null,
    clock: {
      clocked: false,
      break: false,
      history: {
        all: [],
        byId: {}
      },
    }
  },
  mutations: {
    SHOW_SNACKBAR(state, snackbar) {
      state.snackbar = {
        ...state.snackbar,
        ...snackbar,
        show: true,
      }
    },
    SET_AUTHENTICATED_USER(state, { user }) {
      state.authenticatedUser = user
      localStorage.setItem('authenticatedUser', JSON.stringify(user))
    },
    UNSET_AUTHENTICATED_USER(state) {
      state.authenticatedUser = null
      localStorage.removeItem('authenticatedUser')
    },
    ADD_CLOCK_EVENT(state, event) {
      Vue.set(state.clock.history.byId, event.id, event)
      if (!state.clock.history.all.includes(event.id))
        state.clock.history.all.push(event.id)
    }
  },
  actions: {
    showSnackbar({ commit }, snackbar) {
      commit('SHOW_SNACKBAR', snackbar)
    },
    async signIn({ commit, dispatch }, credentials) {
      try {
        const { data } = await axios({
          method: 'POST',
          url: `${baseUrl}/auth/login`,
          data: {
            ...credentials,
            'remember_me': true
          },
        })
        dispatch('getAuthenticatedUser')
        router.push({ name: 'clock' })
        return data
      }
      catch (err) {
        commit('UNSET_AUTHENTICATED_USER')
        return err
      }
    },

    async signUp({ dispatch }, userData) {
      try {
        const { data } = await axios({
          method: 'POST',
          url: `${baseUrl}/auth/register`,
          data: userData
        })
        router.push({ name: 'home' })
        dispatch('showSnackbar', { text: "Check your email to verify your account!" })
        return data
      }
      catch (err) {
        return err
      }
    },

    async signOut({ commit }) {
      await axios({
        method: 'POST',
        url: `${baseUrl}/auth/logout`
      })
      commit('UNSET_AUTHENTICATED_USER')
      router.push({ name: 'home' })
    },

    async getAuthenticatedUser({ commit }) {
      const { data } = await axios({
        method: 'GET',
        url: `${baseUrl}/users/me`,

      })
      commit('SET_AUTHENTICATED_USER', { user: data.authenticated_user })
    },

    async loadClockHistory({ commit }, { offset }) {
      const { data } = await axios.get(`${baseUrl}/clock/history`, {
        params: {
          'week_offset': offset
        }
      })
      data.history.forEach(event => {
        // TODO: Normalize nested data
        commit('ADD_CLOCK_EVENT', normalizeRelations(event, [/*'user'*/]))
        /* commit('ADD_USER', event.user, {
          root: true
        }) */
      })
    }
  },
  getters: {
    // TODO: Transform this and add labels, separated by day of week
    clockEvent: (state, _, __, rootGetters) => id => {
      return resolveRelations(state.clock.history.byId[id], [/*'user'*/], rootGetters)
    },
    clockHistory: (state, getters) => {
      let last

      return state.clock.history.all.flatMap((eventId, i) => {
        const event = getters.clockEvent(eventId)
        const current = new Date(event.time)
        const ret = []

        if (!last || !(last.getDate() === current.getDate()
          && last.getMonth() === current.getMonth()
          && last.getFullYear() === current.getFullYear())) {

          ret.push(
            {
              label: current,
              id: `day${i}`
            }
          )
        }
        ret.push(event)
        last = current
        return ret
      })
    }
  },
  modules: {
  }
})

/* axios.interceptors.request.use(config => {
  // Do something before request is sent
  return config;
}, function (error) {
  // Do something with request error
  return Promise.reject(error);
}) */

axios.interceptors.response.use(response => {
  return response
}, error => {

  // if (error.config.hideErrorMessage) return

  let message;
  const res = error.response.data

  console.log(error.request)

  // TODO: this is stupid, don't keep this. use custom axios config
  if (error.request.responseURL == 'http://localhost:5000/api/users/me') return

  if (res.message || res.response.error) {
    message = res.message || res.response.error
  } else {
    const errorList = error.response.data.response.errors
    message = errorList[Object.keys(errorList)[0]][0]
  }
  store.dispatch('showSnackbar', { text: message })

  return Promise.reject(error)
})

export default store