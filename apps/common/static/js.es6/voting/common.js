import {urls} from '../common/utils';

export const VOTING_TYPE = {
    YES_NO: 1,
    SINGLE_SELECT: 2,
    MULTIPLE_SELECT: 3,
    ELECTION: 4,
    FOR_AGAINST_ABSTAIN: 5,
};

export const FAA_CHOICES = {
    FOR_: 1,
    AGAINST: 2,
    ABSTAIN: 3,
};

export const UrlMaker = {
    make_voting_url(voting_id) {
        return urls.votings_detail.replace('9999', voting_id);
    },

    make_question_url(question) {
        return question.id
            ? urls.votings_questions_detail.replace('1111', question.voting).replace('2222', question.id)
            : urls.votings_questions.replace('1111', question.voting);
    },

    make_voter_url(voter) {
        return voter.id
            ? urls.votings_voters_detail.replace('1111', voter.voting).replace('2222', voter.id)
            : urls.votings_voters.replace('1111', voter.voting);
    },
}