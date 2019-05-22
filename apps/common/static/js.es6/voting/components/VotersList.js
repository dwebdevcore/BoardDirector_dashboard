import {delimiters, template} from "../../common/utils";

export default {
    template: template('#voters-list-template'),
    delimiters,
    props: {
        can_edit: Boolean,
        voters: Array,
        delete: Function,
    },
}