import typer
import os
from ollama import chat
from ollama import ChatResponse
import platform

user = os.getlogin()
os_name = platform.system()
home = os.path.expanduser("~")
cwd = os.getcwd()
try:
    file_list = os.listdir(cwd)
except PermissionError:
    file_list = ["<Erişim reddedildi>"]

SYSTEM_PROMPT = f"""Sen bir terminal komutu asistanısın.

Kullanıcının Türkçe yazdığı bir isteği **sadece geçerli ve güvenli bash komutlarına** çeviriyorsun.

🔒 Çok önemli kurallar:
- Sadece komutu yaz.
- Asla açıklama yapma.
- “Komut önerisi”, “önerilen komut” gibi etiketler ekleme.
- Sadece çalıştırılabilir shell komutlarını içeren düz metin döndür.
- Bash dışında başka şey yazma.

📌 Örnek çıktı formatı:

mkdir yeni_klasor  
touch yeni_klasor/main.py

Gibi komutları sadece yaz. Altına açıklama yazma. Kod bloğu veya ``` işareti koyma. Markdown yok. Yorum satırı bile yok.

Eğer bir işlem birden fazla komut gerektiriyorsa, alt alta sırala.

Kullanılabilecek komutlar: mkdir, touch, ls, cd, cp, mv, rm, cat, echo, zip, unzip, tar, find, grep, chmod, chown, curl, wget, python, pip

Türkçe karakterli klasör ve dosya adlarını sadeleştir.

Güvenli olmayan komutlar (örneğin `rm -rf /`) asla kullanma.

[TERMINAL BAĞLAMI]

- Kullanıcı adı: {user}
- İşletim sistemi: {os_name}
- Ev dizini: {home}
- Çalışma dizini: {cwd}
- Çalışma dizinindeki dosyalar: {file_list}


"""
MODEL_NAME = "gemma3n:latest"
bu
EXAMPLES = [{"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "masaüstüne 'deneme' adında bir klasör oluştur"},
            {"role": "assistant", "content": """mkdir ~/Masaüstü/deneme"""},
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "geçerli klasördeki tüm .py dosyalarını listele"},
            {"role": "assistant", "content": """ls *.py"""},
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "test.py dosyasını scripts klasörüne taşı"},
            {"role": "assistant", "content": """mv test.py scripts/"""},
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "yeni bir klasör oluştur ve içine 'main.py' adında bir dosya koy"},
            {"role": "assistant", "content": """mkdir yeni_klasor
touch yeni_klasor/main.py"""},
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "tüm txt dosyalarını zipleyip yedek.zip yap"},
            {"role": "assistant", "content": """zip yedek.zip *.txt"""}]


def check_model(model) -> bool:
    try:
        chat(model)
    except Exception as e:
        print(f"Hata: {e}")
        return False
    return True


def code_assist(prompt: str, model: str, examples: list) -> str:
    messages = examples + [{"role": "user", "content": prompt}]
    response: ChatResponse = chat(model=model, messages=messages)
    return response["message"]["content"]


def main():
    typer.echo("Gemma Terminal Asistanı")
    if not check_model(MODEL_NAME):
        raise typer.Exit(code=1)
    prompt = typer.prompt("Ne yapmak istiyorsun?")
    command = code_assist(prompt, MODEL_NAME, EXAMPLES)
    typer.echo(f"\n🔧 Önerilen komut:\n{command}")


if __name__ == "__main__":
    typer.run(main)