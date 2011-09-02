(function($) {
    $().ready(function() {
        $('html').removeClass('no-js').addClass('js');

        // Apply language change once another language is selected
        $('#language').change(function() {
            $('#language-switcher').submit();
        });
        $('#browserid-login').click(login);
    });
    var login = function (event) {
        /* link's href goes to no-JavaScript fallback */
        var form;
        event.preventDefault();
        navigator.id.getVerifiedEmail(function(assertion) {
            if (assertion) {
                form = $('form#browserid');
                $('#id_assertion', form).attr('value', assertion.toString());
                form.submit();
            } else {
                window.location = $(this).attr('href');
            }
        });
    };
})(jQuery);
