var slyrtop = 0;
var slyrleft = 0;

function findPosX(obj)
{
    var curleft = 0;
    if (obj.offsetParent)
    {
        while (obj.offsetParent)
        {
            curleft += obj.offsetLeft
            obj = obj.offsetParent;
        }
    }
    else if (obj.x)
        curleft += obj.x;
    return curleft;
}

function findPosY(obj)
{
    var curtop = 0;
    if (obj.offsetParent)
    {
        while (obj.offsetParent)
        {
            curtop += obj.offsetTop
            obj = obj.offsetParent;
        }
    }
    else if (obj.y)
        curtop += obj.y;
    return curtop;
}

function setLyr(obj,lyr)
{
    var newX = findPosX(obj);
    var newY = findPosY(obj);
    var newwidth = obj.offsetWidth;
    var newheight = obj.offsetHeight;
    lyr.style.top = newY + 'px';
    lyr.style.left = newX + 'px';
    slyrtop = newY;
    slyrleft = newX;
    lyr.style.width = newwidth;
    lyr.style.height = newheight;
    lyr.style.clip.height = newheight;
}

function findlayer(layername, searchdoc)
{
    if (searchdoc == undefined)
        searchdoc = document;
    if (searchdoc.getElementById)
        return searchdoc.getElementById(layername);
    else if (searchdoc.all)
        return searchdoc.all[layername];
    else if (searchdoc.layers)
        return searchdoc.layers[layername];
}

function ToggleSpellChecker(obj,button)
{
    var layername = obj.name + '.spellchecklayer';
    var lyr = findlayer(layername);
    var standby_url = lyr.getAttribute("standby_url");
    var target_url = lyr.getAttribute("target_url");

    //if we are starting a spellcheck
    if (button.value == "spellcheck")
    {
        lyr.style.visibility = 'visible';
        lyr.style.background = '#D5E6F7';
        lyr.style.border = 'solid black 1px';
        lyr.style.position = 'absolute';
        setLyr(obj,lyr);

        var framename = obj.name + '.spellcheckframe';
        var spellcheckframe = document.getElementById(framename);
        spellcheckframe.height = lyr.style.height;
        spellcheckframe.width = lyr.style.width;


        //set the form to a new action, then set it back
        theform = obj.form;
        var previousaction = theform.action;
        var previoustarget = theform.target;
        var previousmethod = theform.method;
        var previousencoding = theform.encoding;
        theform.method = 'POST';
        theform.encoding = 'multipart/form-data';
        theform.target = framename;

        //set the action for the form
        var fieldname = obj.name;
        var targeturl = target_url + '?spellcheckfield=' + fieldname;
        theform.action = targeturl;

        theform.submit();

        //return to previous values
        theform.method = previousmethod;
        theform.encoding = previousencoding;
        theform.target = previoustarget;
        theform.action = previousaction;
        
        //toggle the text on the button
        button.value = "resume editing";
    }
    else //if we are ending a spellcheck
    {
        //find the spellchecking iframe
        var framename = obj.name + '.spellcheckframe';
        var spellcheckframe = frames[framename];
        spellcheckframe.location.href = standby_url;
        //var spellcheckframe = document.getElementById(framename);
        //spellcheckframe.src = 'spellingstandby.htm';

        //extract only the text we want
        var newtext = "";
        var debug="";
        var childnodes = spellcheckframe.document.body.firstChild.childNodes;
        
        //Act according to the type of node. This is where we convert from html to plain text
        for(var i=0;i<childnodes.length;i++)
        {
            debug+=childnodes[i].nodeName;
            if (childnodes[i].nodeName == '#text')
            {
                newtext += childnodes[i].data;
            }
            if (childnodes[i].nodeName == 'A')
            {
                newtext += childnodes[i].innerHTML;
            }
        }
        
        obj.value = newtext;

        //hide the iframe
        lyr.style.visibility = 'hidden';

        //hide the suggestions layer in case it is shown
        var suggestionslayer = findlayer('suggestionslayer');
        suggestionslayer.style.visibility = 'hidden';

        //toggle the text on the button
        button.value = "spellcheck";
    }
};

function MakeSelection(anchor,wordindex,selection,layerid)
{
    var lyr = findlayer('suggestionslayer');
    lyr.style.visibility = 'hidden';
    lyr.innerHTML = "";

    //change the anchor
    lyr.obj.innerHTML = selection;
};

function ShowOptions(anchor,index)
{
    //show the suggestions for a word
    var lyr = findlayer('suggestionslayer', parent.document);

    lyr.style.background = '#D5E6F7';
    lyr.style.border = 'solid black 1px';
    lyr.style.position = 'absolute';
    lyr.style.height = 100;
    lyr.style.zindex = 1;
    lyr.style.overflow = 'scroll';
    lyr.style.visibility = 'visible';
    lyr.obj = anchor;
    setLyr(anchor,lyr);

    //we need to modify the position of the layer by the position of the iframe
    var iframe = window.frameElement;
    var modx = iframe.offsetParent.offsetLeft - document.body['scrollLeft'];
    var mody = iframe.offsetParent.offsetTop - document.body['scrollTop'];
    lyr.style.top = slyrtop + mody + 'px';
    lyr.style.left = slyrleft + modx + 'px';

    //modify the size of the layer
    lyr.style.width = anchor.offsetWidth + 50 + 'px';
    lyr.style.height = 100;
    lyr.style.clip.height = 80;

    //set the options
    innerhtml = "<pre>";
    for (i=0; i<wordlist[index][2].length; i++)
    {
        newword = wordlist[index][2][i];
        quotedword = "'" + newword.replace("'", "\\'") + "'";
        innerhtml +=  "<a href=javascript:MakeSelection(this,"+index+","+quotedword+",'suggestionslayer')>"+
                        wordlist[index][2][i] +
                      "</a>\n";
    }
    innerhtml += "</pre>";
    lyr.innerHTML = innerhtml;
};
