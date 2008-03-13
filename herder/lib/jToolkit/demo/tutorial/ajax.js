
/**************************************************
 * Initialisation code for our xmlhttp object
 * which is used to request URLs within javascript
 **************************************************/
function createXmlHttp()
{
	var xmlhttp=false;
	/*@cc_on @*/
	/*@if (@_jscript_version >= 5)
	// JScript gives us Conditional compilation, we can cope with old IE versions.
	// and security blocked creation of the objects.
	 try {
	  xmlhttp = new ActiveXObject("Msxml2.XMLHTTP");
	 } catch (e) {
	  try {
	   xmlhttp = new ActiveXObject("Microsoft.XMLHTTP");
	  } catch (E) {
	   xmlhttp = false;
	  }
	 }
	@end @*/
	if (!xmlhttp && typeof XMLHttpRequest!='undefined') {
          try {
	    xmlhttp = new XMLHttpRequest();
          }
          catch (e) {
            xmlhttp = false;
          }
	}
	return xmlhttp;
}

function XmlHttpGet()
{
	var xmlhttp = createXmlHttp();
	if (xmlhttp) {
	  function xmlhttpwrapper(xmlhttp) {
	    this.xmlhttp = xmlhttp;
	    this.get = function(url, params) {
	      var contentdata = "";
	      for (var key in params)
	      {
	        var value = params[key];
	        if (contentdata) contentdata += "&";
	        contentdata += key + "=" + value;
	      }
	      // WARNING: if the URL is too long this will fail
	      if (url.search("\\?") == -1)
	        url += "?";
	      url += contentdata;
	      this.xmlhttp.open("GET", url);
	      this.send();
	    }
	    this.open = function(method, url) { this.url = url; this.xmlhttp.open(method, url);  },
	    this.send = function() { 
		var parent = this;
		this.xmlhttp.onreadystatechange = function() { parent.onreadystatechange()} ;
		this.xmlhttp.send(""); },
	    this.onreadystatechange = function() { 
		if (this.xmlhttp.readyState == 4)
		{
                  // if (this.xmlhttp.status == "200") {
		    if (this.responsehandler) {
		      var response = this.xmlhttp.responseText;
		      this.responsehandler(response);
		    }
		    else if (this.xmlresponsehandler) {
		      var xmlresponse = this.xmlhttp.responseXML;
		      this.xmlresponsehandler(xmlresponse);
		    }
		  // }
		}
	    }
	  }
	  return new xmlhttpwrapper(xmlhttp);
	}
	return xmlhttp;
}

function PostXmlHttp()
{
	var xmlhttp = createXmlHttp();
	if (xmlhttp) {
	  function xmlhttpwrapper(xmlhttp) {
	    this.xmlhttp = xmlhttp;
	    this.post = function(url, params) {
	      this.xmlhttp.open("POST", url);
	      this.xmlhttp.setRequestHeader("Content-Type", "application/x-www-form-urlencoded")
	      var contentdata = "";
	      for (var key in params)
	      {
	        var value = params[key];
	        if (contentdata) contentdata += "&";
	        contentdata += key + "=" + value;
	      }
	      this.send(contentdata);
	    }
	    this.open = function(method, url) { this.url = url; this.xmlhttp.open(method, url);  },
	    this.send = function(content) { 
		var parent = this;
		this.xmlhttp.onreadystatechange = function() { parent.onreadystatechange()} ;
		this.xmlhttp.send(content); },
	    this.onreadystatechange = function() { 
		if (this.xmlhttp.readyState == 4)
		{
                  if (this.xmlhttp.status == "200") {
		    if (this.responsehandler) {
		      var response = this.xmlhttp.responseText;
		      this.responsehandler(response);
		    }
		    else if (this.xmlresponsehandler) {
		      var xmlresponse = this.xmlhttp.responseXML;
		      this.xmlresponsehandler(xmlresponse);
		    }
		  }
		}
	    }
	  }
	  return new xmlhttpwrapper(xmlhttp);
	}
	return xmlhttp;
}

