import {createRouter, createWebHistory} from 'vue-router';
import App from './App.vue';

const routes = [
  {
    path: '/',
    redirect: '/map',
  },
  {
    path: '/map',
    name: 'map',
    component: App,
  },
  {
    path: '/map/:zoom/:lat/:lon',
    name: 'map-location',
    component: App,
  },
  {
    path: '/search',
    name: 'search',
    component: App,
  },
  {
    path: '/item/Q:id',
    name: 'item',
    component: App,
  },
  {
    path: '/isa/Q:id',
    name: 'isa',
    component: App,
  },
  {
    path: '/documentation',
    name: 'documentation',
    component: App,
  },
];

export default createRouter({
  history: createWebHistory(),
  routes,
});
