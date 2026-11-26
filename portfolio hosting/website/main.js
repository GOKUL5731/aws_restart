/* ================================================================
   NEXORA — Interactive Developer Workspace
   M. Gokul Portfolio · Complete Interaction System
   ================================================================ */

'use strict';

// ── UTILITY ──────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const $$ = s => document.querySelectorAll(s);
const isMobile = () => window.matchMedia('(max-width:900px)').matches;
const isTouch  = () => window.matchMedia('(pointer:coarse)').matches;
const prefersReducedMotion = () => window.matchMedia('(prefers-reduced-motion:reduce)').matches;

// ── HERO NEURAL CANVAS ────────────────────────────────────────────
function initHeroCanvas() {
  if (prefersReducedMotion() || isTouch()) return;
  const canvas = $('hero-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let w, h, nodes = [];
  let mouse = { x: -9999, y: -9999 };

  function resize() {
    w = canvas.width  = canvas.offsetWidth;
    h = canvas.height = canvas.offsetHeight;
  }

  function createNodes() {
    nodes = [];
    const count = Math.floor((w * h) / 14000);
    for (let i = 0; i < count; i++) {
      nodes.push({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - .5) * .25,
        vy: (Math.random() - .5) * .25,
        r: Math.random() * 1.5 + .5
      });
    }
  }

  function draw() {
    ctx.clearRect(0, 0, w, h);
    // Update
    for (const n of nodes) {
      n.x += n.vx;
      n.y += n.vy;
      if (n.x < 0 || n.x > w) n.vx *= -1;
      if (n.y < 0 || n.y > h) n.vy *= -1;
      // Mouse repulsion
      const dx = n.x - mouse.x;
      const dy = n.y - mouse.y;
      const d  = Math.sqrt(dx*dx + dy*dy);
      if (d < 90) {
        n.x += (dx/d) * 1.2;
        n.y += (dy/d) * 1.2;
      }
    }
    // Draw connections
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[i].x - nodes[j].x;
        const dy = nodes[i].y - nodes[j].y;
        const dist = Math.sqrt(dx*dx + dy*dy);
        if (dist < 130) {
          const alpha = (1 - dist/130) * .12;
          ctx.beginPath();
          ctx.moveTo(nodes[i].x, nodes[i].y);
          ctx.lineTo(nodes[j].x, nodes[j].y);
          ctx.strokeStyle = `rgba(200,200,200,${alpha})`;
          ctx.lineWidth = .5;
          ctx.stroke();
        }
      }
    }
    // Draw nodes
    for (const n of nodes) {
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.r, 0, Math.PI*2);
      ctx.fillStyle = 'rgba(220,220,220,.35)';
      ctx.fill();
    }
    requestAnimationFrame(draw);
  }

  window.addEventListener('mousemove', e => {
    const rect = canvas.getBoundingClientRect();
    mouse.x = e.clientX - rect.left;
    mouse.y = e.clientY - rect.top;
  });
  window.addEventListener('mouseleave', () => { mouse.x = -9999; mouse.y = -9999; });
  window.addEventListener('resize', () => { resize(); createNodes(); });
  resize();
  createNodes();
  draw();
}

// Lightweight 3D neural core using spherical projection and animated signal nodes.
function initIntelligenceCore() {
  const canvas = $('core-canvas');
  if (!canvas || prefersReducedMotion()) return;
  const ctx = canvas.getContext('2d');
  let t = 0, pointer = { x: 0, y: 0 };
  const count = isMobile() ? 56 : 110;
  const nodes = Array.from({ length: count }, (_, i) => ({
    lat: Math.acos(1 - 2 * ((i + .5) / count)) - Math.PI / 2,
    lon: i * Math.PI * (1 + Math.sqrt(5)),
    radius: .34 + Math.random() * .66,
    phase: Math.random() * Math.PI * 2
  }));
  function resize() { canvas.width = canvas.offsetWidth * devicePixelRatio; canvas.height = canvas.offsetHeight * devicePixelRatio; }
  function draw() {
    const w = canvas.offsetWidth, h = canvas.offsetHeight;
    ctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0); ctx.clearRect(0, 0, w, h); t += .004;
    const points = nodes.map(n => { const lon = n.lon + t + pointer.x * .35; const lat = n.lat + pointer.y * .16; return { x: w/2 + Math.cos(lat)*Math.cos(lon)*n.radius*w*.43, y: h/2 + Math.sin(lat)*n.radius*h*.43, z: Math.sin(lat)*Math.sin(lon)*n.radius, n }; }).sort((a,b) => a.z-b.z);
    for (let i=0;i<points.length;i++) for (let j=i+1;j<points.length;j++) { const a=points[i],b=points[j],dx=a.x-b.x,dy=a.y-b.y; if (dx*dx+dy*dy<900 && Math.min(a.z,b.z)>-.35) { ctx.strokeStyle=`rgba(34,211,238,${.04+Math.max(a.z,b.z)*.08})`; ctx.lineWidth=.6; ctx.beginPath(); ctx.moveTo(a.x,a.y); ctx.lineTo(b.x,b.y); ctx.stroke(); } }
    points.forEach((p,i) => { const size=1+(p.z+1)*1.3; ctx.fillStyle=`rgba(125,231,247,${.18+(p.z+1)*.25})`; ctx.beginPath(); ctx.arc(p.x,p.y,size,0,Math.PI*2); ctx.fill(); if (i%17===Math.floor(t*20)%17) { ctx.fillStyle='#fff'; ctx.beginPath(); ctx.arc(p.x,p.y,size+1.5,0,Math.PI*2); ctx.fill(); } });
    requestAnimationFrame(draw);
  }
  canvas.addEventListener('pointermove', e => { const r=canvas.getBoundingClientRect(); pointer.x=(e.clientX-r.left)/r.width-.5; pointer.y=(e.clientY-r.top)/r.height-.5; });
  canvas.addEventListener('pointerleave', () => { pointer.x=0; pointer.y=0; }); addEventListener('resize', resize, { passive:true }); resize(); draw();
}

// ── CUSTOM CURSOR ─────────────────────────────────────────────────
function initCursor() {
  if (isTouch() || prefersReducedMotion()) return;
  const dot   = $('cursor-dot');
  const ring  = $('cursor-ring');
  const label = $('cursor-label');
  if (!dot || !ring) return;

  let mx = 0, my = 0;
  let rx = 0, ry = 0;
  let vx = 0, vy = 0;
  let angle = 0;

  function moveDot(e) {
    mx = e.clientX;
    my = e.clientY;
    dot.style.left = mx + 'px';
    dot.style.top  = my + 'px';
  }

  function animateRing() {
    const prevRx = rx;
    const prevRy = ry;

    rx += (mx - rx) * .15;
    ry += (my - ry) * .15;

    vx = rx - prevRx;
    vy = ry - prevRy;
    const speed = Math.sqrt(vx * vx + vy * vy);

    if (speed > 0.1) {
      angle = Math.atan2(vy, vx) * (180 / Math.PI);
    }

    const scaleX = Math.min(1 + speed * 0.015, 1.35);
    const scaleY = Math.max(1 - speed * 0.012, 0.75);

    ring.style.left = rx + 'px';
    ring.style.top  = ry + 'px';

    if (!ring.classList.contains('cursor-hover') && !ring.classList.contains('cursor-btn')) {
      ring.style.transform = `translate(-50%, -50%) rotate(${angle}deg) scale(${scaleX}, ${scaleY})`;
    } else {
      ring.style.transform = `translate(-50%, -50%) scale(1, 1)`;
    }

    label.style.left = mx + 'px';
    label.style.top  = (my - 38) + 'px';

    requestAnimationFrame(animateRing);
  }

  document.addEventListener('mousemove', moveDot);
  animateRing();

  document.addEventListener('mouseenter', e => {
    const el = e.target;
    if (!el) return;
    const cur = el.closest('[data-cursor]');
    if (cur) {
      label.textContent = cur.dataset.cursor;
      label.classList.add('visible');
      ring.classList.add('cursor-btn');
    } else if (el.closest('button, a, .pf-btn, .id-tab, .stag, .pc-detail-btn, .fp-case-btn, .cc-item')) {
      ring.classList.add('cursor-hover');
    }
  }, true);

  document.addEventListener('mouseleave', e => {
    const el = e.target;
    if (!el) return;
    const cur = el.closest('[data-cursor]');
    if (cur) {
      label.classList.remove('visible');
      ring.classList.remove('cursor-btn');
    } else if (el.closest('button, a, .pf-btn, .id-tab, .stag, .pc-detail-btn, .fp-case-btn, .cc-item')) {
      ring.classList.remove('cursor-hover');
    }
  }, true);
}

// ── SCROLL PROGRESS ───────────────────────────────────────────────
function initScrollProgress() {
  const bar = $('scroll-progress-bar');
  if (!bar) return;
  function update() {
    const scrolled = window.scrollY;
    const max = document.documentElement.scrollHeight - window.innerHeight;
    bar.style.width = (max > 0 ? (scrolled/max)*100 : 0) + '%';
  }
  window.addEventListener('scroll', update, { passive: true });
  update();
}

// ── TOP NAV ───────────────────────────────────────────────────────
function initTopNav() {
  const nav = $('topnav');
  const hamburger = $('hamburger');
  const mobileMenu = $('mobileMenu');
  if (!nav) return;

  window.addEventListener('scroll', () => {
    nav.classList.toggle('scrolled', window.scrollY > 40);
  }, { passive: true });

  if (hamburger && mobileMenu) {
    hamburger.addEventListener('click', () => {
      const open = hamburger.classList.toggle('open');
      hamburger.setAttribute('aria-expanded', open);
      mobileMenu.hidden = !open;
    });
    // Close on link click
    mobileMenu.querySelectorAll('a').forEach(a => {
      a.addEventListener('click', () => {
        hamburger.classList.remove('open');
        hamburger.setAttribute('aria-expanded', false);
        mobileMenu.hidden = true;
      });
    });
  }
}

// ── SECTION NAV DOTS & ACTIVE NAV LINKS ──────────────────────────
function initSectionObserver() {
  const sections = $$('section[id]');
  const dots = $$('.snav-dot');
  const navLinks = $$('.tnl');

  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.id;
        dots.forEach(d => d.classList.toggle('active', d.dataset.section === id));
        navLinks.forEach(l => {
          const href = l.getAttribute('href').replace('#','');
          l.classList.toggle('active', href === id);
        });
      }
    });
  }, { rootMargin: '-40% 0px -40% 0px', threshold: 0 });

  sections.forEach(s => observer.observe(s));
}

// ── REVEAL ON SCROLL ──────────────────────────────────────────────
function initReveal() {
  const items = $$('.reveal');
  if (!items.length) return;

  const observer = new IntersectionObserver(entries => {
    entries.forEach((entry, i) => {
      if (entry.isIntersecting) {
        // Staggered delay for siblings
        const parent = entry.target.parentElement;
        const siblings = parent ? [...parent.querySelectorAll('.reveal')] : [];
        const idx = siblings.indexOf(entry.target);
        entry.target.style.transitionDelay = (idx * 0.07) + 's';
        entry.target.classList.add('in-view');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.07, rootMargin: '0px 0px -40px 0px' });

  items.forEach(el => observer.observe(el));
}

// ── HERO ROLE CYCLER ─────────────────────────────────────────────
function initRoleCycler() {
  const lines = $$('.role-line');
  if (!lines.length || prefersReducedMotion()) return;
  let current = 0;
  setInterval(() => {
    lines[current].classList.remove('active');
    current = (current + 1) % lines.length;
    lines[current].classList.add('active');
  }, 2200);
}

// ── MAGNETIC BUTTONS ─────────────────────────────────────────────
function initMagnetic() {
  if (isTouch() || prefersReducedMotion()) return;
  $$('.magnetic').forEach(el => {
    el.addEventListener('mousemove', e => {
      const rect = el.getBoundingClientRect();
      const cx = rect.left + rect.width/2;
      const cy = rect.top  + rect.height/2;
      const dx = (e.clientX - cx) * .22;
      const dy = (e.clientY - cy) * .22;
      el.style.transform = `translate(${dx}px,${dy}px)`;
    });
    el.addEventListener('mouseleave', () => {
      el.style.transform = '';
    });
  });
}

// ── GITHUB STATS (count-up) ───────────────────────────────────────
function initGitHubStats() {
  const el = $('repoCount');
  if (!el) return;
  const cached = sessionStorage.getItem('gh_repos');
  if (cached) { countUp(el, parseInt(cached)); return; }
  fetch('https://api.github.com/users/GOKUL5731')
    .then(r => r.json())
    .then(data => {
      if (data.public_repos) {
        sessionStorage.setItem('gh_repos', data.public_repos);
        countUp(el, data.public_repos);
      }
    })
    .catch(() => {}); // fail silently, static fallback stays
}

function countUp(el, target) {
  if (prefersReducedMotion()) { el.textContent = target; return; }
  let n = 0;
  const step = Math.ceil(target / 40);
  const t = setInterval(() => {
    n = Math.min(n + step, target);
    el.textContent = n;
    if (n >= target) clearInterval(t);
  }, 40);
}

// ── ABOUT IDENTITY TABS ───────────────────────────────────────────
function initAboutTabs() {
  const tabs = $$('.id-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const target = tab.dataset.tab;
      tabs.forEach(t => t.classList.toggle('active', t === tab));
      $$('.id-panel').forEach(p => {
        p.classList.remove('active');
        p.hidden = true;
      });
      const panel = $('tab-' + target);
      if (panel) { panel.hidden = false; panel.classList.add('active'); }
    });
  });
}

// ── PROJECT FILTER ────────────────────────────────────────────────
function initProjectFilter() {
  const btns  = $$('.pf-btn');
  const cards = $$('.proj-card');
  const featured = document.querySelector('.featured-proj');

  btns.forEach(btn => {
    btn.addEventListener('click', () => {
      btns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const filter = btn.dataset.pf;

      // Featured project
      if (featured) {
        const fpCats = (featured.dataset.pcat || '').split(' ');
        const show = filter === 'all' || fpCats.includes(filter);
        featured.style.display = show ? '' : 'none';
      }

      cards.forEach(card => {
        const cats = (card.dataset.pcat || '').split(' ');
        const match = filter === 'all' || cats.some(c => c.includes(filter));
        card.classList.toggle('hidden', !match);
        if (!card.classList.contains('hidden')) {
          card.style.animationDelay = '';
          card.classList.remove('in-view');
          void card.offsetWidth; // reflow
          card.classList.add('in-view');
        }
      });
    });
  });
}

// ── SKILL TAG FILTER (links to project filter) ────────────────────
function initSkillFilter() {
  const stags = $$('.stag');
  const pfBtns = $$('.pf-btn');
  const projSection = $('projects');

  const catMap = {
    ai: 'ai', vision: 'vision', nlp: 'ai',
    lang: 'all', web: 'fullstack', data: 'fullstack',
    tools: 'all', iot: 'systems'
  };

  stags.forEach(tag => {
    tag.addEventListener('click', () => {
      const cat = tag.dataset.filter;
      const pfTarget = catMap[cat] || 'all';

      // Activate matching filter button
      pfBtns.forEach(b => {
        b.classList.toggle('active', b.dataset.pf === pfTarget);
      });
      // Trigger click
      const targetBtn = [...pfBtns].find(b => b.dataset.pf === pfTarget);
      if (targetBtn) targetBtn.click();

      // Scroll to projects
      if (projSection) {
        projSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
}

// ── LIVE GITHUB PROJECTS ─────────────────────────────────────────
function initGithubProjects() {
  const section = $('projects');
  const featured = section?.querySelector('.featured-proj');
  const grid = $('projGrid');
  const more = section?.querySelector('.proj-more');
  if (!section || !grid) return;

  const username = 'GOKUL5731';
  const shell = document.createElement('div');
  shell.className = 'github-projects-shell';
  shell.innerHTML = '<div class="github-projects-state" aria-live="polite">Loading current projects from GitHub…</div>';
  if (featured) featured.before(shell); else grid.before(shell);

  const escapeHtml = value => String(value || '').replace(/[&<>"']/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
  }[char]));

  const categoryFor = repo => {
    const text = `${repo.name} ${repo.description || ''} ${repo.language || ''}`.toLowerCase();
    if (/vision|opencv|face|image|yolo/.test(text)) return 'vision';
    if (/ai|ml|machine|tensorflow|nlp|model|neural/.test(text)) return 'ai';
    if (/flutter|android|mobile|dart/.test(text)) return 'mobile';
    if (/c\b|os|system|compiler|kernel|embedded/.test(text)) return 'systems';
    return 'fullstack';
  };

  const repoCard = (repo, index) => {
    const category = categoryFor(repo);
    const language = repo.language || 'Open source';
    const topics = Array.isArray(repo.topics) ? repo.topics.slice(0, 3) : [];
    const tags = [language, ...topics].filter(Boolean).slice(0, 4);
    const description = repo.description || 'A public software project built and maintained by Gokul.';
    return `<article class="proj-card github-proj-card reveal in-view" data-pcat="${category}">
      <div class="pc-top"><div class="pc-badges"><span class="pc-badge pc-badge-${category}">${category === 'ai' ? 'AI / ML' : category[0].toUpperCase() + category.slice(1)}</span></div>
        <a href="${escapeHtml(repo.html_url)}" target="_blank" rel="noopener noreferrer" class="pc-gh-link" aria-label="Open ${escapeHtml(repo.name)} on GitHub" data-cursor="OPEN GITHUB">↗</a>
      </div>
      <div class="github-card-index">${String(index + 1).padStart(2, '0')} / REPOSITORY</div>
      <h3 class="pc-title">${escapeHtml(repo.name)}</h3>
      <p class="pc-desc">${escapeHtml(description)}</p>
      <div class="pc-stack">${tags.map(tag => `<span>${escapeHtml(tag)}</span>`).join('')}</div>
      <div class="pc-footer"><a class="pc-detail-btn" href="${escapeHtml(repo.html_url)}" target="_blank" rel="noopener noreferrer">View repository →</a><span class="github-stars">★ ${repo.stargazers_count || 0}</span></div>
    </article>`;
  };

  fetch(`https://api.github.com/users/${username}/repos?sort=updated&direction=desc&per_page=100`, {
    headers: { Accept: 'application/vnd.github+json' }
  })
    .then(response => { if (!response.ok) throw new Error('GitHub request failed'); return response.json(); })
    .then(repos => {
      const projects = repos.filter(repo => !repo.fork && !repo.archived && repo.name !== '.github');
      if (!projects.length) throw new Error('No public projects found');
      shell.innerHTML = `<div class="github-projects-heading"><div><span class="eyebrow">LIVE FROM GITHUB</span><h3>Built, shipped, and maintained</h3></div><span class="github-project-count">${projects.length} public projects</span></div><div class="proj-grid github-proj-grid">${projects.map(repoCard).join('')}</div>`;
      if (featured) featured.hidden = true;
      grid.hidden = true;
      if (more) more.hidden = true;
      shell.querySelectorAll('.github-proj-card').forEach(card => {
        card.addEventListener('mouseenter', () => card.classList.add('in-view'));
      });
      $$('.pf-btn').forEach(button => button.addEventListener('click', () => {
        const filter = button.dataset.pf;
        shell.querySelectorAll('.github-proj-card').forEach(card => {
          card.hidden = filter !== 'all' && !(card.dataset.pcat || '').split(' ').includes(filter);
        });
      }));
    })
    .catch(() => {
      shell.innerHTML = '<div class="github-projects-state github-projects-error"><strong>Projects are temporarily unavailable.</strong><a href="https://github.com/GOKUL5731?tab=repositories" target="_blank" rel="noopener noreferrer">Browse the live GitHub profile →</a></div>';
    });
}

// ── PROJECT MODAL DATA ────────────────────────────────────────────
const PROJECT_DATA = {
  'analyticsql': {
    num: '01',
    title: 'AnalyticsQL — Intelligent Analytics IDE',
    problem: 'Building a complete analytics environment that combines compiler theory, machine learning, and desktop GUI development — all in one system.',
    idea: 'Design a custom query language with a real C compiler pipeline (Lexer → Parser → AST → Semantic Analyzer → SQL Generator → Optimizer), backed by a Python ML engine and voice interface — making data analysis accessible through natural language and voice.',
    tech: ['Python', 'C', 'PyQt6', 'SQLite', 'TensorFlow', 'NLP', 'Vosk', 'Machine Learning'],
    highlights: [
      'Pure C compiler: Lexer, Parser, AST, Semantic Analyzer, SQL Codegen pipeline',
      'ML engine: time-series forecasting & anomaly detection',
      'Voice input via Vosk (offline speech recognition)',
      'Natural language query via AI assistant panel',
      'KPI dashboard, AST viewer, charts, PDF/Excel export'
    ],
    github: 'https://github.com/GOKUL5731/Analyticsql'
  },
  'face-recognition': {
    num: '02',
    title: 'AI Face Recognition Attendance',
    problem: 'Manual attendance tracking is error-prone, time-consuming, and easy to manipulate.',
    idea: 'Automate attendance by recognizing registered faces in real-time using a camera, storing records to CSV, and providing an admin dashboard for monitoring.',
    tech: ['Python', 'OpenCV', 'Computer Vision', 'Face Recognition', 'CSV'],
    highlights: [
      'Real-time face detection and recognition',
      'CSV-based attendance records with timestamps',
      'Admin dashboard for filtering and report generation',
      'Automated workflow replacing manual registers'
    ],
    github: 'https://github.com/GOKUL5731'
  },
  'ai-assistant': {
    num: '03',
    title: 'AI Virtual Assistant',
    problem: 'Building a desktop assistant that can process natural language commands and execute system actions using voice.',
    idea: 'A voice-controlled Python assistant with speech recognition, text-to-speech responses, and automation modules for system commands and web queries.',
    tech: ['Python', 'Speech Recognition', 'NLP', 'Text-to-Speech', 'Automation'],
    highlights: [
      'Voice input with offline-capable speech recognition',
      'Natural language command parsing',
      'Text-to-speech response system',
      'System automation: file management, web search, app control'
    ],
    github: 'https://github.com/GOKUL5731'
  },
  'nexora-os': {
    num: '04',
    title: 'Nexora OS',
    problem: 'Exploring systems programming and low-level OS concepts through practical implementation.',
    idea: 'A Python-based OS-level project implementing core OS components to demonstrate deep understanding of system programming fundamentals.',
    tech: ['Python', 'Systems Programming', 'OS Concepts'],
    highlights: [
      'Core OS component implementation',
      'System programming fundamentals',
      'Low-level software architecture exploration'
    ],
    github: 'https://github.com/GOKUL5731/nexora-os'
  },
  'college-mgmt': {
    num: '05',
    title: 'College Management System',
    problem: 'Colleges need a unified digital platform to manage attendance, marks, courses, and multi-role user access.',
    idea: 'A full-stack role-based web platform with separate views for admin, faculty, and students, handling attendance, marks, and course management — built as an internship capstone at CodeBind Technologies.',
    tech: ['PHP', 'MySQL', 'JavaScript', 'Bootstrap', 'HTML5', 'CSS3'],
    highlights: [
      'Role-based access control (Admin / Faculty / Student)',
      'Attendance management with reporting',
      'Marks and grade management',
      'Course and department management',
      'MySQL backend with PHP business logic'
    ],
    github: 'https://github.com/GOKUL5731'
  },
  'click2fix': {
    num: '06',
    title: 'Click2Fix',
    problem: 'Building a cross-platform mobile application that works seamlessly on both iOS and Android from a single codebase.',
    idea: 'A Flutter/Dart mobile application demonstrating cross-platform UI development skills and modern mobile software architecture.',
    tech: ['Dart', 'Flutter', 'Cross-Platform', 'Mobile'],
    highlights: [
      'Cross-platform iOS/Android compatibility',
      'Flutter-based responsive UI',
      'Dart-driven application logic',
      'Mobile architecture patterns'
    ],
    github: 'https://github.com/GOKUL5731/Click2Fix'
  },
  'ml-playground': {
    num: '07',
    title: 'ML Playground',
    problem: 'A structured space to experiment with diverse machine learning algorithms, architectures, and workflows.',
    idea: 'A curated collection of ML experiments and Jupyter notebooks covering classification, regression, deep learning, computer vision, and data analysis.',
    tech: ['Python', 'TensorFlow', 'Jupyter', 'NumPy', 'Pandas', 'Scikit-learn'],
    highlights: [
      'Diverse algorithm implementations',
      'Deep learning model experiments',
      'Data analysis workflows',
      'TensorFlow-based model training',
      'Reproducible Jupyter notebooks'
    ],
    github: 'https://github.com/GOKUL5731/ML-Playground'
  }
};

function openModal(key) {
  const data = PROJECT_DATA[key];
  if (!data) return;
  const modal = $('proj-modal');
  const content = $('proj-modal-content');
  if (!modal || !content) return;

  content.innerHTML = `
    <div class="modal-proj-num">${data.num} / PROJECT</div>
    <h2 class="modal-proj-title">${data.title}</h2>
    <div class="modal-proj-section">
      <h4>The Problem</h4>
      <p>${data.problem}</p>
    </div>
    <div class="modal-proj-section">
      <h4>The Idea</h4>
      <p>${data.idea}</p>
    </div>
    ${data.highlights ? `
    <div class="modal-proj-section">
      <h4>Key Features</h4>
      <ul>${data.highlights.map(h => `<li>${h}</li>`).join('')}</ul>
    </div>` : ''}
    <div class="modal-proj-section">
      <h4>Technology</h4>
      <div class="modal-stack">${data.tech.map(t => `<span class="modal-tech">${t}</span>`).join('')}</div>
    </div>
    ${data.github ? `
    <div class="modal-actions">
      <a href="${data.github}" target="_blank" rel="noopener noreferrer" class="modal-gh-btn">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/></svg>
        View on GitHub
      </a>
    </div>` : ''}
  `;

  modal.hidden = false;
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  const modal = $('proj-modal');
  if (modal) { modal.hidden = true; }
  document.body.style.overflow = '';
}

function initProjectModals() {
  // Open on card button
  $$('[data-modal]').forEach(el => {
    el.addEventListener('click', (e) => {
      e.preventDefault();
      openModal(el.dataset.modal);
    });
  });

  // Close button
  const closeBtn = $('proj-modal-close');
  if (closeBtn) closeBtn.addEventListener('click', closeModal);

  // Close on overlay click
  const modal = $('proj-modal');
  if (modal) {
    modal.addEventListener('click', e => {
      if (e.target === modal) closeModal();
    });
  }

  // Escape key
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      if ($('proj-modal') && !$('proj-modal').hidden) closeModal();
      if ($('cmd-overlay') && !$('cmd-overlay').hidden) closeCommand();
    }
  });
}

// ── COMMAND PALETTE ───────────────────────────────────────────────
const CMD_ITEMS = [
  { icon: '🏠', name: 'Home', hint: 'Hero', action: () => { document.querySelector('#home').scrollIntoView({behavior:'smooth'}); } },
  { icon: '👤', name: 'Profile', hint: 'About me', action: () => { document.querySelector('#about').scrollIntoView({behavior:'smooth'}); } },
  { icon: '⚙️', name: 'Stack', hint: 'Technical skills', action: () => { document.querySelector('#skills').scrollIntoView({behavior:'smooth'}); } },
  { icon: '🚀', name: 'Work', hint: 'Projects', action: () => { document.querySelector('#projects').scrollIntoView({behavior:'smooth'}); } },
  { icon: '📅', name: 'Journey', hint: 'Experience & certs', action: () => { document.querySelector('#experience').scrollIntoView({behavior:'smooth'}); } },
  { icon: '📩', name: 'Connect', hint: 'Contact info', action: () => { document.querySelector('#contact').scrollIntoView({behavior:'smooth'}); } },
  { icon: '⬇️', name: 'Download Resume', hint: 'PDF', action: () => { const a = document.createElement('a'); a.href='assets/resume.pdf'; a.download=''; a.click(); } },
  { icon: '💻', name: 'GitHub Profile', hint: 'GOKUL5731', action: () => { window.open('https://github.com/GOKUL5731','_blank'); } },
  { icon: '🔗', name: 'LinkedIn', hint: 'gokul-m-cse', action: () => { window.open('https://linkedin.com/in/gokul-m-cse','_blank'); } },
  { icon: '✉️', name: 'Email', hint: 'gokulgokul5731@gmail.com', action: () => { window.location.href='mailto:gokulgokul5731@gmail.com'; } },
  // Projects
  { icon: '📊', name: 'AnalyticsQL', hint: 'Featured project', action: () => { openModal('analyticsql'); } },
  { icon: '👁️', name: 'Face Recognition', hint: 'Computer Vision', action: () => { openModal('face-recognition'); } },
  { icon: '🤖', name: 'AI Assistant', hint: 'NLP project', action: () => { openModal('ai-assistant'); } },
  { icon: '🌐', name: 'College Management', hint: 'Full Stack', action: () => { openModal('college-mgmt'); } },
  { icon: '📱', name: 'Click2Fix', hint: 'Mobile app', action: () => { openModal('click2fix'); } },
  { icon: '🧪', name: 'ML Playground', hint: 'AI experiments', action: () => { openModal('ml-playground'); } },
];

let cmdOpen = false;
let cmdSelected = -1;

function openCommand() {
  const overlay = $('cmd-overlay');
  if (!overlay) return;
  overlay.hidden = false;
  cmdOpen = true;
  const input = $('cmd-input');
  if (input) { input.value = ''; input.focus(); }
  renderCmdResults('');
  document.body.style.overflow = 'hidden';
}

function closeCommand() {
  const overlay = $('cmd-overlay');
  if (overlay) overlay.hidden = true;
  cmdOpen = false;
  cmdSelected = -1;
  document.body.style.overflow = '';
}

function renderCmdResults(query) {
  const list = $('cmd-results');
  if (!list) return;
  const q = query.toLowerCase().trim();
  const filtered = q ? CMD_ITEMS.filter(i =>
    i.name.toLowerCase().includes(q) || i.hint.toLowerCase().includes(q)
  ) : CMD_ITEMS;
  list.innerHTML = filtered.map((item, i) => `
    <li class="cmd-result-item${i === cmdSelected ? ' selected' : ''}" data-index="${i}" role="option">
      <span class="cmd-icon">${item.icon}</span>
      <span class="cmd-name">${item.name}</span>
      <span class="cmd-hint">${item.hint}</span>
    </li>
  `).join('');

  list.querySelectorAll('.cmd-result-item').forEach((li, i) => {
    li.addEventListener('click', () => {
      filtered[i].action();
      closeCommand();
    });
    li.addEventListener('mouseenter', () => {
      cmdSelected = i;
      list.querySelectorAll('.cmd-result-item').forEach((l,j) => l.classList.toggle('selected', j===i));
    });
  });
}

function initCommandPalette() {
  const trigger = $('cmd-trigger');
  const overlay = $('cmd-overlay');
  const input   = $('cmd-input');

  if (trigger) trigger.addEventListener('click', openCommand);
  if (overlay) {
    overlay.addEventListener('click', e => { if (e.target === overlay) closeCommand(); });
  }
  if (input) {
    input.addEventListener('input', () => {
      cmdSelected = -1;
      renderCmdResults(input.value);
    });
  }

  document.addEventListener('keydown', e => {
    // Open
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      cmdOpen ? closeCommand() : openCommand();
      return;
    }
    if (!cmdOpen) return;

    const items = $$('.cmd-result-item');
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      cmdSelected = Math.min(cmdSelected + 1, items.length - 1);
      items.forEach((l,i) => l.classList.toggle('selected', i===cmdSelected));
      items[cmdSelected]?.scrollIntoView({ block: 'nearest' });
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      cmdSelected = Math.max(cmdSelected - 1, 0);
      items.forEach((l,i) => l.classList.toggle('selected', i===cmdSelected));
      items[cmdSelected]?.scrollIntoView({ block: 'nearest' });
    } else if (e.key === 'Enter') {
      e.preventDefault();
      const sel = items[cmdSelected];
      if (sel) sel.click();
    }
  });
}

// ── CONTACT AMBIENT CANVAS ────────────────────────────────────────
function initContactCanvas() {
  if (prefersReducedMotion() || isTouch()) return;
  const canvas = $('contact-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let w, h, rings = [];

  function resize() {
    w = canvas.width  = canvas.offsetWidth;
    h = canvas.height = canvas.offsetHeight;
  }

  rings = Array.from({length: 5}, (_, i) => ({
    r: 40 + i * 60,
    angle: Math.random() * Math.PI * 2,
    speed: (.003 + Math.random() * .003) * (i%2===0 ? 1:-1)
  }));

  function draw() {
    ctx.clearRect(0, 0, w, h);
    const cx = w * .75;
    const cy = h * .5;
    for (const ring of rings) {
      ring.angle += ring.speed;
      ctx.beginPath();
      ctx.arc(cx, cy, ring.r, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(180,180,180,${.035 - ring.r*.0001})`;
      ctx.lineWidth = 1;
      ctx.stroke();
      // dot on ring
      const dx = cx + Math.cos(ring.angle) * ring.r;
      const dy = cy + Math.sin(ring.angle) * ring.r;
      ctx.beginPath();
      ctx.arc(dx, dy, 2.5, 0, Math.PI*2);
      ctx.fillStyle = 'rgba(200,200,200,.35)';
      ctx.fill();
    }
    requestAnimationFrame(draw);
  }

  window.addEventListener('resize', resize, { passive: true });
  resize();
  draw();
}

// ── SMOOTH SCROLL FOR NAV LINKS ────────────────────────────────────
function initSmoothScroll() {
  $$('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const target = document.querySelector(a.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
}

// ── INIT ──────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initCursor();
  initScrollProgress();
  initTopNav();
  initSectionObserver();
  initReveal();
  initRoleCycler();
  initMagnetic();
  initGitHubStats();
  initGithubProjects();
  initAboutTabs();
  initProjectFilter();
  initSkillFilter();
  initProjectModals();
  initCommandPalette();
  initContactCanvas();
  initSmoothScroll();
});
