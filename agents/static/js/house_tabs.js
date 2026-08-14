(function () {
    "use strict";

    document.querySelectorAll("[data-tabs]").forEach(function (root) {
        var tabs = root.querySelectorAll(".tabs__tab");
        var panels = root.querySelectorAll(".tabs__panel");

        tabs.forEach(function (tab) {
            tab.addEventListener("click", function () {
                var target = tab.getAttribute("data-tab");
                tabs.forEach(function (t) {
                    var active = t === tab;
                    t.classList.toggle("is-active", active);
                    t.setAttribute("aria-selected", active ? "true" : "false");
                });
                panels.forEach(function (p) {
                    p.classList.toggle(
                        "is-active",
                        p.getAttribute("data-panel") === target
                    );
                });
            });
        });
    });
})();
