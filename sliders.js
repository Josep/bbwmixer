var xhr = new XMLHttpRequest();
function toggle(source) {
  xhr.open("GET", "http://"+location.host+"/checkboxes?"+source.name+"="+source.checked, true);
  xhr.send(); 
}
function send(arg,vall,valr) {
  xhr.open("GET", "http://"+location.host+"/sliders?"+arg+"l="+vall+"&"+arg+"r="+valr, true);
  xhr.send(); 
} 
function getval(output_l,output_r,slider_l,slider_r,lr,who) {
  output_l.innerHTML = slider_l.value;
  slider_l.oninput = function() {
    output_l.innerHTML = this.value;
    if (lr.checked == true) {
      output_r.innerHTML = this.value;
      slider_r.value = this.value;
    }
    send(who,slider_l.value,slider_r.value)
  }
  output_r.innerHTML = slider_r.value;
  slider_r.oninput = function() {
    output_r.innerHTML = this.value;
    if (lr.checked == true) {
      output_l.innerHTML = this.value;
      slider_l.value = this.value;
    }
    send(who,slider_l.value,slider_r.value)
  }
}
getval(document.getElementById("master_lv"),document.getElementById("master_rv"),document.getElementById("masterL"),document.getElementById("masterR"),document.getElementById("bal0"),"m");
getval(document.getElementById("c1_lv"),document.getElementById("c1_rv"),document.getElementById("ch1L"),document.getElementById("ch1R"),document.getElementById("bal1"),"c1");
getval(document.getElementById("c2_lv"),document.getElementById("c2_rv"),document.getElementById("ch2L"),document.getElementById("ch2R"),document.getElementById("bal2"),"c2");
getval(document.getElementById("c3_lv"),document.getElementById("c3_rv"),document.getElementById("ch3L"),document.getElementById("ch3R"),document.getElementById("bal3"),"c3");
getval(document.getElementById("c4_lv"),document.getElementById("c4_rv"),document.getElementById("ch4L"),document.getElementById("ch4R"),document.getElementById("bal4"),"c4");
