import requests
import subprocess
import json
import os
import sys

class TerminalAssistant:
    def __init__(self):
        self.ollama_model = "gemma3n"
        self.ollama_url = "http://localhost:11434/api/generate"
        self.data_science_libraries = "pandas numpy matplotlib seaborn scikit-learn jupyterlab"

    def gather_context(self) -> str:
        # Bu fonksiyon önceki versiyonla aynı
        context_parts = []
        current_dir = os.getcwd()
        context_parts.append(f"Mevcut Dizin: {current_dir}")
        context_parts.append(f"Dizin İçeriği: {', '.join(os.listdir(current_dir)[:10])}")
        if os.path.isdir('.venv'):
            context_parts.append("Sanal Ortam: '.venv' adında bir sanal ortam mevcut.")
        else:
            context_parts.append("Sanal Ortam: Mevcut dizinde sanal ortam bulunmuyor.")
        if not os.path.isdir('.git'):
            context_parts.append("Durum: Bu bir Git deposu değil.")
            return "\n".join(context_parts)
        context_parts.append("Durum: Bu bir Git deposu.")
        branch_result = subprocess.run(['git', 'branch', '--show-current'], capture_output=True, text=True, timeout=5)
        active_branch = "main" # Varsayılan
        if branch_result.returncode == 0 and branch_result.stdout.strip():
            active_branch = branch_result.stdout.strip()
        context_parts.append(f"Aktif Dal: {active_branch}")
        status_result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True, timeout=5)
        if status_result.returncode == 0:
            context_parts.append("Git Durumu: Temiz (kaydedilecek değişiklik yok)." if not status_result.stdout.strip() else "Git Durumu: Kaydedilmemiş değişiklikler var.")
        remote_result = subprocess.run(['git', 'remote', '-v'], capture_output=True, text=True, timeout=5)
        if remote_result.returncode == 0 and 'origin' in remote_result.stdout:
            context_parts.append("Uzak Depo: 'origin' ayarlanmış.")
        else:
            context_parts.append("Uzak Depo: 'origin' ayarlanmamış.")
        return "\n".join(context_parts)

    def get_command_from_gemma(self, user_prompt):
        context = self.gather_context()
        # DEĞİŞTİRİLDİ: Prompt, "mutlaka mesaj sor" kuralını en üste koyacak şekilde yeniden tasarlandı.
        prompt = f"""
Sen son derece dikkatli ve kurallara harfiyen uyan bir terminal asistanısın.

---
BAĞLAM BİLGİSİ:
{context}
---
KULLANICI TALEBİ: {user_prompt}
---

GÖREVİN: Aşağıdaki DÜŞÜNCE SÜRECİ'ni adım adım takip et ve SADECE GEREKLİ KOMUTLARI üret.

---
DÜŞÜNCE SÜRECİ (Bu kısmı sadece kendi içinde analiz et, kullanıcıya gösterme):

1.  **MUTLAK KURAL KONTROLÜ - MESAJ SORMA ZORUNLULUĞU:**
    * Kullanıcı talebinde "kaydet", "mesajla kaydet", "mesaj sorarak yükle", "mesaj belirt" gibi bir ifade var mı?
    * **EVET İSE:** Planım, diğer tüm koşulları (değişiklik olup olmamasını bile) göz ardı ederek, **NE OLURSA OLSUN** `git add .` ve `git commit -m "<COMMIT_MESAJI>"` adımlarını içermek zorundadır. Eğer kullanıcı "gönder" de dediyse sona `git push` ekle. Bu kural diğer tüm mantığı ezer. Planı oluştur ve 3. adıma geç.
    * **HAYIR İSE:** Normal sürece (Adım 2'ye) devam et.

2.  **STANDART SÜREÇ (Mutlak Kural Aktif Değilse):**
    * **Bağlam Kontrolü:** Bağlamda "Git Durumu: Kaydedilmemiş değişiklikler var" yazıyor mu?
    * **Eğer Değişiklik VARSA:** Planım `git add .`, `git commit -m "<COMMIT_MESAJI>"` ve (eğer istendiyse) `git push` içermelidir.
    * **Eğer Değişiklik YOKSA ("Git Durumu: Temiz"):** `git add` ve `git commit` komutlarını KESİNLİKLE üretme. Sadece `git push` gibi başka komutlar istenmişse onları üret. Eğer hiçbir şey yapılamıyorsa, boş yanıt ver.

3.  **SONUÇ:** Oluşturduğun plana göre komutları üret.
---

SADECE KOMUTLAR (Açıklama veya düşünce süreci olmadan, sadece çalıştırılabilir kod):
"""
        payload = {"model": self.ollama_model, "prompt": prompt, "stream": False}
        try:
            print("🧠 Akıllı asistan durumu analiz ediyor ve komut üretiyor...")
            response = requests.post(self.ollama_url, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            raw_command_text = result.get('response', '').strip()
            clean_text = raw_command_text.replace('```', '').replace('`', '').strip()
            commands = [cmd.strip() for cmd in clean_text.split('\n') if cmd.strip()]
            if commands and commands[0].lower() in ['bash', 'sh', 'shell']:
                commands.pop(0)
            if not commands: return None
            return commands[0] if len(commands) == 1 else commands
        except requests.exceptions.RequestException as e:
            print(f"❌ Ollama ile bağlantı hatası: {e}"); return None
        except Exception as e:
            print(f"❌ Beklenmeyen hata: {e}"); return None

    # Kalan tüm fonksiyonlar (is_safe_command, execute_command, vb.) aynı kalabilir.
    def is_safe_command(self, command):
        if not command: return False
        dangerous_patterns = ['rm -rf', 'rm -fr', '> /etc/', 'mv /*']
        for pattern in dangerous_patterns:
            if pattern in command: return False
        safe_commands = ['touch', 'mkdir', 'ls', 'pwd', 'cd', 'cat', 'echo', 'cp', 'mv', 'git', 'pip', 'python3', 'source']
        command_start = command.strip().split()[0]
        if '/' in command_start:
            command_start = command_start.split('/')[-1]
        return command_start in safe_commands

    def execute_command(self, command):
        if not self.is_safe_command(command):
            print(f"⚠️  Güvenlik nedeniyle bu komut çalıştırılamaz: {command}"); return False
        if command.strip().startswith('source '):
            print(f"ℹ️ Sanal ortamı aktive etmek için lütfen bu komutu manuel olarak terminalinizde çalıştırın: {command}")
            return True
        try:
            print(f"🚀 Çalıştırılıyor: {command}")
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=300)
            # Değişiklik olmasa bile commit denemesinden gelen hatayı başarı say
            if "nothing to commit, working tree clean" in result.stderr or "işlenecek bir şey yok, çalışma ağacı temiz" in result.stderr:
                print("ℹ️ Kaydedilecek yeni değişiklik bulunamadı, ancak isteğiniz üzerine commit denendi.")
                return True
            if "Requirement already satisfied" in result.stdout or "Gereksinim zaten karşılandı" in result.stdout:
                print("✅ Kütüphane(ler) zaten yüklü.")
                return True
            if result.returncode == 0:
                print("✅ Komut başarıyla çalıştırıldı!");
                if result.stdout: print(f"📤 Çıktı:\n{result.stdout.strip()}")
                if result.stderr: print(f"ℹ️ Bilgi/Uyarı:\n{result.stderr.strip()}")
            else:
                print(f"❌ Komut hatalı: {result.stderr.strip() or result.stdout.strip()}")
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print("⏱️  Komut zaman aşımına uğradı!"); return False
        except Exception as e:
            print(f"❌ Komut çalıştırılırken hata: {e}"); return False

    def execute_command_sequence(self, commands):
        processed_commands = []
        for command in commands:
            if "<" in command and ">" in command:
                placeholder = command[command.find("<"):command.find(">") + 1]
                try: user_value = input(f"ℹ️ Lütfen '{placeholder}' için bir değer girin: ")
                except EOFError: print("\n❌ Giriş iptal edildi."); return
                final_command = command.replace(placeholder, user_value)
                processed_commands.append(final_command)
            else:
                processed_commands.append(command)
        print("\n--- Çalıştırılacak Komut Dizisi ---")
        for i, cmd in enumerate(processed_commands, 1): print(f"{i}. {cmd}")
        print("---------------------------------")
        try: confirm = input("✅ Bu komut dizisini çalıştırmak istiyor musunuz? (e/h): ").strip().lower()
        except EOFError: confirm = 'h'
        if confirm not in ['e', 'evet', 'yes', 'y']: print("❌ Komut dizisi iptal edildi."); return
        for cmd in processed_commands:
            if not self.execute_command(cmd):
                print(f"❌ Komut '{cmd}' başarısız olduğu için dizi durduruldu."); break

    def run(self):
        print("🤖 Akıllı Veri Bilimci Asistanı v16 (Mutlak Mesaj Sorma Kuralı) başlatıldı!")
        print("💡 Örnek: 'çalışmamı kaydet' veya 'değişiklikleri githuba gönder'")
        print("📁 Mevcut dizin:", os.getcwd()); print("-" * 50)
        while True:
            try:
                user_input = input("\n🎯 Ne yapmak istersin? (çıkış: 'exit'): ").strip()
                if not user_input: continue
                if user_input.lower() in ['exit', 'quit', 'çıkış']: print("👋 Görüşürüz!"); break
                command_or_list = self.get_command_from_gemma(user_input)
                if not command_or_list:
                    print("✅ Yapılacak bir işlem bulunamadı.")
                    continue
                if isinstance(command_or_list, list): self.execute_command_sequence(command_or_list)
                else:
                    command = command_or_list
                    print(f"🔍 Önerilen komut: {command}")
                    confirm = input("✅ Bu komutu çalıştırmak istiyor musunuz? (e/h): ").strip().lower()
                    if confirm in ['e', 'evet', 'yes', 'y']: self.execute_command(command)
                    else: print("❌ Komut iptal edildi.")
            except KeyboardInterrupt:
                print("\n👋 Program sonlandırıldı!"); break
            except Exception as e:
                print(f"❌ Ana döngüde beklenmeyen hata: {e}")

if __name__ == "__main__":
    assistant = TerminalAssistant()
    assistant.run()