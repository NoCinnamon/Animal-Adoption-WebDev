const API = location.hostname
  ? location.protocol + "//" + location.hostname + ":8000"
  : "http://127.0.0.1:8000";

function addPreview(list, animal) {
  const item = document.createElement("li");

  const link = document.createElement("a");
  link.href = "animals.html";

  if (animal.image) {
    const image = document.createElement("img");
    image.src = animal.image;
    image.alt = animal.name;
    link.appendChild(image);
  }

  const card = document.createElement("div");
  card.className = "preview-card";

  const name = document.createElement("h3");
  name.className = "preview-name";
  name.textContent = animal.name;

  const meta = document.createElement("p");
  meta.className = "preview-meta";

  const age = document.createElement("span");
  age.append("Age ");
  const ageValue = document.createElement("span");
  ageValue.textContent = animal.age;
  age.appendChild(ageValue);

  const gender = document.createElement("span");
  // gender.append("Gender ");
  const genderValue = document.createElement("span");
  genderValue.textContent = animal.gender;
  gender.appendChild(genderValue);

  meta.append(age, gender);
  card.append(name, meta);
  item.append(link, card);
  list.appendChild(item);
}

function fillPreviews(animals) {
  const list = document.querySelector("#animal-preview");
  list.replaceChildren();
  const available = animals.filter((animal) => animal.status === "Available");
  available.slice(0, 3).forEach((animal) => addPreview(list, animal));
}

fetch(API + "/animals")
  .then((response) => response.json())
  .then(fillPreviews);


