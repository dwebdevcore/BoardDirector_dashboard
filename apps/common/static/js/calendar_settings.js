$(document).ready(function(){

  $('body').on('submit', '#cal-setting-form', function (e) {
      e.preventDefault();

      // init message box
      $('.alert-cal-setting').removeClass('alert-success').removeClass('alert-danger').hide();
      $('.alert-cal-setting .cal-message').html('');
      console.log('here');

      // send ajax request
      $.ajax({
          data: $(this).serialize(),
          type: $(this).attr('method'),
          url: $(this).attr('action'),
          success: function (resp) {
              if(resp.result === 'success'){
                  console.log('success');
                  $('.alert-cal-setting .cal-message').html('Successfully saved !');
                  $('.alert-cal-setting').addClass('alert-success').show();
              }else{
                  console.log('fail');
                  $('.alert-cal-setting .cal-message').html('This connection does not exist !');
                  $('.alert-cal-setting').addClass('alert-danger').show();
              }
          },
          error: function (resp) {
              console.log('error');
              $('.alert-cal-setting .cal-message').html('Something was wrong !');
              $('.alert-cal-setting').addClass('alert-danger').show();
          }

      });
  })

});
