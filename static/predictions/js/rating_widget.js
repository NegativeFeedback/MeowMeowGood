(function () {
    var TIER_NAMES = { 1: "Pariah", 2: "Meh", 3: "Solid", 4: "Good", 5: "Icon" };

    function initWidget(root) {
        var slider = root.querySelector("[data-cat-slider]");
        var numOut = root.querySelector("[data-cat-num]");
        var tierOut = root.querySelector("[data-cat-tier]");
        var faces = root.querySelectorAll("[data-tier]");
        if (!slider) return;

        function render() {
            var v = parseFloat(slider.value || "3");
            var nearest = Math.min(5, Math.max(1, Math.round(v)));
            var pct = ((v - 1) / 4) * 100;

            numOut.textContent = v.toFixed(2);
            tierOut.textContent = TIER_NAMES[nearest];
            root.style.setProperty("--tier-color", "var(--tier-" + nearest + ")");
            slider.style.setProperty("--pct", pct + "%");
            slider.setAttribute("aria-valuetext", v.toFixed(2) + " out of 5, " + TIER_NAMES[nearest]);

            faces.forEach(function (face) {
                face.classList.toggle("active", Number(face.dataset.tier) === nearest);
            });
        }

        slider.addEventListener("input", render);
        render();
    }

    document.querySelectorAll("[data-cat-rating]").forEach(initWidget);
})();
