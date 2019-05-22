import {template, delimiters, urls, error_handler, request} from '../../common/utils';
import VuejsPaginate from 'vuejs-paginate';

export default {
    template: template('#main-template'),
    delimiters,
    props: ['all'],
    components: {
        paginate: VuejsPaginate,
    },
    data: function () {
        return {
            votings: [],
            is_admin: window.is_admin,
            page_size: 50,
            page: 1,
        }
    },
    methods: {
        update_voting_list: function () {
            const that = this;
            const url = this.is_admin && this.all ? urls.votings_list : urls.available_votings_list;
            request(url + '?page=' + this.page).then(function (data) {
                that.votings = data;
            }, error_handler);
        },
        show_page: function (page) {
            this.page = page;
            this.update_voting_list();
        },
    },
    watch: {
        all() {
            this.update_voting_list();
        }
    },
    beforeRouteUpdate: function () {
        console.log('before update');
        this.update_voting_list();
    },
    mounted: function () {
        console.log('mounted');
        this.update_voting_list();
    }
}