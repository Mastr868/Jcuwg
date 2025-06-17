// منوی همبرگری
const hamburgerMenu = document.getElementById('hamburgerMenu');
const navLinks = document.getElementById('navLinks');

hamburgerMenu.addEventListener('click', () => {
    navLinks.classList.toggle('active');
});

// دکمه انتشار و پاپ‌آپ لاگین
const uploadBtn = document.getElementById('uploadBtn');
const loginPopup = document.getElementById('loginPopup');
const closeLoginPopup = document.getElementById('closeLoginPopup');
const loginLink = document.getElementById('loginLink');

uploadBtn.addEventListener('click', () => {
    loginPopup.style.display = 'flex';
});

loginLink.addEventListener('click', (e) => {
    e.preventDefault();
    loginPopup.style.display = 'flex';
});

closeLoginPopup.addEventListener('click', () => {
    loginPopup.style.display = 'none';
});
