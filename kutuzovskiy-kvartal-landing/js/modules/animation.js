function initAnimation() {
    const heroContainer = document.getElementById('heroContainer');
    const formWrapper = document.getElementById('formWrapper');
    const formContainer = document.querySelector('.form-container')
    
    if (heroContainer && formWrapper) {
        setTimeout(() => {
            heroContainer.classList.add('move-up');
            
            setTimeout(() => {
                formWrapper.style.display = 'block';

                setTimeout(() => {
                    formWrapper.classList.add('visible');
                    

                    setTimeout(() => {
                        formContainer.style.backdropFilter = 'blur(1px)';

                        setTimeout(() => {
                            formContainer.style.backdropFilter = 'blur(2px)';
                            
                            setTimeout(() => {
                                formContainer.style.backdropFilter = 'blur(3px)';
                                
                                setTimeout(() => {
                                    formContainer.style.backdropFilter = 'blur(4px)';
                                    
                                    setTimeout(() => {
                                        formContainer.style.backdropFilter = 'blur(5px)';
                                        
                                        setTimeout(() => {
                                            formContainer.style.backdropFilter = 'blur(6px)';
                                            
                                        }, 100)
                                    }, 100)
                                }, 100)
                            }, 100)
                        }, 100)
                    }, 100)

                    
                }, 20); // микро-пауза для запуска transition
            }, 600);
        }, 3000);
    }
}

document.addEventListener('DOMContentLoaded', initAnimation);