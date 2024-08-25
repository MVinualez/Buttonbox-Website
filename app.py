from flask import Flask, request, send_file, jsonify, url_for
import os
import subprocess

app = Flask(__name__)

@app.route('/')
def index():
    return send_file('templates/index.html')

@app.route('/compile', methods=['POST'])
def compile_code():
    board = request.form['board']
    led_pin = request.form['led_pin']

    # Code source à modifier en fonction des paramètres de l'utilisateur
    code_template = f"""
    #include <Arduino.h>

    void setup() {{
      pinMode({led_pin}, OUTPUT);
    }}

    void loop() {{
      digitalWrite({led_pin}, HIGH);
      delay(1000);
      digitalWrite({led_pin}, LOW);
      delay(1000);
    }}
    """

    # Écriture du code dans un fichier temporaire
    src_path = "src/main.cpp"
    with open(src_path, "w") as f:
        f.write(code_template)

    # Sélection du bon environnement PlatformIO selon le type de carte
    if board == "arduino":
        env = "micro"
    elif board == "esp32":
        env = "esp32dev"
    else:
        return jsonify({"success": False, "error": "Carte non supportée"}), 400

    # Exécution de PlatformIO pour compiler le code
    try:
        subprocess.run(["platformio", "run", "-e", env], check=True)
    except subprocess.CalledProcessError:
        return jsonify({"success": False, "error": "Erreur lors de la compilation"}), 500

    # Chemin du fichier .bin généré
    bin_path = f".pio/build/{env}/firmware.bin"

    if os.path.exists(bin_path):
        # Générer l'URL de téléchargement
        download_url = url_for('download', env=env)
        return jsonify({"success": True, "download_url": download_url})
    else:
        return jsonify({"success": False, "error": "Fichier .bin non trouvé"}), 500

@app.route('/download/<env>')
def download(env):
    bin_path = f".pio/build/{env}/firmware.bin"
    if os.path.exists(bin_path):
        return send_file(bin_path, as_attachment=True)
    else:
        return "Fichier introuvable", 404

if __name__ == '__main__':
    app.run(debug=True)
