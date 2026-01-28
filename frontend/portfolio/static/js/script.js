// Professional API Consulting Portfolio - JavaScript
// Mobile-First Design with iPhone Optimizations
// Handles form submission, animations, mobile navigation, and dark mode

document.addEventListener('DOMContentLoaded', () => {
    initContactForm();
    initSmoothScroll();
    initNavigation();
    initMobileNavigation();
    initDarkModeToggle();
    initAnimations();
    initScrollFadeIn();
    initSkillBars();
    initTouchOptimizations();
    initRealityEffects(); // New: Scroll effects for Dual-Reality
});

// New function for Reality-specific scroll effects
function initRealityEffects() {
    window.addEventListener('scroll', () => {
        if (document.body.classList.contains('mobile-reality')) {
            const scrollPos = window.scrollY;
            const maxHeight = document.documentElement.scrollHeight - window.innerHeight;
            const ratio = maxHeight > 0 ? scrollPos / maxHeight : 0;

            // Intensify ocean shimmer as we scroll down
            // Starts at 0.2, reaches 1.0 at bottom
            const depth = 0.2 + (ratio * 0.8);
            document.body.style.setProperty('--ocean-depth', depth.toString());
        }
    }, { passive: true });
}

// Mobile Navigation Handler
function initMobileNavigation() {
    const navToggle = document.querySelector('.nav-toggle');
    const navLinks = document.querySelector('.nav-links');
    const navLinksItems = document.querySelectorAll('.nav-link');

    if (navToggle && navLinks) {
        // Toggle mobile menu
        navToggle.addEventListener('click', () => {
            const isActive = navToggle.classList.contains('active');

            if (isActive) {
                closeMobileMenu();
            } else {
                openMobileMenu();
            }
        });

        // Close menu when clicking nav links
        navLinksItems.forEach(link => {
            link.addEventListener('click', () => {
                closeMobileMenu();
            });
        });

        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!navToggle.contains(e.target) && !navLinks.contains(e.target)) {
                closeMobileMenu();
            }
        });

        // Handle escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeMobileMenu();
            }
        });
    }

    function openMobileMenu() {
        navToggle.classList.add('active');
        navLinks.classList.add('active');
        document.body.style.overflow = 'hidden'; // Prevent background scroll

        // Focus trap for accessibility
        const firstLink = navLinks.querySelector('.nav-link');
        if (firstLink) firstLink.focus();
    }

    function closeMobileMenu() {
        navToggle.classList.remove('active');
        navLinks.classList.remove('active');
        document.body.style.overflow = ''; // Restore scroll
    }
}

// Dark Mode Toggle Handler
function initDarkModeToggle() {
    const toggle = document.querySelector('.dark-mode-toggle');
    const body = document.body;

    if (!toggle) return;

    // Check for saved theme preference or default to system preference
    const savedTheme = localStorage.getItem('theme');
    const systemDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (savedTheme === 'dark' || (!savedTheme && systemDarkMode)) {
        enableDarkMode();
    } else {
        enableLightMode();
    }

    // Toggle event listener
    toggle.addEventListener('click', () => {
        if (body.classList.contains('dark-mode')) {
            enableLightMode();
            localStorage.setItem('theme', 'light');
        } else {
            enableDarkMode();
            localStorage.setItem('theme', 'dark');
        }
    });

    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem('theme')) {
            if (e.matches) {
                enableDarkMode();
            } else {
                enableLightMode();
            }
        }
    });

    function enableDarkMode() {
        body.classList.add('dark-mode');
        toggle.querySelector('.dark-mode-icon').textContent = '☀️';
        toggle.setAttribute('aria-label', 'Switch to light mode');
    }

    function enableLightMode() {
        body.classList.remove('dark-mode');
        toggle.querySelector('.dark-mode-icon').textContent = '🌙';
        toggle.setAttribute('aria-label', 'Switch to dark mode');
    }
}

// Touch Optimizations for iOS
function initTouchOptimizations() {
    // Prevent iOS bounce scroll
    document.addEventListener('touchstart', {}, { passive: true });
    document.addEventListener('touchmove', {}, { passive: true });

    // Add touch feedback to buttons
    const buttons = document.querySelectorAll('.btn-primary, .btn-secondary, .nav-link');
    buttons.forEach(button => {
        button.addEventListener('touchstart', function () {
            this.style.transform = 'scale(0.95)';
        }, { passive: true });

        button.addEventListener('touchend', function () {
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
        }, { passive: true });
    });

    // Optimize scroll performance on mobile
    let ticking = false;
    function updateOnScroll() {
        initScrollFadeIn();
        ticking = false;
    }

    window.addEventListener('scroll', () => {
        if (!ticking) {
            requestAnimationFrame(updateOnScroll);
            ticking = true;
        }
    }, { passive: true });
}

// Enhanced Scroll Animations - 60fps optimized
function initScrollFadeIn() {
    const elements = document.querySelectorAll('.fade-in, .slide-in-left, .slide-in-right');

    // Use Intersection Observer for better performance
    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });

        elements.forEach(el => observer.observe(el));
    } else {
        // Fallback for older browsers
        elements.forEach(el => {
            const rect = el.getBoundingClientRect();
            const isVisible = rect.top < window.innerHeight && rect.bottom > 0;
            if (isVisible) {
                el.classList.add('visible');
            }
        });
    }
}

// Contact Form Handler with Rate Limiting Protection
function initContactForm() {
    const form = document.getElementById('contactForm');
    const messageDiv = document.getElementById('formMessage');

    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const submitButton = form.querySelector('.btn-submit');
            const originalText = submitButton.textContent;

            // Disable submit button
            submitButton.disabled = true;
            submitButton.textContent = 'Sending...';

            // Collect form data
            const formData = {
                name: document.getElementById('name').value.trim(),
                email: document.getElementById('email').value.trim(),
                message: document.getElementById('message').value.trim()
            };

            try {
                // Send to FastAPI backend with security
                const response = await fetch('/api/contact', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify(formData)
                });

                const data = await response.json();

                if (response.ok) {
                    // Success message
                    showMessage(messageDiv, data.message, 'success');
                    form.reset();

                    // Track conversion (Cialdini: Commitment & Consistency)
                    if (typeof gtag !== 'undefined') {
                        gtag('event', 'contact_form_submission', {
                            'event_category': 'engagement',
                            'event_label': 'contact_form'
                        });
                    }
                } else {
                    // Error handling
                    showMessage(messageDiv, data.detail || 'Something went wrong. Please try again.', 'error');
                }
            } catch (error) {
                console.error('Form submission error:', error);
                showMessage(messageDiv, 'Network error. Please check your connection and try again.', 'error');
            } finally {
                // Re-enable submit button
                submitButton.disabled = false;
                submitButton.textContent = originalText;
            }
        });
    }
}

// Show form message with auto-hide
function showMessage(element, message, type) {
    element.textContent = message;
    element.className = `form-message ${type}`;
    element.style.display = 'block';

    // Auto-hide after 5 seconds
    setTimeout(() => {
        element.style.display = 'none';
    }, 5000);
}

// Smooth Scroll Navigation
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));

            if (target) {
                const navHeight = document.querySelector('.navbar').offsetHeight;
                const targetPosition = target.offsetTop - navHeight;

                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// Active Navigation Highlighting
function initNavigation() {
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.nav-link');

    window.addEventListener('scroll', () => {
        let current = '';
        const scrollPosition = window.pageYOffset;

        sections.forEach(section => {
            const sectionTop = section.offsetTop - 100;
            const sectionHeight = section.clientHeight;

            if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${current}`) {
                link.classList.add('active');
            }
        });
    });
}

// Scroll Animations
function initAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe cards and sections
    const elementsToAnimate = document.querySelectorAll(
        '.project-card, .testimonial-card, .resource-card, .tool-item, .cert-item'
    );

    elementsToAnimate.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
}

// Add animation class
const style = document.createElement('style');
style.textContent = `
    .animate-in {
        opacity: 1 !important;
        transform: translateY(0) !important;
    }
`;
document.head.appendChild(style);

// Skill Bars Animation (Mobile Optimized)
function initSkillBars() {
    const skillBars = document.querySelectorAll('.skill-bar');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const bar = entry.target;
                const percentage = bar.dataset.percentage;
                const fill = bar.querySelector('.skill-fill');

                if (fill) {
                    // Use transform instead of width for better performance
                    fill.style.transform = `scaleX(${percentage / 100})`;
                    fill.style.transformOrigin = 'left center';
                }

                observer.unobserve(bar);
            }
        });
    }, {
        threshold: 0.5
    });

    skillBars.forEach(bar => observer.observe(bar));
}

// Project Cards - Load projects dynamically (optional enhancement)
async function loadProjects() {
    try {
        const response = await fetch('/api/projects');
        const data = await response.json();

        if (data.projects) {
            // Projects are already rendered server-side
            console.log('Projects loaded:', data.projects.length);
        }
    } catch (error) {
        console.error('Error loading projects:', error);
    }
}

// Testimonials Carousel (optional enhancement)
function initTestimonialsCarousel() {
    const testimonials = document.querySelectorAll('.testimonial-card');
    let currentIndex = 0;

    if (testimonials.length > 3) {
        // Add carousel functionality for mobile
        // Implementation here if needed
    }
}

// Form Validation Enhancement
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Add real-time validation feedback
document.querySelectorAll('.form-group input, .form-group textarea').forEach(input => {
    input.addEventListener('blur', function () {
        if (this.hasAttribute('required') && !this.value.trim()) {
            this.style.borderColor = '#ef4444';
        } else if (this.type === 'email' && !validateEmail(this.value)) {
            this.style.borderColor = '#ef4444';
        } else {
            this.style.borderColor = '#d1d5db';
        }
    });

    input.addEventListener('focus', function () {
        this.style.borderColor = '#6366f1';
    });
});

// Security: Prevent XSS in form inputs
function sanitizeInput(input) {
    const div = document.createElement('div');
    div.textContent = input;
    return div.innerHTML;
}

// Performance: Lazy load images
function initLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');

    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                observer.unobserve(img);
            }
        });
    });

    images.forEach(img => imageObserver.observe(img));
}

// Cialdini Principle: Scarcity Timer (optional)
function updateAvailability() {
    const availabilityElement = document.querySelector('.availability-notice span:last-child');
    if (availabilityElement) {
        // Could update dynamically based on calendar availability
        // This is a static example
        const currentDate = new Date();
        const quarter = Math.floor(currentDate.getMonth() / 3) + 1;
        const year = currentDate.getFullYear();

        // Example: Show limited availability
        const messages = [
            `Currently accepting 2 new clients for Q${quarter} ${year}`,
            `1 spot remaining for Q${quarter} ${year}`,
            `Fully booked - accepting Q${quarter + 1} ${year} projects`
        ];

        // Randomly show scarcity (in production, use real data)
        // availabilityElement.textContent = messages[Math.floor(Math.random() * messages.length)];
    }
}

// Call initialization functions
// updateAvailability();
initLazyLoading();

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        sanitizeInput,
        validateEmail
    };
}

// Scroll Fade-In Animations for Sections
function initScrollFadeIn() {
    const fadeElements = document.querySelectorAll('.fade-in-section');

    const fadeObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, {
        threshold: 0.15,
        rootMargin: '0px 0px -100px 0px'
    });

    fadeElements.forEach(el => fadeObserver.observe(el));
}

// Animated Skill Bars
function initSkillBars() {
    const skillBars = document.querySelectorAll('.skill-fill');

    const skillObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const bar = entry.target;
                const width = bar.style.width;
                bar.style.width = '0';

                setTimeout(() => {
                    bar.style.width = width;
                }, 100);

                skillObserver.unobserve(bar);
            }
        });
    }, {
        threshold: 0.5
    });

    skillBars.forEach(bar => skillObserver.observe(bar));
}

// Voice Message CTA - Track Clicks
document.addEventListener('DOMContentLoaded', () => {
    const voiceCTA = document.querySelector('.voice-cta');
    if (voiceCTA) {
        voiceCTA.addEventListener('click', () => {
            // Track engagement
            if (typeof gtag !== 'undefined') {
                gtag('event', 'voice_message_click', {
                    'event_category': 'engagement',
                    'event_label': 'twilio_cta'
                });
            }
            console.log('Voice message CTA clicked - Twilio integration ready!');
        });
    }
});

// Building Badge Hover Effect
document.addEventListener('DOMContentLoaded', () => {
    const buildingBadge = document.querySelector('.building-badge');
    if (buildingBadge) {
        buildingBadge.addEventListener('mouseenter', () => {
            buildingBadge.style.transform = 'translateY(-3px)';
        });
        buildingBadge.addEventListener('mouseleave', () => {
            buildingBadge.style.transform = 'translateY(0)';
        });
    }
});

