from flask import Flask, render_template_string, request, send_file
import segno
import barcode
from barcode.writer import ImageWriter
from fpdf import FPDF
import io

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Étiquette Colissimo</title>
<style>
body { font-family: Arial; padding: 20px; max-width: 500px; margin: auto; }
input { width: 100%; padding: 10px; margin: 8px 0; font-size: 16px; }
button { padding: 14px; width: 100%; background: #ff6600; color: white; font-size: 18px; border: none; }
h2 { text-align: center; }
</style>
</head>
<body>
<h2>📦 Générateur d'étiquette Colissimo</h2>
<form method="POST">
  Numéro Colissimo : <input name="num" required>
  Nom destinataire : <input name="name" required>
  Adresse : <input name="addr" required>
  Ville : <input name="city" required>
  Code postal : <input name="zip" required>
  Poids (kg) : <input name="weight" required>
  Téléphone (optionnel) : <input name="phone">
  <button type="submit">Générer l'étiquette PDF</button>
</form>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "GET":
        return render_template_string(HTML)

    num = request.form["num"].replace(" ", "")
    name = request.form["name"]
    addr = request.form["addr"]
    city = request.form["city"]
    zipc = request.form["zip"]
    weight = request.form["weight"]
    phone = request.form["phone"]

    payload = (
        f"[)>\x1E01\x1D02\x1D{num}\x1D250\x1D801\x1D{num}"
        f"\x1DGEOP\x1D000000\x1D317\x1D"
        f"\x1D001/001\x1D{weight}KG\x1DN"
        f"\x1D{name}\x1D{addr}\x1D{city}\x1D{zipc}"
    )

    az = segno.helpers.make_aztec(payload)
    az_bytes = io.BytesIO()
    az.save(az_bytes, kind="png", scale=4)
    az_bytes.seek(0)

    code128 = barcode.get("code128", num, writer=ImageWriter())
    barcode_bytes = io.BytesIO()
    code128.write(barcode_bytes)
    barcode_bytes.seek(0)

    pdf = FPDF("P", "mm", (150, 100))
    pdf.add_page()
    pdf.set_auto_page_break(False)

    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(255, 102, 0)
    pdf.cell(0, 12, "Colissimo", ln=True)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 8, f"Numéro : {num}", ln=True)
    pdf.cell(0, 8, f"Poids : {weight} kg", ln=True)
    pdf.ln(3)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "Destinataire :", ln=True)

    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 7, f"{name}\n{addr}\n{zipc} {city}")

    if phone:
        pdf.cell(0, 8, f"Tél : {phone}", ln=True)

    pdf.ln(4)

    az_path = "/mnt/data/aztec.png"
    code_path = "/mnt/data/code128.png"

    with open(az_path, "wb") as f:
        f.write(az_bytes.getvalue())
    with open(code_path, "wb") as f:
        f.write(barcode_bytes.getvalue())

    pdf.image(az_path, x=65, y=10, w=30)
    pdf.image(code_path, x=10, y=75, w=80)

    pdf_bytes = pdf.output(dest="S").encode("latin1")

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        download_name="etiquette_colissimo.pdf",
        as_attachment=True
    )

if __name__ == "__main__":
    app.run()
