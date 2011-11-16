/*
 * SimpleModal Basic Modal Dialog
 * http://www.ericmmartin.com/projects/simplemodal/
 * http://code.google.com/p/simplemodal/
 *
 * Copyright (c) 2010 Eric Martin - http://ericmmartin.com
 *
 * Licensed under the MIT license:
 *   http://www.opensource.org/licenses/mit-license.php
 *
 * Revision: $Id: basic.js 254 2010-07-23 05:14:44Z emartin24 $
 */

jQuery(function ($) {
	// Load dialog on page load
	//$('#basic-modal-content').modal();
	$('#itlink2').click(function (e) {
        e.preventDefault();
        $.get(this.href, function(data) {
            var resp = $('<div></div>').append(data); // wrap response
            $(resp).modal();
        });
		//$('#itlink2content').modal();
	});
});

$('a.simple_modal').click(
	    function (e) {
	        e.preventDefault();
	        $.get(this.href, function(data) {
	            var resp = $('<div></div>').append(data); // wrap response
	            $(resp).modal();
	        });
	    }
	);
