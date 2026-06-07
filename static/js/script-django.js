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
  if (typeof allSongs === 'undefined') return null;
  return allSongs.find(s => s.id === id);
}

// ===== Player =====
let isPlaying = false;
let currentPreviewUrl = '';
const audioEl = document.getElementById('audioEl');
const player = document.getElementById('audioPlayer');
const playerToggle = document.getElementById('playerToggle');
const playerClose = document.getElementById('playerClose');
const playerImg = document.getElementById('playerImg');
const playerTitle = document.getElementById('playerTitle');
const playerArtist = document.getElementById('playerArtist');

let playQueue = [];
let queueIndex = -1;

function updatePlayButtons() {
  document.querySelectorAll('.play-btn').forEach(btn => {
    const url = btn.dataset.previewUrl || '';
    const isThisOne = url && url === currentPreviewUrl;
    const icon = btn.querySelector('.play-icon');
    if (icon) {
      icon.outerHTML = isThisOne && isPlaying
        ? '<i data-lucide="pause" class="play-icon w-4 h-4 fill-current"></i>'
        : '<i data-lucide="play" class="play-icon w-4 h-4 fill-current"></i>';
    }
  });
  lucide.createIcons();
}

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
  isPlaying = true; currentPreviewUrl = s.previewUrl || '';
  player.classList.remove('translate-y-full');
  updatePlayerIcon();
}

window.playPreview = (title, artist, cover, previewUrl) => {
  if (previewUrl && previewUrl === currentPreviewUrl && isPlaying) {
    togglePlay();
    return;
  }
  // Check if this arranged download needs subscription confirm
  if (previewUrl && previewUrl.includes('/download/') && previewUrl.includes('/arranged')) {
    const songIdMatch = previewUrl.match(/\/download\/(\d+)\/arranged/);
    if (songIdMatch && typeof purchasedSongIds !== 'undefined') {
      const sid = parseInt(songIdMatch[1]);
      if (!purchasedSongIds.has(sid) && typeof hasSubscription !== 'undefined' && hasSubscription) {
        showConfirm(() => {
          playerImg.src = cover; playerTitle.textContent = title; playerArtist.textContent = artist;
          audioEl.src = previewUrl; audioEl.play();
          isPlaying = true; currentPreviewUrl = previewUrl;
          player.classList.remove('translate-y-full');
          updatePlayerIcon();
          addToQueue({ title, artist, cover, previewUrl });
        });
        return;
      }
    }
  }
  playerImg.src = cover; playerTitle.textContent = title; playerArtist.textContent = artist;
  audioEl.src = previewUrl || audioSample; audioEl.play();
  isPlaying = true; currentPreviewUrl = previewUrl || '';
  player.classList.remove('translate-y-full');
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
  updatePlayButtons();
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

// ===== Confirm Modal =====
const confirmModal = document.getElementById('confirmModal');
const confirmText = document.getElementById('confirmText');
const confirmOk = document.getElementById('confirmOk');
const confirmCancel = document.getElementById('confirmCancel');

function showConfirm(callback) {
  confirmText.textContent = 'آیا می‌خواهید این آهنگ را دانلود کنید؟ یک عدد از اشتراک شما کم می‌شود.';
  confirmOk.onclick = () => { confirmModal.classList.remove('open'); callback(); };
  confirmCancel.onclick = () => { confirmModal.classList.remove('open'); };
  confirmModal.classList.add('open');
}

playerToggle.addEventListener('click', togglePlay);
playerClose.addEventListener('click', () => {
  audioEl.pause(); isPlaying = false; currentPreviewUrl = '';
  player.classList.add('translate-y-full');
  document.getElementById('progressBar').value = 0;
  document.getElementById('currentTime').textContent = '0:00';
  updatePlayButtons();
});
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
  else { isPlaying = false; currentPreviewUrl = ''; updatePlayerIcon(); }
});

const progressBar = document.getElementById('progressBar');

progressBar.addEventListener('input', (e) => {
  if (!audioEl.duration || isNaN(audioEl.duration)) return;
  audioEl.currentTime = (Number(e.target.value) / 100) * audioEl.duration;
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
  if (!slides.length) return;
  const dots = document.querySelectorAll('.hero-dot');
  const bgs = document.querySelectorAll('.hero-bg');
  const glow = document.getElementById('heroGlow');
  slides.forEach(s => s.classList.remove('active'));
  slides[index].classList.add('active');
  dots.forEach(d => d.classList.remove('active'));
  dots[index].classList.add('active');
  bgs.forEach((img, i) => img.classList.toggle('active', i === index));
  if (glow) glow.className = `absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] rounded-full blur-[120px] z-0 transition-all duration-700 ${typeof heroSlides !== 'undefined' ? (heroSlides[index]?.glow_color || 'bg-purple-600/20') : 'bg-purple-600/20'}`;
  const scrollHint = document.getElementById('scrollHint');
  if (scrollHint) scrollHint.style.opacity = index === 0 ? '1' : '0';
  currentSlide = index;
}

function resetSlideInterval() {
  clearInterval(slideInterval);
  const total = typeof totalSlides !== 'undefined' ? totalSlides : 0;
  if (!total) return;
  slideInterval = setInterval(() => goToSlide((currentSlide + 1) % total), 5000);
}

const heroNext = document.getElementById('heroNext');
const heroPrev = document.getElementById('heroPrev');
const heroDots = document.getElementById('heroDots');
const hasHero = heroNext && heroPrev && heroDots && typeof totalSlides !== 'undefined';

if (hasHero) {
  heroNext.addEventListener('click', () => { goToSlide((currentSlide + 1) % totalSlides); resetSlideInterval(); });
  heroPrev.addEventListener('click', () => { goToSlide((currentSlide - 1 + totalSlides) % totalSlides); resetSlideInterval(); });
  heroDots.innerHTML = Array.from({ length: totalSlides }, (_, i) => `<button class="hero-dot${i===0?' active':''}" data-slide="${i}"></button>`).join('');
  heroDots.addEventListener('click', (e) => { const btn = e.target.closest('.hero-dot'); if (btn) { goToSlide(parseInt(btn.dataset.slide)); resetSlideInterval(); }});
  slideInterval = setInterval(() => goToSlide((currentSlide + 1) % totalSlides), 5000);
}

// ===== API helpers =====
function getCookie(name) {
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  return match ? match[2] : null;
}

async function apiPost(url, data) {
  try {
    const resp = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      body: JSON.stringify(data),
    });
    return await resp.json();
  } catch (e) {
    return { success: false, message: 'خطا در ارتباط با سرور' };
  }
}

async function apiGet(url) {
  try {
    const resp = await fetch(url);
    return await resp.json();
  } catch (e) {
    return { success: false, message: 'خطا در ارتباط با سرور' };
  }
}

// ===== Cart =====
let cart = [];
let cartLoaded = false;

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

async function loadCart() {
  const data = await apiGet('/cart/get/');
  if (data.authenticated === false) {
    cart = JSON.parse(localStorage.getItem('cart_django')) || [];
    cartLoaded = true;
    renderCart();
    return;
  }
  cart = data.items || [];
  cartLoaded = true;
  renderCart();
}

function renderCart() {
  const itemsEl = document.getElementById('cartItems');
  const footerEl = document.getElementById('cartFooter');
  const emptyEl = document.getElementById('cartEmpty');
  const badgeEl = document.getElementById('cartBadge');
  const totalItems = cart.reduce((sum, i) => sum + (i.quantity || 1), 0);
  badgeEl.textContent = totalItems;
  badgeEl.classList.toggle('hidden', totalItems === 0);

  if (cart.length === 0) { itemsEl.innerHTML = ''; footerEl.classList.add('hidden'); emptyEl.classList.remove('hidden'); return; }
  footerEl.classList.remove('hidden'); emptyEl.classList.add('hidden');

  const isLocal = !cart[0].hasOwnProperty('item_type');

  itemsEl.innerHTML = cart.map(item => {
    const cover = item.cover || '';
    const title = item.title;
    const artist = item.artist || '';
    const price = item.price || 0;
    const qty = item.quantity || 1;
    const id = item.id;
    return `
    <div class="cart-item">
      ${cover ? `<img src="${cover}" alt="${title}" class="w-12 h-12 rounded-lg object-cover" loading="lazy">` : '<div class="w-12 h-12 rounded-lg bg-white/5 flex items-center justify-center text-slate-500"><i data-lucide="package" class="w-5 h-5"></i></div>'}
      <div class="flex-1 min-w-0">
        <p class="text-sm font-bold truncate">${title}</p>
        ${artist ? `<p class="text-xs text-slate-400 truncate">${artist}</p>` : ''}
        <p class="text-xs text-purple-300 mt-0.5">${formatPrice(price)}</p>
      </div>
      <div class="flex items-center gap-1">
        <button onclick="changeQty(${id},-1,${isLocal})" class="p-1 text-slate-400 hover:text-white transition-colors rounded hover:bg-white/5 cursor-pointer"><i data-lucide="minus" class="w-3.5 h-3.5"></i></button>
        <span class="text-sm font-bold w-6 text-center">${qty}</span>
        <button onclick="changeQty(${id},1,${isLocal})" class="p-1 text-slate-400 hover:text-white transition-colors rounded hover:bg-white/5 cursor-pointer"><i data-lucide="plus" class="w-3.5 h-3.5"></i></button>
        <button onclick="removeItem(${id},${isLocal})" class="p-1 text-red-400 hover:text-red-300 transition-colors mr-1 cursor-pointer"><i data-lucide="trash-2" class="w-4 h-4"></i></button>
      </div>
    </div>`;
  }).join('');
  const total = cart.reduce((sum, i) => sum + (i.price || 0) * (i.quantity || 1), 0);
  document.getElementById('cartTotal').textContent = formatPrice(total);
  lucide.createIcons();
}

function saveCartLocal() {
  localStorage.setItem('cart_django', JSON.stringify(cart));
}

window.addToCart = async function(id, title, artist, cover, price) {
  if (!title) {
    const song = findSongById(id);
    if (!song) return;
    title = song.title; artist = song.artist; cover = song.cover; price = song.price;
  }
  const data = await apiPost('/cart/add/', {
    item_type: 'song', item_id: id,
    title: title, artist: artist,
    cover: cover, price: price,
  });
  if (data.success) {
    showToast(`«${title}» به سبد خرید اضافه شد`, 'success');
    loadCart();
  } else if (data.authenticated === false) {
    const existing = cart.find(i => i.id === id);
    if (existing) { existing.quantity = (existing.quantity || 1) + 1; }
    else { cart.push({ id, title, artist, cover, price, quantity: 1 }); }
    saveCartLocal();
    renderCart();
    showToast(`«${title}» به سبد خرید اضافه شد`, 'success');
  } else {
    showToast(data.message, 'error');
  }
};

window.addToCartPackage = async function(id, title, cover, price) {
  const data = await apiPost('/cart/add/', {
    item_type: 'album', item_id: id,
    title: title, cover: cover, price: price,
  });
  if (data.success) {
    showToast('آلبوم به سبد خرید اضافه شد', 'success');
    loadCart();
  } else {
    showToast(data.message, 'error');
  }
};

window.addToCartSubscription = async function(id, title, price) {
  const data = await apiPost('/cart/add/', {
    item_type: 'subscription', item_id: id,
    title: title, price: price,
  });
  if (data.success) {
    showToast('اشتراک به سبد خرید اضافه شد', 'success');
    loadCart();
  } else {
    showToast(data.message, 'error');
  }
};

window.changeQty = async function(id, delta, isLocal) {
  if (isLocal) {
    const item = cart.find(i => i.id === id);
    if (!item) return;
    item.quantity = (item.quantity || 1) + delta;
    if (item.quantity <= 0) cart = cart.filter(i => i.id !== id);
    saveCartLocal(); renderCart();
    return;
  }
  const action = delta > 0 ? 'increase' : 'decrease';
  const data = await apiPost('/cart/update/', { item_id: id, action });
  if (data.success) loadCart();
};

window.removeItem = async function(id, isLocal) {
  if (isLocal) {
    cart = cart.filter(i => i.id !== id);
    saveCartLocal(); renderCart();
    showToast('آیتم از سبد خرید حذف شد', 'info');
    return;
  }
  const data = await apiPost('/cart/update/', { item_id: id, action: 'remove' });
  if (data.success) { loadCart(); showToast('آیتم از سبد خرید حذف شد', 'info'); }
};

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
  document.getElementById('modalDuration').textContent = song.duration || '—';
  document.getElementById('modalBpm').textContent = song.bpm ? song.bpm + ' BPM' : '—';
  document.getElementById('modalRating').textContent = song.avg_rating ? song.avg_rating + ' / 5' : '—';
  document.getElementById('modalViews').textContent = (song.views_count || 0) + ' بازدید';
  document.getElementById('modalPurchases').textContent = (song.purchase_count || 0) + ' خرید';
  document.getElementById('modalDetailLink').href = '/song/' + song.id + '/';
  const cartBtn = document.getElementById('modalAddToCart');
  if (typeof purchasedSongIds !== 'undefined' && purchasedSongIds.has(id)) {
    cartBtn.style.display = 'none';
  } else if (typeof hasSubscription !== 'undefined' && hasSubscription) {
    cartBtn.style.display = 'none';
  } else {
    cartBtn.style.display = '';
  }
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

window.downloadArranged = function(songId) {
  const url = '/download/' + songId + '/arranged/';
  if (typeof purchasedSongIds !== 'undefined' && !purchasedSongIds.has(songId) && typeof hasSubscription !== 'undefined' && hasSubscription) {
    showConfirm(() => { window.location.href = url; });
  } else {
    window.location.href = url;
  }
};

// ===== Login / Auth =====
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

authBtn.addEventListener('click', () => {
  apiGet('/accounts/me/').then(data => {
    if (data.authenticated) {
      document.getElementById('userName').textContent = data.user.name;
      document.getElementById('userPhone').textContent = data.user.phone;
      toggleUserDrawer(true);
    } else {
      openLoginModal();
    }
  });
});

loginModalClose.addEventListener('click', closeLoginModal);
loginModal.addEventListener('click', (e) => { if (e.target === loginModal) closeLoginModal(); });
userClose.addEventListener('click', () => toggleUserDrawer(false));
userOverlay.addEventListener('click', () => toggleUserDrawer(false));

// OTP Flow
const phoneInput = document.getElementById('phoneInput');
const sendOtpBtn = document.getElementById('sendOtpBtn');
const loginStep1 = document.getElementById('loginStep1');
const loginStep2 = document.getElementById('loginStep2');
const otpInput = document.getElementById('otpInput');
const loginBtn = document.getElementById('loginBtn');
const loginPhoneDisplay = document.getElementById('loginPhoneDisplay');
const backToPhoneBtn = document.getElementById('backToPhoneBtn');

let currentPhone = '';

sendOtpBtn.addEventListener('click', async () => {
  const phone = phoneInput.value.trim();
  if (phone.length < 10) { showToast('شماره موبایل نامعتبر است', 'error'); return; }
  sendOtpBtn.disabled = true;
  sendOtpBtn.textContent = 'در حال ارسال...';
  const data = await apiPost('/accounts/send-otp/', { phone });
  sendOtpBtn.disabled = false;
  sendOtpBtn.textContent = 'ارسال کد';
  if (data.success) {
    currentPhone = phone;
    loginPhoneDisplay.textContent = phone;
    loginStep1.classList.add('hidden');
    loginStep2.classList.remove('hidden');
    if (data.debug_code) {
      otpInput.value = data.debug_code;
      showToast('کد تایید: ' + data.debug_code, 'info');
    } else {
      showToast(data.message, 'success');
    }
  } else {
    showToast(data.message, 'error');
  }
});

loginBtn.addEventListener('click', async () => {
  const code = otpInput.value.trim();
  if (code.length < 4) { showToast('کد را وارد کنید', 'error'); return; }
  loginBtn.disabled = true;
  loginBtn.textContent = 'در حال ورود...';
  const data = await apiPost('/accounts/verify-otp/', { phone: currentPhone, code });
  loginBtn.disabled = false;
  loginBtn.textContent = 'ورود';
  if (data.success) {
    closeLoginModal();
    showToast('ورود موفق', 'success');
    document.getElementById('userName').textContent = data.user.name;
    document.getElementById('userPhone').textContent = data.user.phone;
    loadCart();
  } else {
    showToast(data.message, 'error');
  }
});

backToPhoneBtn.addEventListener('click', () => {
  loginStep2.classList.add('hidden');
  loginStep1.classList.remove('hidden');
  otpInput.value = '';
});

document.getElementById('logoutBtn').addEventListener('click', async function() {
  try {
    await apiPost('/accounts/logout/', {});
  } catch(e) {}
  toggleUserDrawer(false);
  showToast('خروج موفق', 'info');
  cart = [];
  saveCartLocal();
  renderCart();
  window.location.reload();
});

// ===== Enter key support for inputs =====
if (phoneInput) {
  phoneInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); sendOtpBtn.click(); } });
}
if (otpInput) {
  otpInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); loginBtn.click(); } });
}
const couponInput = document.getElementById('couponInput');
const couponApplyBtn = document.getElementById('couponApplyBtn');
if (couponInput && couponApplyBtn) {
  couponInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); couponApplyBtn.click(); } });
}

// ===== Checkout =====
document.getElementById('checkoutBtn').addEventListener('click', async () => {
  const btn = document.getElementById('checkoutBtn');
  btn.disabled = true;
  btn.textContent = 'در حال اتصال به درگاه...';
  const data = await apiPost('/cart/checkout/', {});
  if (data.success && data.url) {
    window.location.href = data.url;
  } else {
    showToast(data.message || 'خطا در اتصال به درگاه', 'error');
    btn.disabled = false;
    btn.textContent = 'ثبت سفارش';
  }
});

// ===== Coupon =====
(function() {
  const couponInput = document.getElementById('couponInput');
  const applyBtn = document.getElementById('couponApplyBtn');
  const couponForm = document.getElementById('couponForm');
  const couponApplied = document.getElementById('couponApplied');
  const couponCodeDisplay = document.getElementById('couponCodeDisplay');
  const couponDiscountDisplay = document.getElementById('couponDiscountDisplay');
  const couponRemoveBtn = document.getElementById('couponRemoveBtn');
  let activeCoupon = null;

  if (applyBtn) {
    applyBtn.addEventListener('click', async () => {
      if (!couponInput) return;
      const code = couponInput.value.trim();
      if (!code) { showToast('کد تخفیف را وارد کنید', 'error'); return; }
      applyBtn.disabled = true;
      applyBtn.textContent = '...';
      const data = await apiPost('/cart/coupon/apply/', { code });
      applyBtn.disabled = false;
      applyBtn.textContent = 'اعمال';
      if (data.success) {
        activeCoupon = code;
        couponForm.classList.add('hidden');
        couponApplied.classList.remove('hidden');
        couponCodeDisplay.textContent = data.code;
        couponDiscountDisplay.textContent = data.discount.toLocaleString('fa-IR') + ' تومان';
        showToast(data.message, 'success');
      } else {
        showToast(data.message, 'error');
      }
    });
  }

  if (couponRemoveBtn) {
    couponRemoveBtn.addEventListener('click', async () => {
      activeCoupon = null;
      couponApplied.classList.add('hidden');
      couponForm.classList.remove('hidden');
      if (couponInput) couponInput.value = '';
      await apiPost('/cart/coupon/remove/', {});
      showToast('کد تخفیف حذف شد', 'info');
    });
  }
})();

// ===== Wishlist =====
let wishlistedIds = new Set();

async function loadWishlist() {
  const data = await apiGet('/api/wishlist/');
  if (data.wishlisted_ids) {
    wishlistedIds = new Set(data.wishlisted_ids);
    updateWishlistButtons();
  }
}

function updateWishlistButtons() {
  document.querySelectorAll('.wishlist-btn').forEach(btn => {
    const id = parseInt(btn.dataset.songId);
    const isWishlisted = wishlistedIds.has(id);
    btn.classList.toggle('text-red-400', isWishlisted);
    btn.classList.toggle('text-slate-400', !isWishlisted);
    btn.title = isWishlisted ? 'حذف از علاقه‌مندی‌ها' : 'افزودن به علاقه‌مندی‌ها';
  });
}

window.toggleWishlist = async function(songId, btn) {
  if (btn) btn.disabled = true;
  const data = await apiPost('/api/wishlist/toggle/', { song_id: songId });
  if (btn) btn.disabled = false;
  if (data.success) {
    if (data.wishlisted) {
      wishlistedIds.add(songId);
      showToast('به علاقه‌مندی‌ها اضافه شد', 'success');
    } else {
      wishlistedIds.delete(songId);
      showToast('از علاقه‌مندی‌ها حذف شد', 'info');
    }
    updateWishlistButtons();
  } else {
    showToast(data.message, 'error');
  }
};

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

const testimonialNext = document.getElementById('testimonialNext');
const testimonialPrev = document.getElementById('testimonialPrev');
const testimonialDots = document.getElementById('testimonialDots');
const testimonialSection = document.getElementById('testimonials');

if (testimonialNext && testimonialPrev && testimonialDots && testimonialSection) {
  testimonialNext.addEventListener('click', () => { goToTestimonial(testimonialIndex + 1); resetTestimonialInterval(); });
  testimonialPrev.addEventListener('click', () => { goToTestimonial(testimonialIndex - 1); resetTestimonialInterval(); });
  testimonialDots.addEventListener('click', (e) => {
    const btn = e.target.closest('.hero-dot');
    if (btn) { goToTestimonial(parseInt(btn.dataset.tindex)); resetTestimonialInterval(); }
  });
  testimonialSection.addEventListener('mouseenter', () => clearInterval(testimonialInterval));
  testimonialSection.addEventListener('mouseleave', () => {
    clearInterval(testimonialInterval);
    testimonialInterval = setInterval(() => goToTestimonial(testimonialIndex + 1), 4000);
  });
}

// ===== Comments =====
document.querySelectorAll('#ratingStars .star-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const val = parseInt(btn.dataset.star);
    document.getElementById('ratingInput').value = val;
    document.querySelectorAll('#ratingStars .star-btn').forEach((b, i) => {
      b.style.color = i < val ? '#facc15' : '';
    });
  });
});
document.getElementById('commentForm')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const form = e.target;
  const btn = form.querySelector('button[type="submit"]');
  btn.disabled = true;
  btn.textContent = 'در حال ارسال...';
  const captchaEl = document.getElementById('captchaAnswer');
  const parentId = form.querySelector('[name="parent_id"]')?.value;
  const body = {
    content_type: form.querySelector('[name="content_type"]').value,
    object_id: form.querySelector('[name="object_id"]').value,
    name: form.querySelector('[name="name"]').value,
    text: form.querySelector('[name="text"]').value,
    rating: form.querySelector('[name="rating"]').value,
  };
  if (parentId) body.parent_id = parentId;
  if (captchaEl) {
    body.captcha_answer = captchaEl.value;
    body.captcha_token = document.getElementById('captchaToken')?.value || '';
  }
  const data = await apiPost('/comment/', body);
  btn.disabled = false;
  btn.textContent = 'ارسال نظر';
  if (data.success) {
    showToast('نظر شما ثبت شد و پس از تایید نمایش داده می‌شود', 'success');
    form.reset();
    document.getElementById('parentIdInput') && (document.getElementById('parentIdInput').value = '');
    document.getElementById('replyInfo') && (document.getElementById('replyInfo').classList.add('hidden'));
    document.getElementById('commentFormTitle') && (document.getElementById('commentFormTitle').textContent = 'ثبت نظر');
    loadCaptcha();
  } else {
    showToast(data.message || 'خطا در ثبت نظر', 'error');
    loadCaptcha();
  }
});

async function loadCaptcha() {
  const field = document.getElementById('captchaField');
  if (!field) return;
  try {
    const resp = await fetch('/captcha/');
    const data = await resp.json();
    document.getElementById('captchaQuestion').textContent = data.question;
    document.getElementById('captchaToken').value = data.token;
    document.getElementById('captchaAnswer').value = '';
    field.classList.remove('hidden');
  } catch (e) {}
}
document.addEventListener('DOMContentLoaded', loadCaptcha);

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

// ===== Search Autocomplete =====
const searchInput = document.getElementById('searchInput');
const searchDropdown = document.getElementById('searchDropdown');
let searchTimer = null;

if (searchInput && searchDropdown) {
  searchInput.addEventListener('input', () => {
    clearTimeout(searchTimer);
    const q = searchInput.value.trim();
    if (q.length < 1) { searchDropdown.classList.add('hidden'); return; }
    searchTimer = setTimeout(async () => {
      try {
        const resp = await fetch('/search/autocomplete/?q=' + encodeURIComponent(q));
        const data = await resp.json();
        let html = '';
        if (data.songs.length) {
          html += '<div class="px-3 py-2 text-xs text-purple-400 font-bold border-b border-white/5">آهنگ‌ها</div>';
          data.songs.forEach(s => {
            html += '<a href="' + s.url + '" class="flex items-center gap-2 px-3 py-2 hover:bg-white/5 transition-colors"><img src="' + s.cover + '" class="w-8 h-8 rounded object-cover flex-shrink-0"><div class="min-w-0 flex-1"><p class="text-sm font-medium truncate">' + s.title + '</p><p class="text-xs text-slate-500 truncate">' + s.artist + '</p></div></a>';
          });
        }
        if (data.artists && data.artists.length) {
          html += '<div class="px-3 py-2 text-xs text-orange-400 font-bold border-b border-white/5">خواننده‌ها</div>';
          data.artists.forEach(a => {
            const img = a.image ? '<img src="' + a.image + '" class="w-8 h-8 rounded-full object-cover flex-shrink-0">' : '<div class="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center flex-shrink-0"><i data-lucide="mic-vocal" class="w-4 h-4 text-orange-400"></i></div>';
            html += '<a href="' + a.url + '" class="flex items-center gap-2 px-3 py-2 hover:bg-white/5 transition-colors">' + img + '<div class="min-w-0 flex-1"><p class="text-sm font-medium truncate">' + a.name + '</p></div></a>';
          });
        }
        if (data.albums.length) {
          html += '<div class="px-3 py-2 text-xs text-indigo-400 font-bold border-b border-white/5">آلبوم‌ها</div>';
          data.albums.forEach(a => {
            html += '<a href="' + a.url + '" class="flex items-center gap-2 px-3 py-2 hover:bg-white/5 transition-colors"><img src="' + a.cover + '" class="w-8 h-8 rounded object-cover flex-shrink-0"><div class="min-w-0 flex-1"><p class="text-sm font-medium truncate">' + a.title + '</p></div></a>';
          });
        }
        if (data.posts.length) {
          html += '<div class="px-3 py-2 text-xs text-emerald-400 font-bold border-b border-white/5">مقالات</div>';
          data.posts.forEach(p => {
            html += '<a href="' + p.url + '" class="flex items-center gap-2 px-3 py-2 hover:bg-white/5 transition-colors"><div class="w-8 h-8 rounded bg-white/5 flex items-center justify-center flex-shrink-0"><i data-lucide="file-text" class="w-4 h-4 text-emerald-400"></i></div><div class="min-w-0 flex-1"><p class="text-sm font-medium truncate">' + p.title + '</p></div></a>';
          });
        }
        if (!data.songs.length && !data.albums.length && !data.posts.length) {
          html = '<div class="px-3 py-4 text-xs text-slate-500 text-center">نتیجه‌ای یافت نشد</div>';
        } else {
          html += '<a href="/search/?q=' + encodeURIComponent(q) + '" class="block px-3 py-2 text-xs text-purple-400 hover:bg-white/5 transition-colors text-center border-t border-white/5">مشاهده همه نتایج</a>';
        }
        searchDropdown.innerHTML = html;
        searchDropdown.classList.remove('hidden');
        lucide.createIcons();
      } catch (e) { searchDropdown.classList.add('hidden'); }
    }, 300);
  });

  document.addEventListener('click', (e) => {
    if (!searchInput.parentElement.contains(e.target)) searchDropdown.classList.add('hidden');
  });
}

// ===== Infinite Scroll =====
(function() {
  const grid = document.getElementById('itemsGrid');
  if (!grid || typeof window.listPage === 'undefined') return;
  const loader = document.getElementById('listLoading');
  const skeleton = document.getElementById('listSkeleton');
  let loading = false;
  let { hasNext, currentPage, totalPages } = window.listPage;

  async function loadNextPage() {
    if (loading || !hasNext) return;
    loading = true;
    if (skeleton) skeleton.classList.remove('hidden');
    try {
      const resp = await fetch(window.location.pathname + '?page=' + (currentPage + 1) + '&ajax=1');
      const data = await resp.json();
      const temp = document.createElement('div');
      temp.innerHTML = data.html;
      while (temp.firstChild) grid.appendChild(temp.firstChild);
      currentPage++;
      hasNext = data.has_next;
      lucide.createIcons();
    } catch (e) {}
    if (skeleton) skeleton.classList.add('hidden');
    loading = false;
  }

  window.addEventListener('scroll', () => {
    if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 600) loadNextPage();
  });
})();

// ===== Init =====
async function init() {
  lucide.createIcons();
  setTheme(localStorage.getItem('theme') || 'dark');
  AOS.refresh();
  if (document.getElementById('testimonialTrack')) {
    testimonialInterval = setInterval(() => goToTestimonial(testimonialIndex + 1), 4000);
  }
  await loadCart();
  await loadWishlist();
}
init();
