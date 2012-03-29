//$(document).ready(function() {
$(window).bind("load", function() {
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
    });
    
    $('#play-video').click(function() {
        $(this).hide();
        $('#the-video').css('display', 'block');
        return false;
    });
    
    $('#ceo').height($('#ceo-info').innerHeight() - 6);
    
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
