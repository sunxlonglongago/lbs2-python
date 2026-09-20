// Show/Hide Sidebar
function showHideSidebar(){
  try{
    var objSidebar=document.getElementById("sidebar");
    var objContent=document.getElementById("content");
    if(objSidebar.className!="sidebar-hide"){
      objSidebar.className="sidebar-hide";
      objSidebar.style.display="none";
      objContent.className="content-wide";
    }else{
      objSidebar.className="sidebar";
      objSidebar.style.display="block";
      objContent.className="content";
    }
  }catch(e){}
}

// Show/Hide Login Panel
function showLogin(){
  try{
    var panel=document.getElementById("panelUser");
    if(panel){
      if(panel.style.display=='none'){
        panel.style.display='block';
      }else{
        panel.style.display='none';
      }
    }else{
      document.location="login.asp";
    }
  }catch(e){}
}

// Dynamic write object tag - SiC/CYAN 2004-2005
function ubbShowObj(strType,strID,strURL,intWidth,intHeight)
{
	var objPrefix="bShow";
	var tmpstr="";
	var bSwitch = false;
	//Reverse the State
	bSwitch = document.getElementById(objPrefix+strID).value;
	bSwitch	=~bSwitch;
	document.getElementById(objPrefix+strID).value = bSwitch;
	if(bSwitch){
		//Code for already shown
		document.getElementById(strID).innerHTML = "<a href=\""+strURL+'" target="_blank">'+strURL+"</a>";
	}else{
		//Code for not shown
		switch(strType){
			case "swf":
				tmpstr=strURL+'<br /><object codebase="http://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=7,0,0,0" classid="clsid:D27CDB6E-AE6D-11cf-96B8-444553540000" width="'+intWidth+'" height="'+intHeight+'"><param name="movie" value="'+strURL+'" /><param name="quality" value="high" /><param name="AllowScriptAccess" value="never" /><embed src="'+strURL+'" quality="high" pluginspage="http://www.macromedia.com/go/getflashplayer" type="application/x-shockwave-flash" width="'+intWidth+'" height="'+intHeight+'" /></object>';
				break;
			case "wmp":
				tmpstr=strURL+'<br /><object classid="clsid:22D6F312-B0F6-11D0-94AB-0080C74C7E95" codebase="http://activex.microsoft.com/activex/controls/mplayer/en/nsmp2inf.cab#Version=6,0,02,902" type="application/x-oleobject" standby="Loading..." width="'+intWidth+'" height="'+intHeight+'"><param name="FileName" VALUE="'+strURL+'" /><param name="ShowStatusBar" value="-1" /><param name="AutoStart" value="true" /><embed type="application/x-mplayer2" pluginspage="http://www.microsoft.com/Windows/MediaPlayer/" src="'+strURL+'" autostart="true" width="'+intWidth+'" height="'+intHeight+'" /></object>';
				break;
			case "rm":
				tmpstr=strURL+'<br /><object classid="clsid:CFCDAA03-8BE4-11cf-B84B-0020AFBBCCFA" width="'+intWidth+'" height="'+intHeight+'"><param name="SRC" value="'+strURL+'" /><param name="CONTROLS" VALUE="ImageWindow" /><param name="CONSOLE" value="one" /><param name="AUTOSTART" value="true" /><embed src="'+strURL+'" nojava="true" controls="ImageWindow" console="one" width="'+intWidth+'" height="'+intHeight+'"></object>'+
        '<br /><object classid="clsid:CFCDAA03-8BE4-11cf-B84B-0020AFBBCCFA" width="'+intWidth+'" height="32" /><param name="CONTROLS" value="StatusBar" /><param name="AUTOSTART" value="true" /><param name="CONSOLE" value="one" /><embed src="'+strURL+'" nojava="true" controls="StatusBar" console="one" width="'+intWidth+'" height="24" /></object>'+'<br /><object classid="clsid:CFCDAA03-8BE4-11cf-B84B-0020AFBBCCFA" width="'+intWidth+'" height="32" /><param name="CONTROLS" value="ControlPanel" /><param name="AUTOSTART" value="true" /><param name="CONSOLE" value="one" /><embed src="'+strURL+'" nojava="true" controls="ControlPanel" console="one" width="'+intWidth+'" height="24" autostart="true" loop="false" /></object>';
				break;
			case "qt":
				tmpstr=strURL+'<br /><embed src="'+strURL+'" autoplay="true" loop="false" controller="true" playeveryframe="false" cache="false" scale="TOFIT" bgcolor="#000000" kioskmode="false" targetcache="false" pluginspage="http://www.apple.com/quicktime/" />';
		}
		document.getElementById(strID).innerHTML = tmpstr;
	}
}

// Quote Comment Text - SiC/CYAN 2004-2005
function doQuote(objID,strAuthor){
  var obj=document.getElementById(objID);
  var text=obj.innerHTML;
  text=text.replace(/alt\=(\"|)([^\"\s]*)(\"|)/g,"> $2 <");
  text=text.replace(/\<[^\<\>]+\>/g,"\n");
  text=text.replace(/ +/g," ");
  text=text.replace(/\n+/g,"\n");
  text=text.replace(/^\n*/gm,"");
  text=text.replace(/^\s*/gm,"");
  text=text.replace(/\n*$/gm,"");
  text=text.replace(/\s*$/gm,"");
	document.inputform.message.value += "[quote="+strAuthor+"]\n"+text+"\n[/quote]\n";
	window.location.hash="commentbox";
}

// Show/Hide Comments & Trackback - SiC/CYAN 2005
function toggleComments(bShowComment,bShowTrackback){
  var objs=document.getElementById("commentWrapper");
  objs=objs.getElementsByTagName("div");
  for(var i=0;i<objs.length;i++){
    if(objs[i].id.indexOf("comment")>-1&&objs[i].id!="commentTop"){
      if(bShowComment){
        objs[i].style.display="block";
      }else{
        objs[i].style.display="none";
      }
    }
    if(objs[i].id.indexOf("trackback")>-1&&objs[i].id!="commentTop"){
      if(bShowTrackback){
        objs[i].style.display="block";
      }else{
        objs[i].style.display="none";
      }
    }
  }
}

// Toggle Comments & Trackback Order
var bOrder=true;
function toggleOrder(){
  var obj=document.getElementById("commentWrapper");
  // I want to use outerHTML but that stupid fox does not support it
  var objtopHTML='<div id="commentTop" class="comment-top">\n'+document.getElementById("commentTop").innerHTML+'</div>\n';
  var objs=obj.getElementsByTagName("div");
  var tmpArray=new Array();
  for(var i=0;i<objs.length;i++){
    if((objs[i].id.indexOf("comment")>-1||objs[i].id.indexOf("trackback")>-1)&&objs[i].id!="commentTop"){
      tmpArray[i]='<div id="'+objs[i].id+'" class="'+objs[i].className+'">\n'+objs[i].innerHTML+'</div>\n';
    }
  }
  tmpArray.reverse();
  obj.innerHTML=objtopHTML+tmpArray.join("\n");
  delete tmpArray;
}

// Search - SiC/CYAN 2004-2005
function doSearch(){
  var form=document.getElementById("searchForm");
  if(lengthW(form.q.value)<3){
    alert("Keyword length must greater than 3 chars.");
    return false;
  }
  switch(form.searchType.value){
    case "comments":
      form.action="comment.asp";
      return true;
      break;
    case "guestbook":
      form.action="gbook.asp";
      return true;
    case "trackbacks":
      form.action="trackback.asp?act=list";
      return true;
    default:
      form.action="default.asp";
      return true;
      break;
  }
}

// String Length with unicode support
function lengthW(str){
  if(str==undefined){ return 0; }
  str=String(str);
  var tLen=0;
  for(var i=0;i<str.length;i++){
    charCode=str.charCodeAt(i);
    if(charCode<0||charCode>255){ tLen+=2 }else{ tLen++ }
  }
  return tLen;
}

// Set Article Font Size
function setFontSize(pt){
  try{
    var t=document.getElementById("textboxContent");
    if(t){
      t.style.fontSize=pt+"pt";
    }
  }catch(e){}
}
