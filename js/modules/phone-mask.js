// ========== МАСКА ДЛЯ ТЕЛЕФОНА ==========
const phoneInput = document.querySelector('#callback-form input[type="tel"]');

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