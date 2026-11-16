const API = location.hostname
  ? location.protocol + "//" + location.hostname + ":8000"
  : "http://127.0.0.1:8000";

const list = document.querySelector("#application-list");
const form = document.querySelector("#application-form");
const notice = document.querySelector("#login-required");

function loadAnimals() {
  const select = form.querySelector("[name=animal_id]");
  fetch(API + "/animals")
    .then((response) => response.json())
    .then((animals) => {
      animals.forEach((animal) => {
        const option = document.createElement("option");
        option.value = animal.id;
        option.textContent = animal.id + " — " + animal.name;
        select.appendChild(option);
      });
      const animalId = new URLSearchParams(window.location.search).get("animal_id");
      if (animalId) {
        select.value = animalId;
      }
    });
}

function addApplication(list, application) {
  const item = document.createElement("li");
  item.textContent =
    application.date + " " +
    application.first_name + " " + application.last_name +
    " applied for " + application.animal_id + " — " + application.animal_name;
  list.appendChild(item);
}

fetch(API + "/sessions", { credentials: "include" })
  .then((response) => {
    if (response.status !== 200) {
      notice.hidden = false;
      return null;
    }
    return response.json();
  })
  .then((user) => {
    if (!user) {
      return null;
    }
    notice.hidden = true;
    list.hidden = false;
    form.hidden = false;
    form.user_name.value = user.first_name + " " + user.last_name;
    loadAnimals();
    return fetch(API + "/applications", { credentials: "include" });
  })
  .then((response) => {
    if (!response) {
      return null;
    }
    return response.json();
  })
  .then((applications) => {
    if (!applications) {
      return;
    }
    applications.forEach((application) => addApplication(list, application));
  });

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const data = {
    animal_id: form.animal_id.value,
    phone: form.phone.value,
    message: form.message.value,
  };
  fetch(API + "/applications", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  }).then((response) => {
    if (response.status === 201) {
      window.location.reload();
    }
  });
});
