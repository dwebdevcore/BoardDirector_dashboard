import {delimiters, template} from "../../common/utils";
import Errors from "../../common/components/Errors";
import Vue from "vue";
import Vue2Selectize from "../../common/components/Vue2Selectize";

export default {
    template: template('.voter-form-template'),
    delimiters: delimiters,
    props: ['voter', 'memberships', 'existing_voters', 'committees'],
    data() {
        return {}
    },
    components: {
        Errors,
        Vue2Selectize,
    },
    computed: {
        errors() {
            if (!this.voter._errors) {
                Vue.set(this.voter, '_errors', {});
            }
            return this.voter._errors;
        },
        available_memberships() {
            let result = [];
            let selected = {};
            this.existing_voters.forEach(v => selected[v.membership] = 1);
            result = this.memberships.filter(m => !selected[m.id]);
            return result;
        },
        voter_options() {
            return this.available_memberships.map(m => {
                return {text: m.first_name + ' ' + m.last_name, value: {id: m.id}}
            })
        },
    }
}
