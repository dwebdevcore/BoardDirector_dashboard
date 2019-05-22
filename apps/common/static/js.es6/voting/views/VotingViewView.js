import {delimiters, error_handler, is_admin, request, template, trans, urls} from "../../common/utils";
import Vue from "vue";
import QuestionAnswerResult from "../components/QuestionAnswerResult";
import Errors from "../../common/components/Errors";
import VotersList from "../components/VotersList";
import {UrlMaker} from "../common";

export default {
    template: template('#voting-view-template'),
    delimiters: delimiters,
    data() {
        return {
            voting: {},
            quorum_is_met: false,
            is_admin,
        }
    },
    components: {
        QuestionAnswerResult,
        VotersList,
        Errors,
    },
    methods: {
        init_voting() {
            request(this.make_voting_url(this.$route.params.id)).then(voting => this.voting = voting, error_handler);
        },

        publish() {
            request(this.make_voting_url(this.voting.id) + 'publish/', 'POST').then(
                success => this.init_voting(),
                error => {
                    if (error.status === 400) {
                        Vue.set(this.voting, '_errors', error.responseJSON);
                    } else {
                        error_handler(error)
                    }
                }
            );
        },

        publish_results() {
            request(this.make_voting_url(this.voting.id) + 'publish_results/', 'POST').then(success => this.init_voting(), error_handler);
        },

        resend_email() {
            request(this.make_voting_url(this.voting.id) + 'publish/', 'POST').then(
                success => {
                    swal({
                        title: trans.success,
                        text: trans.resend_done,
                        type: 'success',
                    })
                }, error_handler);
        },

        make_voting_url(voting_id) {
            return urls.votings_detail.replace('9999', voting_id);
        },

        answer_result(question_id, answer_id) {
            return this.voting.result && this.voting.result.questions[question_id] && this.voting.result.questions[question_id][answer_id];
        },

        delete_voting() {
            swal({
                title: trans.delete_voting,
                text: trans.delete_voting_text,
                type: 'warning',
                showCancelButton: true,
                confirmButtonClass: 'bg-danger',
                confirmButtonText: trans.delete_text,
                cancelButtonText: trans.cancel_text,
            }).then(() => {
                request(UrlMaker.make_voting_url(this.voting.id), 'DELETE')
                    .then(success => this.$router.push('/'), error_handler);
            }, function () {
            });
        },
    },
    mounted() {
        this.init_voting();
        $('#content').addClass('has-right-side');
    },
    destroyed() {
        $('#content').removeClass('has-right-side');
    },
}