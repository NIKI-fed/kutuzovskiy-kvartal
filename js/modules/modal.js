// ========== МОДАЛЬНОЕ ОКНО ==========
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