import {delimiters, template, trans} from "../../common/utils";
import popover from "../../common/directives/popover";

export default {
    delimiters,
    template: template('#question-answer-result-template'),
    props: {
        result: {},
        is_anonymous: Boolean,
    },
    directives: {
        popover
    },
    computed: {
        voter_content() {
            let content = this.result.voters.map(voter => {
                let vote = '';
                if (voter.first_name) {
                    vote += voter.first_name;
                }
                if (voter.last_name) {
                    if (vote) {
                        vote += ' ';
                    }
                    vote += voter.last_name;
                }

                if (voter.vote_note) {
                    if (vote) {
                        vote += ': ';
                    }
                    vote += voter.vote_note;
                }
                return vote;
            }).join('<br/>');

            if (this.is_anonymous) {
                if (content) {
                    content = trans.anonymous_voting + ':<br/>' + content;
                } else {
                    content = trans.anonymous_voting;
                }
            }

            return content;
        }
    },
    methods: {
        max(a, b) {
            return Math.max(a, b);
        },
    },
}