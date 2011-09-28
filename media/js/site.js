
$(document).ready(function() {
	
	// FORMS WITH ANCHOR TAGS:
	$('.form-submitter').parent().each(function () {
		var btn = '<button type="submit" class="hidden">&nbsp;</button>';
		$(this).html($(this).html() + btn);
	});
	$('.form-submitter').click(function() {
		$(this).parents('form').submit();
		return false;
	});
	
	// Font replacement
	replaceFonts();	
});

// Font replacement
function replaceFonts() {
	Cufon.replace('.futura, h1, h2', { fontFamily: 'Futura Md BT', hover: true, hoverables: {a: true, button: true}});	
}

