import VueRouter from "vue-router";
import Vue from "vue";
import VotingMainView from "./voting/views/VotingMainView";
import VotingCreateView from "./voting/views/VotingCreateView";
import VotingQuestionsView from "./voting/views/VotingQuestionsView";
import {datetime_filter, nl2br} from "./common/filters";
import VotingViewView from "./voting/views/VotingViewView";

const admin_routes = [
    {path: '/', component: VotingMainView, props: {all: false}},
    {path: '/all', component: VotingMainView, props: {all: true}},
    {path: '/create', component: VotingCreateView},
    {path: '/view/:id', component: VotingViewView},
    {path: '/edit/:id', component: VotingCreateView},
    {path: '/questions/:id', component: VotingQuestionsView},
    {path: '/*', redirect: '/'},
];

const user_routes = [
    {path: '/', component: VotingMainView, props: {all: false}},
    {path: '/view/:id', component: VotingViewView},
    {path: '/*', redirect: '/'},
];

const router = new VueRouter({routes: window.is_admin ? admin_routes : user_routes});

Vue.filter('datetime', datetime_filter);
Vue.filter('nl2br', nl2br);

new Vue({
    router: router
}).$mount('#app');
