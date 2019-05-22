// function setHeaderText($header, isExpanded) {
//     $header.text(function () {
//         var txt = $header.text().replace(/\<\</g, "").replace(/\>\>/g, "").trim();
//         return (isExpanded) ? "<< " + txt : txt + " >>";
//     });
// }
function setHeaderText($header, isExpanded) {
    $i = $header.find('i');
    if(isExpanded){
        $i.removeClass('fa-chevron-down').addClass('fa-chevron-up');
    }else{
        $i.removeClass('fa-chevron-up').addClass('fa-chevron-down');
    }
}

$(document).ready(function() {
    // $(".expand-header").each(function() {setHeaderText($(this));});
    $(".expand-header").click(function () {
        $header = $(this);
        $content = $header.next(); // content is expected directly next to header in the DOM
        //open up the content needed - toggle the slide- if visible, slide up, if not slidedown.
        $content.slideToggle(500, function () { setHeaderText($header, $content.is(":visible")); });
    }).click();
});
