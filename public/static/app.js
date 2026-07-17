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

  // End-of-session celebration: confetti + the score counting up.
  var celebrate = document.getElementById("celebrate");
  var calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (celebrate && !calm) {
    var colors = ["#6b4ea8", "#8a6fd0", "#f0a818", "#1f9d55", "#e0608a", "#4ea8d8"];
    for (var i = 0; i < 80; i++) {
      var piece = document.createElement("i");
      piece.className = "confetti";
      piece.style.left = Math.random() * 100 + "%";
      piece.style.background = colors[i % colors.length];
      piece.style.animationDelay = Math.random() * 1.2 + "s";
      piece.style.animationDuration = 2.2 + Math.random() * 1.8 + "s";
      piece.style.transform = "rotate(" + Math.floor(Math.random() * 360) + "deg)";
      document.body.appendChild(piece);
    }
  }
  var count = document.getElementById("count");
  if (count && !calm) {
    var target = parseInt(count.textContent, 10);
    if (!isNaN(target) && target > 0) {
      var shown = 0;
      count.textContent = "0";
      var tick = setInterval(function () {
        shown += 1;
        count.textContent = String(shown);
        if (shown >= target) clearInterval(tick);
      }, Math.min(90, 700 / target));
    }
  }
});
