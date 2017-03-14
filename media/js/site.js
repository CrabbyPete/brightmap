$(document).ready(function() {
	$('.fancypop').fancybox({
		'overlayColor': '#000000',
		'overlayOpacity': .5,
		'margin': 0,
		'padding': 0
	});
    $('.fancypop-video').fancybox({
		'overlayColor': '#000000',
		'overlayOpacity': .5,
		'margin': 0,
		'padding': 10
	});
	$('.fancy-close').click(function() {
		$.fancybox.close();
		return false;
	});
	
	clearInputs('form input');
    
    $('.form-popup').click(function() {
        $('#pop-up-wrapper').fadeIn(600);
        $('#popup-connect').delay(200).fadeIn(300);
    });
	
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
        $('#pop-up-wrapper, #actual-popup').fadeOut(620);/* , 0, function() {
            $(this).css('display', 'none');
        }); */
        return false;
    });
    $('.popup .btn-close, .btn-pop-ok').click(function() {
        $(this).parent().parent().fadeOut(620);        
        $('#pop-up-wrapper').fadeOut(620);
        
        return false;
    });
    
    $('#play-video').click(function() {
        $(this).hide();
        $('#the-video').css('display', 'block');
        return false;
    });
    
    var pn = $('#under-30-info .pic.name').outerHeight();
    var bq = $('#under-30-info blockquote').outerHeight();
    if(pn > bq) $('#under-30-info blockquote').height(pn-106);
    else $('#under-30-info .pic.name').height(bq-6);
    
    
    var hl = $('#ceo').outerHeight();
    var hr = $('#ceo-info').outerHeight();
    if(hl < hr) $('#ceo').height($('#ceo-info').innerHeight() - 6);
    else $('#ceo-info div').height($('#ceo').innerHeight()-91);    
    
    console.log('hl: ' + hl + '\nhr: ' + hr);
    
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