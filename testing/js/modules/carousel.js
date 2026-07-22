// ========== УНИВЕРСАЛЬНАЯ КАРУСЕЛЬ ==========
// Каждая карусель инициализируется по атрибуту [data-carousel].
// Опционально data-carousel-perview задаёт макс. число слайдов на десктопе.

function initCarousel(root) {
    const track = root.querySelector('[data-carousel-track]');
    const viewport = root.querySelector('.carousel__viewport');
    const prevBtn = root.querySelector('[data-carousel-prev]');
    const nextBtn = root.querySelector('[data-carousel-next]');
    if (!track) return;

    const allSlides = Array.from(root.querySelectorAll('[data-carousel-slide]'));
    let visible = allSlides.slice();
    let index = 0;
    let perView = 1;

    function getPerView() {
        const max = parseInt(root.dataset.carouselPerview) || 1;
        const w = window.innerWidth;
        if (w >= 1024) return Math.max(1, max);
        if (w >= 640) return Math.min(max, 2);
        return 1;
    }

    function gap() {
        const g = parseFloat(getComputedStyle(track).gap);
        return isFinite(g) ? g : 0;
    }

    function render() {
        perView = getPerView();
        const g = gap();
        const count = visible.length;

        visible.forEach(slide => {
            slide.style.flex = `0 0 calc((100% - ${g * (perView - 1)}px) / ${perView})`;
        });

        const maxIndex = Math.max(0, count - perView);
        if (index > maxIndex) index = maxIndex;
        if (index < 0) index = 0;

        const containerWidth = (viewport || root).clientWidth;
        const slideStep = count > 0 ? (containerWidth - g * (perView - 1)) / perView + g : 0;
        track.style.transform = `translateX(-${index * slideStep}px)`;

        if (prevBtn) prevBtn.disabled = (index === 0);
        if (nextBtn) nextBtn.disabled = (count <= perView || index >= maxIndex);
    }

    function goTo(i) {
        const maxIndex = Math.max(0, visible.length - perView);
        index = Math.max(0, Math.min(i, maxIndex));
        render();
    }

    function filter(predicate) {
        visible = allSlides.filter(predicate);
        allSlides.forEach(slide => {
            slide.style.display = visible.includes(slide) ? '' : 'none';
        });
        index = 0;
        render();
    }

    nextBtn?.addEventListener('click', () => goTo(index + 1));
    prevBtn?.addEventListener('click', () => goTo(index - 1));

    window.addEventListener('resize', render);

    render();
    root.__carousel = { render, goTo, filter };
}

document.querySelectorAll('[data-carousel]').forEach(initCarousel);
