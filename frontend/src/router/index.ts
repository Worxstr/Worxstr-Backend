import Vue from 'vue'
import VueRouter, { RouteConfig } from 'vue-router'

import Home from '../views/Home.vue'
import SignIn from '../views/SignIn.vue'
import SignUp from '../views/SignUp.vue'
import Clock from '../views/Clock.vue'
import Availability from '../views/Availability.vue'
import Schedule from '../views/Schedule.vue'
import Messages from '../views/messages/Messages.vue'
import Conversation from '../views/messages/Conversation.vue'

import store from '../store'

Vue.use(VueRouter)

const routes = [
  {
    path: '/',
    name: 'home',
    component: Home,
  },
  {
    path: '/sign-in',
    name: 'signIn',
    component: SignIn
  },
  {
    path: '/sign-up',
    alias: '/confirmed',
    name: 'signUp',
    component: SignUp
  },
  {
    path: '/clock',
    name: 'clock',
    component: Clock,
  },
  {
    path: '/availability',
    name: 'availability',
    component: Availability,
  },
  {
    path: '/schedule',
    name: 'schedule',
    component: Schedule,
  },
  {
    path: '/messages',
    name: 'messages',
    component: Messages,
    children: [{
      name: 'conversation',
      path: 'conversation/:conversationId',
      component: Conversation
    }]
  }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

export default router
