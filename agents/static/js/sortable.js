(function () {
    "use strict";

    function cellValue(td) {
        var v = td.getAttribute("data-sort");
        return v === null ? (td.textContent || "").trim() : v;
    }

    function isNumericColumn(rows, index) {
        var count = 0, numeric = 0;
        for (var r = 0; r < rows.length; r++) {
            var td = rows[r].cells[index];
            if (!td) continue;
            var raw = td.getAttribute("data-sort");
            if (raw === null || raw === "") raw = (td.textContent || "").trim();
            if (raw === "") continue;
            count++;
            if (/^-?\d+(\.\d+)?$/.test(raw)) numeric++;
        }
        return count > 0 && numeric === count;
    }

    function sortRows(tbody, colIndex, direction, numeric) {
        var rows = Array.prototype.slice.call(tbody.rows);
        rows.sort(function (a, b) {
            var av = a.cells[colIndex] ? cellValue(a.cells[colIndex]) : "";
            var bv = b.cells[colIndex] ? cellValue(b.cells[colIndex]) : "";
            var cmp;
            if (numeric) {
                cmp = (parseFloat(av) || 0) - (parseFloat(bv) || 0);
            } else {
                cmp = av.localeCompare(bv, "ru", { numeric: true, sensitivity: "base" });
            }
            return direction === "desc" ? -cmp : cmp;
        });
        for (var i = 0; i < rows.length; i++) tbody.appendChild(rows[i]);
    }

    function setIndicator(table, activeTh, direction) {
        var heads = table.tHead && table.tHead.rows[0] ? table.tHead.rows[0].cells : [];
        for (var i = 0; i < heads.length; i++) {
            var th = heads[i];
            th.removeAttribute("data-sort-dir");
            th.setAttribute("aria-sort", "none");
        }
        activeTh.setAttribute("data-sort-dir", direction);
        activeTh.setAttribute("aria-sort", direction === "asc" ? "ascending" : "descending");
    }

    function applySort(table, th, direction) {
        var heads = table.tHead.rows[0].cells;
        var index = Array.prototype.indexOf.call(heads, th);
        var tbody = table.tBodies[0];
        if (!tbody) return;
        sortRows(tbody, index, direction, isNumericColumn(tbody.rows, index));
        setIndicator(table, th, direction);
    }

    function initTable(table) {
        var heads = table.tHead && table.tHead.rows[0] ? table.tHead.rows[0].cells : [];
        for (var i = 0; i < heads.length; i++) {
            (function (th) {
                if (!th.getAttribute("data-sort")) return;
                th.setAttribute("role", "button");
                th.setAttribute("tabindex", "0");
                function trigger() {
                    var current = th.getAttribute("data-sort-dir");
                    var next;
                    if (current === "asc") next = "desc";
                    else if (current === "desc") next = "asc";
                    else next = th.getAttribute("data-sort-dir-default") === "desc" ? "desc" : "asc";
                    applySort(table, th, next);
                }
                th.addEventListener("click", trigger);
                th.addEventListener("keydown", function (e) {
                    if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        trigger();
                    }
                });
            })(heads[i]);
        }

        var def = table.querySelector("th[data-sort-default]");
        if (def) {
            var dir = def.getAttribute("data-sort-default") === "desc" ? "desc" : "asc";
            applySort(table, def, dir);
        }
    }

    function init() {
        var tables = document.querySelectorAll("table.is-sortable");
        for (var i = 0; i < tables.length; i++) initTable(tables[i]);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
