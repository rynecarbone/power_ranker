jQuery(document).ready(function() {
 jQuery('[data-toggle="tooltip"]').each(function() {
        var $elem = jQuery($(this));
        $elem.tooltip({
            html:true,
            container: $elem,
            delay: {hide:400}
        });
    });
});
