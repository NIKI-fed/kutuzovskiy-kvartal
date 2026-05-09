// ========== ОТПРАВКА ФОРМЫ ==========
const form = document.getElementById('callback-form');
const phoneInput = document.querySelector('#callback-form input[type="tel"]');
const nameInput = document.querySelector('#callback-form input[name="name"]');
const consentCheckbox = document.querySelector('#callback-form #consent');
const submitBtn = document.querySelector('#callback-form button[type="submit"]');
const modalBody = document.getElementById('modal-body');
const modalSuccess = document.getElementById('modal-success');

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
                // Вызываем события, чтобы триггернуть валидацию
                if (nameInput) {
                    const inputEvent = new Event('input');
                    nameInput.dispatchEvent(inputEvent);
                }
                if (consentCheckbox) {
                    const changeEvent = new Event('change');
                    consentCheckbox.dispatchEvent(changeEvent);
                }
                if (phoneInput) {
                    const inputEvent = new Event('input');
                    phoneInput.dispatchEvent(inputEvent);
                }
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