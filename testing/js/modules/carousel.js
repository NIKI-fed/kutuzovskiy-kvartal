// ========== КАРУСЕЛЬ АКЦИЙ ==========
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