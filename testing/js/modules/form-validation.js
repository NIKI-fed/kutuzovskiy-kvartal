// ========== ВАЛИДАЦИЯ ФОРМЫ ==========
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