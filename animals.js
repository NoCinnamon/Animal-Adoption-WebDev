const API = location.hostname
  ? location.protocol + "//" + location.hostname + ":8000"
  : "http://127.0.0.1:8000";

let isWorker = false;
const filters = document.querySelector(".animal-filters");
let allAnimals = [];

function showAnimals() {
  const list = document.querySelector("#animal-list");
  list.replaceChildren();
  allAnimals
    .filter((animal) => {
      if (filters.species.value && animal.species !== filters.species.value) {
        return false;
      }
      if (filters.gender.value && animal.gender !== filters.gender.value) {
        return false;
      }
      if (filters.age.value === "young" && Number(animal.age) >= 2) {
        return false;
      }
      if (filters.age.value === "adult" && Number(animal.age) < 2) {
        return false;
      }
      return true;
    })
    .forEach((animal) => addAnimal(list, animal));
}

fetch(API + "/sessions", { credentials: "include" })
  .then((response) => {
    if (response.status !== 200) {
      return null;
    }
    return response.json();
  })
  .then((user) => {
    if (user && user.role === "worker") {
      isWorker = true;
      document.querySelector("#animal-form").hidden = false;
      document.querySelector(".add-button").hidden = false;
    }
    return fetch(API + "/animals");
  })
  .then((response) => response.json())
  .then((animals) => {
    allAnimals = animals;
    showAnimals();
  });

filters.addEventListener("change", showAnimals);
  
function addAnimal(list, animal) {
  const item = document.createElement("li");
  item.className = "animal-row";

  if (animal.image) {
    const image = document.createElement("img");
    image.src = animal.image;
    image.alt = animal.name;
    item.appendChild(image);
  }

  const info = document.createElement("div");
  info.className = "animal-info";

  const name = document.createElement("h2");
  name.textContent = animal.name;

  const meta = document.createElement("p");
  meta.className = "animal-meta";
  meta.textContent = animal.species + " · " + animal.breed + " · " + animal.gender + " · " + animal.age;

  const statusRow = document.createElement("div");
  statusRow.className = "animal-status-row";

  const status = document.createElement("p");
  status.className = "animal-status";
  if (animal.status === "Available") {
    status.classList.add("is-available");
  }
  status.textContent = animal.status;

  const adopt = document.createElement("a");
  adopt.className = "adopt-button";
  adopt.href = "applications.html?animal_id=" + animal.id;
  adopt.textContent = "Adopt me";
  statusRow.append(status, adopt);

  const edit = document.createElement("a")
  edit.className = "edit-button";
  edit.textContent = "Edit";
  edit.href = "#animal-form";
  edit.addEventListener("click", (event) => {
    event.preventDefault();
    fetch(API + "/sessions", { credentials: "include" })
      .then((response) => {
        if (response.status !== 200) {
          return null;
        }
        return response.json();
      })
      .then((user) => {
        if (!user || user.role !== "worker") {
          alert("You do not have permission to edit this animal.");
          return;
        }
        editingId = animal.id;
        editingImage = animal.image || "";
        document.querySelector("#animal-form [name=name]").value = animal.name;
        document.querySelector("#animal-form [name=species]").value = animal.species;
        document.querySelector("#animal-form [name=breed]").value = animal.breed;
        document.querySelector("#animal-form [name=gender]").value = animal.gender;
        document.querySelector("#animal-form [name=age]").value = animal.age;
        document.querySelector("#animal-form [name=description]").value = animal.description;
        document.querySelector("#animal-form [name=status]").value = animal.status;
        document.querySelector("#animal-form").scrollIntoView();
      })
      .catch(() => {
        alert("You do not have permission to edit this animal.");
      });
  });
  

  const remove = document.createElement("button");
  remove.className = "delete-button";
  remove.textContent = "Delete";
  remove.addEventListener("click", () => {
    const yes = confirm("Delete " + animal.name + "?");
    if (yes) {
      fetch(API + "/animals/" + animal.id, { method: "DELETE", credentials: "include" })
        .then((response) => {
          if (response.status === 200) {
            item.remove();
            return;
          }
          alert("You do not have permission to delete this animal.");
        });
    }
  });

  info.append(name, meta, statusRow);
  if (animal.description) {
    const description = document.createElement("p");
    description.className = "animal-description";
    description.textContent = animal.description;
    info.appendChild(description);
  }

  item.appendChild(info);
  list.appendChild(item);
  if (isWorker) {
    info.appendChild(edit);
    info.appendChild(remove);
  }

}

let queuedImagesArray = [],
  editingId = null,                                     // editingId = null => Adding; when edit is not null => Editing
  editingImage = "",
  queuedDiv = document.querySelector(".queued-form"),
  inputDiv = document.querySelector(".input-div"),
  input = document.querySelector(".input-div input");

  // QUEUE IN FRONTEND IMAGES
  input.addEventListener("change", () => {
    const files = input.files
    for (let i =0; i < files.length; i++){
      queuedImagesArray.push(files[i])
    }
    input.value = ""
    displayQueuedImages()
  })

  inputDiv.addEventListener("drop", (e) => {
    e.preventDefault();
    const files = e.dataTransfer.files;
    for(let i=0; i < files.length; i++){
      if (!files[i].type.match("image")) continue
      if(queuedImagesArray.every(image => image.name !== files[i].name))
        queuedImagesArray.push(files[i])
    }
    displayQueuedImages()
  })


function displayQueuedImages(){
  let images = ""
  queuedImagesArray.forEach((image, index) => {
    images += `<div class="image">
                <img src="${URL.createObjectURL(image)}" alt="image">
                <span onclick="deleteQueuedImage(${index})">&times;</span>
              </div>`
  })
  queuedDiv.innerHTML= images;
}

function deleteQueuedImage(index){
  queuedImagesArray.splice(index, 1)
  displayQueuedImages()
}

function addNewAnimal(e) {
  e.preventDefault();

  const sendAnimal = (imagePath) => {
    const animal = {
      name: document.querySelector("#animal-form [name=name]").value,
      species: document.querySelector("#animal-form [name=species]").value,
      breed: document.querySelector("#animal-form [name=breed]").value,
      gender: document.querySelector("#animal-form [name=gender]").value,
      age: document.querySelector("#animal-form [name=age]").value,
      description: document.querySelector("#animal-form [name=description]").value,
      status: document.querySelector("#animal-form [name=status]").value,
      image: imagePath,
    };

    const url = editingId ? API + "/animals/" + editingId : API + "/animals";
    const method = editingId ? "PUT" : "POST";

    fetch(url, {
      method: method,
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(animal),
    })
      .then((response) => {
        if (method === "PUT" && response.status !== 200) {
          alert("You do not have permission to edit this animal.");
          return null;
        }
        return response.json();
      })
      .then((data) => {
        if (!data) {
          return null;
        }
        editingId = null;
        editingImage = "";
        queuedImagesArray = [];
        displayQueuedImages();
        document.querySelector("#animal-form").reset();
        return fetch(API + "/animals");
      })
      .then((response) => {
        if (!response) {
          return null;
        }
        return response.json();
      })
      .then((animals) => {
        if (!animals) {
          return;
        }
        const list = document.querySelector("#animal-list");
        list.replaceChildren();
        animals.forEach((animal) => addAnimal(list, animal));
      });
  };

  if (queuedImagesArray.length === 0) {
    sendAnimal(editingImage);
    return;
  }

  const formData = new FormData();
  queuedImagesArray.forEach((image, index) => {
    formData.append("file[" + index + "]", image);
  });

  fetch(API + "/upload", {
    method: "POST",
    credentials: "include",
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      sendAnimal((data.saved || [])[0] || "");
    });
}
document.querySelector("#animal-form").addEventListener("submit", addNewAnimal);
document.querySelector(".add-button").addEventListener("click", (event) => {
  event.preventDefault();
  fetch(API + "/sessions", { credentials: "include" })
  .then((response) => {
    if (response.status !== 200) {
      return null;
    } 
    return response.json();
  })
  .then((user) => {
    if (!user || user.role !== "worker") {
      alert("You do not have permission to add animal.");
      return;
    }
  editingId = null;
  editingImage = "";
  queuedImagesArray = [];
  displayQueuedImages();
  document.querySelector("#animal-form").reset();
  document.querySelector("#animal-form").scrollIntoView();
  });
});