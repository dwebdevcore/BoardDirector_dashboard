import {deep_copy, delimiters, error_handler, request, template, trans, urls} from "../../common/utils";
import Vue from "vue";
import QuestionForm from "../components/QuestionForm";
import VoterForm from "../components/VoterForm";
import QuestionAnswerResult from "../components/QuestionAnswerResult";
import Errors from "../../common/components/Errors";
import {UrlMaker} from "../common";

export default {
    template: template('#voting-questions-template'),
    delimiters: delimiters,
    data() {
        return {
            voting: {},
            memberships: [],
            committees: [],
            edit_questions: {}, // key 0 is for new question
        }
    },
    components: {
        QuestionForm,
        VoterForm,
        QuestionAnswerResult,
        Errors,
    },
    methods: {
        init_voting() {
            request(UrlMaker.make_voting_url(this.$route.params.id)).then(data => {
                this.voting = data;

                if (!this.voting.questions.length) {
                    this.add_question();
                }
                if (!this.voting.voters.length) {
                    this.add_voter();
                }
            }, error_handler);
        },

        init_members() {
            request(urls.profiles_memberships_list).then(memberships => this.memberships = memberships.results, error_handler);
        },

        init_committees() {
            request(urls.committees_list).then(committees => this.committees = committees.results, error_handler);
        },

        add_question() {
            Vue.set(this.edit_questions, 0, {
                question_type: 1,
                question: '',
                voting: this.voting.id,
                ordering: 1000,
                answers: [],
                candidates: [],
            });
        },

        start_edit_question(question) {
            Vue.set(this.edit_questions, question.id, deep_copy(question));
        },

        save_question(question) {
            let data = deep_copy(question);
            delete data._errors;

            request(UrlMaker.make_question_url(question), question.id ? 'PUT' : 'POST', data).then(
                success => {
                    this.init_voting();
                    this.edit_questions[question.id || 0] = null;
                },
                error => {
                    if (error.status === 400) {
                        question._errors = error.responseJSON;
                    } else {
                        error_handler(error);
                    }
                });
        },

        delete_question(question) {
            swal({
                title: trans.delete_question,
                text: trans.delete_question_text,
                type: 'warning',
                showCancelButton: true,
                confirmButtonClass: 'bg-danger',
                confirmButtonText: trans.delete_text,
                cancelButtonText: trans.cancel_text,
            }).then(() => {
                request(UrlMaker.make_question_url(question), 'DELETE')
                    .then(success => this.init_voting(), error_handler);
            }, function () {
            });
        },

        publish() {
            request(UrlMaker.make_voting_url(this.voting.id) + 'publish/', 'POST').then(
                success => this.$router.push('/view/' + success.id),
                error => {
                    if (error.status === 400) {
                        Vue.set(this.voting, '_errors', error.responseJSON);
                    } else {
                        error_handler(error)
                    }
                }
            );
        },

        answer_result(question_id, answer_id) {
            return this.voting.result && this.voting.result.questions[question_id] && this.voting.result.questions[question_id][answer_id];
        }
    },
    computed: {
        membership_by_id() {
            const result = {};
            this.memberships.forEach(m => result[m.id] = m);
            return result;
        }
    },
    mounted() {
        this.init_voting();
        this.init_members();
        this.init_committees();
        $('#content').addClass('has-right-side');
    },
    destroyed() {
        $('#content').removeClass('has-right-side');
    },
}