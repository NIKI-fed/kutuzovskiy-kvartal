// ========== ВАЛИДАЦИЯ ФОРМЫ ==========
const phoneInput = document.querySelector('#callback-form input[type="tel"]');
const nameInput = document.querySelector('#callback-form input[name="name"]');
const emailInput = document.querySelector('#callback-form input[name="email"]');
const consentCheckbox = document.querySelector('#callback-form #consent');
const submitBtn = document.querySelector('#callback-form button[type="submit"]');

// Функция проверки email
function isValidEmail(email) {
    if (!email) return true; // пустое поле — ок, оно необязательное
    const emailRegex = /^[^\s@]+@([^\s@.,]+\.)+[^\s@.,]{2,}$/;
    return emailRegex.test(email);
}

// Функция проверки валидности формы (для активации/деактивации кнопки)
function validateForm() {
    const name = nameInput?.value.trim() || '';
    const phone = phoneInput?.value || '';
    const digits = phone.replace(/\D/g, '');
    const email = emailInput?.value.trim() || '';
    const isConsentChecked = consentCheckbox?.checked || false;
    
    const isEmailValid = isValidEmail(email);
    const isValid = name.length >= 2 && digits.length === 11 && isConsentChecked && isEmailValid;
    
    if (submitBtn) {
        submitBtn.disabled = !isValid;
    }
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

// ===== ВАЛИДАЦИЯ EMAIL =====
if (emailInput) {
    // Убираем подсветку во время ввода
    emailInput.addEventListener('input', () => {
        emailInput.classList.remove('input-error');
        validateForm();
    });
    
    // Подсвечиваем только при потере фокуса, если email введён некорректно
    emailInput.addEventListener('blur', () => {
        const email = emailInput.value.trim();
        if (email && !isValidEmail(email)) {
            emailInput.classList.add('input-error');
        } else {
            emailInput.classList.remove('input-error');
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

// Связь с телефоном (перепроверяем при изменении телефона)
if (phoneInput) {
    phoneInput.addEventListener('blur', () => {
        validateForm();
    });
    phoneInput.addEventListener('input', () => {
        validateForm();
    });
}

// Вызов валидации при загрузке страницы
validateForm();