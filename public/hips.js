(function($) {
    $( ".jqconsole-ansi-hidden").replaceWith(function() {
        body = $(this).contents();
        alert("hi " + body);
    });
    //$('.hidden').on("click", function(e) {
    //
    //});
})($);