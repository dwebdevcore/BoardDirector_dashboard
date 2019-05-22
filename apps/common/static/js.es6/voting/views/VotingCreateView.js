import {deep_copy, delimiters, error_handler, request, template, urls} from "../../common/utils";
import VoterForm from "../components/VoterForm";
import VotersList from "../components/VotersList";
import Errors from "../../common/components/Errors";
import datetimepicker from "../../common/directives/datetimepicker";
import {UrlMaker} from "../common";

export default {
    template: template('#voting-create-template'),
    delimiters: delimiters,
    data() {
        return {
            voting: null,
            memberships: [],
            committees: [],
        }
    },
    directives: {
        datetimepicker
    },
    components: {
        VoterForm,
        VotersList,
        Errors,
    },
    methods: {
        save() {
            this._save((success, is_new) => {
                if (is_new) {
                    this.$router.push('/questions/' + success.id)
                } else {
                    this.$router.push('/view/' + success.id)
                }
            })
        },

        publish() {
            this._save(voting => {
                request(UrlMaker.make_voting_url(voting.id) + 'publish/', 'POST').then(
                    success => this.$router.push('/view/' + success.id),
                    error => {
                        if (error.status === 400) {
                            Vue.set(this.voting, '_errors', error.responseJSON);
                        } else {
                            error_handler(error)
                        }
                    }
                );
            })
        },

        _save(on_success) {
            const is_new = !this.voting.id;
            const copy = deep_copy(this.voting);
            delete copy._errors;

            if (!copy.add_voters.memberships && !copy.add_voters.committees && !copy.add_voters.all_members) {
                delete copy.add_voters;
            } else {
                copy.add_voters.memberships = copy.add_voters.memberships || [];
                copy.add_voters.committees = copy.add_voters.committees || [];
                copy.add_voters.all_members = copy.add_voters.all_members || [];
            }

            const url = is_new ? urls.votings_list : UrlMaker.make_voting_url(this.voting.id);

            request(url, is_new ? 'POST' : 'PUT', copy).then(
                success => {
                    on_success(success, is_new);
                },
                error => {
                    if (error.status === 400) {
                        this.voting._errors = error.responseJSON;
                    } else {
                        error_handler(error);
                    }
                });
        },

        init_members() {
            request(urls.profiles_memberships_list).then(memberships => this.memberships = memberships.results, error_handler);
        },

        init_committees() {
            request(urls.committees_list).then(committees => this.committees = committees.results, error_handler);
        },

        init_new_voting() {
            this.voting = {
                name: '',
                start_time: new Date(),
                end_time: '',
                is_anonymous: false,
                state: 0,
                voters: [],
                add_voters: {
                    all_members: ["members"],
                    memberships: [],
                    committees: [],
                    weight: 1,
                },
            };
        },

        init_voting() {
            request(UrlMaker.make_voting_url(this.$route.params.id)).then(
                data => {
                    this.voting = data;
                    this.voting.add_voters = {
                        all_members: [],
                        memberships: [],
                        committees: [],
                        weight: 1,
                    }
                },
                error_handler
            );
        },

        delete_voter(voter) {
            swal({
                title: trans.delete_voter,
                text: trans.delete_voter_text,
                type: 'warning',
                showCancelButton: true,
                confirmButtonClass: 'bg-danger',
                confirmButtonText: trans.delete_text,
                cancelButtonText: trans.cancel_text,
            }).then(() => {
                request(UrlMaker.make_voter_url(voter), 'DELETE')
                    .then(success => this.init_voting(), error_handler);
            }, function () {
            });
        },
    },
    computed: {
        errors() {
            if (!this.voting._errors) {
                Vue.set(this.voting, '_errors', {});
            }
            return this.voting._errors;
        }
    },
    mounted() {
        $('#content').addClass('has-right-side');
        this.init_members();
        this.init_committees();
        if (this.$route.params.id) {
            this.init_voting();
        } else {
            this.init_new_voting();
        }
    },
    destroyed() {
        $('#content').removeClass('has-right-side');
    },
}