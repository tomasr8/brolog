document.addEventListener("DOMContentLoaded", () => {
  const simple = document.getElementById("animate-simple");
  const images = [...simple.querySelectorAll("img")];
  images.slice(0, -1).forEach((elem) => (elem.style.display = "none"));

  const input = simple.querySelector('input[type="range"]');
  input.addEventListener("input", (e) => {
    console.log(e.target.value);
    const value = parseInt(e.target.value, 10);
    images.forEach((elem, i) => {
      if (i === value - 1) {
        elem.style.display = "block";
      } else {
        elem.style.display = "none";
      }
    });
  });
});

document.addEventListener("DOMContentLoaded", () => {
  const simple = document.getElementById("animate-complex");
  const images = [...simple.querySelectorAll("img")];
  images.slice(0, -1).forEach((elem) => (elem.style.display = "none"));

  const input = simple.querySelector('input[type="range"]');
  input.addEventListener("input", (e) => {
    console.log(e.target.value);
    const value = parseInt(e.target.value, 10);
    images.forEach((elem, i) => {
      if (i === value - 1) {
        elem.style.display = "block";
      } else {
        elem.style.display = "none";
      }
    });
  });
});
