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