export function datetime_filter(value) {
    if (value) {
        return moment(value).format('MMM DD, YYYY h:mm a');
    }
}

export function nl2br(value) {
    // Temporary removal of html entites, so that it works as simple escaper also.
    return value && value.replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br/>\n');
}