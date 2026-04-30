// ========== 1. КАРУСЕЛЬ АКЦИЙ ==========
const track = document.getElementById('actionsTrack');
const slides = Array.from(track?.children || []);
const nextBtn = document.getElementById('actionsNext');
const prevBtn = document.getElementById('actionsPrev');
let currentIndex = 0;
let slidesPerView = 1;

function updateCarousel() {
    if (!track || slides.length === 0) return;
    
    if (window.innerWidth >= 1024) slidesPerView = 3;
    else if (window.innerWidth >= 640) slidesPerView = 2;
    else slidesPerView = 1;
    
    const slideWidth = 100 / slidesPerView;
    const gap = 30;
    const gapPercent = (gap * (slidesPerView - 1)) / (window.innerWidth > 1024 ? 1280 : window.innerWidth);
    
    slides.forEach(slide => {
        slide.style.flex = `0 0 calc(${slideWidth}% - ${(gapPercent * slideWidth)}%)`;
    });
    
    const maxIndex = Math.max(0, slides.length - slidesPerView);
    if (currentIndex > maxIndex) currentIndex = maxIndex;
    
    const shift = currentIndex * slideWidth;
    track.style.transform = `translateX(-${shift}%)`;
    
    if (prevBtn) prevBtn.style.opacity = currentIndex === 0 ? '0.3' : '1';
    if (nextBtn) nextBtn.style.opacity = currentIndex >= maxIndex ? '0.3' : '1';
}

if (track && slides.length) {
    updateCarousel();
    window.addEventListener('resize', updateCarousel);
    
    nextBtn?.addEventListener('click', () => {
        const maxIndex = Math.max(0, slides.length - slidesPerView);
        if (currentIndex < maxIndex) {
            currentIndex++;
            updateCarousel();
        }
    });
    
    prevBtn?.addEventListener('click', () => {
        if (currentIndex > 0) {
            currentIndex--;
            updateCarousel();
        }
    });
}

// ========== 2. МОДАЛЬНОЕ ОКНО ==========
const modal = document.getElementById('modal');
const modalBody = document.getElementById('modal-body');
const modalSuccess = document.getElementById('modal-success');

function openModal() {
    if (!modal) return;
    modal.classList.add('active');
    if (modalBody) modalBody.style.display = 'block';
    if (modalSuccess) modalSuccess.style.display = 'none';
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    if (!modal) return;
    modal.classList.remove('active');
    document.body.style.overflow = '';
}

document.querySelectorAll('[data-modal-open]').forEach(btn => {
    btn.addEventListener('click', openModal);
});

document.querySelectorAll('[data-modal-close]').forEach(btn => {
    btn.addEventListener('click', closeModal);
});

modal?.addEventListener('click', (e) => {
    if (e.target === modal) closeModal();
});

// ========== 3. ОТПРАВКА ФОРМЫ ==========
const form = document.getElementById('callback-form');
if (form) {
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(form);
        
        // ⚠️ ЗАМЕНИТЕ НА URL ВАШЕГО БЭКА
        const BACKEND_URL = 'https://ваш-бэк.ру/api/send';
        
        try {
            const response = await fetch(BACKEND_URL, {
                method: 'POST',
                body: formData
            });
            if (response.ok) {
                if (modalBody) modalBody.style.display = 'none';
                if (modalSuccess) modalSuccess.style.display = 'block';
                form.reset();
            } else {
                alert('Ошибка отправки. Попробуйте позже.');
            }
        } catch (error) {
            alert('Ошибка соединения. Проверьте интернет.');
        }
    });
}

// ========== 4. COOKIES-УВЕДОМЛЕНИЕ ==========
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

// ========== 5. АНИМАЦИЯ ПРИ СКРОЛЛЕ ==========
const animatedElements = document.querySelectorAll('.section, .hero, .cta');
animatedElements.forEach(el => {
    el.classList.add('fade-up');
});

function checkVisibility() {
    animatedElements.forEach(el => {
        const rect = el.getBoundingClientRect();
        if (rect.top < window.innerHeight - 100) {
            el.classList.add('visible');
        }
    });
}

window.addEventListener('scroll', checkVisibility);
window.addEventListener('resize', checkVisibility);
checkVisibility();

// ========== 6. МОБИЛЬНОЕ МЕНЮ (ЗАГЛУШКА) ==========
const mobileToggle = document.querySelector('.mobile-menu-toggle');
if (mobileToggle) {
    mobileToggle.addEventListener('click', () => {
        alert('Мобильное меню — доработайте под свои нужды');
    });
}