// Suivi en temps réel côté client : met à jour une zone de la page sans la recharger.
// Chaque élément portant data-actualiser="<url>" est rechargé toutes les data-secondes
// secondes ; s'il a changé, il est remplacé et brièvement mis en évidence.
(function () {
  var zones = document.querySelectorAll("[data-actualiser]");

  zones.forEach(function (zone) {
    var url = zone.dataset.actualiser;
    var secondes = parseInt(zone.dataset.secondes, 10) || 10;
    var dernier = zone.innerHTML.trim();
    var minuteur = null;

    function verifier() {
      if (document.hidden) return;
      fetch(url, { headers: { "X-Requested-With": "fetch" }, credentials: "same-origin", cache: "no-store" })
        .then(function (reponse) {
          if (reponse.redirected || !reponse.ok) throw new Error("session");
          return reponse.text();
        })
        .then(function (html) {
          html = html.trim();
          if (html === dernier) return;
          dernier = html;
          zone.innerHTML = html;
          zone.classList.remove("zone--mise-a-jour");
          void zone.offsetWidth; // relance l'animation
          zone.classList.add("zone--mise-a-jour");
        })
        .catch(function () {
          clearInterval(minuteur); // session expirée ou erreur : on arrête sans casser la page
        });
    }

    minuteur = setInterval(verifier, secondes * 1000);
    document.addEventListener("visibilitychange", function () {
      if (!document.hidden) verifier();
    });
  });
})();
