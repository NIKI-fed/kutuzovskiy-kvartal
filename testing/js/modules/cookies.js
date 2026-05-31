// ========== COOKIES-УВЕДОМЛЕНИЕ ==========
const cookiesNotice = document.getElementById('cookies-notice');

function checkCookiesConsent() {
    const consent = localStorage.getItem('cookiesAccepted');
    if (!consent && cookiesNotice) {
        cookiesNotice.style.display = 'flex';
    }
}

function acceptCookies() {
    localStorage.setItem('cookiesAccepted', 'true');
    if (cookiesNotice) {
        cookiesNotice.style.display = 'none';
    }
}

checkCookiesConsent();

const acceptBtn = document.getElementById('cookies-accept');
if (acceptBtn) {
    acceptBtn.addEventListener('click', acceptCookies);
}