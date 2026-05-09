const goTopBtn = document.querySelector('.go-top');

window.addEventListener('scroll', () => {
    if (window.scrollY > 500) {
        goTopBtn.classList.add('show');
    } else {
        goTopBtn.classList.remove('show');
    }
});

goTopBtn?.addEventListener('click', () => {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
});