function parse_date(value) {
    if (typeof value === 'string') {
        value = moment(value).toDate();
    }
    return value;
}

export default {
    inserted: function (el, binding, vnode) {
        const context = vnode.context;
        const keys = binding.expression.split('.');

        $(el).kendoDateTimePicker({
            format: "MMM. dd, yyyy h:mm tt",
            change: function () {
                let target = context;
                keys.slice(0, -1).forEach(function (key) {
                    target = target[key];
                });
                target[keys[keys.length - 1]] = this.value();
            }
        });

        const picker = $(el).data('kendoDateTimePicker');
        picker.value(parse_date(binding.value));
        picker.trigger('change');
    },
    update: function (el, binding) {
        const picker = $(el).data('kendoDateTimePicker');
        picker.value(parse_date(binding.value));
        picker.trigger('change');
    }
};
