// Progressive enhancement only — the app works fully without JS.
// 1) autofocus the answer box and time the response, 2) let Enter trigger "Next".
document.addEventListener("DOMContentLoaded", function () {
  var input = document.querySelector("input.answer");
  if (input) {
    input.focus();
    var form = document.getElementById("answer-form");
    var t0 = Date.now();
    if (form) {
      form.addEventListener("submit", function () {
        var ms = document.getElementById("ms");
        if (ms) ms.value = String(Date.now() - t0);
      });
    }
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
