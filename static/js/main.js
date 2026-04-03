// JavaScript para Django - Fondo de Inversiones
document.addEventListener('DOMContentLoaded', function() {
    // Elementos del DOM
    const registerBtn = document.getElementById('registerBtn');
    const heroRegisterBtn = document.getElementById('heroRegisterBtn');
    const demoBtn = document.getElementById('demoBtn');
    const loginBtn = document.getElementById('loginBtn');
    const closeModal = document.getElementById('closeModal');
    const registerModal = document.getElementById('registerModal');
    const registerForm = document.getElementById('registerForm');
    const chartSelect = document.getElementById('chartSelect');
    const totalValueElement = document.getElementById('totalValue');
    const growthRateElement = document.getElementById('growthRate');

    // Variables para simular datos
    let portfolioValue = 42580;
    let growthRate = 12.5;

    // Inicializar gráfico
    const chartCanvas = document.getElementById('performanceChart');
    const ctx = chartCanvas.getContext('2d');
    let performanceChart;

    // Configurar datos del gráfico
    const chartConfigs = {
        year: {
            labels: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'],
            data: [38000, 39500, 41000, 39800, 41500, 42000, 41800, 42500, 43000, 42800, 43500, 42580],
            color: 'rgba(0, 82, 204, 0.8)'
        },
        month: {
            labels: ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4'],
            data: [41000, 41500, 42200, 42580],
            color: 'rgba(0, 201, 183, 0.8)'
        },
        week: {
            labels: ['Lun', 'Mar', 'Mié', 'Jue', 'Vie'],
            data: [42300, 42450, 42500, 42400, 42580],
            color: 'rgba(255, 107, 107, 0.8)'
        }
    };

    // Inicializar el gráfico
    function initChart(period = 'year') {
        const config = chartConfigs[period];

        if (performanceChart) {
            performanceChart.destroy();
        }

        performanceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: config.labels,
                datasets: [{
                    label: 'Valor de la cartera ($)',
                    data: config.data,
                    backgroundColor: 'rgba(0, 82, 204, 0.1)',
                    borderColor: config.color,
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: config.color,
                    pointRadius: 5,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                return `$${context.parsed.y.toLocaleString()}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    // Simular crecimiento de la cartera
    function simulatePortfolioGrowth() {
        // Incremento aleatorio entre -0.5% y 1.5%
        const change = (Math.random() * 2 - 0.5);
        growthRate += change;

        // Actualizar valor de la cartera basado en la tasa de crecimiento
        portfolioValue += portfolioValue * (change / 100);

        // Actualizar elementos del DOM
        totalValueElement.textContent = `$${Math.round(portfolioValue).toLocaleString()}`;
        growthRateElement.textContent = `${growthRate > 0 ? '+' : ''}${growthRate.toFixed(2)}%`;
        growthRateElement.className = `portfolio-change ${growthRate >= 0 ? 'positive' : 'negative'}`;

        // Actualizar datos del gráfico actual
        const currentPeriod = chartSelect.value;
        const config = chartConfigs[currentPeriod];

        if (config && config.data.length > 0) {
            // Agregar nuevo dato y eliminar el más antiguo
            config.data.push(portfolioValue);
            config.data.shift();

            // Actualizar gráfico
            performanceChart.update();
        }
    }

    // Mostrar/ocultar modal de registro
    function showRegisterModal() {
        registerModal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function hideRegisterModal() {
        registerModal.classList.remove('active');
        document.body.style.overflow = 'auto';
    }

    // Efecto de aparición al hacer scroll
    function checkFadeInElements() {
        const fadeElements = document.querySelectorAll('.fade-in');

        fadeElements.forEach(element => {
            const elementTop = element.getBoundingClientRect().top;
            const windowHeight = window.innerHeight;

            if (elementTop < windowHeight - 100) {
                element.classList.add('visible');
            }
        });
    }

    // Manejar envío del formulario
    function handleFormSubmit(e) {
        e.preventDefault();

        const name = document.getElementById('name').value;
        const email = document.getElementById('email').value;
        const investmentLevel = document.getElementById('investment').value;

        // Simular envío de formulario
        const submitBtn = registerForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;

        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';
        submitBtn.disabled = true;

        setTimeout(() => {
            alert(`¡Gracias ${name}! Tu cuenta ha sido creada exitosamente. Hemos enviado un correo de confirmación a ${email}.`);
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
            hideRegisterModal();
            registerForm.reset();

            // Simular inicio de sesión automático
            loginBtn.innerHTML = '<i class="fas fa-user"></i> ' + name.split(' ')[0];
            registerBtn.style.display = 'none';
        }, 2000);
    }

    // Simular demostración
    function showDemo() {
        alert("¡Bienvenido a la demostración de FinvestPro! En una versión completa, aquí podrías explorar todas las funcionalidades de la plataforma con datos de ejemplo.");

        // Animación para destacar características
        const features = document.querySelectorAll('.feature-card');
        features.forEach((feature, index) => {
            setTimeout(() => {
                feature.style.transform = 'scale(1.05)';
                feature.style.boxShadow = '0 20px 40px rgba(0, 82, 204, 0.25)';

                setTimeout(() => {
                    feature.style.transform = '';
                    feature.style.boxShadow = '';
                }, 1000);
            }, index * 300);
        });
    }

    // Event Listeners
    registerBtn.addEventListener('click', showRegisterModal);
    heroRegisterBtn.addEventListener('click', showRegisterModal);
    demoBtn.addEventListener('click', showDemo);
    loginBtn.addEventListener('click', () => alert('Funcionalidad de inicio de sesión en desarrollo.'));
    closeModal.addEventListener('click', hideRegisterModal);
    registerModal.addEventListener('click', (e) => {
        if (e.target === registerModal) hideRegisterModal();
    });

    registerForm.addEventListener('submit', handleFormSubmit);
    chartSelect.addEventListener('change', (e) => initChart(e.target.value));

    // Inicializar efectos al cargar la página
    window.addEventListener('scroll', checkFadeInElements);
    window.addEventListener('load', checkFadeInElements);

    // Inicializar gráfico y simulación
    initChart();
    setInterval(simulatePortfolioGrowth, 5000);

    // Inicializar datos simulados
    setTimeout(() => {
        simulatePortfolioGrowth();
    }, 1000);

    // Smooth scroll para enlaces internos
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();

            const targetId = this.getAttribute('href');
            if (targetId === '#') return;

            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Efecto de escritura para el título principal
    const heroTitle = document.querySelector('.hero h1 span');
    if (heroTitle) {
        const originalText = heroTitle.textContent;
        heroTitle.textContent = '';

        let i = 0;
        function typeWriter() {
            if (i < originalText.length) {
                heroTitle.textContent += originalText.charAt(i);
                i++;
                setTimeout(typeWriter, 50);
            }
        }

        // Iniciar efecto de escritura después de un breve retraso
        setTimeout(typeWriter, 500);
    }
});