// Autocomplete logic
const input = document.getElementById('query');
const dropdown = document.getElementById('autocomplete-dropdown');

let lastTerm = "";
input.addEventListener('input', async function (e) {
    let val = e.target.value.trim();
    lastTerm = val;
    if (val.length < 2) {
        dropdown.style.display = 'none';
        return;
    }
    const resp = await fetch('/autocomplete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: 'query=' + encodeURIComponent(val)
    });
    const suggestions = await resp.json();

    dropdown.innerHTML = '';
    if (suggestions.length === 0) {
        dropdown.style.display = 'none';
        return;
    }
    suggestions.forEach(s => {
        const li = document.createElement('li');
        li.className = "dropdown-item";
        li.innerHTML = `<strong>${s.name || ""}</strong> <small class="text-muted">${s.category || ""}</small>`;
        li.style.cursor = "pointer";
        li.onclick = () => {
            input.value = s.name;
            dropdown.style.display = 'none';
            input.form.submit(); //submit search
        };
        dropdown.appendChild(li);
    });
    dropdown.style.display = 'block';
});
//hide dropdown on click outside i.e. not on input(searchbox) or dropdown
document.addEventListener('click', function (event) {
    if (!input.contains(event.target) && !dropdown.contains(event.target)) {
        dropdown.style.display = 'none';
    }
});

// up/down arrrow key navigation
input.addEventListener('keydown', function (e) {
    const items = dropdown.querySelectorAll('.dropdown-item');
    let idx = Array.from(items).findIndex(item => item.classList.contains('active'));
    if (e.key === "ArrowDown") {
        if (idx < items.length - 1) idx++;
        else idx = 0;
        items.forEach(item => item.classList.remove('active'));
        if (items[idx]) {
            items[idx].classList.add('active');
            items[idx].scrollIntoView({ block: 'nearest' });
        }
        e.preventDefault();
    } else if (e.key === "ArrowUp") {
        if (idx > 0) idx--;
        else idx = items.length - 1;
        items.forEach(item => item.classList.remove('active'));
        if (items[idx]) {
            items[idx].classList.add('active');
            items[idx].scrollIntoView({ block: 'nearest' });
        }
        e.preventDefault();
    } else if (e.key === "Enter" && idx !== -1) {
        items[idx].click();
        e.preventDefault();
    }
}
);