// Progressive enhancement only — the app works fully without JS.
// 1) autofocus the answer box and time the response, 2) let Enter trigger "Next",
// 3) on multiple-choice problems, keys a-d (or 1-4) pick an option.
document.addEventListener("DOMContentLoaded", function () {
  var form = document.getElementById("answer-form");
  if (form) {
    var t0 = Date.now();
    form.addEventListener("submit", function () {
      var ms = document.getElementById("ms");
      if (ms) ms.value = String(Date.now() - t0);
    });
  }

  var input = document.querySelector("input.answer");
  if (input) input.focus();

  var radios = form
    ? form.querySelectorAll('input[type="radio"][name="answer"]')
    : [];
  if (radios.length) {
    document.addEventListener("keydown", function (e) {
      var k = e.key.toLowerCase();
      var i = "abcdefgh".indexOf(k);
      if (i < 0 && k >= "1" && k <= "8") i = k.charCodeAt(0) - 49;
      if (i >= 0 && i < radios.length) radios[i].checked = true;
    });
  }

  var next = document.getElementById("next");
  if (next) {
    next.focus();
    document.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        next.click();
      }
    });
  }
});
