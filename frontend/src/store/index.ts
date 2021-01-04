import Vue from 'vue'
import Vuex from 'vuex'
import axios from 'axios'
import router from '../router'

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
      history: {}
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
    SET_CLOCK_HISTORY(state, { history }) {
      state.clock.history = {
        ...state.clock.history,
        ...history.reduce((obj, item) => {
          obj[item.id] = item
          return obj
        }, {})
      }
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

    async getAuthenticatedUser({ commit, dispatch }) {
      const { data } = await axios({
        method: 'GET',
        url: `${baseUrl}/users/me`,
        
      })
      commit('SET_AUTHENTICATED_USER', { user: data.authenticated_user })
    },

    async getClockHistory({ commit }, { limit, offset }) {
      const { data } = await axios.get(`${baseUrl}/clock/history`, {
        params: {
          limit,
          offset
        }
      })
      commit('SET_CLOCK_HISTORY', data)
    }
  },
  getters: {
    // TODO: Transform this and add labels, separated by day of week
    clockHistory: state => state.clock.history
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