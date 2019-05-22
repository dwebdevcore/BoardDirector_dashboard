$(document).ready(function () {
    $("#id_country").selectize();

    var $modal = $('.change-plan-dialog');
    $modal.dialog({
        autoOpen: false,
        width: 696,
        resizable: false,
        buttons: [
            {
                text: $modal.attr('data-cancel-button-text'),
                click: function () {
                    $(this).dialog('close');
                },
                class: 'cancel-button'
            },
            {
                text: $modal.attr('data-send-button-text'),
                click: function () {
                    var $selected = $('.billing-plan-selection .selected-plan');
                    $('#id_plan').val($selected.attr('data-plan-id'));
                    $('#id_cycle').val($selected.attr('data-cycle'));

                    var plan_name = $selected.closest('.billing-plan').find('.plan-name').text();
                    var cost_text = $selected.attr('data-cost-text');

                    var $plan_form = $('.plan-form');
                    $plan_form.find('.plan-cost-description').text(cost_text);
                    $plan_form.find('.plan-name').text(plan_name);
                    $plan_form.find('.save-warning').removeClass('hidden');

                    $(this).dialog('close');
                },
                class: 'form-send-button'
            }
        ],
        beforeClose: function (event, ui) {
            $('.popup-overlay').hide();
        }
    });

    $('.refresh-plan').click(function () {
        $modal.dialog('open');
        $('.popup-overlay').show();
    });

    $modal.on('click', '.billing-plan-selection .btn', function () {
        $('.billing-plan-selection .selected-plan').removeClass('selected-plan');
        $(this).addClass('selected-plan');
    });

    $('.change-payment-method').click(function () {
        var $info = $('.creditcard-info');
        $info[$info.is(':visible') ? 'fadeOut' : 'fadeIn']();
    });

    setupStripe();


    // Setup Stripe
    var forceSubmit = false;
    function setupStripe() {
        var stripe_style = {};

        var public_key = $('#card-element').attr('data-stripe-public-key');
        var stripe = Stripe(public_key);
        var elements = stripe.elements();
        var card = elements.create('card', {
            style: stripe_style,
            hidePostalCode: true
        });
        card.mount('#card-element');

        // Handle real-time validation errors from the card Element.
        card.addEventListener('change', function (event) {
            const displayError = document.getElementById('card-errors');
            if (event.error) {
                displayError.textContent = event.error.message;
            } else {
                displayError.textContent = '';
            }
        });

        // Handle form submission
        var $billing_form = $('#billing-form');
        $billing_form.submit(function (event) {
            if ($('#card-element').hasClass('StripeElement--empty') || forceSubmit) {
                // Just continue saving form
                return;
            }

            event.preventDefault();

            var options = {
                name: $('#id_name').val(),
                address_line1: $('#id_address').val(),
                address_city: $('#id_city').val(),
                address_state: $('#id_state').val(),
                address_zip: $('#id_zip').val(),
                address_country: $('#id_country').val()
            };

            stripe.createToken(card, options).then(function (result) {
                if (result.error) {
                    console.log(result);
                    var errorElement = document.getElementById('card-errors');
                    errorElement.textContent = result.error.message;
                } else {
                    // Send the token to your server
                    $('#id_stripe_token').val(JSON.stringify(result.token));
                    forceSubmit = true;
                    $billing_form.submit();
                }
            });
        });
    }
});
