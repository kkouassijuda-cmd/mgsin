// Rafraîchit les pages de suivi (statuts des commandes) à intervalle régulier.
// Activé par l'attribut data-rafraichir="<secondes>" sur <body>.
// Ne recharge pas si l'utilisateur est en train de saisir quelque chose.
(function () {
  var secondes = parseInt(document.body.dataset.rafraichir, 10);
  if (!secondes || secondes < 5) return;

  var saisieEnCours = false;
  document.addEventListener("input", function () { saisieEnCours = true; });

  setInterval(function () {
    var actif = document.activeElement;
    var champActif = actif && /^(INPUT|TEXTAREA|SELECT)$/.test(actif.tagName);
    var detailsOuvert = document.querySelector("details[open]");
    if (document.hidden || saisieEnCours || champActif || detailsOuvert) return;
    window.location.reload();
  }, secondes * 1000);
})();
