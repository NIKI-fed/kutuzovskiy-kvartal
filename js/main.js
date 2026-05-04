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
    // document.body.style.overflow = 'hidden';
}

function closeModal() {
    if (!modal) return;
    modal.classList.remove('active');
    // document.body.style.overflow = '';
}

document.querySelectorAll('[data-modal-open]').forEach(btn => {
    btn.addEventListener('click', openModal);
});

document.querySelectorAll('[data-modal-close]').forEach(btn => {
    btn.addEventListener('click', closeModal);
});

modal?.addEventListener('mousedown', (e) => {
    if (e.target === modal) closeModal();
});


// ========== 3. МАСКА ДЛЯ ТЕЛЕФОНА И ВАЛИДАЦИЯ ФОРМЫ ==========
const phoneInput = document.querySelector('#callback-form input[type="tel"]');
const nameInput = document.querySelector('#callback-form input[name="name"]');
const consentCheckbox = document.querySelector('#callback-form #consent');
const submitBtn = document.querySelector('#callback-form button[type="submit"]');

// Функция проверки валидности формы (для активации/деактивации кнопки)
function validateForm() {
    const name = nameInput?.value.trim() || '';
    const phone = phoneInput?.value || '';
    const digits = phone.replace(/\D/g, '');
    const isConsentChecked = consentCheckbox?.checked || false;
    
    const isValid = name.length >= 2 && digits.length === 11 && isConsentChecked;
    
    if (submitBtn) {
        submitBtn.disabled = !isValid;
    }
}

// ===== МАСКА ДЛЯ ТЕЛЕФОНА =====
if (phoneInput) {
    // Автоматическая подстановка "+7 (" при фокусе, если поле пустое
    phoneInput.addEventListener('focus', () => {
        if (!phoneInput.value) {
            phoneInput.value = '+7 (';
        }
    });

    // Обработка потери фокуса — убираем +7, если ничего не введено
    phoneInput.addEventListener('blur', () => {
        if (phoneInput.value === '+7 (') {
            phoneInput.value = '';
        }
        // Подсветка, если номер неполный
        const digits = phoneInput.value.replace(/\D/g, '');
        if (digits.length !== 11 && digits.length > 0) {
            phoneInput.classList.add('input-error');
        } else {
            phoneInput.classList.remove('input-error');
        }
        validateForm();
    });

    // Убираем подсветку при начале ввода
    phoneInput.addEventListener('input', () => {
        phoneInput.classList.remove('input-error');
    });

    // Обработка ввода (форматирование)
    phoneInput.addEventListener('input', (e) => {
        let value = e.target.value;
        
        // Если +7 не в начале, добавляем его
        if (!value.startsWith('+7')) {
            value = '+7' + value.replace(/[^\d]/g, '');
        }
        
        // Удаляем всё, кроме цифр, но сохраняем +7 в начале
        let digits = value.slice(2).replace(/\D/g, '');
        
        // Ограничиваем длину (10 цифр после +7)
        if (digits.length > 10) digits = digits.slice(0, 10);
        
        // Форматируем
        let formatted = '+7 (';
        
        if (digits.length > 0) {
            formatted += digits.slice(0, 3);
        }
        if (digits.length >= 4) {
            formatted += ') ' + digits.slice(3, 6);
        }
        if (digits.length >= 7) {
            formatted += '-' + digits.slice(6, 8);
        }
        if (digits.length >= 9) {
            formatted += '-' + digits.slice(8, 10);
        }
        
        e.target.value = formatted.trim();
        
        validateForm();
    });
    
    // Блокируем ввод любых символов, кроме цифр
    phoneInput.addEventListener('keydown', (e) => {
        const key = e.key;
        const cursorPos = e.target.selectionStart;

        // Разрешаем Delete и Backspace
        if (key === 'Delete' || key === 'Backspace') {
            return;
        }
        
        // Разрешаем только цифры (0-9)
        if (!/^\d$/.test(key)) {
            e.preventDefault();
            return;
        }
        
        // Запрещаем ввод 7 на позиции открывающей скобки (позиция 4)
        if (key === '7' && cursorPos === 4) {
            e.preventDefault();
            return;
        }
    });
}

// ===== ВАЛИДАЦИЯ ИМЕНИ =====
if (nameInput) {
    // Убираем подсветку во время ввода
    nameInput.addEventListener('input', () => {
        nameInput.classList.remove('input-error');
        validateForm();
    });
    
    // Подсвечиваем только при потере фокуса, если имя введено некорректно
    nameInput.addEventListener('blur', () => {
        const name = nameInput.value.trim();
        if (name.length < 2 && name.length > 0) {
            nameInput.classList.add('input-error');
        } else {
            nameInput.classList.remove('input-error');
        }
        validateForm();
    });
}

// ===== ВАЛИДАЦИЯ ЧЕКБОКСА =====
if (consentCheckbox) {
    consentCheckbox.addEventListener('change', () => {
        validateForm();
    });
}

// Вызов валидации при загрузке страницы
validateForm();


// ========== 4. ОТПРАВКА ФОРМЫ ==========
const form = document.getElementById('callback-form');

if (form) {
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Дополнительная проверка перед отправкой (на случай, если кнопка стала активной по ошибке)
        const name = nameInput?.value.trim() || '';
        const phone = phoneInput?.value || '';
        const digits = phone.replace(/\D/g, '');
        const isConsentChecked = consentCheckbox?.checked || false;
        
        // Если форма невалидна — подсвечиваем проблемные поля и выходим
        if (name.length < 2 || digits.length !== 11 || !isConsentChecked) {
            if (phoneInput && digits.length !== 11) {
                phoneInput.classList.add('input-error');
                phoneInput.focus();
            }
            if (nameInput && name.length < 2) {
                nameInput.classList.add('input-error');
                if (!phoneInput || digits.length === 11) nameInput.focus();
            }
            return;
        }
        
        // Убираем подсветку, если всё ок
        phoneInput?.classList.remove('input-error');
        nameInput?.classList.remove('input-error');
        
        const formData = new FormData(form);
        
        // ⚠️ ЗАМЕНИТЕ НА URL ВАШЕГО БЭКА
        const BACKEND_URL = 'https://ваш-бэк.ру/api/send';
        
        // Блокируем кнопку на время отправки, чтобы не было двойных запросов
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Отправка...';
        }
        
        try {
            const response = await fetch(BACKEND_URL, {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                // Показываем сообщение об успехе
                if (modalBody) modalBody.style.display = 'none';
                if (modalSuccess) modalSuccess.style.display = 'block';
                
                // Очищаем форму
                form.reset();
                if (phoneInput) phoneInput.value = '';
                
                // Пересчитываем валидацию (кнопка станет неактивной)
                validateForm();
            } else {
                alert('Ошибка отправки. Попробуйте позже.');
                // Возвращаем кнопке активность
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Отправить';
                }
            }
        } catch (error) {
            alert('Ошибка соединения. Проверьте интернет.');
            // Возвращаем кнопке активность
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Отправить';
            }
        }
    });
}


// ========== 5. COOKIES-УВЕДОМЛЕНИЕ ==========
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