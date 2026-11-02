/* Menu des catégories : une fois ouvert, il reste ouvert d'une page à l'autre
   jusqu'à ce que l'utilisateur le referme (choix mémorisé dans le navigateur). */
(function () {
  var CLE = "categories-ouvert";
  var menu = document.querySelector(".categories");
  if (!menu) return;

  try {
    if (localStorage.getItem(CLE) === "1") menu.open = true;
  } catch (e) { /* stockage indisponible : le menu reste fermé */ }

  menu.addEventListener("toggle", function () {
    try {
      localStorage.setItem(CLE, menu.open ? "1" : "0");
    } catch (e) { /* rien à faire */ }
  });
})();
