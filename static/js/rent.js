function checkLogin(itemId) {
    fetch('/check_login')
    .then(res => res.json())
    .then(data => {
        if (data.logged_in) {
            window.location.href = '/payment/' + itemId;
        } else {
            window.location.href = '/auth';   // 👈 THIS IS KEY
        }
    });
}