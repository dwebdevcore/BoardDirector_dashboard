$(function(){
	initCustomForms();
	$('.txt').clearDefault();


    // Activates the PDF Viewer iFrame and its modal
    $("a.view.pdf").add(".item.pdf .revisions h3").on("click", function(event) {
        var url = $(this).attr('data-href');
        $("iframe#pdf-viewer").attr("src", url);
        $("#pdf-wrapper").show();
    });

    // Closes the PDF Viewer iFrame and its modal
    $("#pdf-wrapper").on("click", function(event) {
        $("#pdf-wrapper").hide();
    });

    // fix conflict in slide-checkbox
    $('.slide-toggle .checkboxAreaChecked, .slide-toggle .checkboxArea').css('display', 'none');

    // change color in slide-checkbox
    $('.slide-toggle input[type="checkbox"]').change(function () {
      is_checked = $(this).is(":checked");
      if(is_checked){
          $(this).closest('.slide-toggle').css('border-color', '#37a000');
          $(this).next().css('background-color', '#37a000');
      }else{
          $(this).closest('.slide-toggle').css('border-color', '#d50000');
          $(this).next().css('background-color', '#d50000');
      }
    }).each(function () {
      // $(this).trigger('change');
      $(this).change();
    });
});

function heightSetter(el, footer){
  function heightCounter(element){
    return $(element).length ? $(element).outerHeight() : 0
  }

    var n_headerHeight = heightCounter('#header'),
        n_footerHeight = heightCounter('#footer'),
        n_docHeight = heightCounter(window);

  var minHeight;
  if (footer == true) {
    minHeight = n_docHeight-n_headerHeight-n_footerHeight;
  } else {
    minHeight = n_docHeight-n_headerHeight;
  }
    $(el).css('min-height', Math.max(minHeight, 690));
}

function display_message(data){
    var message = $('<div class="'+data.type +'">' + data.type + '</div>');
    $('.heading').prepend(message);
    setTimeout(function(){
        $(message).fadeOut('medium',function(){
            $(message).remove()
        })
    }, 3000);
}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
var csrftoken = getCookie('csrftoken');

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    crossDomain: false, // obviates need for sameOrigin test
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type)) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

$.fn.clearDefault = function(){
	return this.each(function(){
		var default_value = $(this).attr('placeholder');
		$(this).focus(function(){
			if ($(this).val() == default_value) $(this).val("").addClass('focus');
		});
		$(this).blur(function(){
			if ($(this).val() == "") $(this).removeClass('focus');
		});
	});
};
/* custom form */
var _selectHeight = 30;
var inputs = new Array;
var selects = new Array;
var labels = new Array;
var radios = new Array;
var radioLabels = new Array;
var checkboxes = new Array;
var checkboxLabels = new Array;
var buttons = new Array;
var all_selects = false;
var active_select = null;
var selectText = "Select";

function is_mac() {
    if (navigator.appVersion.indexOf("Safari") != -1)
        if (!window.getComputedStyle) return true;
    return false
}

function initCustomForms() {
    if (!document.getElementById) return false;
    getElements();
    separateElements();
    // replaceRadios();
    replaceCheckboxes();
    $('#id_timezone').chosen({width:"270px"});
    replaceSelects();
    initSubmitFormHelpers();

    var _selects = $('select:not(.multiple)');
    var _SelctClassName = [];
     if (_selects) {
     for (var i = 0; i < _selects.length; i++)
     if (_selects[i].className != "" && _selects[i].className != "outtaHere") _SelctClassName[i] = " drop-" + _selects[i].className;
     for (var i = 0; i < _SelctClassName.length; i++) {
     var _selectDrop = document.getElementById("optionsDiv" + i);
     if (_selectDrop)
     if (_SelctClassName[i]) _selectDrop.className += _SelctClassName[i]
     }
     }
}

function getElements() {
    var _frms = document.getElementsByTagName("form");
    for (var nf = 0; nf < _frms.length; nf++)
        if (_frms[nf].className.indexOf("default") == -1) {
            var a = document.forms[nf].getElementsByTagName("input");
            for (var nfi = 0; nfi < a.length; nfi++) inputs.push(a[nfi]);
            var b = document.forms[nf].getElementsByTagName("label");
            for (var nfl = 0; nfl < b.length; nfl++) labels.push(b[nfl]);
//            var c = document.forms[nf].getElementsByTagName("select");
            var c = $(_frms[nf]).find('select:not(.multiple)');
            for (var nfs = 0; nfs < c.length; nfs++) selects.push(c[nfs])
        }
}

function separateElements() {
    var r = 0;
    var c = 0;
    var t = 0;
    var rl = 0;
    var cl = 0;
    var tl = 0;
    var b = 0;
    for (var q = 0; q < inputs.length; q++) {
        if (inputs[q].type == "radio") {
            radios[r] = inputs[q];
            ++r;
            for (var w = 0; w < labels.length; w++)
                if (inputs[q].id && labels[w].htmlFor == inputs[q].id) radioLabels[rl] = labels[w];
            ++rl
        }
        if (inputs[q].type == "checkbox") {
            checkboxes[c] = inputs[q];
            ++c;
            for (var w = 0; w < labels.length; w++)
                if (inputs[q].id && labels[w].htmlFor == inputs[q].id) checkboxLabels[cl] = labels[w];
            ++cl
        }
        if (inputs[q].type == "submit" || inputs[q].type == "button") {
            buttons[b] = inputs[q];
            ++b
        }
    }
}

function replaceRadios() {
    for (var i = 0; i < radios.length; i++) {
        if (radios[0].classList.contains('outtaHere')) { continue; }
        radios[i].classList.add("outtaHere");
        var radioArea = document.createElement("div");
        if (radios[q].checked) {
            radioArea.className = "radioAreaChecked";
            if (radioLabels[i]) radioLabels[i].classList.add("radioAreaCheckedLabel")
        } else radioArea.className = "radioArea";
        radioArea.id = "myRadio" + i;
        radios[i].parentNode.insertBefore(radioArea, radios[i]);
        radios[i]._ra = radioArea;
        radioArea.onclick = new Function("rechangeRadios(" + i + ")");
        if (radioLabels[i]) radioLabels[i].onclick = new Function("rechangeRadios(" + i + ")")
    }
    return true
}

function checkRadios(who) {
    var what = radios[who]._ra;
    for (var q = 0; q < radios.length; q++)
        if (radios[q]._ra.className == "radioAreaChecked" && radios[q]._ra.nextSibling.name == radios[who].name) {
            radios[q]._ra.className = "radioArea";
            if (radioLabels[q]) radioLabels[q].className = radioLabels[q].className.replace("radioAreaCheckedLabel", "")
        }
    what.className = "radioAreaChecked";
    if (radioLabels[who]) radioLabels[who].className += " radioAreaCheckedLabel"
}

function changeRadios(who) {
    if (radios[who].checked)
        for (var q = 0; q < radios.length; q++) {
            if (radios[q].name == radios[who].name) radios[q].checked = false;
            radios[who].checked = true;
            checkRadios(who)
        }
}

function rechangeRadios(who) {
    if (!radios[who].checked)
        for (var q = 0; q < radios.length; q++) {
            if (radios[q].name == radios[who].name) radios[q].checked = false;
            radios[who].checked = true;
            checkRadios(who)
        }
}

function replaceCheckboxes() {
    for (var q = 0; q < checkboxes.length; q++) {
        if (checkboxes[q].classList.contains('outtaHere')) { continue; }
        if (checkboxes[q].classList.contains('default')) { continue; }
        checkboxes[q].classList.add("outtaHere");
        var checkboxArea = document.createElement("div");
        if (checkboxes[q].checked) {
            checkboxArea.className = "checkboxAreaChecked";
            if (checkboxLabels[q]) checkboxLabels[q].classList.add("checkboxAreaCheckedLabel");
        } else checkboxArea.className = "checkboxArea";
        checkboxArea.id = "myCheckbox" + q;
        checkboxes[q].parentNode.insertBefore(checkboxArea, checkboxes[q]);
        checkboxes[q]._ca = checkboxArea;
        checkboxArea.onclick = checkboxArea.onclick2 = new Function("rechangeCheckboxes(" + q + ")");
        if (checkboxLabels[q]) checkboxLabels[q].onclick = new Function("changeCheckboxes(" + q + ")");
        checkboxes[q].onkeydown = checkEvent
    }
    return true
}

function checkCheckboxes(who, action) {
    var what = checkboxes[who]._ca;
    if (action == true) {
        what.className = "checkboxAreaChecked";
        what.checked = true;
        if (checkboxLabels[who]) checkboxLabels[who].className += " checkboxAreaCheckedLabel"
    }
    if (action == false) {
        what.className = "checkboxArea";
        what.checked = false;
        if (checkboxLabels[who]) checkboxLabels[who].className = checkboxLabels[who].className.replace("checkboxAreaCheckedLabel", "")
    }
}

function changeCheckboxes(who) {
    if (checkboxes[who].checked) checkCheckboxes(who, false);
    else checkCheckboxes(who, true)
}

function rechangeCheckboxes(who) {
    var tester = false;
    if (checkboxes[who].checked == true) tester = false;
    else tester = true;
    checkboxes[who].checked = tester;
    checkCheckboxes(who, tester)
}

function checkEvent(e) {
    if (!e) var e = window.event;
    if (e.keyCode == 32)
        for (var q = 0; q < checkboxes.length; q++)
            if (this == checkboxes[q]) changeCheckboxes(q)
}

function replaceSelects() {
    for (var q = 0; q < selects.length; q++) {
        if (!selects[q].replaced && selects[q].offsetWidth && selects[q].className.indexOf("default") == -1) {
            selects[q]._number = q;
            var selectArea = document.createElement("div");
            var left = document.createElement("span");
            left.className = "left";
            selectArea.appendChild(left);
            var disabled = document.createElement("span");
            disabled.className = "disabled";
            selectArea.appendChild(disabled);
            selects[q]._disabled = disabled;
            var center = document.createElement("span");
            var button = document.createElement("a");
            var text = document.createTextNode(selectText);
            center.id = "mySelectText" + q;
            var stWidth = selects[q].offsetWidth;
            selectArea.style.minWidth = stWidth + "px";
            if (selects[q].parentNode.className.indexOf("type2") != -1) button.href = "javascript:showOptions(" + q + ",true)";
            else button.href = "javascript:showOptions(" + q + ",false)";
            button.className = "selectButton";
            selectArea.className = "selectArea";
            selectArea.className += " " + selects[q].className;
            selectArea.id = "sarea" + q;
            center.className = "center";
            center.appendChild(text);
            selectArea.appendChild(center);
            selectArea.appendChild(button);
            selects[q].className += " outtaHere";
            selects[q].parentNode.insertBefore(selectArea, selects[q]);
            var optionsDiv = document.createElement("div");
            var optionsListParent = document.createElement("div");
            optionsListParent.className = "select-center";
            var optionsListParent2 = document.createElement("div");
            optionsListParent2.className = "select-center-right";
            var optionsList = document.createElement("ul");
            optionsDiv.innerHTML += "<div class='select-top'><div class='select-top-left'></div><div class='select-top-right'></div></div>";
            optionsListParent.appendChild(optionsListParent2);
            optionsListParent.appendChild(optionsList);
            optionsDiv.appendChild(optionsListParent);
            selects[q]._options = optionsList;
            optionsDiv.style.width = stWidth + "px";
            optionsDiv._parent = selectArea;
            optionsDiv.className = "optionsDivInvisible";
            optionsDiv.id = "optionsDiv" + q;
            populateSelectOptions(selects[q]);
            optionsDiv.innerHTML += "<div class='select-bottom'><div class='select-bottom-left'></div><div class='select-bottom-right'></div></div>";
            document.getElementsByTagName("body")[0].appendChild(optionsDiv);
            selects[q].replaced = true
        }
        all_selects = true
    }
}

function populateSelectOptions(me) {
    me._options.innerHTML = "";
    for (var w = 0; w < me.options.length; w++)
        if (me.options[w].title.indexOf("title") == -1) {
            var optionHolder = document.createElement("li");
            var optionLink = document.createElement("a");
            var optionTxt;
            if (me.options[w].title.indexOf("image") != -1) {
                optionTxt = document.createElement("img");
                optionSpan = document.createElement("span");
                optionTxt.src = me.options[w].title;
                optionSpan = document.createTextNode(me.options[w].text)
            } else optionTxt = document.createTextNode(me.options[w].text);
            optionLink.href = "javascript:showOptions(" + me._number + "); selectMe('" + me.id + "'," + w + "," + me._number + ");";
            if (me.options[w].title.indexOf("image") != -1) {
                optionLink.appendChild(optionTxt);
                optionLink.appendChild(optionSpan)
            } else optionLink.appendChild(optionTxt);
            optionHolder.appendChild(optionLink);
            me._options.appendChild(optionHolder);
            if (me.options[w].selected) selectMe(me.id, w, me._number)
        } else if (me.options[w].selected) selectMe(me.id, w, me._number);
    if (me.disabled) me._disabled.style.display = "block";
    else me._disabled.style.display = "none"
}

function selectMe(selectFieldId, linkNo, selectNo) {
    selectField = selects[selectNo];
    for (var k = 0; k < selectField.options.length; k++)
        if (k == linkNo) {
            selectField.options[k].selected = true;
            $(selectField).trigger("change");
        }
        else selectField.options[k].selected = false;
//    console.log(selectField.options[linkNo].selected);
//    console.log(selectField.options[linkNo].text);
    textVar = document.getElementById("mySelectText" + selectNo);
    var newText;
    var optionSpan;
    if (selectField.options[linkNo].title.indexOf("image") != -1) {
        newText = document.createElement("img");
        newText.src = selectField.options[linkNo].title;
        optionSpan = document.createElement("span");
        optionSpan = document.createTextNode(selectField.options[linkNo].text)
    } else newText = document.createTextNode(selectField.options[linkNo].text); if (selectField.options[linkNo].title.indexOf("image") != -1) {
        if (textVar.childNodes.length > 1) textVar.removeChild(textVar.childNodes[0]);
        textVar.replaceChild(newText, textVar.childNodes[0]);
        textVar.appendChild(optionSpan)
    } else {
        if (textVar.childNodes.length > 1) textVar.removeChild(textVar.childNodes[0]);
        textVar.replaceChild(newText, textVar.childNodes[0])
    } if (selectField.onchange && all_selects) eval(selectField.onchange())
}

function showOptions(g) {
    _elem = document.getElementById("optionsDiv" + g);
    var divArea = document.getElementById("sarea" + g);
    if (active_select && active_select != _elem) {
        active_select.className = active_select.className.replace("optionsDivVisible", "optionsDivInvisible");
        active_select.style.height = "auto";
        _active.className = _active.className.replace("selectAreaActive", "")
    }
    if (_elem.className.indexOf("optionsDivInvisible") != -1) {
        _elem.style.left = "-9999px";
        _elem.style.top = findPosY(divArea) + _selectHeight + "px";
        _elem.className = _elem.className.replace("optionsDivInvisible", "");
        _elem.style.width = $(divArea).width() + 'px'
        _elem.className += " optionsDivVisible";
        _elem.style.left = findPosX(divArea) + "px";
        divArea.className += " selectAreaActive";
        _active = divArea;
        active_select = _elem;
        if (document.documentElement) document.documentElement.onclick = hideSelectOptions;
        else window.onclick = hideSelectOptions
    } else if (_elem.className.indexOf("optionsDivVisible") != -1) {
        _elem.style.height = "auto";
        _elem.className = _elem.className.replace("optionsDivVisible", "");
        _elem.className += " optionsDivInvisible";
        divArea.className = divArea.className.replace("selectAreaActive", "")
    }
}
_active = false;

function hideSelectOptions(e) {
    if (active_select) {
        if (!e) e = window.event;
        var _target = e.target || e.srcElement;
        if (isElementBefore(_target, "selectArea") == 0 && isElementBefore(_target, "optionsDiv") == 0) {
            active_select.className = active_select.className.replace("optionsDivVisible", "");
            active_select.className = active_select.className.replace("optionsDivInvisible", "");
            active_select.className += " optionsDivInvisible";
            _active.className = _active.className.replace("selectAreaActive", "");
            active_select = false;
            if (document.documentElement) document.documentElement.onclick = function () {};
            else window.onclick = null
        }
    }
}

function isElementBefore(_el, _class) {
    var _parent = _el;
    do _parent = _parent.parentNode; while (_parent && _parent.className != null && _parent.className.indexOf(_class) == -1);
    if (_parent.className && _parent.className.indexOf(_class) != -1) return 1;
    else return 0
}

function findPosY(obj) {
    return $(obj).offset().top;
}

function findPosX(obj) {
    return $(obj).offset().left - 1;
}

function initSubmitFormHelpers() {
    $('.submit-form').change(function () {
        $(this).closest('form').submit();
    });

    $('.submit-form-on-click').click(function () {
        $(this).closest('form').submit();
    });
}

$(document).ajaxStart(function () {
   $('body').addClass('loading');
}).ajaxStop(function () {
   $('body').removeClass('loading');
});

// inner-menu support, bootstrap-like without tabs. Naive implementation, href is always #id, no history.
$(function ($) {
    var menu_links = $('.inner-menu a');
    menu_links.click(function (event) {
        event.preventDefault();
        select_tab($(this).attr('href'));
        if (window.history) {
            window.history.pushState({}, null, $(this).attr('href'));
        }
    });

    function init() {
        if (location.hash) {
            var $tab;
            try {
                $tab = $(location.hash);
            } catch (ignored) {};

            if ($tab && $tab.length) {
                select_tab(location.hash);
                return;
            }
        }

        select_tab($('.inner-menu a.active').attr('href'));
    }

    init();

    if (menu_links.length) {
        $(window).on('popstate', init);
    }

    function select_tab(hash_id) {
        $('.section-tab').not(hash_id).removeClass('active');
        $(hash_id).addClass('active');
        $('.inner-menu a').removeClass('active');
        $('.inner-menu a[href="' + hash_id + '"]').addClass('active');
    }
})

// show alert
var SUCCESS = 0;
var FAIL = 1;
var WARNING = 2;
var INFO = 3;

function show_alert(type, msg){
    type = type || SUCCESS;
    msg = msg || '';
    var $alert = $('#alert-board');
    $alert.removeClass('alert-success alert-danger alert-warning');
    $alert.find('.message').html(msg);

    switch (type){
        case SUCCESS:
            $alert.addClass('alert-success');
            break;
        case FAIL:
            $alert.addClass('alert-danger');
            break;
        case WARNING:
            $alert.addClass('alert-warning');
            break;
        case INFO:
            $alert.addClass('alert-info');
            break;
    }

    $alert.slideDown();
}

function hide_alert(){
    $('#alert-board').slideUp();
}
