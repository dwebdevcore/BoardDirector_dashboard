export default {
    inserted: function (el, binding, vnode) {
        console.log('hey there');
        $(el).popover({html: true});
    },
}