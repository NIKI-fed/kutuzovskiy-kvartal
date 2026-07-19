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
        area: 'От 75 кв метров',
        address: 'Клубный дом "На Кутузова"'
    }
};

// Данные для Клубного дома "На Толстого"
const tolstoyData = {
    2: {
        title: '2 комнатная квартира',
        image: '/assets/images/plans/bs_2/2.png',
        area: 'От 54 кв метров',
        address: 'Клубный дом "На Толстого"'
    },
    3: {
        title: '3 комнатная квартира',
        image: '/assets/images/plans/bs_2/3.png',
        area: 'От 73 кв метров',
        address: 'Клубный дом "На Толстого"'
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
    const imageElement = document.querySelector('.image-placeholder');
    const titleElement = document.querySelector('.apartment-card__title');
    const infoSpans = document.querySelectorAll('.apartment-card__info span');

    // Функция обновления контента
    function updateRoom(roomNumber) {
        const roomData = roomsData[roomNumber];
        if (!roomData) return;

        // Меняем картинку
        imageElement.src = roomData.image;
        imageElement.alt = roomData.title;

        // Меняем заголовок
        titleElement.textContent = roomData.title;

        // Меняем информацию
        infoSpans[0].textContent = roomData.area;
        infoSpans[1].textContent = roomData.address;

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