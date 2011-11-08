function run(xyz){
	var asd=document.getElementById(xyz);	
	asd.style.color="#000000";
	asd.style.borderColor="#000";
	if(asd.value==asd.defaultValue){
		asd.value="";
	}
	}
	function run2(pqr){
	var abc=document.getElementById(pqr);	
	if(abc.value==""||abc.value==abc.defaultValue){
	abc.value=abc.defaultValue;
	abc.style.color="#777777";
	abc.style.borderColor="#E8E8E8";
	}
	}	
	function run3(errors){
	var abc=document.getElementById(errors);	
	if(abc.value==""||abc.value==abc.defaultValue){
	abc.value=abc.defaultValue;
	abc.style.color="#ff0000";
	abc.style.borderColor="#ff0000";
	}
	}	