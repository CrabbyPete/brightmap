$(document).ready(function() {
	$('.fancypop').fancybox({
		'overlayColor': '#000000',
		'overlayOpacity': .5,
		'margin': 0,
		'padding': 0
	});
	$('.fancy-close').click(function() {
		$.fancybox.close();
		return false;
	});
	
	clearInputs('form input');
    
	// Place pop-up in middle:
	var pwh = $('#pop-up-wrapper').height();
	var aph = $('#actual-popup').outerHeight();
	$('#pop-up-wrapper').css('padding-top', (pwh/2 - aph/2) + 'px');
	
    $('#select-service').click(function () {
        if($('#service-select').val() == 0) {
            $('#service-error').text('- please select your service type -');
            return false;
        }
    
        // Mock-up for sending the chosen service through POST using Ajax:
        /*value = $('select[name="service"]');
        $.ajax({
            url: "who/handles/the/service.php",
            type: "POST",
            data: {
                service: value
            }
        });*/
        $('#pop-up-wrapper').fadeTo(620, 0, function() {
            $(this).css('display', 'none');
        });
        return false;
    });$('#pop-up-wrapper').fadeTo(620, 0, function() {
            $(this).css('display', 'none');
        });
    
    $('#play-video').click(function() {
        $(this).hide();
        $('#the-video').css('display', 'block');
        return false;
    });
    
    var ch = $('#ceo').outerHeight();
    var cidh = $('#ceo-info div').outerHeight();
    var cihh = $('#ceo-info header').outerHeight();
    if(ch>cidh+cihh) $('#ceo-info div').height(ch-cihh-45);
    else $('#ceo').height(cidh+cihh-6);
    
});

function clearInputs(x) {
	$(x).each(function(i){
		var inputValue = $(this).val();
		var inputTitle = $(this).attr("title");
		
		if (inputValue=="" || inputValue==inputTitle) {
			$(this).focus(function(){ 
				if ($(this).val()==inputValue) {
					$(this).val("");
				}
			});
			$(this).blur(function(){ 
				if ($(this).val()=="") {
					$(this).val(inputValue);
				}
			});
		}
		
	});
}