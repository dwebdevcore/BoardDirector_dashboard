jQuery(document).ready(function($) {

    heightSetter('#content', true);

});

$(window).resize(function() {
    heightSetter('#content', true);
});