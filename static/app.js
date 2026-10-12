/**
 * CineMithresh - Core Application Engine & State Management
 */

// ==========================================
// Media / CDN Configuration
// ==========================================
// All movie posters, backdrops and brand assets are served from a configurable
// origin. For local development this is the built-in '/static/media' folder
// (files live in static/media/). For production, set this to your bucket/CDN
// origin, e.g. 'https://dxxxxxxxx.cloudfront.net'. Leave as '' only if you
// intentionally want the old './<name>' local fallback.
// NOTE: keep this value in sync with MEDIA_BASE_URL in config.py / .env.
const MEDIA_BASE_URL = '/static/media';

// Inline SVG shown when an external image fails to load (e.g. rotted URL).
const MEDIA_PLACEHOLDER = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='450'%3E%3Crect width='100%25' height='100%25' fill='%23131a2b'/%3E%3Ctext x='50%25' y='52%25' fill='%2364748b' font-size='20' text-anchor='middle' font-family='sans-serif'%3ENo Image%3C/text%3E%3C/svg%3E";

// CDN-only mode: when true, refuse the local './<name>' fallback and show the
// placeholder instead. Enable once every asset is hosted externally.
const MEDIA_REQUIRE_CDN = false;

function mediaUrl(name) {
  if (!name) return name;
  if (/^(https?:)?\/\//i.test(name) || name.startsWith('data:')) return name;
  const base = (MEDIA_BASE_URL || '').replace(/\/+$/, '');
  // Already resolved with the configured base — leave untouched (idempotent).
  if (base && (name === base || name.startsWith(base + '/'))) return name;
  // Root-relative path with no base configured — already servable.
  if (!base && name.startsWith('/')) return name;
  const clean = name.replace(/^\.?\//, '');
  if (base) return `${base}/${clean}`;
  if (MEDIA_REQUIRE_CDN) {
    console.error(`[CineMithresh] MEDIA_BASE_URL is not set but MEDIA_REQUIRE_CDN is on; refusing local fallback for "${name}".`);
    return MEDIA_PLACEHOLDER;
  }
  return `./${clean}`;
}

function mediaFallback(img) {
  img.onerror = null;
  img.src = MEDIA_PLACEHOLDER;
}

// Movie Database - Expanded with New Arrivals & Trending Blockbusters
const MOVIES_DATABASE = [
  // Trending Pan-Indian & Global Blockbusters
  {
    id: 'pushpa-2',
    title: 'Pushpa 2: The Rule',
    genre: 'Action / Crime Thriller',
    language: 'Telugu / Tamil / Hindi',
    rating: 8.9,
    votes: '110K',
    duration: '3h 15m',
    certificate: 'UA 16+',
    poster: './pushpa_2.jpg',
    backdrop: './pushpa_2.jpg',
    synopsis: 'Pushpa Raj asserts his iron-fisted dominion over the red sanders smuggling syndicate while facing the vengeful wrath of SP Bhanwar Singh Shekhawat in an explosive showdown.',
    cast: 'Allu Arjun, Rashmika Mandanna, Fahadh Faasil, Sunil',
    director: 'Sukumar',
    trailerUrl: 'https://www.youtube.com/embed/g3JUbgOHgdw',
    formats: ['IMAX', '4DX', 'Dolby Atmos 7.1'],
    status: 'now_showing'
  },
  {
    id: 'deadpool-wolverine',
    title: 'Deadpool & Wolverine',
    genre: 'Action / Comedy / Superhero',
    language: 'English / Tamil / Hindi',
    rating: 8.6,
    votes: '145K',
    duration: '2h 08m',
    certificate: 'A',
    poster: './deadpool_wolverine.jpg',
    backdrop: './deadpool_wolverine.jpg',
    synopsis: 'The Time Variance Authority pulls Wade Wilson from his peaceful civilian life, uniting him with a reluctant, battle-hardened Wolverine to save his home universe.',
    cast: 'Ryan Reynolds, Hugh Jackman, Emma Corrin, Matthew Macfadyen',
    director: 'Shawn Levy',
    trailerUrl: 'https://www.youtube.com/embed/73_1biulkYk',
    formats: ['IMAX 3D', '4DX', 'Dolby Atmos'],
    status: 'now_showing'
  },
  {
    id: 'coolie',
    title: 'Coolie',
    genre: 'Action / Crime Thriller',
    language: 'Tamil / Telugu / Hindi',
    rating: 8.8,
    votes: '75.6K',
    duration: '2h 45m',
    certificate: 'UA',
    poster: './coolie_movie.jpg',
    backdrop: './coolie_movie.jpg',
    synopsis: 'Superstar Rajinikanth takes on a ruthless gold smuggling cartel with unmatched swagger, razor-sharp action sequences, and high-voltage Anirudh background score.',
    cast: 'Rajinikanth, Nagarjuna, Soubin Shahir, Shruti Haasan, Upendra',
    director: 'Lokesh Kanagaraj',
    trailerUrl: 'https://www.youtube.com/embed/qLcx3hL1i1A',
    formats: ['IMAX', 'Dolby Atmos 7.1', '4K Laser'],
    status: 'now_showing'
  },
  {
    id: 'goat',
    title: 'The Greatest of All Time (GOAT)',
    genre: 'Action / Sci-Fi Thriller',
    language: 'Tamil / Telugu / Hindi',
    rating: 8.3,
    votes: '84.2K',
    duration: '2h 59m',
    certificate: 'UA 13+',
    poster: './goat_movie.jpg',
    backdrop: './goat_movie.jpg',
    synopsis: 'An elite hostage negotiator and field operative of the Special Anti-Terrorist Squad confronts an enigmatic clone adversary tied to a clandestine mission.',
    cast: 'Thalapathy Vijay, Prashanth, Prabhu Deva, Sneha, Meenakshi Chaudhary',
    director: 'Venkat Prabhu',
    trailerUrl: 'https://www.youtube.com/embed/jxCRlebieWc',
    formats: ['IMAX', 'Dolby Atmos 7.1', '2D'],
    status: 'now_showing'
  },
  {
    id: 'kalki-2898',
    title: 'Kalki 2898 AD',
    genre: 'Sci-Fi / Epic Fantasy',
    language: 'Telugu / Tamil / Hindi',
    rating: 8.7,
    votes: '98.5K',
    duration: '3h 01m',
    certificate: 'UA',
    poster: './kalki_2898.jpg',
    backdrop: './kalki_2898.jpg',
    synopsis: 'In a dystopian post-apocalyptic future ruled by Supreme Yaskin, the legendary Ashwatthama awakens to protect the carrier of the divine tenth avatar of Vishnu.',
    cast: 'Prabhas, Amitabh Bachchan, Kamal Haasan, Deepika Padukone',
    director: 'Nag Ashwin',
    trailerUrl: 'https://www.youtube.com/embed/y1-w1pU_S8o',
    formats: ['IMAX 3D', 'Dolby Atmos', '4K Laser'],
    status: 'now_showing'
  },

  // User-Added New Arrivals
  {
    id: 'spider-man',
    title: 'Spider-Man: Brand New Day',
    genre: 'Action / Sci-Fi / Superhero',
    language: 'English / Tamil / Hindi',
    rating: 8.8,
    votes: '68.4K',
    duration: '2h 18m',
    certificate: 'UA 13+',
    poster: './spider_man.jpg',
    backdrop: './spider_man.jpg',
    synopsis: 'Peter Parker embarks on a high-stakes adventure swinging through New York City as he confronts emerging threats and protects those who matter most.',
    cast: 'Tom Holland, Zendaya, Jacob Batalon',
    director: 'Destin Daniel Cretton',
    trailerUrl: 'https://www.youtube.com/embed/rt-2cxAiGoI',
    formats: ['IMAX 3D', '4DX', 'Dolby Atmos'],
    status: 'now_showing'
  },
  {
    id: 'demon-slayer',
    title: 'Demon Slayer: Infinity Castle I',
    genre: 'Anime / Action / Fantasy',
    language: 'Japanese / English / Hindi',
    rating: 9.1,
    votes: '92.3K',
    duration: '2h 10m',
    certificate: 'UA 16+',
    poster: './demon_slayer.jpg',
    backdrop: './demon_slayer.jpg',
    synopsis: 'Tanjiro Kamado, the Hashira, and the Demon Slayer Corps plunge headlong into the shifting multidimensional fortress of the Infinity Castle for the ultimate battle against Muzan Kibutsuji.',
    cast: 'Natsuki Hanae, Akari Kito, Hiro Shimono, Takahiro Sakurai',
    director: 'Haruo Sotozaki',
    trailerUrl: 'https://www.youtube.com/embed/1Q_pUo1-zZc',
    formats: ['4K Laser', 'Dolby Atmos 7.1', 'IMAX'],
    status: 'now_showing'
  },
  {
    id: 'viswanath-and-sons',
    title: 'Viswanath & Sons',
    genre: 'Family Drama / Emotional Thriller',
    language: 'Tamil / Telugu',
    rating: 8.5,
    votes: '33.8K',
    duration: '2h 30m',
    certificate: 'U',
    poster: './viswanath_and_sons.jpg',
    backdrop: './viswanath_and_sons.jpg',
    synopsis: 'An intense London-to-Tamil Nadu journey tracing three generations of familial bonds, corporate legacy conflicts, and heartfelt emotional reconciliations.',
    cast: 'Suriya, Pooja Hegde, Prakash Raj, Nassar',
    director: 'Venky Atluri',
    trailerUrl: 'https://www.youtube.com/embed/Z0oY3i5YdKw',
    formats: ['2D', 'Dolby Atmos 7.1', '4K Laser'],
    status: 'now_showing'
  },
  {
    id: 'vvan',
    title: 'VVAN: Force of the Forrest',
    genre: 'Mythological Thriller / Action',
    language: 'Hindi / Tamil / Telugu',
    rating: 8.4,
    votes: '24.1K',
    duration: '2h 22m',
    certificate: 'UA',
    poster: './vvan.jpg',
    backdrop: './vvan.jpg',
    synopsis: 'A mystical forest steeped in primeval folklore awakens when encroachers ignite the wrath of ancient guardians defending a sacred temple of flames.',
    cast: 'Sidharth Malhotra, Tamannaah Bhatia, Sara Ali Khan',
    director: 'Deepak Mishra',
    trailerUrl: 'https://www.youtube.com/embed/9G3eW-n5jZc',
    formats: ['2D', 'Dolby Atmos 7.1'],
    status: 'now_showing'
  },
  {
    id: 'the-paradise',
    title: 'The Paradise',
    genre: 'Action / Period Drama',
    language: 'Telugu / Tamil / Hindi',
    rating: 8.6,
    votes: '39.7K',
    duration: '2h 35m',
    certificate: 'A',
    poster: './paradise.jpg',
    backdrop: './paradise.jpg',
    synopsis: 'Natural Star Nani stars as a fierce tribal champion waging a war of retribution against feudal exploiters in an uncompromising, raw period action spectacle.',
    cast: 'Nani, Janhvi Kapoor, Shine Tom Chacko',
    director: 'Srikanth Odela',
    trailerUrl: 'https://www.youtube.com/embed/K8v9v-Y5t78',
    formats: ['2D', 'Dolby Atmos 7.1'],
    status: 'now_showing'
  },
  {
    id: 'agatha',
    title: 'Agatha',
    genre: 'Supernatural Horror / Mystery',
    language: 'Telugu / Tamil',
    rating: 7.9,
    votes: '15.6K',
    duration: '2h 08m',
    certificate: 'A',
    poster: './agatha.jpg',
    backdrop: './agatha.jpg',
    synopsis: 'An occult mystery set within a remote heritage mansion uncovers ancient dark rituals, cursed apparitions, and chilling psychological dread.',
    cast: 'Avika Gor, MS Raju, Sumanth Ashwin',
    director: 'MS Raju',
    trailerUrl: 'https://www.youtube.com/embed/H0d6w4lE5bE',
    formats: ['2D', 'Dolby Atmos 7.1'],
    status: 'now_showing'
  },

  // Existing Theatre Favorites
  {
    id: 'godzilla-kong',
    title: 'Godzilla x Kong: The New Empire',
    genre: 'Action / Sci-Fi',
    language: 'English / Tamil / Hindi',
    rating: 8.2,
    votes: '56.1K',
    duration: '1h 55m',
    certificate: 'UA 13+',
    poster: './movie4.jpg',
    backdrop: './movie4.jpg',
    synopsis: 'Kong discovers a hidden tribe of apes in Hollow Earth ruled by the ruthless Skar King, forcing him to team up with the radioactive titan Godzilla.',
    cast: 'Rebecca Hall, Brian Tyree Henry, Dan Stevens, Kaylee Hottle',
    director: 'Adam Wingard',
    trailerUrl: 'https://www.youtube.com/embed/lV1OOlGwExM',
    formats: ['IMAX 3D', '4DX', 'Dolby Atmos'],
    status: 'now_showing'
  },
  {
    id: 'manjummel-boys',
    title: 'Manjummel Boys',
    genre: 'Survival / Thriller',
    language: 'Malayalam / Tamil',
    rating: 8.7,
    votes: '42.9K',
    duration: '2h 15m',
    certificate: 'U',
    poster: './movie2.jpg',
    backdrop: './movie6.jpg',
    synopsis: 'A tight-knit gang of friends from Kochi travel to Kodaikanal for a holiday, where one of them tragically slips into the pitch-black abyss of Guna Caves.',
    cast: 'Soubin Shahir, Sreenath Bhasi, Balu Varghese, Ganapathi',
    director: 'Chidambaram',
    trailerUrl: 'https://www.youtube.com/embed/rQn0_E3u5-0',
    formats: ['2D', '4K Laser', 'Dolby Atmos'],
    status: 'now_showing'
  },
  {
    id: 'aranmanai-4',
    title: 'Aranmanai 4',
    genre: 'Horror / Comedy',
    language: 'Tamil',
    rating: 7.8,
    votes: '18.4K',
    duration: '2h 28m',
    certificate: 'UA',
    poster: './movie1.jpg',
    backdrop: './movie7.jpg',
    synopsis: 'A suspicious death in an isolated village leads an advocate brother to investigate a sinister entity called Baak lurking within a haunted ancestral palace.',
    cast: 'Sundar C, Tamannaah Bhatia, Raashii Khanna, Santhosh Prathap',
    director: 'Sundar C.',
    trailerUrl: 'https://www.youtube.com/embed/5U2f4b4A_l8',
    formats: ['2D', 'Dolby Atmos 7.1'],
    status: 'now_showing'
  },
  {
    id: 'bad-boys',
    title: 'Bad Boys: Ride or Die',
    genre: 'Action / Comedy',
    language: 'English / Tamil',
    rating: 8.0,
    votes: '31.2K',
    duration: '1h 55m',
    certificate: 'A',
    poster: './movie5.jpg',
    backdrop: './movie5.jpg',
    synopsis: 'Miami narcotics detectives Mike Lowrey and Marcus Burnett fight to clear the posthumous name of Captain Conrad Howard when he is falsely accused.',
    cast: 'Will Smith, Martin Lawrence, Vanessa Hudgens, Alexander Ludwig',
    director: 'Adil El Arbi, Bilall Fallah',
    trailerUrl: 'https://www.youtube.com/embed/hRFY_Fesa98',
    formats: ['2D', 'Dolby Atmos 7.1'],
    status: 'now_showing'
  }
];

// Resolve every poster/backdrop into a full external URL (or local fallback).
MOVIES_DATABASE.forEach(movie => {
  movie.poster = mediaUrl(movie.poster);
  movie.backdrop = mediaUrl(movie.backdrop);
});

// Initial Reviews Database
const INITIAL_REVIEWS = [
  {
    id: 'rev-1',
    movieId: 'pushpa-2',
    movieTitle: 'Pushpa 2: The Rule',
    userName: 'Karthik Raja',
    email: 'karthik@example.com',
    rating: 5,
    date: '2026-10-09',
    comment: 'Allu Arjun gives a career-defining performance! The theater erupted with claps. Sound mixing in Dolby Atmos here at CineMithresh was ground shaking!'
  },
  {
    id: 'rev-2',
    movieId: 'demon-slayer',
    movieTitle: 'Demon Slayer: Infinity Castle I',
    userName: 'Ananya Sharma',
    email: 'ananya@example.com',
    rating: 5,
    date: '2026-10-08',
    comment: 'UFOTABLE animation on the big screen is pure art! The Infinity Castle visual depth and acoustic sword clashes felt surreal. 10/10 must watch in IMAX!'
  },
  {
    id: 'rev-3',
    movieId: 'deadpool-wolverine',
    movieTitle: 'Deadpool & Wolverine',
    userName: 'Rohan Mehta',
    email: 'rohan@example.com',
    rating: 5,
    date: '2026-10-08',
    comment: 'Non-stop laughter and insane superhero action. Ryan Reynolds and Hugh Jackman have the best on-screen chemistry of the decade!'
  },
  {
    id: 'rev-4',
    movieId: 'spider-man',
    movieTitle: 'Spider-Man: Brand New Day',
    userName: 'Praveen Kumar',
    email: 'praveen@example.com',
    rating: 5,
    date: '2026-10-07',
    comment: 'Spectacular web-swinging action sequences and great emotional moments. The 4K laser projection clarity was razor sharp.'
  },
  {
    id: 'rev-5',
    movieId: 'viswanath-and-sons',
    movieTitle: 'Viswanath & Sons',
    userName: 'Senthil Nathan',
    email: 'senthil@example.com',
    rating: 5,
    date: '2026-10-06',
    comment: 'Suriya sir delivered an emotionally gripping masterclass. GV Prakash songs blend so beautifully with the storyline.'
  },
  {
    id: 'rev-6',
    movieId: 'manjummel-boys',
    movieTitle: 'Manjummel Boys',
    userName: 'Vijay Shankar',
    email: 'vijay@example.com',
    rating: 5,
    date: '2026-10-05',
    comment: 'Cinematic masterpiece! The tension, the friendship, the climax gave goosebumps. Dolby Atmos audio was mindblowing!'
  }
];

// ==========================================
// Authentication State Management
// ==========================================
// ==========================================
// Authentication State Management & API Bridge
// ==========================================

// Global state cache
let _cachedCsrfToken = '';
let _cachedUser = null;

function getClientSessionId() {
  let sid = sessionStorage.getItem('cine_sessionId');
  if (!sid) {
    sid = 'sid_' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
    sessionStorage.setItem('cine_sessionId', sid);
  }
  return sid;
}

async function getCSRFToken() {
  if (_cachedCsrfToken) return _cachedCsrfToken;

  // Check document cookie
  const match = document.cookie.match(/XSRF-TOKEN=([^;]+)/);
  if (match && match[1]) {
    _cachedCsrfToken = decodeURIComponent(match[1]);
    return _cachedCsrfToken;
  }

  try {
    const res = await fetch('/api/auth/csrf');
    const data = await res.json();
    if (data.success && data.csrf_token) {
      _cachedCsrfToken = data.csrf_token;
      return _cachedCsrfToken;
    }
  } catch (e) {
    console.warn('Failed to fetch CSRF token:', e);
  }
  return '';
}

function getCurrentUser() {
  if (_cachedUser) return _cachedUser;
  const userJson = localStorage.getItem('cine_currentUser');
  if (userJson) {
    try {
      _cachedUser = JSON.parse(userJson);
      return _cachedUser;
    } catch (e) {
      return null;
    }
  }
  return null;
}

function setCurrentUser(user) {
  _cachedUser = user;
  if (user) {
    localStorage.setItem('cine_currentUser', JSON.stringify(user));
  } else {
    localStorage.removeItem('cine_currentUser');
  }
  updateNavUserUI();
}

async function fetchCurrentUser() {
  try {
    const res = await fetch('/api/auth/me');
    const data = await res.json();
    if (data.success && data.authenticated && data.user) {
      setCurrentUser(data.user);
      return data.user;
    } else {
      setCurrentUser(null);
      return null;
    }
  } catch (e) {
    return getCurrentUser();
  }
}

async function logoutUser() {
  try {
    const csrf = await getCSRFToken();
    await fetch('/api/auth/logout', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrf
      }
    });
  } catch (e) {
    console.warn('Logout API error:', e);
  }
  setCurrentUser(null);
  showToast('You have been logged out successfully.', 'info');
  setTimeout(() => {
    window.location.reload();
  }, 500);
}

// ==========================================
// Bookings Storage & API Management
// ==========================================
async function fetchUserBookings() {
  const user = getCurrentUser();
  const url = user && user.email ? `/api/bookings/my-tickets?email=${encodeURIComponent(user.email)}` : '/api/bookings/my-tickets';
  try {
    const res = await fetch(url);
    const data = await res.json();
    if (data.success && Array.isArray(data.bookings)) {
      return data.bookings;
    }
  } catch (e) {
    console.warn('Error fetching bookings:', e);
  }
  return getBookings(); // fallback
}

function getBookings() {
  const data = localStorage.getItem('cine_bookings');
  if (data) {
    try {
      return JSON.parse(data);
    } catch (e) {
      return [];
    }
  }
  return [];
}

function saveBooking(booking) {
  const bookings = getBookings();
  bookings.unshift(booking);
  localStorage.setItem('cine_bookings', JSON.stringify(bookings));
  return booking;
}

// ==========================================
// Reviews Storage & API Management
// ==========================================
async function fetchReviewsFromApi(movieId = 'all') {
  const url = movieId && movieId !== 'all' ? `/api/reviews?movie_id=${encodeURIComponent(movieId)}` : '/api/reviews';
  try {
    const res = await fetch(url);
    const data = await res.json();
    if (data.success && Array.isArray(data.reviews)) {
      return data;
    }
  } catch (e) {
    console.warn('Error fetching reviews:', e);
  }
  return { reviews: getReviews(), average_score: 4.8, total_reviews: 148 };
}

function getReviews() {
  const data = localStorage.getItem('cine_reviews');
  if (data) {
    try {
      return JSON.parse(data);
    } catch (e) {
      return INITIAL_REVIEWS;
    }
  }
  return INITIAL_REVIEWS;
}

function saveReview(review) {
  const reviews = getReviews();
  reviews.unshift(review);
  localStorage.setItem('cine_reviews', JSON.stringify(reviews));
  return review;
}

// ==========================================
// Toast Notifications
// ==========================================
function showToast(message, type = 'info') {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  
  let icon = 'ℹ️';
  if (type === 'success') icon = '✅';
  if (type === 'gold') icon = '⭐';
  if (type === 'error') icon = '⚠️';

  toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ==========================================
// Shared Navigation & Header UI
// ==========================================
function updateNavUserUI() {
  const userBadgeContainer = document.getElementById('navUserSlot');
  if (!userBadgeContainer) return;

  const user = getCurrentUser();
  if (user) {
    const initials = user.name ? user.name.slice(0, 2).toUpperCase() : 'U';
    userBadgeContainer.innerHTML = `
      <div class="user-badge" onclick="openMyBookingsModal()" title="View profile & tickets">
        <div class="user-avatar">${initials}</div>
        <span class="user-name">${user.name.split(' ')[0]}</span>
      </div>
      <button onclick="logoutUser()" class="btn btn-secondary btn-sm" style="padding: 6px 10px;" title="Sign out">
        ✕
      </button>
    `;
  } else {
    userBadgeContainer.innerHTML = `
      <a href="./login.html" class="btn btn-secondary btn-sm">
        Sign In
      </a>
    `;
  }
}

// Mobile Hamburger Toggle
function setupMobileMenu() {
  const toggle = document.querySelector('.mobile-toggle');
  const navMenu = document.querySelector('.nav-menu');
  if (toggle && navMenu) {
    toggle.addEventListener('click', () => {
      navMenu.classList.toggle('open');
    });
  }
}

// ==========================================
// Bookings History Modal
// ==========================================
async function openMyBookingsModal() {
  let modal = document.getElementById('bookingsModal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'bookingsModal';
    modal.className = 'modal-overlay';
    document.body.appendChild(modal);
  }

  modal.innerHTML = `
    <div class="ticket-container" style="max-width: 540px;">
      <div class="ticket-header">
        <div style="display: flex; align-items: center; gap: 10px;">
          <span style="font-size: 1.3rem;">🎟️</span>
          <h3 style="font-size: 1.15rem; margin: 0; color: #fff;">My Movie Tickets</h3>
        </div>
        <button onclick="closeModal('bookingsModal')" style="background:none; border:none; color:#fff; font-size:1.4rem; cursor:pointer;">&times;</button>
      </div>
      <div class="ticket-body" style="text-align: center; padding: 30px;">
        <div style="font-size: 1.5rem; margin-bottom: 8px;">⏳</div>
        <div>Loading your movie bookings from database...</div>
      </div>
    </div>
  `;
  modal.classList.add('active');

  const bookings = await fetchUserBookings();
  const user = getCurrentUser();

  let bookingsHtml = '';
  if (!bookings || bookings.length === 0) {
    bookingsHtml = `
      <div style="text-align: center; padding: 40px 20px; color: var(--text-muted);">
        <div style="font-size: 3rem; margin-bottom: 12px;">🎟️</div>
        <h3>No Bookings Yet</h3>
        <p style="margin-top: 6px; font-size: 0.9rem;">Ready for an unforgettable movie experience?</p>
        <a href="./booking.html" class="btn btn-primary btn-sm" style="margin-top: 18px;">Book Your Tickets Now</a>
      </div>
    `;
  } else {
    bookingsHtml = `
      <div style="max-height: 400px; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; padding-right: 4px;">
        ${bookings.map(b => `
          <div style="background: rgba(255,255,255,0.04); border: 1px solid var(--border-light); border-radius: var(--radius-md); padding: 16px; display: flex; justify-content: space-between; align-items: center; gap: 16px;">
            <div>
              <div style="font-size: 0.75rem; color: var(--accent-gold); font-weight: 700; letter-spacing: 1px;">BOOKING #${b.bookingId}</div>
              <h4 style="margin: 4px 0; font-size: 1.1rem; color: #fff;">${b.movieTitle}</h4>
              <div style="font-size: 0.82rem; color: var(--text-secondary);">
                <span>${b.showDate} • ${b.showTime}</span> | <span>${b.theater}</span>
              </div>
              <div style="font-size: 0.82rem; color: #cbd5e1; margin-top: 4px;">
                <strong>Seats:</strong> <span style="color: var(--accent-primary); font-weight: 700;">${Array.isArray(b.seats) ? b.seats.join(', ') : b.seats}</span> (${b.seatCount || (Array.isArray(b.seats) ? b.seats.length : 1)} seats)
              </div>
            </div>
            <div style="text-align: right;">
              <div style="font-size: 1.2rem; font-weight: 800; color: var(--accent-gold);">₹${b.totalAmount}</div>
              <button onclick="displayTicketModal('${b.bookingId}')" class="btn btn-secondary btn-sm" style="margin-top: 8px;">
                View Ticket
              </button>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }

  modal.innerHTML = `
    <div class="ticket-container" style="max-width: 540px;">
      <div class="ticket-header">
        <div style="display: flex; align-items: center; gap: 10px;">
          <span style="font-size: 1.3rem;">🎟️</span>
          <h3 style="font-size: 1.15rem; margin: 0; color: #fff;">My Movie Tickets</h3>
        </div>
        <button onclick="closeModal('bookingsModal')" style="background:none; border:none; color:#fff; font-size:1.4rem; cursor:pointer;">&times;</button>
      </div>
      <div class="ticket-body">
        ${user ? `<div style="margin-bottom: 16px; font-size: 0.88rem; color: var(--text-secondary);">Bookings registered under <strong>${user.name}</strong> (${user.email})</div>` : ''}
        ${bookingsHtml}
      </div>
    </div>
  `;
}

async function displayTicketModal(bookingId) {
  let modal = document.getElementById('ticketModal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'ticketModal';
    modal.className = 'modal-overlay';
    document.body.appendChild(modal);
  }

  let b = null;
  try {
    const res = await fetch(`/api/tickets/${encodeURIComponent(bookingId)}`);
    const data = await res.json();
    if (data.success && data.ticket) {
      b = data.ticket;
    }
  } catch (e) {
    console.warn('Error fetching ticket detail:', e);
  }

  if (!b) {
    const bookings = getBookings();
    b = bookings.find(item => item.bookingId === bookingId) || bookings[0];
  }
  if (!b) return;

  const seatsDisplay = Array.isArray(b.seats) ? b.seats.join(', ') : b.seats;

  modal.innerHTML = `
    <div class="ticket-container" id="printableTicket">
      <div class="ticket-header">
        <div style="display: flex; align-items: center; gap: 8px;">
          <img src="${mediaUrl('logo1.jpg')}" onerror="mediaFallback(this)" style="height: 28px; border-radius: 4px;" alt="Logo">
          <span style="font-weight: 800; font-size: 1.1rem; letter-spacing: 0.5px;">CINEMITHRESH</span>
        </div>
        <span class="ticket-badge">CONFIRMED</span>
      </div>

      <div class="ticket-body">
        <div style="font-size: 0.72rem; color: var(--accent-gold); font-weight: 700; letter-spacing: 1px; text-transform: uppercase;">M-TICKET / ADMIT PASS</div>
        <h2 class="ticket-movie-title">${b.movieTitle}</h2>
        <div style="font-size: 0.82rem; color: var(--text-secondary); margin-bottom: 16px;">
          ${b.theater} • Dolby Atmos 7.1
        </div>

        <div class="ticket-grid">
          <div class="ticket-field">
            <label>Show Date</label>
            <span>${b.showDate}</span>
          </div>
          <div class="ticket-field">
            <label>Show Time</label>
            <span>${b.showTime}</span>
          </div>
          <div class="ticket-field">
            <label>Seats Booked</label>
            <span style="color: var(--accent-primary); font-weight: 700;">${seatsDisplay}</span>
          </div>
          <div class="ticket-field">
            <label>Total Paid</label>
            <span style="color: var(--accent-gold); font-weight: 700;">₹${b.totalAmount}</span>
          </div>
          <div class="ticket-field">
            <label>Customer</label>
            <span>${b.customerName || 'Guest'}</span>
          </div>
          <div class="ticket-field">
            <label>Booking ID</label>
            <span>${b.bookingId}</span>
          </div>
        </div>
      </div>

      <div class="ticket-perforation">
        <div class="perforation-line"></div>
      </div>

      <div class="ticket-barcode-area">
        <svg class="barcode-svg" viewBox="0 0 200 40" preserveAspectRatio="none">
          <line x1="5" y1="0" x2="5" y2="40" stroke="#fff" stroke-width="3" />
          <line x1="12" y1="0" x2="12" y2="40" stroke="#fff" stroke-width="1.5" />
          <line x1="18" y1="0" x2="18" y2="40" stroke="#fff" stroke-width="4" />
          <line x1="26" y1="0" x2="26" y2="40" stroke="#fff" stroke-width="2" />
          <line x1="33" y1="0" x2="33" y2="40" stroke="#fff" stroke-width="1" />
          <line x1="40" y1="0" x2="40" y2="40" stroke="#fff" stroke-width="5" />
          <line x1="50" y1="0" x2="50" y2="40" stroke="#fff" stroke-width="2" />
          <line x1="56" y1="0" x2="56" y2="40" stroke="#fff" stroke-width="3.5" />
          <line x1="64" y1="0" x2="64" y2="40" stroke="#fff" stroke-width="1.5" />
          <line x1="72" y1="0" x2="72" y2="40" stroke="#fff" stroke-width="4" />
          <line x1="82" y1="0" x2="82" y2="40" stroke="#fff" stroke-width="2" />
          <line x1="90" y1="0" x2="90" y2="40" stroke="#fff" stroke-width="3" />
          <line x1="98" y1="0" x2="98" y2="40" stroke="#fff" stroke-width="1.5" />
          <line x1="108" y1="0" x2="108" y2="40" stroke="#fff" stroke-width="5" />
          <line x1="118" y1="0" x2="118" y2="40" stroke="#fff" stroke-width="2" />
          <line x1="126" y1="0" x2="126" y2="40" stroke="#fff" stroke-width="4" />
          <line x1="134" y1="0" x2="134" y2="40" stroke="#fff" stroke-width="1.5" />
          <line x1="142" y1="0" x2="142" y2="40" stroke="#fff" stroke-width="3" />
          <line x1="152" y1="0" x2="152" y2="40" stroke="#fff" stroke-width="2" />
          <line x1="160" y1="0" x2="160" y2="40" stroke="#fff" stroke-width="4.5" />
          <line x1="172" y1="0" x2="172" y2="40" stroke="#fff" stroke-width="2" />
          <line x1="180" y1="0" x2="180" y2="40" stroke="#fff" stroke-width="3" />
          <line x1="190" y1="0" x2="190" y2="40" stroke="#fff" stroke-width="4" />
        </svg>
        <div class="booking-code">${b.bookingId} • VERIFIED IN DATABASE</div>
        
        <div style="margin-top: 18px; display: flex; gap: 10px; justify-content: center;">
          <button onclick="window.print()" class="btn btn-gold btn-sm">🖨️ Print Ticket</button>
          <button onclick="closeModal('ticketModal')" class="btn btn-secondary btn-sm">Close</button>
        </div>
      </div>
    </div>
  `;

  modal.classList.add('active');
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove('active');
}

// Trailer Modal
function openTrailerModal(movieTitle, trailerUrl) {
  let modal = document.getElementById('trailerModal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'trailerModal';
    modal.className = 'modal-overlay';
    document.body.appendChild(modal);
  }

  modal.innerHTML = `
    <div style="background: #0d1222; border: 1px solid var(--border-light); border-radius: var(--radius-lg); width: 90%; max-width: 800px; overflow: hidden; box-shadow: var(--shadow-lg);">
      <div style="padding: 16px 24px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-light);">
        <h3 style="font-size: 1.15rem; color: #fff;">${movieTitle} - Official Trailer</h3>
        <button onclick="closeModal('trailerModal')" style="background: none; border: none; color: #fff; font-size: 1.5rem; cursor: pointer;">&times;</button>
      </div>
      <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden;">
        <iframe src="${trailerUrl}?autoplay=1" style="position: absolute; top:0; left: 0; width: 100%; height: 100%; border: 0;" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
      </div>
    </div>
  `;
  modal.classList.add('active');
}

// ==========================================
// External Media Source Application
// ==========================================
// Applies CDN URLs to any <img data-media="file.jpg"> and any element with
// data-media-bg="file.jpg". Keeps HTML free of hardcoded media domains.
function applyMediaSources() {
  document.querySelectorAll('img[data-media]').forEach(img => {
    if (!img.getAttribute('src')) {
      img.src = mediaUrl(img.dataset.media);
    }
  });
  document.querySelectorAll('[data-media-bg]').forEach(el => {
    el.style.backgroundImage =
      `linear-gradient(135deg, rgba(229, 9, 20, 0.25) 0%, rgba(9, 12, 21, 0.95) 70%), url("${mediaUrl(el.dataset.mediaBg)}")`;
  });
}

// Setup common page behaviors on DOM load
document.addEventListener('DOMContentLoaded', () => {
  applyMediaSources();
  setupMobileMenu();
  updateNavUserUI();
  fetchCurrentUser().then(() => updateNavUserUI());
  getCSRFToken();
});
