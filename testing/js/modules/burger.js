// ============================================
// БУРГЕР-МЕНЮ
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.getElementById('menuToggle');
    const nav = document.getElementById('mainNav');

    if (!menuToggle || !nav) return;

    // Создаём оверлей
    const overlay = document.createElement('div');
    overlay.className = 'nav-overlay';
    document.body.appendChild(overlay);

    function toggleMenu() {
        const isOpen = nav.classList.toggle('open');
        menuToggle.classList.toggle('active');
        overlay.classList.toggle('active');
        document.body.style.overflow = isOpen ? 'hidden' : '';
    }

    function closeMenu() {
        nav.classList.remove('open');
        menuToggle.classList.remove('active');
        overlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    // Открытие/закрытие по кнопке
    menuToggle.addEventListener('click', toggleMenu);

    // Закрытие по клику на оверлей
    overlay.addEventListener('click', closeMenu);

    // Закрытие по клику на ссылку
    nav.querySelectorAll('.nav__link').forEach(link => {
        link.addEventListener('click', closeMenu);
    });

    // Закрытие по Escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && nav.classList.contains('open')) {
            closeMenu();
        }
    });

    // Закрытие при изменении размера окна (если меню открыто и стало широко)
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768 && nav.classList.contains('open')) {
            closeMenu();
        }
    });
});