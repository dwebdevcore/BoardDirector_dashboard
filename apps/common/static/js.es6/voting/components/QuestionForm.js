import {delimiters, template, urls} from "../../common/utils";
import Errors from "../../common/components/Errors";
import Vue2Selectize from "../../common/components/Vue2Selectize";
import Vue from "vue";

export default {
    template: template('.question-form-template'),
    delimiters: delimiters,
    props: ['question', 'memberships'],
    data() {
        return {
            new_answer: '',
            new_candidate: 0,
        }
    },
    components: {
        Errors,
        Vue2Selectize,
    },
    methods: {
        check_add_answer() {
            if (this.new_answer) {
                this.question.answers.push({answer: this.new_answer});
                this.new_answer = '';
            }
        },
        answer_error(index) {
            return this.errors.answers && this.errors.answers[index] && this.errors.answers[index].answer;
        }
    },
    watch: {
        new_candidate() {
            if (this.new_candidate) {
                let m = this.membership_by_id[this.new_candidate];
                let candidate = {
                    membership: this.new_candidate,
                    first_name: m.first_name,
                    last_name: m.last_name,
                    bio: m.bio,
                    notes: '',
                };
                this.question.candidates.push(candidate);
                Vue.nextTick(() => this.new_candidate = 0);
            }
        },
    },
    computed: {
        errors() {
            if (!this.question._errors) {
                Vue.set(this.question, '_errors', {});
            }
            return this.question._errors;
        },
        membership_by_id() {
            let result = {};
            this.memberships.forEach(m => result[m.id] = m);
            return result;
        },
        available_memberships() {
            let result = [];
            let selected = {};
            this.question.candidates.forEach(c => selected[c.membership] = 1);
            result = this.memberships.filter(m => !selected[m.id]);
            return result;
        },
    }
}
