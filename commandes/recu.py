"""Reçu PDF d'une commande, généré côté serveur avec ReportLab."""

from io import BytesIO

from django.conf import settings
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from catalogue.templatetags.fcfa import formater_fcfa

from .models import Mode

BLEU = colors.HexColor("#2E4A62")
JAUNE = colors.HexColor("#F2B400")
GRIS = colors.HexColor("#EEF1F4")


def montant(valeur):
    # La police Helvetica du PDF n'a pas l'espace fine du site : on prend l'espace insécable.
    return formater_fcfa(valeur).replace(" ", " ")


def generer_recu(commande):
    tampon = BytesIO()
    magasin = settings.MAGASIN
    doc = SimpleDocTemplate(
        tampon, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=18 * mm,
        title=f"Reçu {commande.numero}", author=magasin["nom"],
    )
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    titre = ParagraphStyle("titre", parent=styles["Title"], textColor=BLEU, alignment=0, spaceAfter=2)
    numero = ParagraphStyle("numero", parent=normal, fontSize=13, textColor=BLEU)
    petit = ParagraphStyle("petit", parent=normal, fontSize=8, textColor=colors.HexColor("#5B6770"))

    coordonnees = [magasin["adresse"], f"Tél. {magasin['telephone']}" if magasin["telephone"] else ""]
    contenu = [
        Paragraph(magasin["nom"], titre),
        Paragraph(" · ".join(c for c in coordonnees if c), petit),
        Spacer(1, 8 * mm),
        Paragraph(f"<b>REÇU · {commande.numero}</b>", numero),
        Spacer(1, 3 * mm),
    ]

    infos = [
        ["Date", timezone.localtime(commande.date_creation).strftime("%d/%m/%Y à %H:%M")],
        ["Client", f"{commande.client_prenom} {commande.client_nom}"],
        ["Téléphone", commande.client_telephone],
        ["Mode", commande.get_mode_display()],
        ["Paiement", commande.get_paiement_display()],
    ]
    if commande.adresse:
        infos.append(["Adresse", Paragraph(commande.adresse.replace("\n", "<br/>"), normal)])
    tableau_infos = Table(infos, colWidths=[35 * mm, None])
    tableau_infos.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    contenu += [tableau_infos, Spacer(1, 6 * mm)]

    lignes = [["Réf.", "Désignation", "Qté", "Prix unitaire", "Montant"]]
    for l in commande.lignes.all():
        lignes.append([
            l.ref, Paragraph(l.nom, normal), str(l.quantite),
            montant(l.prix_unitaire), montant(l.sous_total),
        ])
    lignes.append(["", "", "", "TOTAL", montant(commande.total_fcfa)])
    tableau = Table(lignes, colWidths=[25 * mm, None, 14 * mm, 32 * mm, 32 * mm], repeatRows=1)
    tableau.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLEU),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, GRIS]),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEABOVE", (0, -1), (-1, -1), 1.5, JAUNE),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    contenu += [tableau, Spacer(1, 8 * mm)]

    if commande.mode == Mode.RETRAIT:
        horaires = f" Horaires : {magasin['horaires']}." if magasin["horaires"] else ""
        contenu.append(Paragraph(f"À présenter au magasin pour le retrait et le paiement.{horaires}", petit))
    contenu.append(Paragraph("Merci pour votre confiance.", petit))

    doc.build(contenu)
    return tampon.getvalue()
