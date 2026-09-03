// ============================================
// ПЕРЕКЛЮЧЕНИЕ ПЛАНИРОВОК
// ============================================

// Данные для каждой планировки
const kutuzovData = {
    1: {
        title: '1 комнатная квартира',
        image: '/assets/images/plans/bs_1/1.png',
        area: 'От 43 кв метров',
        address: 'Клубный дом "На Кутузова"'
    },
    2: {
        title: '2 комнатная квартира',
        image: '/assets/images/plans/bs_1/2.png',
        area: 'От 54 кв метров',
        address: 'Клубный дом "На Кутузова"'
    },
    3: {
        title: '3 комнатная квартира',
        image: '/assets/images/plans/bs_1/3.png',
        area: 'От 73 кв метров',
        address: 'Клубный дом "На Кутузова"'
    }
};

// Данные для Клубного дома "На Толстого"
const tolstoyData = {
    2: {
        title: '2 комнатная квартира',
        image: '/assets/images/plans/bs_2/2.png',
        area: 'От 54 кв метров',
        address: 'Клубный дом "На Кутузова"'
    },
    3: {
        title: '3 комнатная квартира',
        image: '/assets/images/plans/bs_2/3.png',
        area: 'От 73 кв метров',
        address: 'Клубный дом "На Кутузова"'
    }
};

const planningSection = document.querySelector('.planning-section');

if (planningSection) {

    // Определяем, какой дом на странице
    let roomsData = {}
    if (planningSection.dataset.house === "kutuzov") {
        roomsData = kutuzovData;
    } else if (planningSection.dataset.house === "tolstoy") {
        roomsData = tolstoyData;
    }

    // Находим все элементы
    const buttons = document.querySelectorAll('.floor-btn');
    const carouselEl = document.querySelector('.planning-section [data-carousel]');
    const imageElement = document.querySelector('.image-placeholder');
    const titleElement = document.querySelector('.apartment-card__title');
    const infoSpans = document.querySelectorAll('.apartment-card__info span');

    // Функция обновления контента
    function updateRoom(roomNumber) {
        const roomData = roomsData[roomNumber];
        if (!roomData) return;

        // Меняем заголовок
        if (titleElement) titleElement.textContent = roomData.title;

        // Меняем информацию
        if (infoSpans[0]) infoSpans[0].textContent = roomData.area;
        if (infoSpans[1]) infoSpans[1].textContent = roomData.address;

        // Обновляем изображение: карусель (фильтрация) или одиночная картинка
        if (carouselEl && carouselEl.__carousel) {
            const roomSlides = carouselEl.querySelectorAll(`[data-carousel-slide][data-room="${roomNumber}"]`);
            if (roomSlides.length > 0) {
                carouselEl.__carousel.filter(slide => parseInt(slide.dataset.room) === roomNumber);
            } else {
                carouselEl.__carousel.filter(() => true);
            }
        } else if (imageElement) {
            imageElement.src = roomData.image;
            imageElement.alt = roomData.title;
        }

        // Меняем активную кнопку
        buttons.forEach(btn => {
            btn.classList.toggle('active', parseInt(btn.dataset.room) === roomNumber);
        });
    }

    // Навешиваем обработчики на кнопки
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            updateRoom(parseInt(this.dataset.room));
        });
    });

    // Устанавливаем активную комнату по умолчанию
    const firstRoom = Object.keys(roomsData)[0]; // берём первый ключ
    updateRoom(parseInt(firstRoom));

}