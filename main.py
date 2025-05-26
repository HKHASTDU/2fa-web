from flask import Flask, render_template_string, request
import pyotp
import qrcode
import io
import base64

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>2FA Generator - Nguyễn Hoàng Kha</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body { font-family: 'Inter', sans-serif; }
    .code-display { letter-spacing: 0.2em; }
  </style>
</head>
<body class="bg-gradient-to-br from-blue-100 to-purple-200 min-h-screen flex items-center justify-center p-4">
  <div class="bg-white p-8 rounded-3xl shadow-2xl max-w-xl w-full text-center">
    <h1 class="text-3xl font-bold text-blue-600 mb-2">🔐 2FA Generator</h1>
    <p class="text-gray-500 mb-6">Tạo mã 2FA realtime + mã QR</p>

    <form method="get" class="mb-4">
      <input name="secret" placeholder="Nhập secret base32" value="{{ secret }}"
             class="w-full p-3 border border-gray-300 rounded-xl mb-3 text-center focus:ring-2 focus:ring-blue-500" required>
      <button type="submit"
              class="w-full bg-gradient-to-r from-blue-500 to-purple-500 text-white py-2 rounded-xl font-semibold hover:scale-105 transition">
        🔁 Tạo Mã 2FA
      </button>
    </form>

    {% if secret %}
    <div class="mb-4">
      <img src="data:image/png;base64,{{ qr_data }}" alt="QR Code" class="mx-auto mb-2 w-40 h-40 shadow-lg rounded">
      <p class="text-sm text-gray-500">Scan bằng Google Authenticator</p>
    </div>

    <div id="otp-section" class="hidden">
      <div id="code" class="text-5xl font-mono text-gray-900 font-bold code-display mb-2">------</div>
      <div class="w-full bg-gray-300 rounded-full h-2 mb-1">
        <div id="progress" class="bg-green-500 h-2 rounded-full transition-all" style="width: 0%;"></div>
      </div>
      <p class="text-sm text-gray-500">Còn lại <span id="countdown">--</span> giây</p>
    </div>

    <script>
      const secret = "{{ secret }}";
      const section = document.getElementById("otp-section");
      const codeEl = document.getElementById("code");
      const progressEl = document.getElementById("progress");
      const countdownEl = document.getElementById("countdown");

      function base32ToHex(base32) {
        const base32chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";
        let bits = "";
        for (const c of base32.replace(/=+$/, '').toUpperCase()) {
          const val = base32chars.indexOf(c);
          bits += val.toString(2).padStart(5, '0');
        }
        let hex = "";
        for (let i = 0; i + 4 <= bits.length; i += 4) {
          hex += parseInt(bits.substr(i, 4), 2).toString(16);
        }
        return hex;
      }

      function getOTP(secret) {
        const epoch = Math.floor(Date.now() / 1000);
        const step = 30;
        const time = Math.floor(epoch / step);
        const key = base32ToHex(secret);
        const timeHex = time.toString(16).padStart(16, '0');

        const crypto = window.crypto || window.msCrypto;
        const keyBytes = new Uint8Array(key.match(/.{1,2}/g).map(byte => parseInt(byte, 16)));
        const timeBytes = new Uint8Array(timeHex.match(/.{1,2}/g).map(byte => parseInt(byte, 16)));

        return crypto.subtle.importKey("raw", keyBytes, {name: "HMAC", hash: "SHA-1"}, false, ["sign"])
          .then(key => crypto.subtle.sign("HMAC", key, timeBytes))
          .then(signature => {
            const h = new Uint8Array(signature);
            const offset = h[h.length - 1] & 0x0f;
            const code = (h[offset] & 0x7f) << 24 | (h[offset+1] & 0xff) << 16 |
                         (h[offset+2] & 0xff) << 8 | (h[offset+3] & 0xff);
            return (code % 1000000).toString().padStart(6, '0');
          });
      }

      function update() {
        const epoch = Math.floor(Date.now() / 1000);
        const step = 30;
        const remaining = step - (epoch % step);
        const progress = ((step - remaining) / step) * 100;

        countdownEl.textContent = remaining;
        progressEl.style.width = `${progress}%`;

        getOTP(secret).then(code => {
          codeEl.textContent = code;
          section.classList.remove("hidden");
        });
      }

      setInterval(update, 1000);
      update();
    </script>
    {% endif %}

    <footer class="mt-8 text-sm text-gray-400 text-center border-t pt-4">
      © 2025 Nguyễn Hoàng Kha • Made with ❤️ in Vietnam
    </footer>
  </div>
</body>
</html>
"""


@app.route("/")
def index():
    secret = request.args.get("secret", "").strip().replace(" ", "")
    qr_data = None
    if secret:
        # Tạo mã otpauth chuẩn
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(name="user@example.com", issuer_name="2FA Live")
        # Tạo QR
        img = qrcode.make(totp_uri)
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        qr_data = base64.b64encode(buffered.getvalue()).decode()
    return render_template_string(HTML, secret=secret, qr_data=qr_data)

if __name__ == "__main__":
    app.run(debug=True)
