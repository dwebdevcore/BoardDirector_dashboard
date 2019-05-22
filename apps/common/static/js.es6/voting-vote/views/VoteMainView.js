import Vue from 'vue'
import Component from 'vue-class-component'
import {template, delimiters, urls, error_handler, request, deep_copy} from '../../common/utils';
import {VOTING_TYPE, FAA_CHOICES} from "../../voting/common";
import Errors from "../../common/components/Errors";
import {focus} from "vue-focus";

@Component({
    template: template('#main-template'),
    delimiters,
    components: {Errors},
    directives: {focus},
})
export default class VoteMainView extends Vue {
    voting = null;
    voter_key = window.voter_key;
    current_question_index = null;
    VOTING_TYPE = VOTING_TYPE;
    FAA_CHOICES = FAA_CHOICES;
    answer = null;
    errors = {};
    show_vote_note = false;

    update_voting() {
        request(urls.vote_voting_details).then(voting => {
            this.voting = voting;
            if (this.current_question_index === null) {
                this._select_first_unanswered_question(voting);
            }
        }, error_handler);
    }

    post_answer() {
        request(urls.vote_voting_details, 'PUT', this.answer).then(
            updated_voting => {
                this.voting = updated_voting;
                if (this.current_question_index + 1 < updated_voting.questions.length) {
                    this.current_question_index += 1;
                    this._update_answer();
                } else {
                    request(urls.vote_voting_mark_done, 'POST', {}).then(done => this.voting = done, error_handler);
                }
            },
            error => {
                if (error.status === 400) {
                    this.errors = error.responseJSON;
                } else {
                    error_handler(error)
                }
            });
    }

    previous_question() {
        this.current_question_index -= 1;
        this._update_answer();
    }

    toggle_vote_note() {
        if (this.show_vote_note) {
            this.show_vote_note = false;
            this.answer.vote_note = null;
        } else {
            this.show_vote_note = true;
        }
    }

    _update_answer() {
        if (this.voting.answers[this.question.id]) {
            this.answer = deep_copy(this.voting.answers[this.question.id]);
        } else {
            this.answer = {
                question: this.question.id,
                yes_no: null,
                answers: [],
                candidate: null,
            };
        }

        this.show_vote_note = !!this.answer.vote_note;
    }

    _select_first_unanswered_question(voting) {
        let answers = {};
        for (let i in voting.answers) {
            answers[voting.answers[i].question] = true;
        }

        voting.questions.some((question, index) => {
            if (!answers[question.id]) {
                this.current_question_index = index;
                return true;
            }
        });

        this._update_answer();
    }

    get question() {
        return this.voting && this.voting.questions[this.current_question_index] || {};
    }

    mounted() {
        this.update_voting();
    }
}