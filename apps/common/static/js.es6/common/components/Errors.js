export default {
    props: {
        error: null
    },
    template: '<span class="k-widget k-tooltip k-tooltip-validation k-invalid-msg" role="alert" v-show="error">' +
    '<span class="k-icon k-warning"></span> {{ error && error.join("; ") }}' +
    '</span>'
}