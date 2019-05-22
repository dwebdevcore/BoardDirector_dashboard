import VueRouter from "vue-router";
import Vue from "vue";
import VoteMainView from "./voting-vote/views/VoteMainView";
import {nl2br} from "./common/filters";

const routes = [
    {path: '/', component: VoteMainView, props: {all: false}},
    {path: '/*', redirect: '/'},
];

const router = new VueRouter({routes});

Vue.filter('nl2br', nl2br);

new Vue({
    router: router
}).$mount('#app');
