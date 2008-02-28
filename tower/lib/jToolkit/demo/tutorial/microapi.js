/* from quirksmode.org DHTML micro API */

function getObj(name)
{
  if (document.getElementById)
  {
  	return document.getElementById(name);
  }
  else if (document.all)
  {
	return document.all[name];
  }
  else if (document.layers)
  {
   	return document.layers[name];
  }
}

function getObjStyle(name)
{
  if (document.getElementById)
  {
	return document.getElementById(name).style;
  }
  else if (document.all)
  {
	return document.all[name].style;
  }
  else if (document.layers)
  {
   	return document.layers[name];
  }
}

