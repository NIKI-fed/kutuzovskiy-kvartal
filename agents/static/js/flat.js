(function () {
    var btn = document.getElementById('reserve-btn');
    var msg = document.getElementById('reserve-msg');
    if (!btn || !msg) return;

    btn.addEventListener('click', function () {
        msg.hidden = false;
        btn.disabled = true;
        btn.textContent = 'Заявка оформлена';
    });
})();
