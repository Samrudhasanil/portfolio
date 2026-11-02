/* ===================================================================
   SAMRUDHA SANIL — EDITORIAL PORTFOLIO JAVASCRIPT
   Interactivity, Canvas Particles, Lightbox, Theme, Motion
   =================================================================== */

document.addEventListener('DOMContentLoaded', () => {

  // --- 1. THEME TOGGLE (Light / Dark) ---
  const themeToggleBtn = document.getElementById('themeToggleBtn');
  const htmlElement = document.documentElement;
  const themeIcon = themeToggleBtn.querySelector('i');

  // Default to light to match user's vintage warm editorial palette
  const savedTheme = localStorage.getItem('samrudha_theme') || 'light';

  function applyTheme(theme) {
    htmlElement.setAttribute('data-theme', theme);
    localStorage.setItem('samrudha_theme', theme);
    if (themeIcon) {
      themeIcon.className = theme === 'light' ? 'ph ph-moon' : 'ph ph-sun';
    }
  }

  applyTheme(savedTheme);

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
      const currentTheme = htmlElement.getAttribute('data-theme') || 'light';
      const newTheme = currentTheme === 'light' ? 'dark' : 'light';
      applyTheme(newTheme);
    });
  }

  // --- 2. CUSTOM MAGNETIC CURSOR ---
  const cursorDot = document.querySelector('.custom-cursor-dot');
  const cursorRing = document.querySelector('.custom-cursor-ring');

  if (cursorDot && cursorRing && window.matchMedia('(pointer: fine)').matches) {
    let mouseX = window.innerWidth / 2;
    let mouseY = window.innerHeight / 2;
    let ringX = mouseX;
    let ringY = mouseY;

    window.addEventListener('mousemove', (e) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
      cursorDot.style.left = `${mouseX}px`;
      cursorDot.style.top = `${mouseY}px`;
    });

    function animateCursorRing() {
      ringX += (mouseX - ringX) * 0.18;
      ringY += (mouseY - ringY) * 0.18;
      cursorRing.style.left = `${ringX}px`;
      cursorRing.style.top = `${ringY}px`;
      requestAnimationFrame(animateCursorRing);
    }
    requestAnimationFrame(animateCursorRing);

    const interactiveElements = document.querySelectorAll('a, button, .poster-item-card, .illus-item-card, .skill-paper-card, .flagship-visual-frame, .filter-btn, .tag-btn, input, textarea, select');
    interactiveElements.forEach(el => {
      el.addEventListener('mouseenter', () => cursorRing.classList.add('active'));
      el.addEventListener('mouseleave', () => cursorRing.classList.remove('active'));
    });
  }

  // --- 3. SUBTLE AMBIENT CANVAS PARTICLES ---
  const canvas = document.getElementById('bg-canvas');
  if (canvas) {
    const ctx = canvas.getContext('2d');
    let width, height;
    let particles = [];
    const particleCount = 35;

    function resizeCanvas() {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    }
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    class Particle {
      constructor() {
        this.x = Math.random() * width;
        this.y = Math.random() * height;
        this.radius = Math.random() * 2 + 1;
        this.vx = (Math.random() - 0.5) * 0.35;
        this.vy = (Math.random() - 0.5) * 0.35;
        this.color = Math.random() > 0.5 ? 'rgba(200, 62, 32, 0.22)' : 'rgba(229, 160, 26, 0.22)';
      }
      update() {
        this.x += this.vx;
        this.y += this.vy;
        if (this.x < 0) this.x = width;
        if (this.x > width) this.x = 0;
        if (this.y < 0) this.y = height;
        if (this.y > height) this.y = 0;
      }
      draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fillStyle = this.color;
        ctx.fill();
      }
    }

    for (let i = 0; i < particleCount; i++) {
      particles.push(new Particle());
    }

    function renderCanvas() {
      ctx.clearRect(0, 0, width, height);

      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 120) {
            ctx.beginPath();
            ctx.strokeStyle = `rgba(200, 62, 32, ${0.1 * (1 - dist / 120)})`;
            ctx.lineWidth = 0.75;
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.stroke();
          }
        }
      }

      particles.forEach(p => {
        p.update();
        p.draw();
      });

      requestAnimationFrame(renderCanvas);
    }
    requestAnimationFrame(renderCanvas);
  }

  // --- 4. SCROLL SPY & ACTIVE NAVIGATION ---
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.nav-link');

  window.addEventListener('scroll', () => {
    let current = '';
    const scrollPosition = window.scrollY + 180;

    sections.forEach(section => {
      const sectionTop = section.offsetTop;
      const sectionHeight = section.offsetHeight;
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

  // --- 5. MOBILE DRAWER TOGGLE ---
  const mobileToggle = document.getElementById('mobileNavToggle');
  const mobileDrawer = document.getElementById('mobileNavDrawer');
  const mobileLinks = mobileDrawer ? mobileDrawer.querySelectorAll('.nav-link') : [];

  if (mobileToggle && mobileDrawer) {
    mobileToggle.addEventListener('click', () => {
      mobileDrawer.classList.toggle('open');
      const icon = mobileToggle.querySelector('i');
      if (icon) {
        icon.className = mobileDrawer.classList.contains('open') ? 'ph ph-x' : 'ph ph-list';
      }
    });

    mobileLinks.forEach(link => {
      link.addEventListener('click', () => {
        mobileDrawer.classList.remove('open');
        const icon = mobileToggle.querySelector('i');
        if (icon) icon.className = 'ph ph-list';
      });
    });
  }

  // --- 6. SCROLL REVEAL OBSERVER ---
  const observerOptions = {
    threshold: 0.1,
    rootMargin: "0px 0px -30px 0px"
  };

  const revealObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('active');
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  document.querySelectorAll('.reveal-up').forEach(el => {
    revealObserver.observe(el);
  });

  // --- 7. PRINCESS QUEST PYTHON TESTER ---
  const spellSelect = document.getElementById('spellSelect');
  const runSpellBtn = document.getElementById('runSpellBtn');
  const spellOutput = document.getElementById('spellOutput');
  const spellCodePreview = document.getElementById('spellCodePreview');

  const spellsDatabase = {
    'build_bridge': {
      code: "def build_bridge():\n    gather('wood', 5)\n    lay_planks(span=12)\n    print('Bridge secured! Princess crosses stream.')",
      result: "✨ Success: Wooden bridge spanned across the river! Princess advanced to Level 4 (+50 XP)"
    },
    'cast_lumos': {
      code: "def cast_lumos():\n    wand.glow(lumens=500)\n    reveal_hidden_path('Whispering Woods')\n    return 'Darkness dispersed!'",
      result: "🌟 Spell cast: The ancient forest lights up with emerald fireflies! Secret chest revealed!"
    },
    'tame_dragon': {
      code: "def tame_dragon(dragon_name):\n    while dragon_name.is_grumpy():\n        feed('sweet_berries')\n    play_lute()\n    return 'Dragon is now your ally!'",
      result: "🐉 Dragon befriended: Emerald Drake bows happily and grants access to the high castle!"
    }
  };

  if (spellSelect && runSpellBtn && spellOutput && spellCodePreview) {
    spellSelect.addEventListener('change', (e) => {
      const spell = spellsDatabase[e.target.value];
      if (spell) {
        spellCodePreview.textContent = spell.code;
        spellOutput.innerHTML = `Click 'Run Spell Function' to execute python code...`;
      }
    });

    runSpellBtn.addEventListener('click', () => {
      const selectedKey = spellSelect.value;
      const spell = spellsDatabase[selectedKey];
      spellOutput.innerHTML = `<span style="color: var(--accent-rust);"><i class="ph ph-spinner-gap" style="animation: spin 1s linear infinite;"></i> Executing Python spell...</span>`;
      
      setTimeout(() => {
        spellOutput.innerHTML = `<span style="color: var(--accent-olive);"><i class="ph ph-check-circle"></i> ${spell.result}</span>`;
      }, 500);
    });
  }

  // --- 8. PROJECT CATEGORY FILTERING ---
  const filterBtns = document.querySelectorAll('.filter-btn');
  const workItems = document.querySelectorAll('.work-filterable-item');

  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const filter = btn.getAttribute('data-filter');

      workItems.forEach(item => {
        const itemCategory = item.getAttribute('data-category');
        if (filter === 'all' || itemCategory === filter || (itemCategory && itemCategory.includes(filter))) {
          item.style.display = '';
          setTimeout(() => {
            item.style.opacity = '1';
          }, 30);
        } else {
          item.style.opacity = '0';
          setTimeout(() => {
            item.style.display = 'none';
          }, 250);
        }
      });
    });
  });

  // --- 9. FULL-SCREEN LIGHTBOX MODAL ---
  const lightboxModal = document.getElementById('lightboxModal');
  const lightboxImg = document.getElementById('lightboxImg');
  const lightboxTitle = document.getElementById('lightboxTitle');
  const lightboxCategory = document.getElementById('lightboxCategory');
  const lightboxDesc = document.getElementById('lightboxDesc');
  const lightboxMeta = document.getElementById('lightboxMeta');
  const lightboxCloseBtn = document.getElementById('lightboxCloseBtn');

  const galleryItems = document.querySelectorAll('[data-lightbox="true"]');
  galleryItems.forEach(item => {
    item.addEventListener('click', () => {
      const imgSrc = item.getAttribute('data-img');
      const title = item.getAttribute('data-title');
      const category = item.getAttribute('data-category-label');
      const desc = item.getAttribute('data-desc');
      const meta = item.getAttribute('data-meta');

      if (lightboxImg) lightboxImg.src = imgSrc;
      if (lightboxTitle) lightboxTitle.textContent = title;
      if (lightboxCategory) lightboxCategory.textContent = category;
      if (lightboxDesc) lightboxDesc.textContent = desc;
      if (lightboxMeta) lightboxMeta.textContent = meta;

      if (lightboxModal) {
        lightboxModal.classList.add('active');
        document.body.style.overflow = 'hidden';
      }
    });
  });

  function closeLightbox() {
    if (lightboxModal) {
      lightboxModal.classList.remove('active');
      document.body.style.overflow = '';
    }
  }

  if (lightboxCloseBtn) {
    lightboxCloseBtn.addEventListener('click', closeLightbox);
  }

  if (lightboxModal) {
    lightboxModal.addEventListener('click', (e) => {
      if (e.target === lightboxModal) closeLightbox();
    });

    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && lightboxModal.classList.contains('active')) {
        closeLightbox();
      }
    });
  }

  // --- 10. CONTACT FORM SUBMISSION ---
  const contactForm = document.getElementById('portfolioContactForm');
  const formSuccess = document.getElementById('formSuccessMsg');

  if (contactForm) {
    contactForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const submitBtn = contactForm.querySelector('.btn-send-message');
      const originalText = submitBtn.innerHTML;
      submitBtn.innerHTML = `Sending Message...`;
      submitBtn.disabled = true;

      setTimeout(() => {
        contactForm.reset();
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
        if (formSuccess) {
          formSuccess.style.display = 'block';
          setTimeout(() => {
            formSuccess.style.display = 'none';
          }, 4500);
        }
      }, 700);
    });
  }

  // --- 11. CLICK TO COPY HELPER ---
  const copyTriggers = document.querySelectorAll('.copy-trigger');
  copyTriggers.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const textToCopy = btn.getAttribute('data-copy');
      if (navigator.clipboard) {
        navigator.clipboard.writeText(textToCopy).then(() => {
          const originalHTML = btn.innerHTML;
          btn.innerHTML = `<span style="color: var(--accent-rust); font-weight: 700; padding: 12px;"><i class="ph ph-check-bold"></i> Copied to clipboard!</span>`;
          setTimeout(() => {
            btn.innerHTML = originalHTML;
          }, 2000);
        });
      }
    });
  });

});
