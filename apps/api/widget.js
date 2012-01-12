function iecheck() {
  if (navigator.platform == "Win32" && navigator.appName == "Microsoft Internet Explorer" && window.attachEvent) {
    var rslt = navigator.appVersion.match(/MSIE (\d+\.\d+)/, '');
    var iever = (rslt != null && Number(rslt[1]) >= 5.5 && Number(rslt[1]) <= 7 );
  }
  return iever;
}

MyXssMagic = new function() {
  var BASE_URL = 'http://brightmap.com/media/';
  var STYLESHEET = BASE_URL + "xss_magic.css"
  var CONTENT_URL = BASE_URL + 'people_list.js';
  var ROOT = 'my_xss_magic';

  function requestStylesheet(stylesheet_url) {
    stylesheet = document.createElement("link");
    stylesheet.rel = "stylesheet";
    stylesheet.type = "text/css";
    stylesheet.href = stylesheet_url;
    stylesheet.media = "all";
    document.lastChild.firstChild.appendChild(stylesheet);
  }

  function requestContent( local ) {
    var script = document.createElement('script');
    // How you'd pass the current URL into the request
    // script.src = CONTENT_URL + '&url=' + escape(local || location.href);
    script.src = CONTENT_URL;
    document.getElementsByTagName('head')[0].appendChild(script);
  }

	this.init = function() {
	  this.serverResponse = function(data) {
	    if (!data) return;
	    var div = document.getElementById(ROOT);
	    var txt = "";
	    for (var i = 0; i < data.length; i++) {
	      if (txt.length > 0) { txt += ", "; }
	      txt += data[i];
	    }
	    div.innerHTML = "<strong>Names:</strong> " + txt;  // assign new HTML into #ROOT
	    div.style.display = 'block'; // make element visible
	    div.style.visibility = 'visible'; // make element visible
	  }
	
	  requestStylesheet(STYLESHEET);
	  document.write("<div id='" + ROOT + "' style='display: none'></div>");
	  requestContent();
	  var no_script = document.getElementById('no_script');
	  if (no_script) { no_script.style.display = 'none'; }
	}
}
MyXssMagic.init();