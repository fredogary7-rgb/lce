/**
 * LCE - Leader Chiffre Entreprise
 * Main JavaScript
 */
document.addEventListener('DOMContentLoaded', function () {

    // ============================================================
    // INIT AOS
    // ============================================================
    AOS.init({
        duration: 800,
        easing: 'ease-out-cubic',
        once: true,
        offset: 50,
    });

    // ============================================================
    // NAVBAR SCROLL EFFECT
    // ============================================================
    const navbar = document.getElementById('mainNav');
    if (navbar) {
        window.addEventListener('scroll', function () {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        });
    }

    // ============================================================
    // HERO PREMIUM: ENTRÉE PROGRESSIVE ENGINS + PARTICULES
    // ============================================================
    const heroSection = document.querySelector('.hero');
    const heroEngins = document.querySelectorAll('.hero-engin');

    // --- Apparition progressive des 3 engins ---
    if (heroEngins.length > 0) {
        heroEngins.forEach((engin, i) => {
            setTimeout(() => {
                engin.classList.add('visible');
            }, 300 + i * 600); // 300ms, 900ms, 1500ms
        });
    }

    // --- Particules lumineuses (8 max, subtiles) ---
    const particlesContainer = document.getElementById('heroParticles');
    if (heroSection && particlesContainer) {
        const fragment = document.createDocumentFragment();
        for (let i = 0; i < 8; i++) {
            const particle = document.createElement('div');
            particle.classList.add('hero-particle');
            const size = Math.random() * 2 + 1; // 1px - 3px
            particle.style.width = size + 'px';
            particle.style.height = size + 'px';
            particle.style.left = Math.random() * 100 + '%';
            particle.style.bottom = -(Math.random() * 40 + 10) + '%';
            particle.style.animationDuration = (Math.random() * 12 + 12) + 's'; // 12-24s
            particle.style.animationDelay = (Math.random() * 15) + 's';
            fragment.appendChild(particle);
        }
        particlesContainer.appendChild(fragment);
    }

    // ============================================================
    // COUNTER ANIMATION
    // ============================================================
    const counters = document.querySelectorAll('.counter');
    let counted = false;

    function animateCounters() {
        if (counted) return;
        const section = document.querySelector('.chiffres');
        if (!section) return;
        const rect = section.getBoundingClientRect();
        if (rect.top < window.innerHeight - 100) {
            counted = true;
            counters.forEach(counter => {
                const target = +counter.getAttribute('data-target');
                const duration = 2000;
                const start = performance.now();

                function update(now) {
                    const elapsed = now - start;
                    const progress = Math.min(elapsed / duration, 1);
                    const value = Math.floor(progress * target);
                    counter.textContent = value;
                    if (progress < 1) {
                        requestAnimationFrame(update);
                    } else {
                        counter.textContent = target;
                    }
                }
                requestAnimationFrame(update);
            });
        }
    }

    window.addEventListener('scroll', animateCounters);
    animateCounters(); // trigger on load too

    // ============================================================
    // LIGHTBOX
    // ============================================================
    const lightboxModal = document.getElementById('lightboxModal');
    const lightboxImg = document.getElementById('lightboxImg');

    document.querySelectorAll('.galerie-item').forEach(item => {
        item.addEventListener('click', function (e) {
            e.preventDefault();
            const imgSrc = this.getAttribute('href');
            if (lightboxModal && lightboxImg) {
                lightboxImg.src = imgSrc;
                lightboxModal.classList.add('active');
                document.body.style.overflow = 'hidden';
            }
        });
    });

    if (lightboxModal) {
        lightboxModal.addEventListener('click', function (e) {
            if (e.target === lightboxModal || e.target.classList.contains('lightbox-close')) {
                lightboxModal.classList.remove('active');
                document.body.style.overflow = '';
            }
        });

        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && lightboxModal.classList.contains('active')) {
                lightboxModal.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    }

    // ============================================================
    // ACTIVE NAV LINK ON SCROLL
    // ============================================================
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.nav-link');

    function updateActiveLink() {
        let current = '';
        sections.forEach(section => {
            const sectionTop = section.offsetTop - 100;
            if (window.scrollY >= sectionTop) {
                current = section.getAttribute('id');
            }
        });
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === '#' + current || link.getAttribute('href').includes('#' + current)) {
                link.classList.add('active');
            }
        });
        // Home active if at top
        if (window.scrollY < 100) {
            navLinks.forEach(link => {
                link.classList.remove('active');
                if (link.getAttribute('href') === '/' || link.getAttribute('href') === '#accueil' || link.textContent.trim() === 'Accueil') {
                    link.classList.add('active');
                }
            });
        }
    }

    window.addEventListener('scroll', updateActiveLink);

    // ============================================================
    // CLOSE NAVBAR ON MOBILE CLICK
    // ============================================================
    const navCollapse = document.getElementById('navbarNav');
    if (navCollapse) {
        document.querySelectorAll('#navbarNav .nav-link, #navbarNav .btn').forEach(link => {
            link.addEventListener('click', () => {
                const bsCollapse = bootstrap.Collapse.getInstance(navCollapse);
                if (bsCollapse) bsCollapse.hide();
            });
        });
    }

    // ============================================================
    // FLASH MESSAGES AUTO-DISMISS
    // ============================================================
    const flashMessages = document.querySelector('.flash-messages');
    if (flashMessages) {
        setTimeout(() => {
            flashMessages.style.opacity = '0';
            flashMessages.style.transition = 'opacity 0.5s ease';
            setTimeout(() => flashMessages.remove(), 500);
        }, 5000);
    }

    // ============================================================
    // LOADER BOUTON PUBLIER COMMENTAIRE
    // ============================================================
    const btnPublier = document.getElementById('btnPublierCommentaire');
    if (btnPublier) {
        const form = btnPublier.closest('form');
        if (form) {
            form.addEventListener('submit', function () {
                const icon = btnPublier.querySelector('.btn-icon');
                const text = btnPublier.querySelector('.btn-text');
                const loader = btnPublier.querySelector('.btn-loader');
                if (icon) icon.style.display = 'none';
                if (text) text.style.display = 'none';
                if (loader) loader.style.display = 'inline-flex';
                btnPublier.disabled = true;
                btnPublier.style.opacity = '0.7';
            });
        }
    }

    // ============================================================
    // SMOOTH SCROLL FOR ALL ANCHOR LINKS
    // ============================================================
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            const target = document.querySelector(targetId);
            if (target) {
                e.preventDefault();
                const offset = 80;
                const position = target.getBoundingClientRect().top + window.pageYOffset - offset;
                window.scrollTo({ top: position, behavior: 'smooth' });
            }
        });
    });

});