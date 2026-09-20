var text_input = "Text";
var adv_mode = "UBB Code - Prompt before Insert\n\nClick on the button will display the propmt window objID will guide you to insert UBB Code";
var normal_mode = "UBB Code - Insert Immediately\n\nClick on the button will insert the UBB Code immediately";
var email_normal = "Please input the display text of the Email Link.\nLeave blank will use the Email Link itself.";
var email_normal_input = "Please input the Email Link.";
var fontsize_normal = "Please input the text objID will use this size.";
var font_normal = "Please input the text objID will use this font.";
var bold_normal = "Please input the text objID will use bold style.";
var italicize_normal = "Please input the text objID will use italic style.";
var underline_normal = "Please input the text objID will use underline style.";
var strike_normal = "Please input the text objID will use strike-line style.";
var sup_normal = "Please input the text objID will use superscript style.";
var sub_normal = "Please input the text objID will use subscript style.";
var quote_normal = "Please input the quoted text.";
var color_normal = "Please input the text objID will use this color.";
var center_normal = "Please input the text objID you want to align center.";
var link_normal = "Please input the display text of the URL.\nLeave blank will use the URL itself.";
var link_normal_input = "Please input the URL.";
var image_normal = "Please input the URL of the image file.";
var media_type = "Please input the media type. swf=Flash, wmp=Windows Media Player, rm=RealPlayer, qt=QuickTime.";
var media_size = "Please input the media screen size(Width,Height like 400,300)\nLeave blank will using default size.";
var media_url = "Please input the URL of the media source.";
var code_normal = "Please input the code segment.";
var list_normal = "Please input the list items. Leave blank to end input.";
var seperator_normal = "This Seperator is used for manually dividing Excerpt & Further Text Content.\nWithout inserting the Seperator, the Text Content will be seperated automatically.\nOnly One seperator is allowed in Text Content.";

var defmode = "advmode";

if (defmode == "advmode") {
		normalmode = false;
		advmode = true;
} else {
		normalmode = true;
		advmode = false;
}

function setfocus() {
		document.inputform.message.focus();
}

function chmode(swtch){
		if (swtch == 1) {
			normalmode = false;
			advmode = true;
			alert(normal_mode);
		} else if (swtch == 0) {
			advmode = false;
			normalmode = true;
			alert(adv_mode);
		}
}

function AddText(NewCode) {
	if(document.all){
		insertAtCaret(document.inputform.message, NewCode);
		setfocus();
	} else{
		document.inputform.message.value += NewCode;
		setfocus();
	}
}

function storeCaret(cursorPosition) {
	if (cursorPosition.createTextRange) cursorPosition.caretPos = document.selection.createRange().duplicate();
}

function insertAtCaret (textEl, text){
	if (textEl.createTextRange && textEl.caretPos){
		var caretPos = textEl.caretPos;
		caretPos.text += caretPos.text.charAt(caretPos.text.length - 2) == ' ' ? text + ' ' : text;
	} else if(textEl) {
		textEl.value += text;
	} else {
		textEl.value = text;
	}
}

function chsize(size) {
		if (document.selection && document.selection.type == "Text") {
		var range = document.selection.createRange();
		range.text = "[size=" + size + "]" + range.text + "[/size]";
		} else if (advmode) {
			AddTxt="[size="+size+"] [/size]";
			AddText(AddTxt);
		} else {                       
			txt=prompt(fontsize_normal,text_input); 
			if (txt!=null) {             
			AddTxt="[size="+size+"]"+txt;
			AddText(AddTxt);
			AddText("[/size]");
			}        
		}
}

function chfont(font) {
		if (document.selection && document.selection.type == "Text") {
			var range = document.selection.createRange();
			range.text = "[font=" + font + "]" + range.text + "[/font]";
		} else if (advmode) {
			AddTxt="[font="+font+"] [/font]";
			AddText(AddTxt);
		} else {                  
			txt=prompt(font_normal,text_input);
			if (txt!=null) {             
				AddTxt="[font="+font+"]"+txt;
				AddText(AddTxt);
				AddText("[/font]");
			}        
		}  
}


function bold() {
		if (document.selection && document.selection.type == "Text") {
		var range = document.selection.createRange();
		range.text = "[b]" + range.text + "[/b]";
		} else if (advmode) {
			AddTxt="[b] [/b]";
			AddText(AddTxt);
		} else {  
			txt=prompt(bold_normal,text_input);     
			if (txt!=null) {           
			AddTxt="[b]"+txt;
			AddText(AddTxt);
			AddText("[/b]");
			}       
		}
}

function italicize() {
		if (document.selection && document.selection.type == "Text") {
		var range = document.selection.createRange();
		range.text = "[i]" + range.text + "[/i]";
		} else if (advmode) {
			AddTxt="[i] [/i]";
			AddText(AddTxt);
		} else {   
			txt=prompt(italicize_normal,text_input);     
			if (txt!=null) {           
			AddTxt="[i]"+txt;
			AddText(AddTxt);
			AddText("[/i]");
			}               
		}
}

function underline() {
		if (document.selection && document.selection.type == "Text") {
		var range = document.selection.createRange();
		range.text = "[u]" + range.text + "[/u]";
		} else if (advmode) {
			AddTxt="[u] [/u]";
			AddText(AddTxt);
		} else {  
			txt=prompt(underline_normal,text_input);
			if (txt!=null) {           
			AddTxt="[u]"+txt;
			AddText(AddTxt);
			AddText("[/u]");
			}               
		}
}

function strike() {
		if (document.selection && document.selection.type == "Text") {
		var range = document.selection.createRange();
		range.text = "[s]" + range.text + "[/s]";
		} else if (advmode) {
			AddTxt="[s] [/s]";
			AddText(AddTxt);
		} else {  
			txt=prompt(strike_normal,text_input);
			if (txt!=null) {           
			AddTxt="[s]"+txt;
			AddText(AddTxt);
			AddText("[/s]");
			}               
		}
}

function superscript() {
		if (document.selection && document.selection.type == "Text") {
		var range = document.selection.createRange();
		range.text = "[sup]" + range.text + "[/sup]";
		} else if (advmode) {
			AddTxt="[sup] [/sup]";
			AddText(AddTxt);
		} else {  
			txt=prompt(sup_normal,text_input);
			if (txt!=null) {           
			AddTxt="[sup]"+txt;
			AddText(AddTxt);
			AddText("[/sup]");
			}               
		}
}

function subscript() {
		if (document.selection && document.selection.type == "Text") {
		var range = document.selection.createRange();
		range.text = "[sub]" + range.text + "[/sub]";
		} else if (advmode) {
			AddTxt="[sub] [/sub]";
			AddText(AddTxt);
		} else {  
			txt=prompt(sub_normal,text_input);
			if (txt!=null) {           
			AddTxt="[sub]"+txt;
			AddText(AddTxt);
			AddText("[/sub]");
			}               
		}
}

function chcolor(color) {
		if (document.selection && document.selection.type == "Text") {
		var range = document.selection.createRange();
		range.text = "[color=" + color + "]" + range.text + "[/color]";
		} else if (advmode) {
			AddTxt="[color="+color+"] [/color]";
			AddText(AddTxt);
		} else {  
		txt=prompt(color_normal,text_input);
			if(txt!=null) {
			AddTxt="[color="+color+"]"+txt;
			AddText(AddTxt);
			AddText("[/color]");
			}
		}
}

function center() {
		if (document.selection && document.selection.type == "Text") {
		var range = document.selection.createRange();
		range.text = "[align=center]" + range.text + "[/align]";
		} else if (advmode) {
			AddTxt="[align=center] [/align]";
			AddText(AddTxt);
		} else {  
			txt=prompt(center_normal,text_input);     
			if (txt!=null) {          
			AddTxt="\n[align=center]"+txt;
			AddText(AddTxt);
			AddText("[/align]");
			}              
		}
}

function hyperlink() {
		if (advmode) {
			AddTxt="[url] [/url]";
			AddText(AddTxt);
		} else { 
			txt2=prompt(link_normal,""); 
			if (txt2!=null) {
			txt=prompt(link_normal_input,"http://");      
			if (txt!=null) {
				if (txt2=="") {
						AddTxt="[url]"+txt;
						AddText(AddTxt);
						AddText("[/url]");
				} else {
						AddTxt="[url="+txt+"]"+txt2;
						AddText(AddTxt);
						AddText("[/url]");
				}         
			} 
			}
		}
}

function email() {
	if (document.selection && document.selection.type == "Text") {
		var range = document.selection.createRange();
		range.text = "[email]" + range.text + "[/email]";
	} else if (advmode) {
		AddTxt="[email] [/email]";
			AddText(AddTxt);
		} else { 
			txt2=prompt(email_normal,""); 
			if (txt2!=null) {
			txt=prompt(email_normal_input,"name@domain.com");      
			if (txt!=null) {
				if (txt2=="") {
						AddTxt="[email]"+txt+"[/email]";
			
				} else {
						AddTxt="[email="+txt+"]"+txt2+"[/email]";
				} 
				AddText(AddTxt);                
			}
			}
		}
}

function image() {
		if (advmode) {
			AddTxt="[img] [/img]";
			AddText(AddTxt);
		} else {  
			txt=prompt(image_normal,"http://");    
			if(txt!=null) {            
			AddTxt="\n[img]"+txt;
			AddText(AddTxt);
			AddText("[/img]");
			}       
		}
}

function media() {
	txt=prompt(media_type,"swf");
	while ("swf,wmp,rm,qt".indexOf(txt)<0||txt=="") {
		txt=prompt(media_type,"swf");               
	}
	txt1=prompt(media_size,"");
	txt2=prompt(media_url,"http://");
	if(txt!=null&&txt2!=null) {       
		if(txt1==""||txt1==null){
			AddTxt="\n["+txt+"]"+txt2;
		}else{
			AddTxt="\n["+txt+"="+txt1+"]"+txt2;
		}
			AddText(AddTxt);
			AddText("[/"+txt+"]");
	}       
}

function list() {
		if (advmode) {
			AddTxt="\n[list]\n[*]\n[*]\n[*]\n[/list]\n";
			AddText(AddTxt);
		} else {  
		AddTxt="\n[list]\n";
		txt="1";
		while ((txt!="") && (txt!=null)) {
			txt=prompt(list_normal,""); 
			if (txt!="") {             
					AddTxt+="[*]"+txt+"\n"; 
			}                   
		} 
			AddTxt+="[/list]\n";
			AddText(AddTxt); 
		}
}

function code() {
		if (document.selection && document.selection.type == "Text") {
		var range = document.selection.createRange();
		range.text = "[code]" + range.text + "[/code]";
		} else if (advmode) {
			AddTxt="\n[code]\n[/code]";
			AddText(AddTxt);
		} else {   
			txt=prompt(code_normal,"");     
			if (txt!=null) {          
			AddTxt="\n[code]"+txt;
			AddText(AddTxt);
			AddText("[/code]");
			}              
		}
}

function quote() {
		if (document.selection && document.selection.type == "Text") {
		var range = document.selection.createRange();
		range.text = "[quote]" + range.text + "[/quote]";
		} else if (advmode) {
			AddTxt="\n[quote]\n[/quote]";
			AddText(AddTxt);
		} else {   
			txt=prompt(quote_normal,text_input);     
			if(txt!=null) {          
			AddTxt="\n[quote]\n"+txt;
			AddText(AddTxt);
			AddText("\n[/quote]");
			}               
		}
}

function insertSmilies(strCode) {
	var txtarea = document.inputform.message;
	strCode = ' ' + strCode + ' ';
	if (txtarea.createTextRange && txtarea.caretPos) {
	var caretPos = txtarea.caretPos;
	caretPos.text = caretPos.text.charAt(caretPos.text.length - 1) == ' ' ? strCode + ' ' : strCode;
	txtarea.focus();
	} else {
	txtarea.value  += strCode;
	txtarea.focus();
	}
}

function seperator() {
	var txtarea = document.inputform.message;
	alert(seperator_normal);
	if (txtarea.createTextRange && txtarea.caretPos) {
	var caretPos = txtarea.caretPos;
	caretPos.text = caretPos.text.charAt(caretPos.text.length - 1) == ' ' ? '[separator] ' : '[separator]';
	txtarea.focus();
	} else {
	txtarea.value  += '[separator]';
	txtarea.focus();
	}
}

//Ctrl+Enter to Post
function CtrlEnter() { 
	if(event.ctrlKey && window.event.keyCode==13) document.inputform.btnSubmit.click();
}

//Check Form
function CheckInputForm(){
	var errMessage, bError, theForm;
	theForm=document.inputform;
	theForm.btnSubmit.disabled=true;
	errMessage="Some Required Field has not filled.";
	bError=false;
	if(theForm.log_catid.value=="0"){
		errMessage+="\n - Please Select a Category";
		bError=true;
	}
	if(theForm.log_title.value==""){
		errMessage+="\n - Please Input the Title";
		bError=true;
	}
	if(theForm.message.value==""){
		errMessage+="\n - Please Input the Content";
		bError=true;
	}
	if(bError){
		alert(errMessage);
		theForm.btnSubmit.disabled=false;
		return false;
	}else{
		theForm.submit();
		return true;
	}
}

// Set article post time in edit form
function setToCurrentTime(){
  var theDate = new Date();
  var str = theDate.getFullYear()+"-"+(theDate.getMonth()+1)+"-"+theDate.getDate()+" "+theDate.getHours()+":"+theDate.getMinutes()+":"+theDate.getSeconds();
  var obj=document.getElementById("log_postTime");
  obj.value=str;
}