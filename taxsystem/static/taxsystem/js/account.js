/* global taxsystemsettings, bootstrap */
$(document).ready(function() {
    const characterID = taxsystemsettings.character_id;
    const Url = taxsystemsettings.accountUrl.replace('1234', characterID);
    $.ajax({
        url: Url,
        type: 'GET',
        success: function (accountData) {
            try {
                // Update portrait/image if available
                if (accountData.character_portrait) {
                    $('#portrait').html(accountData.character_portrait);
                }

                // Update account information
                if (accountData.account_name) {
                    $('#account_name').text(accountData.account_name);
                }

                if (accountData.corporation_name) {
                    $('#corporation_name').text(accountData.corporation_name);
                }

                if (accountData.status) {
                    $('#account_status').html(accountData.status);
                }

                // Update financial information
                if (accountData.deposit) {
                    if (accountData.deposit.raw >= 0 && accountData.has_paid.raw === true) {
                        $('#deposit_amount').addClass('text-success');
                    } else {
                        $('#deposit_amount').addClass('text-danger');
                    }
                    $('#deposit_amount').text(accountData.deposit.html);
                }

                if (accountData.has_paid) {
                    $('#payment_status').html(accountData.has_paid.display);
                }

                if (accountData.last_paid) {
                    $('#last_paid').text(accountData.last_paid);
                }

                if (accountData.joined) {
                    $('#joined').text(accountData.joined);
                }

            } catch (e) {
                console.error('Error processing account data:', e);
                $('#account_name').text('No data available');
            }

            $('[data-tooltip-toggle="taxsystem-tooltip"]').tooltip({
                trigger: 'hover',
            });
        },
        error: function(xhr, status, error) {
            console.error('Error fetching account data:', error);
        }
    });
});
