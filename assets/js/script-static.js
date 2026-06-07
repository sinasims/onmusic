AOS.init({ once: true, offset: 80, duration: 800, easing: 'ease-out-cubic' });

const audioSample = 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3';

function formatPrice(num) {
  return num.toLocaleString('fa-IR') + ' تومان';
}

function formatTime(s) {
  const m = Math.floor(s / 60), sec = Math.floor(s % 60);
  return `${m}:${sec.toString().padStart(2, '0')}`;
}

function findSongById(id) {
  return allSongs.find(s => s.id === id);
}

// ===== Pagination =====
document.querySelectorAll('.pagination-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.pagination-btn').forEach(b => {
      b.classList.remove('bg-purple-600','text-white');
      b.classList.add('bg-white/5','text-slate-300');
    });
    btn.classList.remove('bg-white/5','text-slate-300');
    btn.classList.add('bg-purple-600','text-white');
    document.querySelectorAll('#latestSongsGrid > div').forEach((d, i) => {
      d.style.display = i === parseInt(btn.dataset.page) ? '' : 'none';
    });
  });
});

// ===== Player =====
let isPlaying = false;
const audioEl = document.getElementById('audioEl');
const player = document.getElementById('audioPlayer');
const playerToggle = document.getElementById('playerToggle');
const playerClose = document.getElementById('playerClose');
const playerPrev = document.getElementById('playerPrev');
const playerNext = document.getElementById('playerNext');
const playerImg = document.getElementById('playerImg');
const playerTitle = document.getElementById('playerTitle');
const playerArtist = document.getElementById('playerArtist');

let playQueue = [];
let queueIndex = -1;

function addToQueue(song) {
  if (playQueue.length > 0 && playQueue[playQueue.length - 1].title === song.title) return;
  playQueue.splice(queueIndex + 1);
  playQueue.push(song);
  if (playQueue.length > 30) playQueue.splice(0, 10);
  queueIndex = playQueue.length - 1;
}

function playQueueItem() {
  if (queueIndex < 0 || queueIndex >= playQueue.length) return;
  const s = playQueue[queueIndex];
  playerImg.src = s.cover; playerTitle.textContent = s.title; playerArtist.textContent = s.artist;
  audioEl.src = s.previewUrl || audioSample; audioEl.play();
  isPlaying = true; player.classList.remove('translate-y-full');
  updatePlayerIcon();
}

window.playPreview = (title, artist, cover, previewUrl) => {
  playerImg.src = cover; playerTitle.textContent = title; playerArtist.textContent = artist;
  audioEl.src = previewUrl || audioSample; audioEl.play();
  isPlaying = true; player.classList.remove('translate-y-full');
  updatePlayerIcon();
  addToQueue({ title, artist, cover, previewUrl });
};

function togglePlay() {
  if (!audioEl.src) return;
  if (isPlaying) { audioEl.pause(); isPlaying = false; }
  else { audioEl.play(); isPlaying = true; }
  updatePlayerIcon();
}

function updatePlayerIcon() {
  playerToggle.innerHTML = isPlaying
    ? '<i data-lucide="pause" class="w-5 h-5 fill-current"></i>'
    : '<i data-lucide="play" class="w-5 h-5 fill-current"></i>';
  lucide.createIcons();
}

function prevTrack() {
  if (queueIndex > 0) { queueIndex--; playQueueItem(); }
  else audioEl.currentTime = 0;
}

function nextTrack() {
  if (queueIndex < playQueue.length - 1) { queueIndex++; playQueueItem(); }
  else audioEl.currentTime = 0;
}

playerToggle.addEventListener('click', togglePlay);
playerClose.addEventListener('click', () => {
  audioEl.pause(); isPlaying = false;
  player.classList.add('translate-y-full');
  document.getElementById('progressBar').value = 0;
  document.getElementById('currentTime').textContent = '0:00';
});
playerPrev.addEventListener('click', prevTrack);
playerNext.addEventListener('click', nextTrack);

audioEl.addEventListener('timeupdate', () => {
  if (!audioEl.duration) return;
  document.getElementById('progressBar').value = (audioEl.currentTime / audioEl.duration) * 100;
  document.getElementById('currentTime').textContent = formatTime(audioEl.currentTime);
});
audioEl.addEventListener('loadedmetadata', () => {
  document.getElementById('totalTime').textContent = formatTime(audioEl.duration);
});
audioEl.addEventListener('ended', () => {
  if (queueIndex < playQueue.length - 1) setTimeout(nextTrack, 800);
  else { isPlaying = false; updatePlayerIcon(); }
});

document.getElementById('progressBar').addEventListener('input', (e) => {
  if (!audioEl.duration) return;
  audioEl.currentTime = (e.target.value / 100) * audioEl.duration;
});

document.getElementById('volumeSlider').addEventListener('input', (e) => {
  audioEl.volume = parseFloat(e.target.value);
});

// ===== Theme Toggle =====
const themeToggle = document.getElementById('themeToggle');
const metaThemeColor = document.getElementById('themeColorMeta');

function setTheme(theme) {
  const isLight = theme === 'light';
  document.body.classList.toggle('light', isLight);
  metaThemeColor.content = isLight ? '#ffffff' : '#0f172a';
  localStorage.setItem('theme', theme);
  const moon = themeToggle.querySelector('[data-lucide="moon"]');
  const sun = themeToggle.querySelector('[data-lucide="sun"]');
  if (moon) moon.classList.toggle('hidden', isLight);
  if (sun) sun.classList.toggle('hidden', !isLight);
}
themeToggle.addEventListener('click', () => setTheme(document.body.classList.contains('light') ? 'dark' : 'light'));

// ===== Hero Slider =====
let currentSlide = 0;
let slideInterval;

function goToSlide(index) {
  const slides = document.querySelectorAll('.hero-slide');
  const dots = document.querySelectorAll('.hero-dot');
  const bgs = document.querySelectorAll('.hero-bg');
  const glow = document.getElementById('heroGlow');
  slides.forEach(s => s.classList.remove('active'));
  slides[index].classList.add('active');
  dots.forEach(d => d.classList.remove('active'));
  dots[index].classList.add('active');
  bgs.forEach((img, i) => img.classList.toggle('active', i === index));
  glow.className = `absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] rounded-full blur-[120px] z-0 transition-all duration-700 ${heroSlides[index]?.glow_color || 'bg-purple-600/20'}`;
  document.getElementById('scrollHint').style.opacity = index === 0 ? '1' : '0';
  currentSlide = index;
}

function resetSlideInterval() { clearInterval(slideInterval); slideInterval = setInterval(() => goToSlide((currentSlide + 1) % totalSlides), 5000); }

document.getElementById('heroNext').addEventListener('click', () => { goToSlide((currentSlide + 1) % totalSlides); resetSlideInterval(); });
document.getElementById('heroPrev').addEventListener('click', () => { goToSlide((currentSlide - 1 + totalSlides) % totalSlides); resetSlideInterval(); });

const heroDots = document.getElementById('heroDots');
heroDots.innerHTML = Array.from({ length: totalSlides }, (_, i) => `<button class="hero-dot${i===0?' active':''}" data-slide="${i}"></button>`).join('');
heroDots.addEventListener('click', (e) => { const btn = e.target.closest('.hero-dot'); if (btn) { goToSlide(parseInt(btn.dataset.slide)); resetSlideInterval(); }});

slideInterval = setInterval(() => goToSlide((currentSlide + 1) % totalSlides), 5000);

// ===== Cart (local storage) =====
let cart = JSON.parse(localStorage.getItem('cart_static')) || [];

const cartBtn = document.getElementById('cartBtn');
const cartSidebar = document.getElementById('cartSidebar');
const cartOverlay = document.getElementById('cartOverlay');

function toggleCart(open) {
  const isOpen = open !== undefined ? open : !cartSidebar.classList.contains('open');
  cartSidebar.classList.toggle('open', isOpen);
  cartOverlay.classList.toggle('open', isOpen);
  document.body.style.overflow = isOpen ? 'hidden' : '';
}

cartBtn.addEventListener('click', () => toggleCart(true));
document.getElementById('cartClose').addEventListener('click', () => toggleCart(false));
cartOverlay.addEventListener('click', () => toggleCart(false));

function renderCart() {
  const itemsEl = document.getElementById('cartItems');
  const footerEl = document.getElementById('cartFooter');
  const emptyEl = document.getElementById('cartEmpty');
  const badgeEl = document.getElementById('cartBadge');
  const totalItems = cart.reduce((sum, i) => sum + i.quantity, 0);
  badgeEl.textContent = totalItems;
  badgeEl.classList.toggle('hidden', totalItems === 0);

  if (cart.length === 0) { itemsEl.innerHTML = ''; footerEl.classList.add('hidden'); emptyEl.classList.remove('hidden'); return; }
  footerEl.classList.remove('hidden'); emptyEl.classList.add('hidden');

  itemsEl.innerHTML = cart.map(item => `
    <div class="cart-item">
      ${item.cover ? `<img src="${item.cover}" alt="${item.title}" class="w-12 h-12 rounded-lg object-cover" loading="lazy">` : '<div class="w-12 h-12 rounded-lg bg-white/5 flex items-center justify-center text-slate-500"><i data-lucide="package" class="w-5 h-5"></i></div>'}
      <div class="flex-1 min-w-0">
        <p class="text-sm font-bold truncate">${item.title}</p>
        ${item.artist ? `<p class="text-xs text-slate-400 truncate">${item.artist}</p>` : ''}
        <p class="text-xs text-purple-300 mt-0.5">${formatPrice(item.price)}</p>
      </div>
      <div class="flex items-center gap-1">
        <button onclick="changeQty(${item.id},-1)" class="p-1 text-slate-400 hover:text-white transition-colors rounded hover:bg-white/5 cursor-pointer"><i data-lucide="minus" class="w-3.5 h-3.5"></i></button>
        <span class="text-sm font-bold w-6 text-center">${item.quantity}</span>
        <button onclick="changeQty(${item.id},1)" class="p-1 text-slate-400 hover:text-white transition-colors rounded hover:bg-white/5 cursor-pointer"><i data-lucide="plus" class="w-3.5 h-3.5"></i></button>
        <button onclick="removeItem(${item.id})" class="p-1 text-red-400 hover:text-red-300 transition-colors mr-1 cursor-pointer"><i data-lucide="trash-2" class="w-4 h-4"></i></button>
      </div>
    </div>
  `).join('');
  const total = cart.reduce((sum, i) => sum + i.price * i.quantity, 0);
  document.getElementById('cartTotal').textContent = formatPrice(total);
  lucide.createIcons();
}

function saveCart() {
  localStorage.setItem('cart_static', JSON.stringify(cart));
}

window.addToCart = function(id) {
  const song = findSongById(id);
  if (!song) return;
  const existing = cart.find(i => i.id === id && i.itemType === 'song');
  if (existing) existing.quantity++;
  else cart.push({ id, title: song.title, artist: song.artist, cover: song.cover, price: song.price, itemType: 'song', quantity: 1 });
  saveCart(); renderCart();
  showToast(`«${song.title}» به سبد خرید اضافه شد`, 'success');
};

window.addToCartPackage = function(id) {
  const pkg = packagesData.find(p => p.id === id);
  if (!pkg) return;
  const existing = cart.find(i => i.id === id && i.itemType === 'package');
  if (existing) existing.quantity++;
  else cart.push({ id, title: pkg.title, cover: pkg.cover, price: pkg.price, itemType: 'package', quantity: 1 });
  saveCart(); renderCart();
  showToast('پکیج به سبد خرید اضافه شد', 'success');
};

window.addToCartSubscription = function(id) {
  const plan = plansData.find(p => p.id === id);
  if (!plan) return;
  const existing = cart.find(i => i.id === id && i.itemType === 'subscription');
  if (existing) existing.quantity++;
  else cart.push({ id, title: plan.title, price: plan.price, itemType: 'subscription', quantity: 1 });
  saveCart(); renderCart();
  showToast('اشتراک به سبد خرید اضافه شد', 'success');
};

window.changeQty = function(id, delta) {
  const item = cart.find(i => i.id === id);
  if (!item) return;
  item.quantity += delta;
  if (item.quantity <= 0) cart = cart.filter(i => i.id !== id);
  saveCart(); renderCart();
};

window.removeItem = function(id) {
  cart = cart.filter(i => i.id !== id);
  saveCart(); renderCart();
  showToast('آیتم از سبد خرید حذف شد', 'info');
};

// Checkout button (static: just shows a toast)
document.querySelector('#cartFooter button:last-child')?.addEventListener('click', () => {
  if (cart.length === 0) return;
  showToast('ثبت سفارش در نسخه نمایشی فعال نیست', 'info');
});

// ===== Song Modal =====
const modal = document.getElementById('songModal');
let modalCurrentSong = null;

window.openSongModal = function(id) {
  const song = findSongById(id);
  if (!song) return;
  modalCurrentSong = song;
  document.getElementById('modalImg').src = song.cover;
  document.getElementById('modalTitle').textContent = song.title;
  document.getElementById('modalArtist').textContent = song.artist;
  document.getElementById('modalPrice').textContent = formatPrice(song.price);
  modal.classList.add('open');
  document.body.style.overflow = 'hidden';
};

function closeModal() { modal.classList.remove('open'); document.body.style.overflow = ''; }
document.getElementById('modalClose').addEventListener('click', closeModal);
modal.addEventListener('click', (e) => { if (e.target === modal) closeModal(); });
document.getElementById('modalPlay').addEventListener('click', () => {
  if (!modalCurrentSong) return;
  playPreview(modalCurrentSong.title, modalCurrentSong.artist, modalCurrentSong.cover, modalCurrentSong.preview_url);
  closeModal();
});
document.getElementById('modalAddToCart').addEventListener('click', () => {
  if (!modalCurrentSong) return;
  addToCart(modalCurrentSong.id);
  closeModal();
});

// ===== Login Modal (static - no-op) =====
const authBtn = document.getElementById('authBtn');
const loginModal = document.getElementById('loginModal');
const loginModalClose = document.getElementById('loginModalClose');
const userDrawer = document.getElementById('userDrawer');
const userOverlay = document.getElementById('userOverlay');
const userClose = document.getElementById('userClose');

function openLoginModal() { loginModal.classList.add('open'); document.body.style.overflow = 'hidden'; }
function closeLoginModal() { loginModal.classList.remove('open'); document.body.style.overflow = ''; }
function toggleUserDrawer(open) {
  const isOpen = open !== undefined ? open : !userDrawer.classList.contains('open');
  userDrawer.classList.toggle('open', isOpen);
  userOverlay.classList.toggle('open', isOpen);
  document.body.style.overflow = isOpen ? 'hidden' : '';
}

authBtn.addEventListener('click', () => toggleUserDrawer(true));
loginModalClose.addEventListener('click', closeLoginModal);
loginModal.addEventListener('click', (e) => { if (e.target === loginModal) closeLoginModal(); });
userClose.addEventListener('click', () => toggleUserDrawer(false));
userOverlay.addEventListener('click', () => toggleUserDrawer(false));

document.getElementById('sendOtpBtn').addEventListener('click', () => showToast('ورود در نسخه نمایشی فعال نیست', 'info'));
document.getElementById('loginBtn').addEventListener('click', () => showToast('ورود در نسخه نمایشی فعال نیست', 'info'));
document.getElementById('logoutBtn').addEventListener('click', () => toggleUserDrawer(false));

// ===== Testimonials =====
let testimonialIndex = 0;
let testimonialInterval;

function goToTestimonial(index) {
  const cards = document.querySelectorAll('.testimonial-card');
  if (!cards.length) return;
  if (index < 0) index = cards.length - 1;
  if (index >= cards.length) index = 0;
  testimonialIndex = index;
  const track = document.getElementById('testimonialTrack');
  const container = track.parentElement;
  const cardWidth = container.offsetWidth;
  track.style.transform = `translateX(${index * cardWidth}px)`;
  document.querySelectorAll('#testimonialDots .hero-dot').forEach((d, i) => d.classList.toggle('active', i === index));
}

function resetTestimonialInterval() { clearInterval(testimonialInterval); testimonialInterval = setInterval(() => goToTestimonial(testimonialIndex + 1), 4000); }

document.getElementById('testimonialNext').addEventListener('click', () => { goToTestimonial(testimonialIndex + 1); resetTestimonialInterval(); });
document.getElementById('testimonialPrev').addEventListener('click', () => { goToTestimonial(testimonialIndex - 1); resetTestimonialInterval(); });
document.getElementById('testimonialDots').addEventListener('click', (e) => {
  const btn = e.target.closest('.hero-dot');
  if (btn) { goToTestimonial(parseInt(btn.dataset.tindex)); resetTestimonialInterval(); }
});

const testimonialSection = document.getElementById('testimonials');
testimonialSection.addEventListener('mouseenter', () => clearInterval(testimonialInterval));
testimonialSection.addEventListener('mouseleave', () => {
  clearInterval(testimonialInterval);
  testimonialInterval = setInterval(() => goToTestimonial(testimonialIndex + 1), 4000);
});

// ===== Toast =====
function showToast(message, type = 'success') {
  const container = document.getElementById('toastContainer');
  const icons = { success: 'check-circle', error: 'alert-circle', info: 'info' };
  const colors = { success: 'text-green-400', error: 'text-red-400', info: 'text-cyan-400' };
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = `<i data-lucide="${icons[type]||'info'}" class="w-5 h-5 ${colors[type]||'text-cyan-400'} flex-shrink-0"></i><span class="flex-1">${message}</span>`;
  container.appendChild(toast);
  lucide.createIcons();
  setTimeout(() => { toast.classList.add('removing'); setTimeout(() => toast.remove(), 300); }, 3000);
}

// ===== Mobile Menu =====
const mobileMenuBtn = document.getElementById('mobileMenuBtn');
const mobileDrawer = document.getElementById('mobileDrawer');
const mobileOverlay = document.getElementById('mobileOverlay');
const mobileClose = document.getElementById('mobileClose');

function toggleMobileMenu(open) {
  const isOpen = open !== undefined ? open : !mobileDrawer.classList.contains('open');
  mobileDrawer.classList.toggle('open', isOpen);
  mobileOverlay.classList.toggle('open', isOpen);
  document.body.style.overflow = isOpen ? 'hidden' : '';
}

mobileMenuBtn.addEventListener('click', () => toggleMobileMenu(true));
mobileClose.addEventListener('click', () => toggleMobileMenu(false));
mobileOverlay.addEventListener('click', () => toggleMobileMenu(false));
window.addEventListener('resize', () => { if (window.innerWidth >= 768) toggleMobileMenu(false); });

// ===== Navbar Scroll =====
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
  navbar.classList.toggle('shadow-lg', window.scrollY > 50);
  navbar.classList.toggle('shadow-purple-900/10', window.scrollY > 50);
});

// ===== Init =====
function init() {
  lucide.createIcons();
  setTheme(localStorage.getItem('theme') || 'dark');
  AOS.refresh();
  testimonialInterval = setInterval(() => goToTestimonial(testimonialIndex + 1), 4000);
  renderCart();
}
init();
