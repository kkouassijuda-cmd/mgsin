// Page « Finaliser la commande » : affiche l'adresse et le paiement seulement pour une livraison.
(function () {
  var formulaire = document.getElementById("formulaire-commande");
  if (!formulaire) return;

  function appliquer() {
    var choisi = formulaire.querySelector('input[name="mode"]:checked');
    var mode = choisi ? choisi.value : "retrait";
    formulaire.classList.toggle("mode-retrait", mode === "retrait");
    formulaire.classList.toggle("mode-livraison", mode === "livraison");
  }

  formulaire.addEventListener("change", function (e) {
    if (e.target.name === "mode") appliquer();
  });
  appliquer();
})();
